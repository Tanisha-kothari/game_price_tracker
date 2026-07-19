#!/usr/bin/env python3
"""Daily price checker — runs via GitHub Actions to check all tracked game prices."""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("checker")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
REPO_OWNER = os.environ.get("REPO_OWNER")
REPO_NAME = os.environ.get("REPO_NAME")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
NOTIFY_TO = os.environ.get("NOTIFY_TO") or EMAIL_ADDRESS
SEND_UNCHANGED = os.environ.get("SEND_UNCHANGED_SUMMARY", "").lower() in ("true", "1", "yes")


def main():
    missing = []
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not REPO_OWNER:
        missing.append("REPO_OWNER")
    if not REPO_NAME:
        missing.append("REPO_NAME")

    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    from github_manager import GitHubManager
    from database import (
        load_games, load_history, update_game_price, update_price_history,
        detect_price_change, dump_games, dump_history,
        migrate_games, migrate_history, get_price_currency, is_lower_price,
    )
    from price_api import fetch_game_details
    from notifier import send_price_alert, send_summary_email
    from utils import format_price

    gh = GitHubManager(GITHUB_TOKEN, REPO_OWNER, REPO_NAME)

    logger.info("Fetching games from GitHub...")
    games_raw = gh.get_file_content("games.json")
    games = load_games(games_raw) if games_raw else []

    if not games:
        logger.info("No games tracked. Nothing to check.")
        return

    history_raw = gh.get_file_content("history.json")
    history = load_history(history_raw) if history_raw else {}

    games, games_migrated = migrate_games(games)
    history, history_migrated = migrate_history(history, games)

    if games_migrated:
        logger.info("Migrated games to per-price currency model")
    if history_migrated:
        logger.info("Migrated history currency data")

    logger.info("Checking prices for %d game(s)...", len(games))
    alerts = []
    any_change = False

    for game in games:
        game_id = game["id"]
        store = game["store"]
        url = game["url"]
        name = game["name"]
        target_price = game.get("target_price")
        target_currency = get_price_currency(game, "target_price")

        try:
            details = fetch_game_details(store, url)
        except Exception as e:
            logger.error("Failed to check price for %s (%s): %s", name, game_id, e)
            continue

        price = details.current_price
        currency = details.currency

        if price is None:
            logger.warning("Could not fetch price for %s (%s)", name, game_id)
            continue

        old_lowest = game.get("lowest_price")
        old_lowest_currency = get_price_currency(game, "lowest_price")

        games = update_game_price(games, game_id, price, currency)
        history = update_price_history(history, game_id, price, currency)

        updated = next(g for g in games if g["id"] == game_id)
        diff = detect_price_change(history, game_id, price, currency)
        is_new_low = (
            old_lowest is not None
            and is_lower_price(price, currency, old_lowest, old_lowest_currency)
        )

        if diff is not None:
            any_change = True
            prev_price = price - diff
            alerts.append({
                "name": name,
                "store": store,
                "price": format_price(price, currency),
                "prev_price": prev_price,
                "current_price": price,
                "diff": diff,
                "diff_str": format_price(abs(diff), currency),
                "game_id": game_id,
                "currency": currency,
                "cover_image": game.get("cover_image", ""),
                "lowest_price": updated.get("lowest_price"),
                "lowest_currency": get_price_currency(updated, "lowest_price"),
                "target_price": target_price,
                "target_currency": target_currency,
                "is_new_low": is_new_low,
            })
            logger.info("Price changed for %s: diff=%s", name, format_price(diff, currency))

            if EMAIL_ADDRESS and EMAIL_PASSWORD:
                try:
                    send_price_alert(
                        EMAIL_ADDRESS, EMAIL_PASSWORD, NOTIFY_TO,
                        name, store, price, prev_price, diff,
                        updated.get("lowest_price"),
                        get_price_currency(updated, "lowest_price"),
                        target_price, target_currency,
                        game.get("cover_image", ""), currency, is_new_low,
                    )
                except Exception as e:
                    logger.error("Failed to send alert email for %s: %s", name, e)

    commit_msg = "chore: update game prices"
    if games_migrated or history_migrated:
        commit_msg = "chore: migrate and update game prices"

    updated_games_content = dump_games(games)
    gh.save_file("games.json", updated_games_content, commit_msg)

    updated_history_content = dump_history(history)
    gh.save_file("history.json", updated_history_content, "chore: update price history")

    logger.info("Price check complete.")

    if not any_change and SEND_UNCHANGED and EMAIL_ADDRESS and EMAIL_PASSWORD:
        logger.info("No price changes, sending summary email...")
        try:
            send_summary_email(EMAIL_ADDRESS, EMAIL_PASSWORD, NOTIFY_TO, [], len(games))
        except Exception as e:
            logger.error("Failed to send summary email: %s", e)

    if any_change and EMAIL_ADDRESS and EMAIL_PASSWORD:
        unchanged_count = len(games) - len(alerts)
        try:
            send_summary_email(EMAIL_ADDRESS, EMAIL_PASSWORD, NOTIFY_TO, alerts, unchanged_count)
        except Exception as e:
            logger.error("Failed to send summary email: %s", e)


if __name__ == "__main__":
    main()
