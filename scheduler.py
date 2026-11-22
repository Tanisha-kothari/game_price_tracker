import logging
import os
import atexit
from typing import Optional, Any

from database import load_games, load_history, migrate_games, migrate_history
from notifier import send_daily_report

logger = logging.getLogger(__name__)

_scheduler = None


def _parse_time(send_time: str) -> tuple[int, int]:
    parts = send_time.strip().split(":")
    hour = int(parts[0]) if len(parts) > 0 else 9
    minute = int(parts[1]) if len(parts) > 1 else 0
    return max(0, min(23, hour)), max(0, min(59, minute))


def _get_or_create_scheduler():
    global _scheduler
    if _scheduler is None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            _scheduler = BackgroundScheduler(daemon=True)
            _scheduler.start()
            atexit.register(lambda: _scheduler.shutdown(wait=False) if _scheduler else None)
        except ImportError:
            logger.error("apscheduler not installed; scheduler disabled. Add 'apscheduler>=3.10.0' to requirements.txt")
            return None
    return _scheduler


def _get_daily_report_job(gh, email_config, **kwargs):
    def job():
        try:
            logger.info("Daily report job: fetching games, history, and preferences from GitHub")
            games_raw = gh.get_file_content("games.json")
            history_raw = gh.get_file_content("history.json")
            prefs_raw = gh.get_file_content("email_preferences.json")

            from database import load_email_preferences
            prefs = load_email_preferences(prefs_raw) if prefs_raw else None

            games = load_games(games_raw) if games_raw else []
            history = load_history(history_raw) if history_raw else {}
            games, _ = migrate_games(games)
            history, _ = migrate_history(history, games)
            if not games:
                logger.info("Daily report job: no tracked games, skipping report")
                return

            recipient = (prefs.get("recipient_email") if prefs and prefs.get("recipient_email") else None) or email_config.get("to_address", email_config["address"])

            logger.info("Daily report job: sending report for %d games to %s", len(games), recipient)
            send_daily_report(
                email_config["address"],
                email_config["password"],
                recipient,
                games,
                history,
                prefs=prefs,
                smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_config.get("smtp_port", 587),
            )
        except Exception:
            logger.exception("Daily report job failed")
    return job


def start_daily_report_scheduler(
    gh,
    email_address: str,
    email_password: str,
    to_address: Optional[str] = None,
    send_time: str = "09:00",
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> bool:
    sched = _get_or_create_scheduler()
    if sched is None:
        return False

    job_id = "daily_report_job"
    if sched.get_job(job_id):
        logger.info("Daily report job already registered in scheduler")
        return True

    hour, minute = _parse_time(send_time)
    email_config = {
        "address": email_address,
        "password": email_password,
        "to_address": to_address or email_address,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
    }

    job_fn = _get_daily_report_job(gh, email_config)
    sched.add_job(
        job_fn,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id,
        misfire_grace_time=600,
        replace_existing=True,
    )
    logger.info("Daily report scheduler started; will send at %02d:%02d daily", hour, minute)
    return True


def start_price_refresh_scheduler(
    gh,
    interval_hours: int = 6,
    email_config: Optional[dict] = None,
) -> bool:
    """Start an automated price refresh job running every interval_hours (default: 6 hours).

    Uses the canonical price refresh engine from checker.py.
    Guarded by concurrency lock to prevent overlapping runs.
    """
    sched = _get_or_create_scheduler()
    if sched is None:
        return False

    job_id = "automated_price_refresh_job"
    if sched.get_job(job_id):
        logger.info("Price refresh job '%s' already registered in scheduler", job_id)
        return True

    from checker import run_price_check

    def _price_refresh_job():
        logger.info("Scheduler: Executing automated price refresh (every %d hours)...", interval_hours)
        try:
            addr = email_config.get("address") if email_config else None
            pwd = email_config.get("password") if email_config else None
            to = email_config.get("to_address") if email_config else None
            run_price_check(
                gh=gh,
                email_address=addr,
                email_password=pwd,
                notify_to=to,
                is_auto=True,
                interval_hours=interval_hours,
            )
        except Exception:
            logger.exception("Scheduler: Automated price refresh job failed")

    try:
        sched.add_job(
            _price_refresh_job,
            trigger="interval",
            hours=interval_hours,
            id=job_id,
            misfire_grace_time=3600,
            replace_existing=True,
        )
        logger.info("Price refresh scheduler job registered (interval: %d hours)", interval_hours)
        return True
    except Exception as e:
        logger.error("Failed to register price refresh job: %s", e)
        return False


def stop_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
        logger.info("Daily report scheduler stopped")
