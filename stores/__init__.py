"""Store registry — auto-discovers and registers all store implementations.

Usage:
    from stores import get_store, search_all_stores

    for store_name, results in search_all_stores("The Witcher 3").items():
        for r in results:
            print(r.store, r.name, r.current_price)
"""

import logging
from typing import Optional

from stores.base import StoreInterface, SearchResult, PricingInfo

logger = logging.getLogger(__name__)

_STORE_CLASSES: dict[str, type[StoreInterface]] = {}
_STORE_INSTANCES: dict[str, StoreInterface] = {}


def register_store(name: str, store_class: type[StoreInterface]) -> None:
    _STORE_CLASSES[name] = store_class
    logger.debug("Registered store: %s (%s)", name, store_class.__name__)


def get_store(name: str) -> Optional[StoreInterface]:
    if name not in _STORE_INSTANCES:
        cls = _STORE_CLASSES.get(name)
        if not cls:
            logger.warning("Unknown store: %s", name)
            return None
        _STORE_INSTANCES[name] = cls()
    return _STORE_INSTANCES[name]


def get_store_names() -> list[str]:
    return list(_STORE_CLASSES.keys())


def search_all_stores(query: str, limit: int = 5) -> dict[str, list[SearchResult]]:
    results: dict[str, list[SearchResult]] = {}
    for store_name, store_cls in _STORE_CLASSES.items():
        try:
            store = get_store(store_name)
            if store:
                results[store_name] = store.search(query, limit=limit)
        except Exception as e:
            logger.error("Search failed for store '%s': %s", store_name, e)
            results[store_name] = []
    return results


def get_pricing(store: str, store_id: str) -> Optional[PricingInfo]:
    s = get_store(store)
    if not s:
        return None
    return s.get_pricing(store_id)


# Auto-register known stores
from stores.steam import SteamStore
from stores.epic import EpicStore
from stores.gog import GOGStore

register_store("steam", SteamStore)
register_store("epic", EpicStore)
register_store("gog", GOGStore)
