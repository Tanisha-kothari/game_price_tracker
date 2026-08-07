"""Epic Games store implementation — search + pricing via Epic GraphQL API."""

import logging
import re
from typing import Optional

import requests

from stores.base import StoreInterface, SearchResult, PricingInfo
from utils import HEADERS, REQUEST_TIMEOUT, usd_to_inr

logger = logging.getLogger(__name__)

EPIC_GRAPHQL_URL = "https://store.epicgames.com/graphql"
EPIC_STORE_BASE = "https://store.epicgames.com/p"

SEARCH_QUERY = """
query searchStore($searchTerms: String!) {
    Catalog {
        searchStore(count: 10, keywords: $searchTerms) {
            elements {
                id
                title
                keyImages { type url }
                productSlug
                price(currency: INR) {
                    totalPrice {
                        originalPrice
                        discountPrice
                        currencyCode
                        discountPercentage
                    }
                }
            }
        }
    }
}
"""

OFFER_PRICE_QUERY = """
query getOffer($offerId: String!) {
    Catalog {
        catalogOffer(offerId: $offerId) {
            id
            title
            keyImages { type url }
            productSlug
            price(currency: INR) {
                totalPrice {
                    originalPrice
                    discountPrice
                    currencyCode
                    discountPercentage
                }
            }
            promotions {
                promotionalOffers {
                    promotionalOffer {
                        startDate
                        endDate
                        discountSetting { discountPercentage }
                    }
                }
            }
        }
    }
}
"""


class EpicStore(StoreInterface):
    """Epic Games store integration via GraphQL API."""

    @property
    def store_name(self) -> str:
        return "epic"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search Epic Games Store by game name."""
        results: list[SearchResult] = []
        try:
            payload = {
                "query": SEARCH_QUERY,
                "variables": {"searchTerms": query.strip()},
            }
            resp = requests.post(
                EPIC_GRAPHQL_URL,
                json=payload,
                headers={**HEADERS, "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            elements = (
                data.get("data", {})
                .get("Catalog", {})
                .get("searchStore", {})
                .get("elements", [])
            )
            for element in elements[:limit]:
                store_id = element.get("id", "")
                title = element.get("title", "Unknown")
                slug = element.get("productSlug") or store_id
                price_data = element.get("price", {})
                total = price_data.get("totalPrice", {}) if price_data else {}
                current = total.get("discountPrice")
                original = total.get("originalPrice")
                discount = total.get("discountPercentage", 0)
                currency = total.get("currencyCode", "INR")

                if current is not None:
                    current = current / 100.0
                if original is not None:
                    original = original / 100.0

                if currency == "USD":
                    if current is not None:
                        current = usd_to_inr(current)
                    if original is not None:
                        original = usd_to_inr(original)
                    currency = "INR"

                cover = self._find_image(
                    element.get("keyImages", []),
                    ["DieselStoreFrontWide", "OfferImageWide", "Thumbnail"],
                )
                edition = self._detect_edition(title)

                results.append(SearchResult(
                    store=self.store_name,
                    store_id=store_id,
                    name=title,
                    current_price=current,
                    original_price=original,
                    currency=currency,
                    discount_percent=discount,
                    cover_image=cover,
                    url=self.build_url(slug),
                    is_free=(current == 0) if current else False,
                    edition=edition,
                ))
            logger.info("Epic search for '%s' found %d results", query, len(results))
        except requests.RequestException as e:
            logger.error("Epic search failed for '%s': %s", query, e)
        except Exception as e:
            logger.error("Epic search parse error for '%s': %s", query, e)
        return results

    def get_pricing(self, store_id: str) -> Optional[PricingInfo]:
        """Fetch detailed pricing for an Epic offer by offer ID."""
        try:
            payload = {
                "query": OFFER_PRICE_QUERY,
                "variables": {"offerId": store_id},
            }
            resp = requests.post(
                EPIC_GRAPHQL_URL,
                json=payload,
                headers={**HEADERS, "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            offer = (
                data.get("data", {})
                .get("Catalog", {})
                .get("catalogOffer")
            )
            if not offer:
                logger.warning("Epic: no offer found for id %s", store_id)
                return None

            title = offer.get("title", "Unknown")
            slug = offer.get("productSlug") or store_id
            price_data = offer.get("price", {})
            total = price_data.get("totalPrice", {}) if price_data else {}
            current = total.get("discountPrice")
            original = total.get("originalPrice")
            discount = total.get("discountPercentage", 0)
            currency = total.get("currencyCode", "INR")

            if current is not None:
                current = current / 100.0
            if original is not None:
                original = original / 100.0

            if currency == "USD":
                if current is not None:
                    current = usd_to_inr(current)
                if original is not None:
                    original = usd_to_inr(original)
                currency = "INR"

            cover = self._find_image(
                offer.get("keyImages", []),
                ["DieselStoreFrontWide", "OfferImageWide", "Thumbnail"],
            )

            sale_name = None
            promotions = offer.get("promotions", {})
            promo_offers = promotions.get("promotionalOffers", [])
            if promo_offers and discount > 0:
                from recommendations.sale_detector import SaleDetector
                detector = SaleDetector()
                sale_name = detector.detect_sale("epic")

            return PricingInfo(
                store=self.store_name,
                store_id=store_id,
                name=title,
                current_price=current,
                original_price=original or current,
                currency=currency,
                discount_percent=discount,
                cover_image=cover,
                url=self.build_url(slug),
                is_free=(current == 0) if current else False,
                sale_name=sale_name,
                platform="epic",
                drm="Epic Games",
            )
        except requests.RequestException as e:
            logger.error("Epic pricing fetch failed for %s: %s", store_id, e)
            return None
        except Exception as e:
            logger.error("Epic pricing parse error for %s: %s", store_id, e)
            return None

    def build_url(self, store_id: str) -> str:
        return f"{EPIC_STORE_BASE}/{store_id}"

    @staticmethod
    def _find_image(images: list[dict], preferred_types: list[str]) -> str:
        for ptype in preferred_types:
            for img in images:
                if img.get("type") == ptype and img.get("url"):
                    url = img["url"]
                    if url.startswith("//"):
                        url = "https:" + url
                    return url
        if images:
            url = images[0].get("url", "")
            if url.startswith("//"):
                url = "https:" + url
            return url
        return ""

    @classmethod
    def _detect_edition(cls, name: str) -> str:
        patterns = [
            (r"\bGOTY\b", "GOTY"),
            (r"\bGame of the Year\b", "GOTY"),
            (r"\bComplete\b", "Complete"),
            (r"\bDefinitive\b", "Definitive"),
            (r"\bDeluxe\b", "Deluxe"),
            (r"\bPremium\b", "Premium"),
            (r"\bUltimate\b", "Ultimate"),
            (r"\bGold\b", "Gold"),
            (r"\bStandard\b", "Standard"),
        ]
        for pattern, edition in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return edition
        return "Standard"

