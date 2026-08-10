"""Cross-store search engine — orchestrates searches across all stores."""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from stores import search_all_stores, get_pricing, get_store_names
from stores.base import SearchResult, PricingInfo
from utils import strip_edition_suffix, canonical_game_id, DISTINCT_PRODUCT_PATTERNS

logger = logging.getLogger(__name__)


@dataclass
class AggregatedGame:
    """A single game identity with results across stores."""
    canonical_name: str
    canonical_id: str = ""
    results: dict[str, list[SearchResult]] = field(default_factory=dict)
    # results["steam"] = [SearchResult, ...]
    # results["epic"] = [SearchResult, ...]


def search_games(query: str, limit: int = 8) -> list[AggregatedGame]:
    """Search across all stores and aggregate results by conservative game identity.

    Returns a list of AggregatedGame objects, each containing results from
    all stores that had matches.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    logger.info("search_games initiated for '%s'", clean_query)
    raw = search_all_stores(clean_query, limit=limit)
    if not any(raw.values()):
        logger.info("search_games for '%s' returned 0 raw results across stores", clean_query)
        return []

    # Flatten all results into a list
    all_results: list[SearchResult] = []
    for store_name, store_results in raw.items():
        for r in store_results:
            all_results.append(r)

    # Group by conservative canonical game ID
    grouped: dict[str, AggregatedGame] = {}
    for r in all_results:
        cid = canonical_game_id(r.name)
        base = strip_edition_suffix(r.name)
        if cid not in grouped:
            grouped[cid] = AggregatedGame(canonical_name=base, canonical_id=cid)
        else:
            # If current canonical_name is longer/has edition words and base is cleaner, update it
            if len(base) < len(grouped[cid].canonical_name) and len(base) >= 3:
                grouped[cid].canonical_name = base

        if r.store not in grouped[cid].results:
            grouped[cid].results[r.store] = []
        
        # Deduplicate same store_id within this store
        existing_ids = {item.store_id for item in grouped[cid].results[r.store]}
        if r.store_id not in existing_ids:
            grouped[cid].results[r.store].append(r)

    # Sort items within each store so Standard/Base edition comes first
    for agg in grouped.values():
        for store_name, store_list in agg.results.items():
            store_list.sort(
                key=lambda x: (
                    0 if getattr(x, "edition", "") == "Standard" else 1,
                    len(x.name),
                )
            )

    # Sort groups by relevance to the query
    sorted_groups = sorted(
        grouped.values(),
        key=lambda g: _relevance_score(g.canonical_name, clean_query),
        reverse=True,
    )

    logger.info(
        "search_games aggregated '%s' into %d distinct game identities: %s",
        clean_query,
        len(sorted_groups),
        [g.canonical_name for g in sorted_groups[:5]],
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


def _relevance_score(name: str, query: str) -> float:
    """Score how relevant a game name is to the search query."""
    name_lower = name.lower().strip()
    query_lower = query.lower().strip()
    score = 0.0

    # Exact match gets highest score
    if name_lower == query_lower:
        score += 150.0
    # Name starts with query
    elif name_lower.startswith(query_lower):
        score += 80.0
    # Query is substring of name
    elif query_lower in name_lower:
        score += 60.0

    # Word-level matching
    q_words = [w for w in re.findall(r"\w+", query_lower) if len(w) > 1]
    n_words = set(re.findall(r"\w+", name_lower))
    if q_words:
        matched = sum(1 for w in q_words if w in n_words)
        score += (matched / len(q_words)) * 50.0

    # Penalize DLCs, add-ons, packs unless explicitly requested in query
    for pat in DISTINCT_PRODUCT_PATTERNS:
        if re.search(pat, name, re.IGNORECASE) and not re.search(pat, query, re.IGNORECASE):
            score -= 40.0

    # Small penalty for very verbose names
    score -= len(name.split()) * 1.5

    return score
