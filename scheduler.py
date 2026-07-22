import logging
import os
import atexit
from typing import Optional

from database import load_games, load_history, migrate_games, migrate_history
from notifier import send_daily_report

logger = logging.getLogger(__name__)

_scheduler = None


def _parse_time(send_time: str) -> tuple[int, int]:
    parts = send_time.strip().split(":")
    hour = int(parts[0]) if len(parts) > 0 else 9
    minute = int(parts[1]) if len(parts) > 1 else 0
    return max(0, min(23, hour)), max(0, min(59, minute))


def _get_job(scheduler, gh, email_config, **kwargs):
    def job():
        try:
            logger.info("Daily report job: fetching games and history from GitHub")
            games_raw = gh.get_file_content("games.json")
            history_raw = gh.get_file_content("history.json")
            games = load_games(games_raw) if games_raw else []
            history = load_history(history_raw) if history_raw else {}
            games, _ = migrate_games(games)
            history, _ = migrate_history(history, games)
            if not games:
                logger.info("Daily report job: no tracked games, skipping report")
                return
            logger.info("Daily report job: sending report for %d games", len(games))
            send_daily_report(
                email_config["address"],
                email_config["password"],
                email_config.get("to_address", email_config["address"]),
                games,
                history,
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
):
    global _scheduler
    if _scheduler is not None:
        logger.info("Daily report scheduler already running")
        return False

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.error("apscheduler not installed; daily report disabled. Add 'apscheduler>=3.10.0' to requirements.txt")
        return False

    hour, minute = _parse_time(send_time)
    email_config = {
        "address": email_address,
        "password": email_password,
        "to_address": to_address or email_address,
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
    }

    _scheduler = BackgroundScheduler(daemon=True)
    job_fn = _get_job(_scheduler, gh, email_config)
    _scheduler.add_job(job_fn, trigger="cron", hour=hour, minute=minute, misfire_grace_time=600, replace_existing=True)
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    logger.info("Daily report scheduler started; will send at %02d:%02d daily", hour, minute)
    return True


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Daily report scheduler stopped")
