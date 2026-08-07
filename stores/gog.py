"""GOG store implementation — search + pricing via GOG API."""

import logging
import re
from typing import Optional

import requests

from stores.base import StoreInterface, SearchResult, PricingInfo
from utils import HEADERS, REQUEST_TIMEOUT, usd_to_inr

logger = logging.getLogger(__name__)

GOG_SEARCH_URL = "https://catalog.gog.com/v1/catalog"
GOG_PRODUCT_URL = "https://api.gog.com/products"
GOG_PRICE_URL = "https://api.gog.com/products/{}/prices"
GOG_STORE_BASE = "https://www.gog.com/en/game"


class GOGStore(StoreInterface):
    """GOG store integration with search and pricing."""

    @property
    def store_name(self) -> str:
        return "gog"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search GOG catalog by game name."""
        results: list[SearchResult] = []
        try:
            params = {
                "limit": limit,
                "query": query.strip(),
                "order": "desc:score",
                "productType": "in:game,pack,dlc",
            }
            resp = requests.get(
                GOG_SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            products = data.get("products", [])
            for product in products:
                pid = str(product.get("id", ""))
                title = product.get("title", "Unknown")
                slug = product.get("slug", "")

                price_data = product.get("price", {})
                currency = price_data.get("currency", "USD")
                current = price_data.get("finalPrice")
                original = price_data.get("basePrice")
                discount = price_data.get("discountPercentage", 0)

                if current is not None:
                    current = round(float(current), 2)
                if original is not None:
                    original = round(float(original), 2)

                if currency == "USD":
                    if current is not None:
                        current = usd_to_inr(current)
                    if original is not None:
                        original = usd_to_inr(original)
                    currency = "INR"

                cover = ""
                images = product.get("images", {})
                if images.get("logo"):
                    cover = images["logo"]
                    if cover.startswith("//"):
                        cover = "https:" + cover
                elif images.get("background"):
                    cover = images["background"]
                    if cover.startswith("//"):
                        cover = "https:" + cover

                edition = self._detect_edition(title)
                url = self.build_url(slug or pid)

                results.append(SearchResult(
                    store=self.store_name,
                    store_id=pid,
                    name=title,
                    current_price=current,
                    original_price=original,
                    currency=currency,
                    discount_percent=discount,
                    cover_image=cover,
                    url=url,
                    is_free=(current == 0) if current else False,
                    edition=edition,
                ))
            logger.info("GOG search for '%s' found %d results", query, len(results))
        except requests.RequestException as e:
            logger.error("GOG search failed for '%s': %s", query, e)
        except Exception as e:
            logger.error("GOG search parse error for '%s': %s", query, e)
        return results

    def get_pricing(self, store_id: str) -> Optional[PricingInfo]:
        """Fetch detailed pricing for a GOG product by ID."""
        try:
            resp = requests.get(
                f"{GOG_PRODUCT_URL}/{store_id}?expand=description",
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            title = data.get("title", "Unknown")
            slug = data.get("slug", str(store_id))

            cover = ""
            images = data.get("images", {})
            if images.get("logo"):
                cover = images["logo"]
                if cover.startswith("//"):
                    cover = "https:" + cover

            price_resp = requests.get(
                GOG_PRICE_URL.format(store_id),
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            price_resp.raise_for_status()
            price_data = price_resp.json()
            usd = price_data.get("USD", {})
            current = usd.get("finalPrice")
            original = usd.get("basePrice")
            discount = usd.get("discountPercentage", 0)

            if current is not None:
                current = round(float(current), 2)
                current = usd_to_inr(current)
            if original is not None:
                original = round(float(original), 2)
                original = usd_to_inr(original)

            sale_name = None
            if discount > 0:
                from recommendations.sale_detector import SaleDetector
                detector = SaleDetector()
                sale_name = detector.detect_sale("gog")

            return PricingInfo(
                store=self.store_name,
                store_id=store_id,
                name=title,
                current_price=current,
                original_price=original or current,
                currency="INR",
                discount_percent=discount,
                cover_image=cover,
                url=self.build_url(slug),
                is_free=(current == 0) if current else False,
                sale_name=sale_name,
                platform="gog",
                drm="DRM-free",
            )
        except requests.RequestException as e:
            logger.error("GOG pricing fetch failed for %s: %s", store_id, e)
            return None
        except Exception as e:
            logger.error("GOG pricing parse error for %s: %s", store_id, e)
            return None

    def build_url(self, store_id: str) -> str:
        return f"{GOG_STORE_BASE}/{store_id}"

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

