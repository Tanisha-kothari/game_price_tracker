"""Epic Games store implementation — search + pricing via Epic GraphQL API."""

import logging
import re
from typing import Optional

import requests

from stores.base import StoreInterface, SearchResult, PricingInfo
from utils import HEADERS, REQUEST_TIMEOUT, convert_price

logger = logging.getLogger(__name__)

EPIC_GRAPHQL_URL = "https://store.epicgames.com/graphql"
EPIC_STORE_BASE = "https://store.epicgames.com/p"

SEARCH_QUERY = """
query searchStoreQuery($keywords: String, $locale: String, $country: String!) {
    Catalog {
        searchStore(keywords: $keywords, locale: $locale, country: $country, count: 10) {
            elements {
                id
                title
                productSlug
                urlSlug
                namespace
                price(country: $country) {
                    totalPrice {
                        originalPrice
                        discountPrice
                        currencyCode
                    }
                }
                keyImages { type url }
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
        clean_query = query.strip()
        if not clean_query:
            return results

        logger.info("Epic search initiated for query: '%s'", clean_query)
        try:
            payload = {
                "query": SEARCH_QUERY,
                "variables": {
                    "country": "IN",
                    "locale": "en-US",
                    "keywords": clean_query,
                },
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
                offer_id = element.get("id", "")
                title = element.get("title", "Unknown")

                # Extract product slug accurately
                slug = element.get("productSlug") or element.get("urlSlug")
                if not slug:
                    slug = offer_id

                slug = slug.split("/")[-1].lower() if slug else offer_id

                price_data = element.get("price", {})
                total = price_data.get("totalPrice", {}) if price_data else {}
                original_cents = total.get("originalPrice")
                current_cents = total.get("discountPrice", original_cents)
                currency = total.get("currencyCode", "INR")

                current = current_cents / 100.0 if current_cents is not None else None
                original = original_cents / 100.0 if original_cents is not None else None

                if currency != "INR" and current is not None:
                    converted_current = convert_price(current, currency, "INR")
                    converted_original = convert_price(original, currency, "INR") if original else None
                    if converted_current is not None:
                        current = converted_current
                        original = converted_original
                        currency = "INR"

                is_on_sale = (
                    original is not None
                    and current is not None
                    and original > current
                )
                discount = round((original - current) / original * 100) if is_on_sale and original else 0

                cover = self._find_image(
                    element.get("keyImages", []),
                    ["OfferImageTall", "DieselStoreFrontWide", "OfferImageWide", "Thumbnail", "DieselGameBox"],
                )
                edition = self._detect_edition(title)

                results.append(SearchResult(
                    store=self.store_name,
                    store_id=slug,
                    name=title,
                    current_price=current,
                    original_price=original or current,
                    currency=currency,
                    discount_percent=discount,
                    cover_image=cover,
                    url=self.build_url(slug),
                    is_free=(current == 0) if current is not None else False,
                    edition=edition,
                ))
            logger.info("Epic search for '%s' returned %d results", clean_query, len(results))
        except requests.RequestException as e:
            logger.error("Epic search network error for '%s': %s", clean_query, e)
        except Exception as e:
            logger.error("Epic search parse error for '%s': %s", clean_query, e)
        return results

    def get_pricing(self, store_id: str) -> Optional[PricingInfo]:
        """Fetch detailed pricing for an Epic game by its slug or ID."""
        clean_id = store_id.strip().lower()
        if not clean_id:
            return None

        logger.info("Epic pricing requested for slug: '%s'", clean_id)
        try:
            from price_api import EpicFetcher
            fetcher = EpicFetcher()
            url = self.build_url(clean_id)
            details = fetcher.get_game_details(url)
            if details.current_price is None and not details.name:
                logger.warning("Epic: no game details found for slug: %s", clean_id)
                return None

            sale_name = None
            if details.is_on_sale:
                try:
                    from recommendations.sale_detector import SaleDetector
                    detector = SaleDetector()
                    sale_name = detector.detect_sale("epic")
                except Exception:
                    sale_name = "Epic Store Sale"

            return PricingInfo(
                store=self.store_name,
                store_id=details.store_id or clean_id,
                name=details.name,
                current_price=details.current_price,
                original_price=details.original_price or details.current_price,
                currency=details.currency or "INR",
                discount_percent=details.discount_percent or 0,
                cover_image=details.cover_image,
                url=url,
                is_free=(details.current_price == 0) if details.current_price is not None else False,
                sale_name=sale_name,
                platform="epic",
                drm="Epic Games",
            )
        except Exception as e:
            logger.error("Epic get_pricing error for slug '%s': %s", clean_id, e)
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
