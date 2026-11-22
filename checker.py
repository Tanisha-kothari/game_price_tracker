#!/usr/bin/env python3
"""Automated price checker — runs via GitHub Actions or in-app scheduler to check all tracked game prices.

Features:
- Single canonical price refresh implementation
- Prevents overlapping refresh executions via threading locks
- Polite per-store rate limiting (1.0s delay between requests)
- Graceful per-game failure isolation (one failure never halts the batch)
- Valid prices are never overwritten with None/failed fetches
- Synchronizes games.json, history.json, and refresh_status.json via GitHubManager
- Detects price drops, new historic lows, and new sales without duplicate notifications
"""
from __future__ import annotations

import os
import sys
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("checker")

# Global lock to prevent overlapping runs within the same process
_refresh_lock = threading.Lock()


def is_refresh_running() -> bool:
    """Check if a price refresh job is currently in progress."""
    return _refresh_lock.locked()


def run_price_check(
    gh: Any,
    email_address: Optional[str] = None,
    email_password: Optional[str] = None,
    notify_to: Optional[str] = None,
    send_unchanged: bool = False,
    rate_limit_delay: float = 1.0,
    is_auto: bool = True,
    interval_hours: int = 6,
) -> dict[str, Any]:
    """Execute the canonical price check across all tracked games.

    Returns a summary dict containing status, counts, and alert details.
    """
    acquired = _refresh_lock.acquire(blocking=False)
    if not acquired:
        logger.warning("Price refresh already in progress. Skipping overlapping job execution.")
        return {
            "status": "skipped",
            "reason": "overlapping_job_in_progress",
            "message": "A refresh job is currently running.",
        }

    try:
        from database import (
            load_games, load_history, update_price_history,
            detect_price_change, dump_games, dump_history,
            migrate_games, migrate_history, get_price_currency, apply_game_update,
            dump_refresh_status, load_refresh_status,
        )
        from price_api import fetch_game_details
        from notifier import send_price_alert, send_summary_email, send_sale_alert
        from utils import format_price

        logger.info("Fetching game records from GitHub...")
        games_raw = gh.get_file_content("games.json")
        games = load_games(games_raw) if games_raw else []

        if not games:
            logger.info("No games tracked in games.json. Nothing to check.")
            now_iso = datetime.now(timezone.utc).isoformat()
            next_iso = (datetime.now(timezone.utc) + timedelta(hours=interval_hours)).isoformat()
            status_data = {
                "last_automatic_refresh": now_iso,
                "next_scheduled_refresh": next_iso,
                "status": "success",
                "games_checked": 0,
                "successful_checks": 0,
                "failed_checks": 0,
                "refresh_interval_hours": interval_hours,
            }
            try:
                gh.save_file("refresh_status.json", dump_refresh_status(status_data), "chore: update refresh status")
            except Exception as e:
                logger.debug("Could not save refresh_status.json: %s", e)
            return status_data

        history_raw = gh.get_file_content("history.json")
        history = load_history(history_raw) if history_raw else {}

        games, games_migrated = migrate_games(games)
        history, history_migrated = migrate_history(history, games)

        logger.info("Refreshing prices for %d game(s) with %.1fs polite delay...", len(games), rate_limit_delay)
        alerts: list[dict[str, Any]] = []
        any_change = False
        ok_count = 0
        failed_count = 0

        for idx, game in enumerate(games):
            game_id = game.get("id", f"game_{idx}")
            store = game.get("store", "")
            url = game.get("url", "")
            name = game.get("name", "Unknown Game")
            target_price = game.get("target_price")
            target_currency = get_price_currency(game, "target_price")

            # Polite rate limiting between store requests
            if idx > 0 and rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

            try:
                details = fetch_game_details(store, url)
            except Exception as e:
                logger.error("Failed to check price for '%s' (%s, store: %s): %s", name, game_id, store, e)
                failed_count += 1
                continue

            events = apply_game_update(game, details)
            currency = get_price_currency(game, "current_price")
            price = game.get("current_price")

            if details.current_price is not None:
                ok_count += 1
                history = update_price_history(
                    history, game_id, price, currency,
                    is_on_sale=game.get("is_on_sale"),
                    discount_percent=game.get("discount_percent"),
                )
            else:
                failed_count += 1
                logger.warning("Could not fetch price for '%s' (%s) — keeping last known price", name, game_id)

            diff = detect_price_change(history, game_id, price, currency)
            is_new_low = events.get("new_low", False)
            prev_price = (price - diff) if (diff is not None and price is not None) else None

            alert = {
                "name": name,
                "store": store,
                "price": format_price(price, currency),
                "prev_price": prev_price,
                "current_price": price,
                "diff": diff,
                "diff_str": format_price(abs(diff), currency) if diff is not None else None,
                "game_id": game_id,
                "currency": currency,
                "cover_image": game.get("cover_image", ""),
                "lowest_price": game.get("lowest_price"),
                "lowest_currency": get_price_currency(game, "lowest_price"),
                "target_price": target_price,
                "target_currency": target_currency,
                "is_on_sale": game.get("is_on_sale", False),
                "original_price": game.get("original_price"),
                "discount_percent": game.get("discount_percent", 0),
            }

            flagged = any(events.values())
            if flagged:
                any_change = True
                alerts.append(alert)

            # Notifications only when changes detected
            if not flagged or not email_address or not email_password:
                continue

            try:
                recipient = notify_to or email_address
                if events.get("sale_detected") or events.get("discount_increased") or events.get("discount_changed"):
                    send_sale_alert(
                        email_address, email_password, recipient,
                        name, store, price, game.get("original_price"),
                        game.get("discount_percent") or 0, game.get("cover_image", ""),
                        currency, sale_started=bool(events.get("sale_detected")),
                    )
                if events.get("price_changed") and diff is not None:
                    send_price_alert(
                        email_address, email_password, recipient,
                        name, store, price, prev_price, diff,
                        game.get("lowest_price"),
                        get_price_currency(game, "lowest_price"),
                        target_price, target_currency,
                        game.get("cover_image", ""), currency, is_new_low,
                    )
                elif is_new_low:
                    send_price_alert(
                        email_address, email_password, recipient,
                        name, store, price, prev_price, 0,
                        game.get("lowest_price"),
                        get_price_currency(game, "lowest_price"),
                        target_price, target_currency,
                        game.get("cover_image", ""), currency, True,
                    )
            except Exception as e:
                logger.error("Failed to send email alert for '%s': %s", name, e)

        # Commit updated databases
        commit_msg = "chore: update game prices"
        if games_migrated or history_migrated:
            commit_msg = "chore: migrate and update game prices"
        if is_auto:
            commit_msg = f"chore(auto): refresh prices (ok: {ok_count}, failed: {failed_count})"

        gh.save_file("games.json", dump_games(games), commit_msg)
        gh.save_file("history.json", dump_history(history), "chore: update price history")

        # Update refresh status metadata
        now_iso = datetime.now(timezone.utc).isoformat()
        next_iso = (datetime.now(timezone.utc) + timedelta(hours=interval_hours)).isoformat()
        status_str = "success" if failed_count == 0 else ("partial" if ok_count > 0 else "failed")
        status_data = {
            "last_automatic_refresh": now_iso,
            "next_scheduled_refresh": next_iso,
            "status": status_str,
            "games_checked": len(games),
            "successful_checks": ok_count,
            "failed_checks": failed_count,
            "refresh_interval_hours": interval_hours,
        }
        try:
            gh.save_file("refresh_status.json", dump_refresh_status(status_data), "chore: update refresh status")
        except Exception as e:
            logger.warning("Failed to save refresh_status.json: %s", e)

        # Summary email handling
        recipient = notify_to or email_address
        if not any_change and send_unchanged and email_address and email_password:
            try:
                send_summary_email(email_address, email_password, recipient, [], len(games))
            except Exception as e:
                logger.error("Failed to send unchanged summary email: %s", e)

        if any_change and email_address and email_password:
            unchanged_count = len(games) - len(alerts)
            try:
                send_summary_email(email_address, email_password, recipient, alerts, unchanged_count)
            except Exception as e:
                logger.error("Failed to send summary email: %s", e)

        logger.info("Price refresh completed: %d ok, %d failed out of %d games.", ok_count, failed_count, len(games))
        return status_data

    finally:
        _refresh_lock.release()


def main() -> None:
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo_owner = os.environ.get("REPO_OWNER")
    repo_name = os.environ.get("REPO_NAME")
    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")
    notify_to = os.environ.get("NOTIFY_TO") or email_address
    send_unchanged = os.environ.get("SEND_UNCHANGED_SUMMARY", "").lower() in ("true", "1", "yes")

    missing = []
    if not github_token:
        missing.append("GITHUB_TOKEN")
    if not repo_owner:
        missing.append("REPO_OWNER")
    if not repo_name:
        missing.append("REPO_NAME")

    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    from github_manager import GitHubManager
    gh = GitHubManager(github_token, repo_owner, repo_name)
    result = run_price_check(
        gh=gh,
        email_address=email_address,
        email_password=email_password,
        notify_to=notify_to,
        send_unchanged=send_unchanged,
        is_auto=True,
        interval_hours=6,
    )
    if result.get("status") == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
