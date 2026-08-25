import json
import logging
from copy import deepcopy
from typing import Optional, Any

from utils import today_str, convert_price, usd_to_inr, canonical_game_id, generate_game_id

logger = logging.getLogger(__name__)

GAMES_FILE = "games.json"
HISTORY_FILE = "history.json"

DEFAULT_GAMES: list[dict] = []
DEFAULT_HISTORY: dict[str, Any] = {}

HISTORY_CURRENCY_KEY = "__currency__"
HISTORY_SALE_KEY = "__sales__"

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

    # Sale fields — backward compatible defaults for existing saved games.
    if "original_price" not in game:
        game["original_price"] = game.get("current_price")
    if "discount_percent" not in game:
        is_on_sale = game.get("is_on_sale", False)
        game["discount_percent"] = _discount_from_prices(game) if is_on_sale else 0
    game.setdefault("is_on_sale", False)
    game.setdefault("sale_started", None)
    game.setdefault("sale_last_seen", None)
    game.setdefault("sale_end", None)
    if "game_id" not in game or not game.get("game_id"):
        game["game_id"] = canonical_game_id(game.get("name", ""))

    if "store_tags" not in game or not isinstance(game.get("store_tags"), list):
        game["store_tags"] = []
    if "custom_tags" not in game or not isinstance(game.get("custom_tags"), list):
        game["custom_tags"] = []

    return game


def _discount_from_prices(game: dict):
    """Compute discount percent from original/current when the API did not supply it."""
    original = game.get("original_price")
    current = game.get("current_price")
    if original and current is not None and original > 0:
        return round((original - current) / original * 100)
    return 0


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


def apply_game_update(game: dict, details, today: Optional[str] = None) -> dict:
    """Apply a fresh fetch to a stored game, including sale detection.

    Returns a dict of detected events for notifying the user:
    {"sale_started", "discount_increased", "discount_changed", "sale_ended",
     "price_changed", "new_low"} each bool.
    """
    normalize_game(game)
    today = today or today_str()

    price = details.current_price
    currency = details.currency or game["current_currency"]
    original = details.original_price
    discount = details.discount_percent
    is_on_sale = details.is_on_sale
    sale_end = details.sale_end

    events: dict = {
        "sale_detected": False,
        "discount_increased": False,
        "discount_changed": False,
        "sale_ended": False,
        "price_changed": False,
        "new_low": False,
    }

    was_on_sale = bool(game.get("is_on_sale"))
    prev_discount = game.get("discount_percent") or 0

    # Current price (null when fetch failed) — keep existing value on failure.
    if price is not None:
        if game.get("current_price") != price:
            events["price_changed"] = True
        game["current_price"] = price
        game["current_currency"] = currency
        game["currency"] = currency
        game["last_checked"] = today
        if game.get("original_price") is None:
            game["original_price"] = original

    # Resolve sale state.
    if original is not None:
        game["original_price"] = original
    if discount is not None:
        game["discount_percent"] = round(discount)
    if is_on_sale is None:
        is_on_sale = (
            game.get("original_price") is not None
            and game.get("current_price") is not None
            and game["original_price"] > game["current_price"]
        )

    old_on_sale = bool(game.get("is_on_sale"))
    game["is_on_sale"] = bool(is_on_sale)

    if is_on_sale:
        if not old_on_sale:
            events["sale_detected"] = True
            game["sale_started"] = today
        _dup = game.get("discount_percent") or 0
        if not old_on_sale and prev_discount == 0 and _dup > 0:
            events["sale_detected"] = True
        current_discount = game.get("discount_percent") or 0
        if current_discount > prev_discount:
            events["discount_increased"] = True
        elif current_discount != prev_discount:
            events["discount_changed"] = True
        game["sale_last_seen"] = today
    else:
        if old_on_sale:
            events["sale_ended"] = True
        game["sale_started"] = None
        game["sale_last_seen"] = None
        game["discount_percent"] = 0

    if sale_end is not None:
        game["sale_end"] = sale_end

    # Lowest price stays independent of sales — only lowered by a genuinely
    # lower current price.
    if price is not None:
        old_lowest = game.get("lowest_price")
        if old_lowest is None or currency == game.get("lowest_currency") and is_lower_price(
            price, currency, old_lowest, game.get("lowest_currency", currency)
        ):
            if old_lowest is not None and old_lowest > price:
                events["new_low"] = True
            game["lowest_price"] = price
            game["lowest_currency"] = currency

    new_tags = getattr(details, "store_tags", None)
    if new_tags and isinstance(new_tags, list):
        game["store_tags"] = new_tags

    return events


def apply_price_update(game: dict, price: Optional[float], currency: str) -> dict:
    """Backward-compatible single-price update (no sale metadata)."""
    from types import SimpleNamespace

    _currency = currency or "INR"
    details = SimpleNamespace(
        current_price=price,
        original_price=game.get("original_price", price),
        discount_percent=game.get("discount_percent", 0),
        is_on_sale=bool(game.get("is_on_sale")),
        sale_end=game.get("sale_end"),
        currency=_currency,
    )
    apply_game_update(game, details)
    return game


def update_game_price(
    games: list[dict],
    game_id: str,
    price: Optional[float],
    currency: str = "INR",
    details=None,
) -> list[dict]:
    for game in games:
        if game.get("id") == game_id:
            if details is not None:
                apply_game_update(game, details)
            else:
                apply_price_update(game, price, currency)
            break
    return games


def update_price_history(
    history: dict[str, Any],
    game_id: str,
    price: Optional[float],
    currency: str = "INR",
    is_on_sale: Optional[bool] = None,
    discount_percent: Optional[int] = None,
) -> dict[str, Any]:
    today = today_str()
    if game_id not in history:
        history[game_id] = {}
    if price is not None:
        entry = history[game_id]
        hist_currency = entry.get(HISTORY_CURRENCY_KEY)
        if hist_currency and hist_currency != currency:
            for key, value in list(entry.items()):
                if key == HISTORY_CURRENCY_KEY or key == HISTORY_SALE_KEY or not isinstance(value, (int, float)):
                    continue
                converted = _align_price_currency(value, hist_currency, currency)
                if converted is not None:
                    entry[key] = round(converted, 2)
        history[game_id][today] = price
        history[game_id][HISTORY_CURRENCY_KEY] = currency

        # Sale metadata per day so future graphs can shade sale periods.
        if is_on_sale is not None:
            sales = history[game_id].setdefault(HISTORY_SALE_KEY, {})
            sales[today] = {
                "is_on_sale": bool(is_on_sale),
                "discount_percent": discount_percent or 0,
            }
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

    date_keys = sorted(k for k in entry if k not in (HISTORY_CURRENCY_KEY, HISTORY_SALE_KEY))
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
        for k in sorted(k for k in entry if k not in (HISTORY_CURRENCY_KEY, HISTORY_SALE_KEY))
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
        "game_id": canonical_game_id(details.name),
        "name": details.name,
        "store": store,
        "url": url,
        "current_price": details.current_price,
        "current_currency": details.currency,
        "original_price": details.original_price,
        "discount_percent": details.discount_percent or 0,
        "is_on_sale": bool(details.is_on_sale),
        "sale_started": None,
        "sale_last_seen": None,
        "sale_end": None,
        "lowest_price": details.current_price,
        "lowest_currency": details.currency,
        "last_checked": today_str(),
        "currency": details.currency,
        "cover_image": details.cover_image,
        "store_tags": getattr(details, "store_tags", []) or [],
        "custom_tags": [],
    }
    if details.is_on_sale:
        game["sale_started"] = today_str()
        game["sale_last_seen"] = today_str()
    if target_price is not None:
        game["target_price"] = target_price
        game["target_currency"] = details.currency
    return normalize_game(game)


def build_game_from_search_result(
    result,
    target_price: Optional[float] = None,
    pricing=None,
) -> dict:
    """Create a normalized game entry from a store SearchResult."""
    name = result.name
    if pricing is not None:
        name = pricing.name or name
        current = pricing.current_price
        original = pricing.original_price
        currency = pricing.currency
        discount = pricing.discount_percent or 0
        is_on_sale = bool(pricing.discount_percent) or (
            original is not None and current is not None and original > current
        )
        cover = pricing.cover_image or result.cover_image
        url = pricing.url or result.url
    else:
        current = result.current_price
        original = result.original_price
        currency = result.currency
        discount = result.discount_percent or 0
        is_on_sale = discount > 0 or (
            original is not None and current is not None and original > current
        )
        cover = result.cover_image
        url = result.url

    game = {
        "id": generate_game_id(result.store, result.store_id),
        "game_id": canonical_game_id(name),
        "name": name,
        "store": result.store,
        "url": url,
        "current_price": current,
        "current_currency": currency,
        "original_price": original,
        "discount_percent": discount,
        "is_on_sale": is_on_sale,
        "sale_started": today_str() if is_on_sale else None,
        "sale_last_seen": today_str() if is_on_sale else None,
        "sale_end": None,
        "lowest_price": current,
        "lowest_currency": currency,
        "last_checked": today_str(),
        "currency": currency,
        "cover_image": cover,
    }
    if target_price is not None:
        game["target_price"] = target_price
        game["target_currency"] = currency
    return normalize_game(game)


def get_tracked_store_ids(games: list[dict]) -> set[str]:
    return {g["id"] for g in games if g.get("id")}


def get_tracked_stores_for_game(games: list[dict], game_id: str) -> set[str]:
    """Stores tracked for a canonical game identity."""
    return {
        g["store"]
        for g in games
        if g.get("game_id") == game_id and g.get("store")
    }


def group_games_by_identity(games: list[dict]) -> dict[str, list[dict]]:
    """Group store listings by canonical game_id."""
    grouped: dict[str, list[dict]] = {}
    for game in games:
        gid = game.get("game_id") or canonical_game_id(game.get("name", ""))
        game["game_id"] = gid
        grouped.setdefault(gid, []).append(game)
    return grouped


def count_games_with_both_stores(games: list[dict]) -> int:
    """Games tracked on both Steam and Epic (same canonical game_id)."""
    count = 0
    for listings in group_games_by_identity(games).values():
        stores = {g["store"] for g in listings}
        if "steam" in stores and "epic" in stores:
            count += 1
    return count


def store_filter_stats(games: list[dict]) -> dict[str, int]:
    grouped = group_games_by_identity(games)
    steam_games = sum(1 for listings in grouped.values() if any(g["store"] == "steam" for g in listings))
    epic_games = sum(1 for listings in grouped.values() if any(g["store"] == "epic" for g in listings))
    both = count_games_with_both_stores(games)
    return {
        "steam": steam_games,
        "epic": epic_games,
        "both": both,
    }


def filter_grouped_games(
    games: list[dict],
    store_filter: str,
) -> dict[str, list[dict]]:
    """Filter grouped games by store availability."""
    grouped = group_games_by_identity(games)
    if store_filter == "All":
        return grouped
    if store_filter == "Steam":
        return {
            gid: listings
            for gid, listings in grouped.items()
            if any(g["store"] == "steam" for g in listings)
        }
    if store_filter == "Epic Games":
        return {
            gid: listings
            for gid, listings in grouped.items()
            if any(g["store"] == "epic" for g in listings)
        }
    if store_filter == "Steam + Epic":
        return {
            gid: listings
            for gid, listings in grouped.items()
            if any(g["store"] == "steam" for g in listings)
            and any(g["store"] == "epic" for g in listings)
        }
    return grouped


# ── Saved Combinations Persistence & Helper Functions ─────────────────

SAVED_COMBINATIONS_FILE = "saved_combinations.json"


def load_saved_combinations(content: str) -> list[dict]:
    if not content or not content.strip():
        return []
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error("Failed to parse saved_combinations.json: %s", e)
        return []


def dump_saved_combinations(combos: list[dict]) -> str:
    return json.dumps(combos, indent=2, ensure_ascii=False)


def add_saved_combination(combos: list[dict], combo: dict) -> tuple[list[dict], bool]:
    cid = combo.get("id", "")
    for existing in combos:
        if existing.get("id") == cid:
            return combos, False
    combos.insert(0, combo)
    return combos, True


def remove_saved_combination(combos: list[dict], combo_id: str) -> list[dict]:
    return [c for c in combos if c.get("id") != combo_id]


# ── Custom Tags Helper Functions ─────────────────────────────────────

def add_custom_tag_to_game(games: list[dict], game_id: str, tag_name: str) -> bool:
    clean_tag = tag_name.strip()
    if not clean_tag:
        return False
    modified = False
    for game in games:
        if game.get("id") == game_id:
            normalize_game(game)
            tags = game.setdefault("custom_tags", [])
            if clean_tag.lower() not in [t.lower() for t in tags]:
                tags.append(clean_tag)
                modified = True
            break
    return modified


def remove_custom_tag_from_game(games: list[dict], game_id: str, tag_name: str) -> bool:
    clean_tag = tag_name.strip().lower()
    modified = False
    for game in games:
        if game.get("id") == game_id:
            normalize_game(game)
            tags = game.get("custom_tags", [])
            new_tags = [t for t in tags if t.lower() != clean_tag]
            if len(new_tags) != len(tags):
                game["custom_tags"] = new_tags
                modified = True
            break
    return modified


def get_all_unique_tags(games: list[dict]) -> tuple[list[str], list[str]]:
    store_tags_set = set()
    custom_tags_set = set()
    for g in games:
        normalize_game(g)
        for st in g.get("store_tags", []):
            if st and isinstance(st, str):
                store_tags_set.add(st)
        for ct in g.get("custom_tags", []):
            if ct and isinstance(ct, str):
                custom_tags_set.add(ct)
    return sorted(list(store_tags_set)), sorted(list(custom_tags_set))


def filter_grouped_games_by_tag(
    grouped: dict[str, list[dict]],
    tag_filter: str,
) -> dict[str, list[dict]]:
    """Filter grouped canonical games by store or custom tag."""
    if not tag_filter or tag_filter == "All":
        return grouped
    tf_lower = tag_filter.lower()
    matching_grouped = {}
    for gid, listings in grouped.items():
        has_tag = False
        for g in listings:
            normalize_game(g)
            st_match = any(t.lower() == tf_lower for t in g.get("store_tags", []))
            ct_match = any(t.lower() == tf_lower for t in g.get("custom_tags", []))
            if st_match or ct_match:
                has_tag = True
                break
        if has_tag:
            matching_grouped[gid] = listings
    return matching_grouped

