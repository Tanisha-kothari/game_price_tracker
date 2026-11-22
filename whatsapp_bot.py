"""WhatsApp Bot for GameTracker using Meta WhatsApp Cloud API.

Provides:
- Webhook verification (GET /whatsapp/webhook)
- Webhook signature validation (HMAC SHA-256 via X-Hub-Signature-256)
- Message dispatching & command parsing:
    TRACKED, GAME <name>, OWNED, DEALS, SEARCH <query>, REFRESH, HELP
- Clean, WhatsApp-formatted Markdown replies
- Interactive quick-reply buttons
- Security: Authorized sender filtering & refresh rate-limiting
"""
from __future__ import annotations

import os
import hmac
import hashlib
import logging
from typing import Any, Optional, Sequence
import requests

from bot_service import get_service, GameTrackerService

logger = logging.getLogger("whatsapp_bot")

DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes


def get_whatsapp_config() -> dict[str, str]:
    """Retrieve WhatsApp configuration from environment variables or Streamlit secrets."""
    token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
    app_secret = os.environ.get("WHATSAPP_APP_SECRET", "")
    auth_numbers_raw = os.environ.get("WHATSAPP_AUTHORIZED_NUMBERS", "")

    if not (token and phone_id and verify_token and app_secret):
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                token = token or str(st.secrets.get("WHATSAPP_ACCESS_TOKEN", ""))
                phone_id = phone_id or str(st.secrets.get("WHATSAPP_PHONE_NUMBER_ID", ""))
                verify_token = verify_token or str(st.secrets.get("WHATSAPP_VERIFY_TOKEN", ""))
                app_secret = app_secret or str(st.secrets.get("WHATSAPP_APP_SECRET", ""))
                auth_numbers_raw = auth_numbers_raw or str(st.secrets.get("WHATSAPP_AUTHORIZED_NUMBERS", ""))
        except Exception:
            pass

    return {
        "access_token": token,
        "phone_number_id": phone_id,
        "verify_token": verify_token,
        "app_secret": app_secret,
        "authorized_numbers": auth_numbers_raw,
    }


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number by removing non-digits."""
    return "".join(ch for ch in str(phone) if ch.isdigit())


def get_authorized_phone_numbers() -> set[str]:
    """Parse configured authorized phone numbers."""
    cfg = get_whatsapp_config()
    raw = cfg.get("authorized_numbers", "")
    numbers: set[str] = set()
    for item in raw.replace(",", " ").split():
        cleaned = normalize_phone_number(item)
        if cleaned:
            numbers.add(cleaned)
    return numbers


def verify_whatsapp_signature(body_bytes: bytes, signature_header: str, app_secret: str) -> bool:
    """Verify Meta's X-Hub-Signature-256 HMAC SHA256 header.

    Format: 'sha256=<hex_digest>'
    """
    if not app_secret or not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_sig = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, signature_header)


def format_tracked_message(games: Sequence[dict[str, Any]]) -> str:
    """Format tracked games into clean WhatsApp text."""
    if not games:
        return "🎮 *GAMETRACKER — TRACKED GAMES*\n\nNo games are currently tracked. Add games via the web dashboard!"

    lines = [
        "🎮 *GAMETRACKER — TRACKED GAMES*",
        f"Currently tracking *{len(games)}* game(s):\n",
    ]
    # Keep message size reasonable for WhatsApp
    for g in games[:15]:
        name = g.get("name") or g.get("title") or "Unknown Game"
        store = (g.get("store") or "Store").capitalize()
        price = g.get("current_price_str") or "N/A"
        lowest = g.get("lowest_price_str") or "N/A"
        discount = g.get("discount_percent") or 0
        is_sale = bool(g.get("is_on_sale") or (discount and float(discount) > 0))

        sale_badge = f" 🔥 *-{discount}% OFF*" if is_sale else ""
        lines.append(f"🕹️ *{name}*{sale_badge}")
        lines.append(f"• Store: {store}")
        lines.append(f"• Price: *{price}* _(Low: {lowest})_\n")

    if len(games) > 15:
        lines.append(f"_...and {len(games) - 15} more. View all on your web dashboard._")

    return "\n".join(lines).strip()


def format_game_message(game: dict[str, Any]) -> str:
    """Format single game details into clean WhatsApp text."""
    name = game.get("name", "Unknown Game")
    store = (game.get("store") or "Store").capitalize()
    c_price = game.get("current_price_str", "N/A")
    low_price = game.get("lowest_price_str", "N/A")
    orig_price = game.get("original_price_str")
    discount = game.get("discount_percent", 0)
    is_sale = game.get("is_on_sale", False)
    last_checked = game.get("last_checked", "Unknown")
    url = game.get("url", "")

    lines = [
        f"🎮 *{name}*\n",
        f"🏷️ *Store:* {store}",
        f"💰 *Current Price:* *{c_price}*",
        f"📉 *Lowest Recorded:* {low_price}",
    ]
    if is_sale:
        lines.append(f"🔥 *Discount:* {discount}%")
        if orig_price:
            lines.append(f"🏷️ *Original:* ~{orig_price}~")
        lines.append("🎉 *Status:* On Sale")
    else:
        lines.append("🟢 *Status:* Regular Price")

    if game.get("target_price"):
        lines.append(f"🎯 *Target Price:* {game.get('target_price_str')}")

    lines.append(f"⏱️ *Last Checked:* {last_checked}")
    if url:
        lines.append(f"🔗 *Store Link:* {url}")

    return "\n".join(lines)


def format_deals_message(deals: Sequence[dict[str, Any]]) -> str:
    """Format active discounts matching user's requested layout."""
    if not deals:
        return "🎮 *GAMETRACKER — CURRENT DEALS*\n\nNo tracked games are currently on sale. Check back soon!"

    lines = [
        "🎮 *GAMETRACKER — CURRENT DEALS*\n",
    ]
    for d in deals[:10]:
        name = d.get("name", "Unknown Game")
        store = (d.get("store") or "Store").capitalize()
        price = d.get("current_price_str", "N/A")
        lowest = d.get("lowest_price_str", "N/A")
        discount = d.get("discount_percent", 0)

        lines.append(f"🔥 *{name}*")
        lines.append(f"Store: {store}")
        lines.append(f"Current Price: *{price}*")
        lines.append(f"Lowest Recorded: {lowest}")
        lines.append(f"Discount: *{discount}%*\n")

    lines.append(f"*{len(deals)}* active deal(s) found.")
    return "\n".join(lines).strip()


def format_owned_message(purchased: Sequence[dict[str, Any]]) -> str:
    """Format My Library purchased games."""
    if not purchased:
        return "📚 *GAMETRACKER — MY LIBRARY*\n\nYour Loot Vault is empty. Mark games as purchased on GameTracker!"

    lines = [
        "📚 *GAMETRACKER — MY LIBRARY*",
        f"You have *{len(purchased)}* purchased game(s):\n",
    ]
    for p in purchased[:15]:
        name = p.get("name", "Unknown Game")
        store = (p.get("store") or "Store").capitalize()
        p_date = p.get("purchase_date", "Unknown")
        p_price = p.get("purchase_price_str", "Not recorded")
        lines.append(f"📦 *{name}*")
        lines.append(f"• Store: {store} | Acquired: {p_date} | Price: {p_price}\n")

    if len(purchased) > 15:
        lines.append(f"_...and {len(purchased) - 15} more in your library._")

    return "\n".join(lines).strip()


def format_search_message(query: str, matches: Sequence[dict[str, Any]]) -> str:
    """Format search results."""
    if not matches:
        return f"🔍 *Search for '{query}':*\n\nNo tracked games matched your search. Try another title."

    lines = [
        f"🔍 *Search Results for '{query}'* ({len(matches)} found):\n",
    ]
    for m in matches[:10]:
        name = m.get("name", "Unknown Game")
        store = (m.get("store") or "Store").capitalize()
        price = m.get("current_price_str", "N/A")
        discount = m.get("discount_percent", 0)
        sale_str = f" 🔥 -{discount}%" if m.get("is_on_sale") else ""
        lines.append(f"• *{name}* ({store}): *{price}*{sale_str}")

    return "\n".join(lines).strip()


def format_help_message() -> str:
    """Format command help menu."""
    return (
        "🤖 *GAMETRACKER WHATSAPP ASSISTANT*\n\n"
        "Send any of the following commands:\n\n"
        "• *TRACKED* — Show all tracked games and prices\n"
        "• *GAME <title>* — Details & store link for a game (e.g. `GAME Skyrim`)\n"
        "• *DEALS* — Show all games currently discounted\n"
        "• *OWNED* — View your purchased game library\n"
        "• *SEARCH <query>* — Search your tracked collection (e.g. `SEARCH Witcher`)\n"
        "• *REFRESH* — Refresh prices (Authorized only)\n"
        "• *HELP* — Show this command menu\n\n"
        "_Tip: Commands are not case-sensitive._"
    )


def handle_whatsapp_command(
    text: str,
    sender_phone: str,
    service: Optional[GameTrackerService] = None,
    authorized_numbers: Optional[set[str]] = None,
) -> dict[str, Any]:
    """Process incoming text command and return message reply + optional interactive buttons."""
    svc = service or get_service()
    clean_sender = normalize_phone_number(sender_phone)
    auth_nums = authorized_numbers if authorized_numbers is not None else get_authorized_phone_numbers()
    is_authorized = (clean_sender in auth_nums) if auth_nums else True

    raw_text = (text or "").strip()
    if not raw_text:
        return {"body": format_help_message(), "buttons": ["DEALS", "TRACKED", "HELP"]}

    parts = raw_text.split(maxsplit=1)
    cmd = parts[0].upper()
    args = parts[1].strip() if len(parts) > 1 else ""

    # Command: TRACKED
    if cmd == "TRACKED":
        games = svc.get_tracked_games()
        enriched = []
        for g in games:
            d = svc.get_game_details(g.get("name") or g.get("id", ""))
            enriched.append(d or g)
        return {
            "body": format_tracked_message(enriched),
            "buttons": ["DEALS", "REFRESH", "HELP"],
        }

    # Command: GAME <name>
    elif cmd == "GAME":
        if not args:
            return {
                "body": "❓ Please specify a game name. Example:\n*GAME Skyrim*",
                "buttons": ["TRACKED", "DEALS", "HELP"],
            }
        details = svc.get_game_details(args)
        if not details:
            return {
                "body": f"❌ Could not find '*{args}*' in your tracked games radar.\nSend *TRACKED* or *SEARCH {args}* to browse.",
                "buttons": ["TRACKED", "DEALS", "HELP"],
            }
        return {
            "body": format_game_message(details),
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }

    # Command: OWNED / LIBRARY
    elif cmd in ("OWNED", "LIBRARY"):
        if not is_authorized and auth_nums:
            return {
                "body": "🚫 *Access Denied:* Your personal library details are restricted to authorized phone numbers.",
                "buttons": ["DEALS", "TRACKED", "HELP"],
            }
        purchased = svc.get_purchased_games()
        return {
            "body": format_owned_message(purchased),
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }

    # Command: DEALS
    elif cmd in ("DEALS", "SALE", "SALES"):
        deals = svc.get_active_deals()
        return {
            "body": format_deals_message(deals),
            "buttons": ["TRACKED", "REFRESH", "HELP"],
        }

    # Command: SEARCH <query>
    elif cmd == "SEARCH":
        if not args:
            return {
                "body": "❓ Please specify a search query. Example:\n*SEARCH Cyberpunk*",
                "buttons": ["TRACKED", "DEALS", "HELP"],
            }
        matches = svc.search_tracked_games(args)
        return {
            "body": format_search_message(args, matches),
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }

    # Command: REFRESH
    elif cmd == "REFRESH":
        res = svc.refresh_all_prices(
            requester_id=f"wa_{clean_sender}",
            is_authorized=is_authorized,
            cooldown_seconds=DEFAULT_COOLDOWN_SECONDS,
        )
        if not res.get("success"):
            status = res.get("status")
            if status == "unauthorized":
                msg = "🚫 *Access Denied:* Only authorized operators can trigger application-wide price refreshes."
            elif status == "cooldown":
                rem = res.get("remaining_seconds", 0)
                msg = f"⏳ *Cooldown Active:* Price refresh was executed recently. Please wait *{rem}s* before requesting again."
            elif status == "busy":
                msg = "⚠️ *Busy:* A price refresh is already currently running. Please wait a moment."
            else:
                msg = f"❌ {res.get('message', 'Refresh failed.')}"
            return {"body": msg, "buttons": ["DEALS", "TRACKED", "HELP"]}

        return {
            "body": f"🔄 *REFRESH COMPLETED!*\n\n{res.get('message')}",
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }

    # Command: HELP
    elif cmd in ("HELP", "START", "MENU", "?"):
        return {
            "body": format_help_message(),
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }

    # Fallback: Assume query is a game name if not recognized
    else:
        details = svc.get_game_details(raw_text)
        if details:
            return {
                "body": format_game_message(details),
                "buttons": ["DEALS", "TRACKED", "HELP"],
            }

        return {
            "body": f"❓ Unrecognized command '*{raw_text}*'.\n\n{format_help_message()}",
            "buttons": ["DEALS", "TRACKED", "HELP"],
        }


def verify_webhook_subscription(
    query_params: dict[str, list[str] | str],
    expected_verify_token: Optional[str] = None,
) -> tuple[int, str]:
    """Handle Meta's GET verification challenge.

    Meta sends:
    - hub.mode = 'subscribe'
    - hub.verify_token = '<configured_verify_token>'
    - hub.challenge = '<challenge_number>'
    """
    cfg = get_whatsapp_config()
    expected_token = expected_verify_token or cfg.get("verify_token", "")

    def _get_param(key: str) -> str:
        val = query_params.get(key, "")
        if isinstance(val, list):
            return val[0] if val else ""
        return str(val)

    mode = _get_param("hub.mode")
    token = _get_param("hub.verify_token")
    challenge = _get_param("hub.challenge")

    if mode == "subscribe" and token and expected_token and token == expected_token:
        logger.info("WhatsApp webhook subscription verified successfully.")
        return 200, challenge
    logger.warning("WhatsApp webhook verification failed: token mismatch or invalid mode (mode=%s)", mode)
    return 403, "Forbidden: Verification token mismatch"


def process_webhook_payload(
    body_bytes: bytes,
    signature_header: str,
    config: Optional[dict[str, str]] = None,
    service: Optional[GameTrackerService] = None,
) -> tuple[int, dict[str, Any]]:
    """Process incoming Meta WhatsApp Cloud API POST event.

    Verifies HMAC SHA-256 signature, dispatches commands, and triggers replies.
    """
    import json
    cfg = config or get_whatsapp_config()
    app_secret = cfg.get("app_secret", "")

    # 1. Cryptographic HMAC verification if app_secret is set
    if app_secret and not app_secret.lower().startswith("placeholder"):
        if not verify_whatsapp_signature(body_bytes, signature_header, app_secret):
            logger.warning("Rejected WhatsApp webhook: invalid HMAC SHA-256 signature.")
            return 401, {"error": "unauthorized", "message": "Invalid webhook signature"}

    # 2. Parse JSON payload
    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        logger.error("Failed to parse WhatsApp webhook payload: %s", e)
        return 400, {"error": "bad_request", "message": "Invalid JSON"}

    if data.get("object") != "whatsapp_business_account":
        return 200, {"status": "ignored", "reason": "not_whatsapp_business_account"}

    processed_count = 0
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                sender = msg.get("from")
                msg_type = msg.get("type")
                text = ""

                if msg_type == "text":
                    text = msg.get("text", {}).get("body", "")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    if interactive.get("type") == "button_reply":
                        text = interactive.get("button_reply", {}).get("id", "")
                    elif interactive.get("type") == "list_reply":
                        text = interactive.get("list_reply", {}).get("id", "")

                if sender and text:
                    reply = handle_whatsapp_command(text, sender, service=service)
                    send_whatsapp_message(
                        to_phone=sender,
                        message_text=reply["body"],
                        buttons=reply.get("buttons"),
                        config=cfg,
                    )
                    processed_count += 1

    return 200, {"status": "ok", "messages_processed": processed_count}


def send_whatsapp_message(
    to_phone: str,
    message_text: str,
    buttons: Optional[Sequence[str]] = None,
    config: Optional[dict[str, str]] = None,
) -> bool:
    """Send message via Meta WhatsApp Cloud API."""
    cfg = config or get_whatsapp_config()
    token = cfg.get("access_token")
    phone_id = cfg.get("phone_number_id")

    if not token or not phone_id or token.lower().startswith("placeholder"):
        logger.warning("WhatsApp credentials not configured; skipping actual HTTP send to %s", to_phone)
        return False

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Build payload: interactive buttons (up to 3 buttons) if provided
    payload: dict[str, Any]
    if buttons and 1 <= len(buttons) <= 3:
        btn_items = [
            {"type": "reply", "reply": {"id": b.upper(), "title": b.capitalize()[:20]}}
            for b in buttons
        ]
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalize_phone_number(to_phone),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message_text},
                "action": {"buttons": btn_items},
            },
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalize_phone_number(to_phone),
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message_text,
            },
        }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            logger.info("Successfully sent WhatsApp message to %s", to_phone)
            return True
        else:
            logger.error("Meta WhatsApp Cloud API error (%s): %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("Failed to send WhatsApp message to %s: %s", to_phone, e)
        return False
