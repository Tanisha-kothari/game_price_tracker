import re
import json
import csv
import io
import logging
import time
from datetime import datetime, date
from typing import Optional, Any
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

STORE_DOMAINS = {
    "steam": ["store.steampowered.com", "steamcommunity.com"],
    "epic": ["store.epicgames.com", "epicgames.com"],
    "gog": ["gog.com", "www.gog.com"],
}

STORE_NAMES = {
    "steam": "Steam",
    "epic": "Epic Games",
    "gog": "GOG",
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


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def parse_price(price_str: str) -> Optional[float]:
    if not price_str or price_str == "N/A":
        return None
    cleaned = re.sub(r"[^\d.,]", "", price_str)
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def format_inr(amount: Optional[float]) -> str:
    if amount is None:
        return "N/A"
    s = f"{amount:,.2f}"
    return f"\u20b9{s}"


def format_price(price: Optional[float], currency: str = "USD") -> str:
    if price is None:
        return "N/A"
    if currency == "INR":
        return format_inr(price)
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142"}
    symbol = symbols.get(currency, currency + " ")
    if currency == "PLN":
        return f"{price:.2f}{symbol}"
    return f"{symbol}{price:.2f}"


def display_price_inr(price: Optional[float], currency: str = "USD") -> str:
    if price is None:
        return "N/A"
    if currency == "INR":
        return format_inr(price)
    return format_inr(usd_to_inr(price))


def get_display_price(price: Optional[float], currency: str = "USD") -> Optional[float]:
    if price is None:
        return None
    if currency == "INR":
        return price
    return usd_to_inr(price)


def games_to_csv(games: list[dict]) -> str:
    output = io.StringIO()
    fieldnames = [
        "id", "name", "store", "url",
        "current_price", "currency", "current_price_inr",
        "target_price", "target_price_inr",
        "lowest_price", "lowest_price_inr",
        "last_checked", "cover_image",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for game in games:
        row = dict(game)
        row["current_price_inr"] = display_price_inr(game.get("current_price"), game.get("currency", "USD"))
        row["target_price_inr"] = display_price_inr(game.get("target_price"), game.get("currency", "USD"))
        row["lowest_price_inr"] = display_price_inr(game.get("lowest_price"), game.get("currency", "USD"))
        writer.writerow(row)
    return output.getvalue()


def history_to_csv(history: dict[str, dict[str, float]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["game_id", "date", "price_usd", "price_inr"])
    for game_id, dates in history.items():
        for d, price in sorted(dates.items()):
            inr_price = usd_to_inr(price)
            writer.writerow([game_id, d, price, inr_price])
    return output.getvalue()


def load_json_from_string(content: str) -> Any:
    return json.loads(content)


def dump_json_to_string(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
