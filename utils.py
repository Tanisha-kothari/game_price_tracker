import re
import json
import csv
import io
import logging
import time
from datetime import date
from typing import Optional, Any
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

STORE_DOMAINS = {
    "steam": ["store.steampowered.com", "steamcommunity.com"],
    "epic": ["store.epicgames.com", "epicgames.com"],
    "gog": ["gog.com", "www.gog.com"],
}

INR_CACHE: dict[str, Any] = {"rate": None, "timestamp": 0}
INR_CACHE_TTL = 86400
FALLBACK_INR_RATE = 86.0


def get_usd_to_inr_rate() -> float:
    now = time.time()
    if INR_CACHE["rate"] is not None and (now - INR_CACHE["timestamp"]) < INR_CACHE_TTL:
        return INR_CACHE["rate"]
    try:
        resp = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"].get("INR", FALLBACK_INR_RATE)
        INR_CACHE["rate"] = rate
        INR_CACHE["timestamp"] = now
        logger.info("Fetched USD/INR rate: %.4f", rate)
        return rate
    except Exception as e:
        logger.warning("Failed to fetch INR rate, using fallback %.2f: %s", FALLBACK_INR_RATE, e)
        return FALLBACK_INR_RATE


def usd_to_inr(usd_amount: Optional[float]) -> Optional[float]:
    if usd_amount is None:
        return None
    rate = get_usd_to_inr_rate()
    return round(usd_amount * rate, 2)


def inr_to_usd(inr_amount: Optional[float]) -> Optional[float]:
    if inr_amount is None:
        return None
    rate = get_usd_to_inr_rate()
    return round(inr_amount / rate, 2)


def convert_price(
    amount: Optional[float],
    from_currency: str,
    to_currency: str,
) -> Optional[float]:
    if amount is None or from_currency == to_currency:
        return amount
    if from_currency == "USD" and to_currency == "INR":
        return usd_to_inr(amount)
    if from_currency == "INR" and to_currency == "USD":
        return inr_to_usd(amount)
    logger.warning("Unsupported currency conversion: %s -> %s", from_currency, to_currency)
    return None


def detect_store(url: str) -> Optional[str]:
    for store, domains in STORE_DOMAINS.items():
        for domain in domains:
            if domain in url.lower():
                return store
    return None


def extract_steam_app_id(url: str) -> Optional[str]:
    match = re.search(r"(?:app|store\.steampowered\.com/app)/(\d+)", url)
    return match.group(1) if match else None


def extract_gog_game_id(url: str) -> Optional[str]:
    match = re.search(r"gog\.com/(?:en/)?game/([a-z0-9_-]+)", url.lower())
    return match.group(1) if match else None


def extract_epic_slug(url: str) -> Optional[str]:
    match = re.search(r"store\.epicgames\.com/(?:[a-z]{2}-[a-z]{2}/)?p/([a-z0-9_-]+)", url.lower())
    if match:
        return match.group(1)
    match = re.search(r"epicgames\.com/(?:[a-z]{2}-[a-z]{2}/)?p/([a-z0-9_-]+)", url.lower())
    return match.group(1) if match else None


def generate_game_id(store: str, store_id: str) -> str:
    return f"{store}_{store_id}"


def today_str() -> str:
    return date.today().isoformat()


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_inr(amount: Optional[float]) -> str:
    if amount is None:
        return "N/A"
    whole = int(amount) if amount == int(amount) else None
    if whole is not None:
        s = f"{whole:,}"
    else:
        s = f"{amount:,.2f}"
    return f"\u20b9{s}"


def format_price(price: Optional[float], currency: str = "INR") -> str:
    if price is None:
        return "N/A"
    if currency == "INR":
        return format_inr(price)
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142"}
    symbol = symbols.get(currency, currency + " ")
    if currency == "PLN":
        return f"{price:.2f}{symbol}"
    whole = int(price) if price == int(price) else None
    if whole is not None and currency == "USD":
        return f"{symbol}{whole:,}"
    return f"{symbol}{price:.2f}"


def _resolve_currency(game: dict, field: str) -> str:
    from database import get_price_currency
    return get_price_currency(game, field)


PRICE_EXPORT_FIELDS = ("current_price", "target_price", "lowest_price")


def _build_fieldnames(games: list[dict]) -> list[str]:
    preferred = [
        "id", "name", "store", "url",
        "current_price", "current_currency",
        "lowest_price", "lowest_currency",
        "target_price", "target_currency",
        "last_checked", "cover_image", "currency",
    ]
    keys: set[str] = set()
    for g in games:
        keys.update(g.keys())
    ordered = [k for k in preferred if k in keys]
    remaining = sorted(k for k in keys if k not in ordered)
    return ordered + remaining


def games_to_csv(games: list[dict]) -> str:
    output = io.StringIO()
    base_fields = _build_fieldnames(games)
    price_fields = [f for f in PRICE_EXPORT_FIELDS if f in base_fields]
    fieldnames = base_fields + [f"{f}_display" for f in price_fields]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for game in games:
        row = dict(game)
        for f in price_fields:
            currency = _resolve_currency(game, f)
            row[f"{f}_display"] = format_price(game.get(f), currency)
        writer.writerow(row)
    return output.getvalue()


def games_to_json(games: list[dict]) -> str:
    enriched = []
    for g in games:
        entry = dict(g)
        for f in PRICE_EXPORT_FIELDS:
            if f in entry:
                currency = _resolve_currency(g, f)
                entry[f"{f}_display"] = format_price(g.get(f), currency)
        enriched.append(entry)
    return json.dumps(enriched, indent=2, ensure_ascii=False)


def history_to_csv(history: dict[str, dict[str, Any]]) -> str:
    from database import HISTORY_CURRENCY_KEY

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["game_id", "date", "price", "currency", "price_display"])
    for game_id, dates in history.items():
        currency = dates.get(HISTORY_CURRENCY_KEY, "INR")
        for d, price in sorted(dates.items()):
            if d == HISTORY_CURRENCY_KEY:
                continue
            if not isinstance(price, (int, float)):
                continue
            writer.writerow([game_id, d, price, currency, format_price(price, currency)])
    return output.getvalue()


def dump_json_to_string(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def render_sparkline_svg(prices: list[float], width: int = 120, height: int = 32) -> str:
    if len(prices) < 2:
        return ""
    mn, mx = min(prices), max(prices)
    span = mx - mn or 1.0
    step = width / (len(prices) - 1)
    points = []
    for i, p in enumerate(prices):
        x = i * step
        y = height - ((p - mn) / span) * (height - 4) - 2
        points.append(f"{x:.1f},{y:.1f}")
    polyline = " ".join(points)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'class="sparkline" aria-hidden="true">'
        f'<polyline fill="none" stroke="#22c55e" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" points="{polyline}"/>'
        f"</svg>"
    )
