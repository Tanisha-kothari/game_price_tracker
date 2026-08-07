"""Deal recommendation engine — analyzes prices and suggests buy/wait."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from comparison.comparator import ComparisonResult, ComparisonRow
from recommendations.sale_detector import SaleDetector

logger = logging.getLogger(__name__)


@dataclass
class DealRecommendation:
    """A recommendation for a single game/store combination."""

    game_name: str
    store: str
    store_display: str
    action: str  # "buy_now", "good_deal", "wait", "track_only"
    reason: str
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: int = 0
    currency: str = "INR"
    sale_name: Optional[str] = None
    is_lowest_recorded: bool = False
    url: str = ""
    cover_image: str = ""

    @property
    def emoji(self) -> str:
        mapping = {
            "buy_now": "\U0001f525",
            "good_deal": "\U0001f7e2",
            "wait": "\U0001f7e1",
            "track_only": "\u2139\ufe0f",
        }
        return mapping.get(self.action, "\u2139\ufe0f")

    @property
    def label(self) -> str:
        mapping = {
            "buy_now": "Buy Now",
            "good_deal": "Good Deal",
            "wait": "Wait",
            "track_only": "Tracking",
        }
        return mapping.get(self.action, self.action)


class RecommendationEngine:
    """Generates buy/wait recommendations based on price data."""

    def __init__(self):
        self.sale_detector = SaleDetector()

    def recommend(
        self,
        comparison: ComparisonResult,
        price_history: Optional[dict[str, list[float]]] = None,
    ) -> list[DealRecommendation]:
        """Generate recommendations for each store option."""
        recommendations = []
        for row in comparison.rows:
            rec = self._recommend_single(
                comparison.canonical_name, row, comparison, price_history
            )
            recommendations.append(rec)
        action_priority = {"buy_now": 0, "good_deal": 1, "track_only": 2, "wait": 3}
        recommendations.sort(key=lambda r: action_priority.get(r.action, 99))
        return recommendations

    def _recommend_single(
        self,
        game_name: str,
        row: ComparisonRow,
        comparison: ComparisonResult,
        price_history: Optional[dict[str, list[float]]] = None,
    ) -> DealRecommendation:
        """Generate recommendation for a single store row."""
        reasons: list[str] = []
        is_best = row.is_best_deal
        has_discount = row.discount_percent > 0
        deep_discount = row.discount_percent >= 70
        moderate_discount = 30 <= row.discount_percent < 70
        sale = self.sale_detector.detect_sale(row.store) or row.sale_name

        is_hist_low = False
        if price_history and row.store in price_history:
            hist = price_history[row.store]
            if hist and row.current_price is not None and row.current_price <= min(hist):
                is_hist_low = True
                reasons.append("Lowest recorded price")

        if row.is_free:
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action="buy_now",
                reason="Free! Grab it now.", current_price=0,
                original_price=row.original_price, currency=row.currency,
                sale_name=sale, is_lowest_recorded=True,
                url=row.url, cover_image=row.cover_image,
            )

        if sale:
            reasons.append(sale)

        if is_best and deep_discount:
            reasons.append("Best overall deal with deep discount")
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action="buy_now",
                reason=" | ".join(reasons),
                current_price=row.current_price,
                original_price=row.original_price,
                discount_percent=row.discount_percent,
                currency=row.currency, sale_name=sale,
                is_lowest_recorded=is_hist_low,
                url=row.url, cover_image=row.cover_image,
            )

        if is_hist_low and has_discount:
            reasons.append("All-time low price")
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action="buy_now",
                reason=" | ".join(reasons),
                current_price=row.current_price,
                original_price=row.original_price,
                discount_percent=row.discount_percent,
                currency=row.currency, sale_name=sale,
                is_lowest_recorded=True,
                url=row.url, cover_image=row.cover_image,
            )

        if deep_discount:
            reasons.append(f"{row.discount_percent}% OFF - deep discount")
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action="buy_now",
                reason=" | ".join(reasons),
                current_price=row.current_price,
                original_price=row.original_price,
                discount_percent=row.discount_percent,
                currency=row.currency, sale_name=sale,
                url=row.url, cover_image=row.cover_image,
            )

        if has_discount:
            reasons.append(f"{row.discount_percent}% OFF")
            action = "good_deal"
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action=action,
                reason=" | ".join(reasons),
                current_price=row.current_price,
                original_price=row.original_price,
                discount_percent=row.discount_percent,
                currency=row.currency, sale_name=sale,
                url=row.url, cover_image=row.cover_image,
            )

        upcoming = self.sale_detector.get_upcoming_sales(row.store, months_ahead=2)
        if upcoming:
            next_sale = upcoming[0]
            reasons.append(f"Expected to be cheaper during {next_sale['name']}")
            return DealRecommendation(
                game_name=game_name, store=row.store,
                store_display=row.store_name_display, action="wait",
                reason=" | ".join(reasons),
                current_price=row.current_price,
                original_price=row.original_price,
                currency=row.currency,
                url=row.url, cover_image=row.cover_image,
            )

        return DealRecommendation(
            game_name=game_name, store=row.store,
            store_display=row.store_name_display, action="track_only",
            reason="No active discount. Price tracked for future changes.",
            current_price=row.current_price,
            original_price=row.original_price,
            currency=row.currency,
            url=row.url, cover_image=row.cover_image,
        )

