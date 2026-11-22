"""Comprehensive tests for WhatsApp and Discord Bots and the Shared Service Layer."""
from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch
import pytest

from bot_service import GameTrackerService, get_service
from discord_bot import (
    build_tracked_embed, build_game_embed, build_owned_embed,
    build_deals_embed, build_search_embed, build_help_embed,
    create_discord_bot, StoreButtonView, get_authorized_user_ids,
)
from whatsapp_bot import (
    verify_whatsapp_signature, verify_webhook_subscription,
    handle_whatsapp_command, format_deals_message, format_game_message,
    format_tracked_message, format_owned_message, format_help_message,
    process_webhook_payload, normalize_phone_number,
)


@pytest.fixture
def mock_service_data():
    """Sample games and library data for service layer tests."""
    games = [
        {
            "id": "steam_489830",
            "name": "The Elder Scrolls V: Skyrim Special Edition",
            "store": "steam",
            "url": "https://store.steampowered.com/app/489830/",
            "current_price": 449.0,
            "currency": "₹",
            "original_price": 1799.0,
            "lowest_price": 449.0,
            "discount_percent": 75,
            "is_on_sale": True,
            "last_checked": "2026-11-22 06:00:00 UTC",
            "cover_image": "https://cdn.akamai.steamstatic.com/steam/apps/489830/header.jpg",
            "custom_tags": ["rpg", "open-world"],
        },
        {
            "id": "epic_survivalists",
            "name": "The Survivalists",
            "store": "epic",
            "url": "https://store.epicgames.com/p/the-survivalists",
            "current_price": 399.0,
            "currency": "₹",
            "original_price": 1999.0,
            "lowest_price": 350.0,
            "discount_percent": 80,
            "is_on_sale": True,
            "last_checked": "2026-11-22 06:00:00 UTC",
            "cover_image": "",
            "custom_tags": ["survival", "co-op"],
        },
        {
            "id": "steam_10",
            "name": "Counter-Strike",
            "store": "steam",
            "url": "https://store.steampowered.com/app/10/",
            "current_price": 500.0,
            "currency": "₹",
            "original_price": 500.0,
            "lowest_price": 250.0,
            "discount_percent": 0,
            "is_on_sale": False,
            "last_checked": "2026-11-22 06:00:00 UTC",
            "cover_image": "",
        },
    ]

    purchased = [
        {
            "id": "purchased_1",
            "title": "Elden Ring",
            "store": "steam",
            "purchase_date": "2026-01-15",
            "purchase_price": 2499.0,
            "currency": "₹",
            "notes": "Deluxe Edition",
        }
    ]

    mock_gh = MagicMock()
    mock_gh.get_file_content.side_effect = lambda filename: {
        "games.json": json.dumps(games),
        "history.json": json.dumps({}),
        "purchased_games.json": json.dumps(purchased),
    }.get(filename, None)

    return GameTrackerService(gh=mock_gh)


# ── 1. Shared Service Layer Tests ────────────────────────────────────

def test_service_get_tracked_games(mock_service_data):
    games = mock_service_data.get_tracked_games()
    assert len(games) == 3
    names = [g["name"] for g in games]
    assert "The Survivalists" in names


def test_service_get_game_details_exact_and_fuzzy(mock_service_data):
    # Fuzzy match on Skyrim
    details = mock_service_data.get_game_details("Skyrim")
    assert details is not None
    assert "Skyrim" in details["name"]
    assert details["store"] == "steam"
    assert details["current_price"] == 449.0
    assert details["discount_percent"] == 75
    assert details["is_on_sale"] is True
    assert details["status"] == "On Sale"

    # Not found
    none_game = mock_service_data.get_game_details("NonExistentGameXYZ")
    assert none_game is None


def test_service_get_purchased_games(mock_service_data):
    purchased = mock_service_data.get_purchased_games()
    assert len(purchased) == 1
    assert purchased[0]["name"] == "Elden Ring"
    assert purchased[0]["purchase_price"] == 2499.0


def test_service_get_active_deals_sorted_by_discount(mock_service_data):
    deals = mock_service_data.get_active_deals()
    assert len(deals) == 2
    # Survivalists has 80% discount, Skyrim has 75% -> Survivalists must be first
    assert deals[0]["name"] == "The Survivalists"
    assert deals[0]["discount_percent"] == 80
    assert deals[1]["discount_percent"] == 75


def test_service_search_tracked_games(mock_service_data):
    results = mock_service_data.search_tracked_games("survival")
    assert len(results) == 1
    assert results[0]["name"] == "The Survivalists"

    # Search by store
    steam_results = mock_service_data.search_tracked_games("steam")
    assert len(steam_results) == 2


def test_service_refresh_authorization_and_cooldown(mock_service_data):
    # Unauthorized request must be rejected
    unauth_res = mock_service_data.refresh_all_prices("user_123", is_authorized=False)
    assert unauth_res["success"] is False
    assert unauth_res["status"] == "unauthorized"

    # Authorized request with mock price check
    with patch("bot_service.run_price_check") as mock_check:
        mock_check.return_value = {
            "status": "success",
            "games_checked": 3,
            "successful_checks": 3,
            "failed_checks": 0,
        }
        res1 = mock_service_data.refresh_all_prices("user_admin", is_authorized=True, cooldown_seconds=60)
        assert res1["success"] is True
        assert res1["status"] == "success"

        # Immediate follow-up request must trigger cooldown
        res2 = mock_service_data.refresh_all_prices("user_admin", is_authorized=True, cooldown_seconds=60)
        assert res2["success"] is False
        assert res2["status"] == "cooldown"
        assert res2["remaining_seconds"] > 0


# ── 2. Discord Bot Tests ─────────────────────────────────────────────

def test_discord_embed_builders(mock_service_data):
    games = mock_service_data.get_tracked_games()
    tracked_embed = build_tracked_embed(games)
    assert "Tracked Games Radar" in tracked_embed.title
    assert len(tracked_embed.fields) == 3

    skyrim = mock_service_data.get_game_details("Skyrim")
    game_embed, view = build_game_embed(skyrim)
    assert "Skyrim" in game_embed.title
    assert view is not None
    assert len(view.children) == 1  # Store button

    purchased = mock_service_data.get_purchased_games()
    owned_embed = build_owned_embed(purchased)
    assert "My Library" in owned_embed.title

    deals = mock_service_data.get_active_deals()
    deals_embed = build_deals_embed(deals)
    assert "Hot Deals" in deals_embed.title

    search_matches = mock_service_data.search_tracked_games("survival")
    search_embed = build_search_embed("survival", search_matches)
    assert "Search Results" in search_embed.title

    help_embed = build_help_embed()
    assert "Command Guide" in help_embed.title
    command_names = [f.name for f in help_embed.fields]
    assert "`/tracked`" in command_names
    assert "`/refresh`" in command_names


def test_discord_bot_tree_commands():
    bot = create_discord_bot(authorized_users={12345, 67890})
    # Verify slash commands registered on command tree
    registered = [cmd.name for cmd in bot.tree.get_commands()]
    assert "tracked" in registered
    assert "game" in registered
    assert "owned" in registered
    assert "deals" in registered
    assert "search" in registered
    assert "refresh" in registered
    assert "help" in registered


# ── 3. WhatsApp Bot Tests ────────────────────────────────────────────

def test_whatsapp_webhook_verification():
    # Valid subscription challenge
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "my_secret_token",
        "hub.challenge": "1158201244",
    }
    status, body = verify_webhook_subscription(params, expected_verify_token="my_secret_token")
    assert status == 200
    assert body == "1158201244"

    # Mismatch token
    status_bad, body_bad = verify_webhook_subscription(params, expected_verify_token="wrong_token")
    assert status_bad == 403


def test_whatsapp_hmac_signature_verification():
    secret = "secret_app_key_123"
    body = b'{"object": "whatsapp_business_account"}'
    import hmac, hashlib
    expected_hex = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    valid_header = f"sha256={expected_hex}"

    assert verify_whatsapp_signature(body, valid_header, secret) is True
    assert verify_whatsapp_signature(body, "sha256=invalidhex", secret) is False
    assert verify_whatsapp_signature(body, "", secret) is False


def test_whatsapp_commands_and_authorizations(mock_service_data):
    auth_numbers = {"919876543210"}

    # 1. TRACKED
    res_tracked = handle_whatsapp_command("TRACKED", "919876543210", service=mock_service_data)
    assert "TRACKED GAMES" in res_tracked["body"]
    assert "Skyrim" in res_tracked["body"]

    # 2. GAME <title>
    res_game = handle_whatsapp_command("GAME Skyrim", "919876543210", service=mock_service_data)
    assert "The Elder Scrolls V: Skyrim" in res_game["body"]
    assert "Current Price:" in res_game["body"]

    # 3. DEALS
    res_deals = handle_whatsapp_command("DEALS", "919876543210", service=mock_service_data)
    assert "CURRENT DEALS" in res_deals["body"]
    assert "Skyrim" in res_deals["body"]

    # 4. SEARCH
    res_search = handle_whatsapp_command("SEARCH Survivalists", "919876543210", service=mock_service_data)
    assert "The Survivalists" in res_search["body"]

    # 5. OWNED: Authorized sender
    res_owned_auth = handle_whatsapp_command("OWNED", "919876543210", service=mock_service_data, authorized_numbers=auth_numbers)
    assert "Elden Ring" in res_owned_auth["body"]

    # 6. OWNED: Unauthorized sender rejection
    res_owned_unauth = handle_whatsapp_command("OWNED", "1111111111", service=mock_service_data, authorized_numbers=auth_numbers)
    assert "Access Denied" in res_owned_unauth["body"]

    # 7. REFRESH: Unauthorized sender rejection
    res_refresh_unauth = handle_whatsapp_command("REFRESH", "1111111111", service=mock_service_data, authorized_numbers=auth_numbers)
    assert "Access Denied" in res_refresh_unauth["body"]

    # 8. HELP
    res_help = handle_whatsapp_command("HELP", "919876543210", service=mock_service_data)
    assert "GAMETRACKER WHATSAPP ASSISTANT" in res_help["body"]


def test_whatsapp_process_webhook_payload(mock_service_data):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.12345",
                                    "timestamp": "1710000000",
                                    "text": {"body": "DEALS"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    body_bytes = json.dumps(payload).encode("utf-8")
    with patch("whatsapp_bot.send_whatsapp_message") as mock_send:
        mock_send.return_value = True
        status, resp = process_webhook_payload(
            body_bytes=body_bytes,
            signature_header="",
            config={"app_secret": ""},
            service=mock_service_data,
        )

        assert status == 200
        assert resp.get("status") == "ok"
        assert resp.get("messages_processed") == 1
        assert mock_send.called
        sent_args = mock_send.call_args[1]
        assert "CURRENT DEALS" in sent_args["message_text"]
