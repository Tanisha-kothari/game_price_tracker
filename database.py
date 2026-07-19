import json
import logging
from copy import deepcopy
from typing import Optional, Any

from utils import today_str, convert_price, usd_to_inr

logger = logging.getLogger(__name__)

GAMES_FILE = "games.json"
HISTORY_FILE = "history.json"

DEFAULT_GAMES: list[dict] = []
DEFAULT_HISTORY: dict[str, Any] = {}

HISTORY_CURRENCY_KEY = "__currency__"

PRICE_FIELDS = ("current_price", "lowest_price", "target_price")
CURRENCY_FIELDS = {
    "current_price": "current_currency",
    "lowest_price": "lowest_currency",
    "target_price": "target_currency",
}

STORE_DEFAULT_CURRENCY = {
    "steam": "INR",
    "epic": "INR",
    "gog": "INR",
}


def load_games(content: str) -> list[dict]:
    if not content.strip():
        return deepcopy(DEFAULT_GAMES)
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return deepcopy(DEFAULT_GAMES)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse games.json: %s", e)
        return deepcopy(DEFAULT_GAMES)


def load_history(content: str) -> dict[str, Any]:
    if not content.strip():
        return deepcopy(DEFAULT_HISTORY)
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        return deepcopy(DEFAULT_HISTORY)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse history.json: %s", e)
        return deepcopy(DEFAULT_HISTORY)


def dump_games(games: list[dict]) -> str:
    normalized = [normalize_game(g) for g in games]
    return json.dumps(normalized, indent=2, ensure_ascii=False)


def dump_history(history: dict[str, Any]) -> str:
    return json.dumps(history, indent=2, ensure_ascii=False)


def get_price_currency(game: dict, field: str) -> str:
    currency_key = CURRENCY_FIELDS.get(field)
    if currency_key and game.get(currency_key):
        return game[currency_key]
    store = game.get("store", "")
    return game.get("currency") or STORE_DEFAULT_CURRENCY.get(store, "USD")


def _default_currency(game: dict) -> str:
    store = game.get("store", "")
    legacy = game.get("currency")
    if legacy:
        return legacy
    return STORE_DEFAULT_CURRENCY.get(store, "USD")


def normalize_game(game: dict) -> dict:
    """Ensure every price field has a matching currency field."""
    default = _default_currency(game)
    if game.get("current_currency"):
        default = game["current_currency"]
    elif game.get("currency"):
        default = game["currency"]
        game["current_currency"] = default

    if "current_currency" not in game:
        game["current_currency"] = default

    if "lowest_currency" not in game:
        game["lowest_currency"] = game["current_currency"]

    target = game.get("target_price")
    if target is not None and "target_currency" not in game:
        game["target_currency"] = game["current_currency"]

    game["currency"] = game["current_currency"]
    return game


def _align_price_currency(
    price: Optional[float],
    from_currency: str,
    to_currency: str,
) -> Optional[float]:
    if price is None or from_currency == to_currency:
        return price
    return convert_price(price, from_currency, to_currency)


def _fix_currency_mismatch(
    game: dict,
    price_field: str,
    target_currency: str,
) -> bool:
    price = game.get(price_field)
    if price is None:
        return False

    currency_field = CURRENCY_FIELDS[price_field]
    price_currency = game.get(currency_field, target_currency)
    if price_currency == target_currency:
        return False

    converted = _align_price_currency(price, price_currency, target_currency)
    if converted is not None:
        logger.info(
            "Migrating %s for %s: %.2f %s -> %.2f %s",
            price_field,
            game.get("name", "?"),
            price,
            price_currency,
            converted,
            target_currency,
        )
        game[price_field] = converted
        game[currency_field] = target_currency
        return True

    logger.info(
        "Resetting %s for %s (could not convert %s -> %s)",
        price_field,
        game.get("name", "?"),
        price_currency,
        target_currency,
    )
    game[price_field] = game.get("current_price")
    game[currency_field] = target_currency
    return True


def _detect_legacy_lowest_currency(game: dict) -> Optional[str]:
    """Infer if lowest_price was stored in USD while current is INR."""
    current = game.get("current_price")
    lowest = game.get("lowest_price")
    if current is None or lowest is None:
        return None

    current_currency = game.get("current_currency") or game.get("currency", "USD")
    if current_currency != "INR":
        return None

    if game.get("lowest_currency") and game["lowest_currency"] != current_currency:
        return game["lowest_currency"]

    if lowest >= current * 0.5:
        return current_currency

    converted = usd_to_inr(lowest)
    if converted is not None and abs(converted - current) / max(current, 1) < 0.5:
        return "USD"

    if lowest < current * 0.15:
        return "USD"

    return current_currency


def migrate_game(game: dict) -> bool:
    """Migrate a single game to the per-price currency model. Returns True if changed."""
    before = json.dumps(game, sort_keys=True, default=str)

    legacy_lowest_currency = _detect_legacy_lowest_currency(game)
    if legacy_lowest_currency and "lowest_currency" not in game:
        game["lowest_currency"] = legacy_lowest_currency

    normalize_game(game)

    target_currency = game["current_currency"]
    changed = False

    for field in ("lowest_price", "target_price"):
        if _fix_currency_mismatch(game, field, target_currency):
            changed = True

    current = game.get("current_price")
    lowest = game.get("lowest_price")
    if (
        current is not None
        and lowest is not None
        and game["current_currency"] == game["lowest_currency"]
        and lowest > current
    ):
        game["lowest_price"] = current
        changed = True

    normalize_game(game)
    after = json.dumps(game, sort_keys=True, default=str)
    return changed or before != after


def migrate_games(games: list[dict]) -> tuple[list[dict], bool]:
    changed = False
    for game in games:
        if migrate_game(game):
            changed = True
    return games, changed


def migrate_history_entry(
    entry: dict[str, Any],
    target_currency: str,
) -> tuple[dict[str, Any], bool]:
    if not entry:
        return entry, False

    hist_currency = entry.get(HISTORY_CURRENCY_KEY, target_currency)
    changed = False

    if hist_currency != target_currency:
        for key, value in list(entry.items()):
            if key == HISTORY_CURRENCY_KEY or not isinstance(value, (int, float)):
                continue
            converted = _align_price_currency(value, hist_currency, target_currency)
            if converted is not None:
                entry[key] = round(converted, 2)
                changed = True
        entry[HISTORY_CURRENCY_KEY] = target_currency
        changed = True
    elif HISTORY_CURRENCY_KEY not in entry:
        entry[HISTORY_CURRENCY_KEY] = target_currency
        changed = True

    return entry, changed


def migrate_history(history: dict[str, Any], games: list[dict]) -> tuple[dict[str, Any], bool]:
    game_currencies = {g["id"]: g["current_currency"] for g in games if "id" in g}
    changed = False

    for game_id, entry in history.items():
        target = game_currencies.get(game_id, entry.get(HISTORY_CURRENCY_KEY, "INR"))
        updated, entry_changed = migrate_history_entry(entry, target)
        history[game_id] = updated
        if entry_changed:
            changed = True

    return history, changed


def prices_comparable(
    price_a: Optional[float],
    currency_a: str,
    price_b: Optional[float],
    currency_b: str,
) -> bool:
    if price_a is None or price_b is None:
        return False
    return currency_a == currency_b


def is_lower_price(
    candidate: float,
    candidate_currency: str,
    reference: float,
    reference_currency: str,
) -> bool:
    if candidate_currency != reference_currency:
        converted = _align_price_currency(candidate, candidate_currency, reference_currency)
        if converted is None:
            return False
        candidate = converted
    return candidate < reference


def is_target_met(
    current: Optional[float],
    current_currency: str,
    target: Optional[float],
    target_currency: str,
) -> bool:
    if current is None or target is None:
        return False
    if current_currency != target_currency:
        converted = _align_price_currency(current, current_currency, target_currency)
        if converted is None:
            converted = _align_price_currency(target, target_currency, current_currency)
            if converted is None:
                return False
            return current <= converted
        return converted <= target
    return current <= target


def apply_price_update(game: dict, price: Optional[float], currency: str) -> dict:
    """Update current price and lowest price with currency-safe comparison."""
    normalize_game(game)
    game["current_price"] = price
    game["current_currency"] = currency
    game["currency"] = currency
    game["last_checked"] = today_str()

    if price is not None:
        lowest = game.get("lowest_price")
        lowest_currency = game.get("lowest_currency", currency)
        if lowest is None or currency != lowest_currency or is_lower_price(price, currency, lowest, lowest_currency):
            game["lowest_price"] = price
            game["lowest_currency"] = currency

    return game


def update_game_price(
    games: list[dict],
    game_id: str,
    price: Optional[float],
    currency: str = "INR",
) -> list[dict]:
    for game in games:
        if game.get("id") == game_id:
            apply_price_update(game, price, currency)
            break
    return games


def update_price_history(
    history: dict[str, Any],
    game_id: str,
    price: Optional[float],
    currency: str = "INR",
) -> dict[str, Any]:
    today = today_str()
    if game_id not in history:
        history[game_id] = {}
    if price is not None:
        entry = history[game_id]
        hist_currency = entry.get(HISTORY_CURRENCY_KEY)
        if hist_currency and hist_currency != currency:
            for key, value in list(entry.items()):
                if key == HISTORY_CURRENCY_KEY or not isinstance(value, (int, float)):
                    continue
                converted = _align_price_currency(value, hist_currency, currency)
                if converted is not None:
                    entry[key] = round(converted, 2)
        history[game_id][today] = price
        history[game_id][HISTORY_CURRENCY_KEY] = currency
    return history


def detect_price_change(
    history: dict[str, Any],
    game_id: str,
    current_price: Optional[float],
    currency: str = "INR",
) -> Optional[float]:
    if game_id not in history or not history[game_id]:
        return None

    entry = history[game_id]
    hist_currency = entry.get(HISTORY_CURRENCY_KEY, currency)
    if hist_currency != currency:
        return None

    date_keys = sorted(k for k in entry if k != HISTORY_CURRENCY_KEY)
    if len(date_keys) < 2:
        return None

    prev_price = entry[date_keys[-2]]
    if current_price is None:
        return None

    diff = current_price - prev_price
    if abs(diff) < 0.001:
        return None
    return diff


def get_history_prices(history: dict[str, Any], game_id: str) -> list[float]:
    entry = history.get(game_id, {})
    if not entry:
        return []
    return [
        entry[k]
        for k in sorted(k for k in entry if k != HISTORY_CURRENCY_KEY)
        if isinstance(entry[k], (int, float))
    ]


def add_game(games: list[dict], game: dict) -> tuple[list[dict], bool]:
    game_id = game.get("id", "")
    for existing in games:
        if existing.get("id") == game_id:
            logger.warning("Duplicate game skipped: %s (%s)", game.get("name"), game_id)
            return games, False

    currency = game.get("current_currency") or game.get("currency", "INR")
    game["current_currency"] = currency
    game["lowest_currency"] = game.get("lowest_currency", currency)
    if game.get("target_price") is not None:
        game["target_currency"] = game.get("target_currency", currency)
    game["currency"] = currency
    normalize_game(game)
    games.append(game)
    return games, True


def remove_game(games: list[dict], game_id: str) -> list[dict]:
    return [g for g in games if g.get("id") != game_id]


def get_game_by_id(games: list[dict], game_id: str) -> Optional[dict]:
    for game in games:
        if game.get("id") == game_id:
            return game
    return None


def get_lowest_price(games: list[dict], game_id: str) -> Optional[float]:
    game = get_game_by_id(games, game_id)
    return game.get("lowest_price") if game else None


def get_history_currency(history: dict[str, Any], game_id: str) -> Optional[str]:
    entry = history.get(game_id)
    if not entry:
        return None
    return entry.get(HISTORY_CURRENCY_KEY)


def build_game_from_details(details, url: str, store: str, target_price: Optional[float] = None) -> dict:
    """Create a normalized game entry from API GameDetails."""
    game = {
        "id": f"{store}_{details.store_id}",
        "name": details.name,
        "store": store,
        "url": url,
        "current_price": details.current_price,
        "current_currency": details.currency,
        "lowest_price": details.current_price,
        "lowest_currency": details.currency,
        "last_checked": today_str(),
        "currency": details.currency,
        "cover_image": details.cover_image,
    }
    if target_price is not None:
        game["target_price"] = target_price
        game["target_currency"] = details.currency
    return normalize_game(game)
