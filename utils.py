import re
import json
import csv
import io
import logging
from datetime import datetime, date
from typing import Optional, Any
from urllib.parse import urlparse

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


def format_price(price: Optional[float], currency: str = "USD") -> str:
    if price is None:
        return "N/A"
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "PLN": "z\u0142", "INR": "\u20b9"}
    symbol = symbols.get(currency, currency + " ")
    if currency == "PLN":
        return f"{price:.2f}{symbol}"
    return f"{symbol}{price:.2f}"


def games_to_csv(games: list[dict]) -> str:
    output = io.StringIO()
    fieldnames = ["id", "name", "store", "url", "current_price", "target_price",
                  "lowest_price", "last_checked", "currency", "cover_image"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for game in games:
        writer.writerow(game)
    return output.getvalue()


def history_to_csv(history: dict[str, dict[str, float]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["game_id", "date", "price"])
    for game_id, dates in history.items():
        for d, price in sorted(dates.items()):
            writer.writerow([game_id, d, price])
    return output.getvalue()


def load_json_from_string(content: str) -> Any:
    return json.loads(content)


def dump_json_to_string(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
