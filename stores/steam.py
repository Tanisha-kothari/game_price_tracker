"""Steam store implementation — search + pricing via Steam storefront APIs."""

import logging
import re
from typing import Optional

import requests

from stores.base import StoreInterface, SearchResult, PricingInfo
from utils import HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

STEAM_STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch"
STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_STORE_BASE = "https://store.steampowered.com/app"


class SteamStore(StoreInterface):
    """Steam store integration with name search and price fetching."""

    @property
    def store_name(self) -> str:
        return "steam"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search Steam storefront by game name."""
        results: list[SearchResult] = []
        clean_query = query.strip()
        if not clean_query:
            return results

        logger.info("Steam search initiated for query: '%s'", clean_query)
        try:
            params = {"term": clean_query, "l": "en", "cc": "in"}
            resp = requests.get(
                STEAM_STORE_SEARCH_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            for item in items[:limit]:
                app_id = str(item.get("id", ""))
                name = item.get("name", "Unknown")
                price_data = item.get("price", {})
                if price_data:
                    current_price = price_data.get("final", 0) / 100.0
                    original_price = price_data.get("initial", 0) / 100.0
                    discount = price_data.get("discount_percent", 0)
                else:
                    current_price = None
                    original_price = None
                    discount = 0

                cover = item.get("tiny_image", "") or item.get("header_image", "")
                if app_id and not cover:
                    cover = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"

                edition = self._detect_edition(name)

                results.append(SearchResult(
                    store=self.store_name,
                    store_id=app_id,
                    name=name,
                    current_price=current_price,
                    original_price=original_price or current_price,
                    currency="INR",
                    discount_percent=discount,
                    cover_image=cover,
                    url=self.build_url(app_id),
                    is_free=(current_price == 0) if current_price is not None else False,
                    edition=edition,
                ))
            logger.info("Steam search for '%s' returned %d results", clean_query, len(results))
        except requests.RequestException as e:
            logger.error("Steam search network error for '%s': %s", clean_query, e)
        except Exception as e:
            logger.error("Steam search parse error for '%s': %s", clean_query, e)
        return results

    def get_pricing(self, store_id: str) -> Optional[PricingInfo]:
        """Fetch detailed pricing for a Steam app by app ID."""
        clean_id = store_id.strip()
        if not clean_id:
            return None

        logger.info("Steam pricing requested for app: '%s'", clean_id)
        try:
            resp = requests.get(
                f"{STEAM_APP_DETAILS_URL}?appids={clean_id}&cc=in&l=en",
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            app_data = data.get(clean_id, {})
            if not app_data.get("success"):
                logger.warning("Steam API success=false for app %s", clean_id)
                return None
            details = app_data.get("data", {})
            name = details.get("name", "Unknown Game")
            price_info = details.get("price_overview", {})
            current_price = price_info.get("final", 0) / 100.0 if price_info else None
            original_price = price_info.get("initial", 0) / 100.0 if price_info else None
            currency = price_info.get("currency", "INR") if price_info else "INR"
            discount = price_info.get("discount_percent", 0) if price_info else 0
            cover = details.get("header_image", "")
            sale_name = self._detect_sale_from_page(clean_id, discount)
            return PricingInfo(
                store=self.store_name,
                store_id=clean_id,
                name=name,
                current_price=current_price,
                original_price=original_price or current_price,
                currency=currency,
                discount_percent=discount,
                cover_image=cover,
                url=self.build_url(clean_id),
                is_free=(current_price == 0) if current_price is not None else False,
                sale_name=sale_name,
                platform="steam",
                drm="Steam",
            )
        except requests.RequestException as e:
            logger.error("Steam pricing fetch failed for app %s: %s", clean_id, e)
            return None

    def build_url(self, store_id: str) -> str:
        return f"{STEAM_STORE_BASE}/{store_id}"

    _EDITION_PATTERNS = [
        (r"\bGOTY\b", "GOTY"),
        (r"\bGame of the Year\b", "GOTY"),
        (r"\bComplete\b", "Complete"),
        (r"\bDefinitive\b", "Definitive"),
        (r"\bDeluxe\b", "Deluxe"),
        (r"\bPremium\b", "Premium"),
        (r"\bUltimate\b", "Ultimate"),
        (r"\bGold\b", "Gold"),
        (r"\bEnhanced\b", "Enhanced"),
        (r"\bRemastered\b", "Remastered"),
        (r"\bStandard\b", "Standard"),
        (r"\bDigital Deluxe\b", "Deluxe"),
        (r"\bCollector's?\b", "Collector"),
    ]

    @classmethod
    def _detect_edition(cls, name: str) -> str:
        for pattern, edition in cls._EDITION_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return edition
        return "Standard"

    @classmethod
    def _detect_sale_from_page(cls, app_id: str, discount_percent: int) -> Optional[str]:
        if discount_percent <= 0:
            return None
        try:
            url = f"{STEAM_STORE_BASE}/{app_id}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            html = resp.text
            sale_patterns = [
                (r"Steam Summer Sale", "Steam Summer Sale"),
                (r"Steam Winter Sale", "Steam Winter Sale"),
                (r"Steam Autumn Sale", "Steam Autumn Sale"),
                (r"Steam Spring Sale", "Steam Spring Sale"),
                (r"Steam Halloween Sale", "Steam Halloween Sale"),
                (r"Golden Week", "Golden Week Sale"),
            ]
            for pattern, sale_name in sale_patterns:
                if sale_name and re.search(pattern, html, re.IGNORECASE):
                    return sale_name
            if discount_percent >= 10:
                return "Store Sale"
            return None
        except Exception:
            return None
