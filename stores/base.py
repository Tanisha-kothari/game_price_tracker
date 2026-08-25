"""Store abstraction layer — pluggable interface for all game stores.

Adding a new store:
1. Create a new module in stores/ (e.g. humble.py)
2. Implement StoreInterface
3. Register in stores/__init__.py
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


logger = logging.getLogger(__name__)


# ── Data Transfer Objects ────────────────────────────────────────────


@dataclass
class SearchResult:
    """A single game result from a store search."""
    store: str
    store_id: str
    name: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    currency: str = "INR"
    discount_percent: int = 0
    cover_image: str = ""
    url: str = ""
    is_free: bool = False
    edition: str = ""  # e.g. "Standard", "Deluxe", "Complete", "GOTY"
    store_tags: list[str] = field(default_factory=list)


@dataclass
class PricingInfo:
    """Detailed pricing information for a game on a store."""
    store: str
    store_id: str
    name: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    currency: str = "INR"
    discount_percent: int = 0
    cover_image: str = ""
    url: str = ""
    is_free: bool = False
    sale_name: Optional[str] = None  # e.g. "Steam Summer Sale"
    platform: str = ""  # e.g. "steam", "epic", "gog"
    drm: str = ""  # e.g. "Steam", "Epic", "DRM-free"
    store_tags: list[str] = field(default_factory=list)


@dataclass
class CrossStoreResult:
    """Aggregated result for a single game across all stores."""
    canonical_name: str
    editions: dict[str, list[PricingInfo]] = field(default_factory=dict)
    # editions["Standard"] = [PricingInfo(store="steam", ...), PricingInfo(store="epic", ...)]


# ── Abstract Interface ───────────────────────────────────────────────


class StoreInterface(ABC):
    """Every store module implements this interface.

    Two capabilities:
      1. search(query) - Search for games by name, returns SearchResult list
      2. get_pricing(store_id) - Get detailed pricing for a specific game
    """

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Canonical short name, e.g. 'steam', 'epic', 'gog'."""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search the store for games matching the query."""
        ...

    @abstractmethod
    def get_pricing(self, store_id: str) -> Optional[PricingInfo]:
        """Get detailed pricing for a specific game given its store-internal ID."""
        ...

    def build_url(self, store_id: str) -> str:
        """Build the store page URL for a game."""
        ...
