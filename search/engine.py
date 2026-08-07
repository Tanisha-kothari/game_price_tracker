"""Cross-store search engine — orchestrates searches across all stores."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from stores import search_all_stores, get_pricing, get_store_names
from stores.base import SearchResult, PricingInfo

logger = logging.getLogger(__name__)


@dataclass
class AggregatedGame:
    """A single game identity with results across stores."""
    canonical_name: str
    results: dict[str, list[SearchResult]] = field(default_factory=dict)
    # results["steam"] = [SearchResult, ...]
    # results["epic"] = [SearchResult, ...]


def search_games(query: str, limit: int = 5) -> list[AggregatedGame]:
    """Search across all stores and aggregate results by game name.

    Returns a list of AggregatedGame objects, each containing results from
    all stores that had matches.
    """
    raw = search_all_stores(query, limit=limit)
    if not any(raw.values()):
        return []

    # Flatten all results into a list
    all_results: list[SearchResult] = []
    for store_name, store_results in raw.items():
        for r in store_results:
            all_results.append(r)

    # Group by canonical name (using base game name without edition)
    grouped: dict[str, AggregatedGame] = {}
    for r in all_results:
        base = _strip_edition(r.name)
        if base not in grouped:
            grouped[base] = AggregatedGame(canonical_name=base)
        if r.store not in grouped[base].results:
            grouped[base].results[r.store] = []
        grouped[base].results[r.store].append(r)

    # Sort groups: the group whose result best matches the query comes first
    query_lower = query.lower().strip()
    sorted_groups = sorted(
        grouped.values(),
        key=lambda g: _relevance_score(g.canonical_name, query_lower),
        reverse=True,
    )

    return sorted_groups


def get_cross_store_pricing(store_ids: dict[str, str]) -> dict[str, PricingInfo]:
    """Get pricing for the same game across multiple stores.

    Args:
        store_ids: dict mapping store_name -> store_id

    Returns:
        dict mapping store_name -> PricingInfo (if available)
    """
    results: dict[str, PricingInfo] = {}
    for store, store_id in store_ids.items():
        try:
            info = get_pricing(store, store_id)
            if info:
                results[store] = info
        except Exception as e:
            logger.error("Failed to get pricing for %s/%s: %s", store, store_id, e)
    return results


# ── Helpers ──────────────────────────────────────────────────────────

_EDITION_KEYWORDS = [
    "GOTY", "Game of the Year", "Complete", "Definitive", "Deluxe",
    "Premium", "Ultimate", "Gold", "Enhanced", "Remastered",
    "Standard", "Digital Deluxe", "Collector", "Collector's",
    "Edition", "Special Edition", "Limited Edition",
]


def _strip_edition(name: str) -> str:
    """Remove edition info from game name to get the base/canonical name."""
    # Remove common edition suffixes
    result = name
    for keyword in _EDITION_KEYWORDS:
        # Remove " - <Edition>" or " <Edition>" patterns at end
        import re
        result = re.sub(rf"[-–—\s]+{re.escape(keyword)}\s*$", "", result, flags=re.IGNORECASE)
        result = re.sub(rf"\s+{re.escape(keyword)}\s*$", "", result, flags=re.IGNORECASE)
    return result.strip()


def _relevance_score(name: str, query: str) -> float:
    """Score how relevant a game name is to the search query."""
    name_lower = name.lower()
    score = 0.0

    # Exact match gets highest score
    if name_lower == query:
        score += 100.0
    # Query is substring of name
    elif query in name_lower:
        score += 50.0
    # Name starts with query
    elif name_lower.startswith(query):
        score += 40.0
    # Word-level matching
    query_words = set(query.split())
    name_words = set(name_lower.split())
    common = query_words & name_words
    score += len(common) * 10.0

    # Penalize very long names (often wrong matches)
    score -= len(name.split()) * 2.0

    return score

