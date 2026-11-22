"""Unit and integration tests for Automated Uptime Monitoring & Price Refresh."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from health import get_health_status, VERSION, SERVICE_NAME
from database import (
    load_refresh_status, dump_refresh_status, calculate_next_refresh,
    DEFAULT_REFRESH_STATUS,
)
from checker import run_price_check, is_refresh_running, _refresh_lock
from scheduler import start_price_refresh_scheduler, stop_scheduler


def test_health_check_payload_contract():
    """Verify health endpoint strictly matches the required specification."""
    status = get_health_status()
    assert isinstance(status, dict)
    assert status.get("status") == "healthy"
    assert status.get("service") == "GameTracker"
    assert "timestamp" in status
    assert "version" in status
    assert status["version"] == VERSION
    # No sensitive credentials exposed
    for forbidden in ("token", "password", "secret", "email"):
        for k in status.keys():
            assert forbidden not in k.lower()


def test_refresh_status_serialization():
    """Verify refresh_status serialization and deserialization."""
    default_status = load_refresh_status("")
    assert default_status["status"] == "idle"
    assert default_status["refresh_interval_hours"] == 6

    corrupt_status = load_refresh_status("NOT_JSON{{{")
    assert corrupt_status["status"] == "idle"

    custom_data = {
        "last_automatic_refresh": "2026-11-22T10:00:00+00:00",
        "next_scheduled_refresh": "2026-11-22T16:00:00+00:00",
        "status": "success",
        "games_checked": 5,
        "successful_checks": 5,
        "failed_checks": 0,
        "refresh_interval_hours": 6,
    }
    json_str = dump_refresh_status(custom_data)
    loaded = load_refresh_status(json_str)
    assert loaded["last_automatic_refresh"] == "2026-11-22T10:00:00+00:00"
    assert loaded["status"] == "success"
    assert loaded["games_checked"] == 5


def test_calculate_next_refresh_timing():
    """Verify calculate_next_refresh produces human-readable UTC timestamps."""
    last_iso = "2026-11-22T12:00:00+00:00"
    last_disp, next_disp = calculate_next_refresh(last_iso, interval_hours=6)
    assert "22 Nov 2026, 12:00 UTC" in last_disp
    assert "22 Nov 2026, 18:00 UTC" in next_disp

    # Fallback when None
    fallback_last, fallback_next = calculate_next_refresh(None, interval_hours=6)
    assert fallback_last == "Pending first run"
    assert "UTC" in fallback_next


def test_prevent_overlapping_refresh_runs():
    """Ensure run_price_check aborts if a refresh job is already active."""
    mock_gh = MagicMock()
    # Acquire the lock manually to simulate concurrent run
    acquired = _refresh_lock.acquire(blocking=False)
    assert acquired is True
    try:
        assert is_refresh_running() is True
        result = run_price_check(mock_gh)
        assert result.get("status") == "skipped"
        assert result.get("reason") == "overlapping_job_in_progress"
    finally:
        _refresh_lock.release()
    assert is_refresh_running() is False


def test_run_price_check_per_game_failure_isolation():
    """Ensure failure in one game does not halt refresh for other games, and valid prices are never lost."""
    mock_gh = MagicMock()

    sample_games = [
        {
            "id": "steam_10",
            "name": "Counter-Strike",
            "store": "steam",
            "url": "https://store.steampowered.com/app/10",
            "current_price": 500.0,
            "currency": "₹",
            "lowest_price": 400.0,
            "target_price": 300.0,
        },
        {
            "id": "epic_broken",
            "name": "Broken Game",
            "store": "epic",
            "url": "https://store.epicgames.com/p/broken",
            "current_price": 1200.0,
            "currency": "₹",
            "lowest_price": 1200.0,
        },
    ]

    mock_gh.get_file_content.side_effect = lambda filename: {
        "games.json": json.dumps(sample_games),
        "history.json": json.dumps({}),
    }.get(filename, None)

    saved_files = {}

    def mock_save_file(path, content, msg):
        saved_files[path] = content

    mock_gh.save_file.side_effect = mock_save_file

    from price_api import GameDetails
    mock_details_good = GameDetails(
        name="Counter-Strike",
        current_price=450.0,
        original_price=500.0,
        currency="₹",
        is_on_sale=True,
        discount_percent=10,
        cover_image="",
        sale_end=None,
    )

    def mock_fetch(store, url):
        if store == "steam":
            return mock_details_good
        raise RuntimeError("Store network timeout")

    with patch("price_api.fetch_game_details", side_effect=mock_fetch):
        summary = run_price_check(gh=mock_gh, rate_limit_delay=0.0, is_auto=True)

    assert summary["games_checked"] == 2
    assert summary["successful_checks"] == 1
    assert summary["failed_checks"] == 1
    assert summary["status"] == "partial"

    # Confirm games.json was saved and broken game retained its previous valid price (1200.0)
    saved_games = json.loads(saved_files["games.json"])
    assert len(saved_games) == 2
    cs = next(g for g in saved_games if g["id"] == "steam_10")
    broken = next(g for g in saved_games if g["id"] == "epic_broken")
    assert cs["current_price"] == 450.0
    assert broken["current_price"] == 1200.0  # NOT overwritten with None!

    # Confirm refresh_status.json was written
    assert "refresh_status.json" in saved_files
    saved_status = json.loads(saved_files["refresh_status.json"])
    assert saved_status["successful_checks"] == 1
    assert saved_status["failed_checks"] == 1


def test_scheduler_registration_and_stop():
    """Verify price refresh scheduler can be started without duplicating jobs."""
    mock_gh = MagicMock()
    try:
        started_1 = start_price_refresh_scheduler(mock_gh, interval_hours=6)
        assert started_1 is True

        # Second invocation should detect existing job and return True without duplication
        started_2 = start_price_refresh_scheduler(mock_gh, interval_hours=6)
        assert started_2 is True
    finally:
        stop_scheduler()
