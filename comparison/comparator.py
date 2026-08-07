"""Cross-store price comparison engine."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from stores.base import PricingInfo

logger = logging.getLogger(__name__)


@dataclass
class ComparisonRow:
    """A single row in a cross-store price comparison."""
    store: str
    store_name_display: str
    current_price: Optional[float]
    original_price: Optional[float]
    currency: str
    discount_percent: int
    cover_image: str
    url: str
    sale_name: Optional[str]
    is_free: bool
    platform: str
    drm: str

    # Rankings
    is_cheapest: bool = False
    is_highest_discount: bool = False
    is_best_deal: bool = False

    @property
    def savings(self) -> Optional[float]:
        if self.original_price and self.current_price:
            return round(self.original_price - self.current_price, 2)
        return None


@dataclass
class ComparisonResult:
    """Full comparison result for a single game."""
    canonical_name: str
    rows: list[ComparisonRow] = field(default_factory=list)

    @property
    def cheapest(self) -> Optional[ComparisonRow]:
        priced = [r for r in self.rows if r.current_price is not None]
        if not priced:
            return None
        return min(priced, key=lambda r: r.current_price)

    @property
    def highest_discount(self) -> Optional[ComparisonRow]:
        discounted = [r for r in self.rows if r.discount_percent > 0]
        if not discounted:
            return None
        return max(discounted, key=lambda r: r.discount_percent)

    @property
    def best_deal(self) -> Optional[ComparisonRow]:
        """Best overall deal: weighted score of discount + price."""
        if not self.rows:
            return None
        priced = [r for r in self.rows if r.current_price is not None]
        if not priced:
            return None

        max_discount = max(r.discount_percent for r in priced) if any(r.discount_percent > 0 for r in priced) else 1
        max_price = max(r.current_price for r in priced)  # highest price (worst)

        scored = []
        for r in priced:
            discount_score = (r.discount_percent / max_discount) * 50 if max_discount > 0 else 0
            price_score = (1 - (r.current_price / max_price)) * 50 if max_price > 0 else 0
            scored.append((discount_score + price_score, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    def rank(self):
        """Assign ranking badges to each row."""
        cheapest = self.cheapest
        highest_discount = self.highest_discount
        best_deal = self.best_deal

        for row in self.rows:
            if cheapest and row.store == cheapest.store:
                row.is_cheapest = True
            if highest_discount and row.store == highest_discount.store:
                row.is_highest_discount = True
            if best_deal and row.store == best_deal.store:
                row.is_best_deal = True


def compare_prices(game_name: str, pricing_info: dict[str, PricingInfo]) -> ComparisonResult:
    """Build a comparison from PricingInfo dict.

    Args:
        game_name: Canonical name of the game.
        pricing_info: dict mapping store_name -> PricingInfo.

    Returns:
        ComparisonResult with ranked rows.
    """
    result = ComparisonResult(canonical_name=game_name)

    STORE_DISPLAY = {
        "steam": "Steam",
        "epic": "Epic Games",
        "gog": "GOG",
    }

    for store, info in pricing_info.items():
        if info is None:
            continue
        row = ComparisonRow(
            store=store,
            store_name_display=STORE_DISPLAY.get(store, store.title()),
            current_price=info.current_price,
            original_price=info.original_price,
            currency=info.currency,
            discount_percent=info.discount_percent,
            cover_image=info.cover_image,
            url=info.url,
            sale_name=info.sale_name,
            is_free=info.is_free,
            platform=info.platform,
            drm=info.drm,
        )
        result.rows.append(row)

    result.rank()
    return result
