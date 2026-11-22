"""Shared Backend Service Layer for GameTracker.

Provides a unified business logic interface consumed by:
- Discord Bot (/tracked, /game, /owned, /deals, /search, /refresh)
- WhatsApp Bot (TRACKED, GAME, OWNED, DEALS, SEARCH, REFRESH)
- Streamlit Web Dashboard
"""
from __future__ import annotations

import os
import time
import logging
from typing import Any, Optional

from database import (
    load_games, load_history, migrate_games, migrate_history,
    load_purchased_games, get_price_currency,
)
from utils import format_price
from checker import run_price_check, is_refresh_running
from github_manager import GitHubManager

logger = logging.getLogger(__name__)

# In-memory cooldown tracking for bot price refreshes
_last_refresh_timestamp: float = 0.0
_last_refresher_id: str = ""
DEFAULT_REFRESH_COOLDOWN: int = 300  # 5 minutes


def init_github_client() -> Optional[GitHubManager]:
    """Attempt to initialize a GitHubManager instance from environment variables or Streamlit secrets."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    owner = os.environ.get("REPO_OWNER", "")
    repo = os.environ.get("REPO_NAME", "")

    if not token or not owner or not repo:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                token = token or st.secrets.get("GITHUB_TOKEN", "")
                owner = owner or st.secrets.get("REPO_OWNER", "")
                repo = repo or st.secrets.get("REPO_NAME", "")
        except Exception:
            pass

    if token and owner and repo:
        try:
            return GitHubManager(token, owner, repo)
        except Exception as e:
            logger.warning("Failed to initialize GitHubManager: %s", e)
    return None


class GameTrackerService:
    """Unified service layer wrapping GameTracker operations."""

    def __init__(self, gh: Optional[GitHubManager] = None) -> None:
        self.gh = gh or init_github_client()

    def _get_raw_content(self, filename: str) -> Optional[str]:
        """Fetch raw file content from GitHub or fallback to local disk."""
        if self.gh:
            try:
                content = self.gh.get_file_content(filename)
                if content:
                    return content
            except Exception as e:
                logger.debug("GitHub fetch error for %s: %s", filename, e)

        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error("Failed to read local %s: %s", filename, e)
        return None

    def get_tracked_games(self) -> list[dict[str, Any]]:
        """Retrieve all currently tracked games normalized and migrated."""
        raw = self._get_raw_content("games.json")
        games = load_games(raw) if raw else []
        games, _ = migrate_games(games)
        return games

    def get_game_details(self, query: str) -> Optional[dict[str, Any]]:
        """Find details of a specific game by exact or fuzzy title/name or ID."""
        if not query or not query.strip():
            return None
        q = query.strip().lower()
        games = self.get_tracked_games()
        if not games:
            return None

        # 1. Exact match by ID or Name
        exact = None
        for g in games:
            name = (g.get("name") or g.get("title") or "").strip().lower()
            gid = str(g.get("id", "")).strip().lower()
            if q == name or q == gid:
                exact = g
                break

        # 2. Substring match
        matched = exact
        if not matched:
            for g in games:
                name = (g.get("name") or g.get("title") or "").strip().lower()
                if q in name:
                    matched = g
                    break

        if not matched:
            return None

        curr = get_price_currency(matched, "current_price")
        lowest_curr = get_price_currency(matched, "lowest_price")
        orig_curr = get_price_currency(matched, "original_price")
        c_price = matched.get("current_price")
        low_price = matched.get("lowest_price")
        orig_price = matched.get("original_price")
        discount = matched.get("discount_percent") or 0
        is_sale = bool(matched.get("is_on_sale") or (discount and float(discount) > 0))

        return {
            "id": matched.get("id", ""),
            "name": matched.get("name") or matched.get("title") or "Unknown Game",
            "store": matched.get("store", "Store"),
            "current_price": c_price,
            "current_price_str": format_price(c_price, curr),
            "lowest_price": low_price,
            "lowest_price_str": format_price(low_price, lowest_curr),
            "original_price": orig_price,
            "original_price_str": format_price(orig_price, orig_curr),
            "discount_percent": int(discount) if discount else 0,
            "is_on_sale": is_sale,
            "status": "On Sale" if is_sale else "Normal",
            "target_price": matched.get("target_price"),
            "target_price_str": format_price(matched.get("target_price"), curr) if matched.get("target_price") else "None",
            "last_checked": matched.get("last_checked", "Never"),
            "url": matched.get("url", ""),
            "cover_image": matched.get("cover_image", ""),
            "currency": curr,
        }

    def get_purchased_games(self) -> list[dict[str, Any]]:
        """Retrieve purchased games from My Library."""
        raw = self._get_raw_content("purchased_games.json")
        purchased = load_purchased_games(raw) if raw else []
        results = []
        for p in purchased:
            price = p.get("purchase_price")
            curr = p.get("currency", "INR")
            results.append({
                "id": p.get("id", ""),
                "name": p.get("title") or p.get("name") or "Unknown Game",
                "store": p.get("store", "Store"),
                "purchase_date": p.get("purchase_date", "Unknown"),
                "purchase_price": price,
                "purchase_price_str": format_price(price, curr) if price is not None else "Not recorded",
                "notes": p.get("notes", ""),
                "currency": curr,
            })
        return results

    def get_active_deals(self) -> list[dict[str, Any]]:
        """Retrieve all currently discounted tracked games, sorted by highest discount."""
        games = self.get_tracked_games()
        deals = []
        for g in games:
            discount = g.get("discount_percent") or 0
            is_sale = bool(g.get("is_on_sale") or (discount and float(discount) > 0))
            if is_sale:
                curr = get_price_currency(g, "current_price")
                lowest_curr = get_price_currency(g, "lowest_price")
                orig_curr = get_price_currency(g, "original_price")
                deals.append({
                    "id": g.get("id", ""),
                    "name": g.get("name") or g.get("title") or "Unknown Game",
                    "store": g.get("store", "Store"),
                    "current_price": g.get("current_price"),
                    "current_price_str": format_price(g.get("current_price"), curr),
                    "lowest_price": g.get("lowest_price"),
                    "lowest_price_str": format_price(g.get("lowest_price"), lowest_curr),
                    "original_price": g.get("original_price"),
                    "original_price_str": format_price(g.get("original_price"), orig_curr),
                    "discount_percent": int(discount) if discount else 0,
                    "is_on_sale": True,
                    "url": g.get("url", ""),
                    "cover_image": g.get("cover_image", ""),
                    "last_checked": g.get("last_checked", "Unknown"),
                })
        deals.sort(key=lambda d: d.get("discount_percent", 0), reverse=True)
        return deals

    def search_tracked_games(self, query: str) -> list[dict[str, Any]]:
        """Search tracked games collection by name, store, or tag."""
        if not query or not query.strip():
            return []
        q = query.strip().lower()
        games = self.get_tracked_games()
        matches = []
        for g in games:
            name = (g.get("name") or g.get("title") or "").lower()
            store = (g.get("store") or "").lower()
            tags = [t.lower() for t in g.get("custom_tags", [])]
            if q in name or q in store or any(q in t for t in tags):
                curr = get_price_currency(g, "current_price")
                lowest_curr = get_price_currency(g, "lowest_price")
                discount = g.get("discount_percent") or 0
                matches.append({
                    "id": g.get("id", ""),
                    "name": g.get("name") or g.get("title") or "Unknown Game",
                    "store": g.get("store", "Store"),
                    "current_price": g.get("current_price"),
                    "current_price_str": format_price(g.get("current_price"), curr),
                    "lowest_price": g.get("lowest_price"),
                    "lowest_price_str": format_price(g.get("lowest_price"), lowest_curr),
                    "discount_percent": int(discount) if discount else 0,
                    "is_on_sale": bool(g.get("is_on_sale") or (discount and float(discount) > 0)),
                    "url": g.get("url", ""),
                    "cover_image": g.get("cover_image", ""),
                })
        return matches

    def refresh_all_prices(
        self,
        requester_id: str,
        is_authorized: bool,
        cooldown_seconds: int = DEFAULT_REFRESH_COOLDOWN,
    ) -> dict[str, Any]:
        """Trigger an application-wide price refresh with authorization, cooldown, and lock guards."""
        global _last_refresh_timestamp, _last_refresher_id

        # 1. Authorization check
        if not is_authorized:
            return {
                "status": "unauthorized",
                "success": False,
                "message": "🚫 You are not authorized to trigger an application-wide price refresh.",
            }

        # 2. Cooldown check
        now = time.time()
        elapsed = now - _last_refresh_timestamp
        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            return {
                "status": "cooldown",
                "success": False,
                "remaining_seconds": remaining,
                "message": f"⏳ Price refresh is on cooldown. Please wait {remaining} second(s) before requesting again.",
            }

        # 3. Active execution lock
        if is_refresh_running():
            return {
                "status": "busy",
                "success": False,
                "message": "⚠️ A price refresh job is already currently running. Please try again shortly.",
            }

        # 4. Check GitHub connection
        if not self.gh:
            return {
                "status": "error",
                "success": False,
                "message": "❌ GitHub connection not configured for price synchronization.",
            }

        try:
            summary = run_price_check(gh=self.gh, is_auto=False)
            if summary.get("status") == "skipped":
                return {
                    "status": "busy",
                    "success": False,
                    "message": "⚠️ Price refresh could not be started: another task is active.",
                }

            _last_refresh_timestamp = time.time()
            _last_refresher_id = requester_id

            ok_count = summary.get("successful_checks", 0)
            total_count = summary.get("games_checked", 0)
            failed_count = summary.get("failed_checks", 0)

            msg = f"✅ Price refresh completed: {ok_count}/{total_count} game(s) refreshed successfully."
            if failed_count > 0:
                msg += f" ({failed_count} store(s) kept last known prices)"

            return {
                "status": "success",
                "success": True,
                "message": msg,
                "summary": summary,
            }
        except Exception as e:
            logger.exception("Failed to execute refresh from bot service")
            return {
                "status": "error",
                "success": False,
                "message": f"❌ An error occurred during refresh: {str(e)}",
            }


# Singleton instance helper
_default_service: Optional[GameTrackerService] = None


def get_service(gh: Optional[GitHubManager] = None) -> GameTrackerService:
    global _default_service
    if gh is not None:
        return GameTrackerService(gh)
    if _default_service is None:
        _default_service = GameTrackerService()
    return _default_service
