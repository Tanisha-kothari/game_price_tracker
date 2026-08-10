import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests

# ─────────────────────────────────────────────
# price_api.py — Fetchers for Steam, Epic, GOG
# Every price returned carries its own currency.
# Steam: cc=in, never converted (native INR).
# Epic: storefront GraphQL; native INR preferred (country=IN),
#       falls back to USD -> INR conversion when unavailable.
# GOG: USD -> INR converted at fetch time.
# ─────────────────────────────────────────────

from utils import (
    extract_steam_app_id, extract_gog_game_id, extract_epic_slug,
    usd_to_inr, convert_price,
)

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


@dataclass
class GameDetails:
    name: str = "Unknown Game"
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percent: Optional[int] = None
    is_on_sale: bool = False
    sale_started: Optional[str] = None
    sale_last_seen: Optional[str] = None
    sale_end: Optional[str] = None
    currency: str = "INR"
    cover_image: str = ""
    store_id: str = ""


class BaseFetcher(ABC):
    @abstractmethod
    def get_game_details(self, url: str) -> GameDetails:
        ...

    @abstractmethod
    def get_current_price(self, url: str) -> Optional[float]:
        ...


class SteamFetcher(BaseFetcher):
    DEFAULT_CURRENCY = "INR"

    def _fetch_details(self, app_id: str) -> dict:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=in&l=en"
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        app_data = data.get(app_id, {})
        if not app_data.get("success"):
            logger.warning("Steam API success=false for app %s", app_id)
            return {}
        return app_data.get("data", {})

    def _extract_price(self, details: dict) -> dict:
        """Pull current/original/discount from Steam's price_overview.

        Steam already reports discount_percent — we never compute it ourselves.
        """
        price_info = details.get("price_overview")
        if not price_info:
            logger.info("No price info for Steam app")
            return {
                "current": None, "original": None,
                "discount_percent": 0, "is_on_sale": False,
            }

        final_cents = price_info.get("final")
        initial_cents = price_info.get("initial", final_cents)
        discount_percent = price_info.get("discount_percent", 0) or 0

        current = final_cents / 100.0 if final_cents is not None else None
        original = initial_cents / 100.0 if initial_cents is not None else None

        return {
            "current": current,
            "original": original,
            "discount_percent": int(discount_percent),
            "is_on_sale": discount_percent > 0,
        }

    def get_game_details(self, url: str) -> GameDetails:
        app_id = extract_steam_app_id(url)
        if not app_id:
            return GameDetails()
        try:
            details = self._fetch_details(app_id)
            if not details:
                return GameDetails(store_id=app_id)
            price = self._extract_price(details)
            currency = (details.get("price_overview") or {}).get("currency", self.DEFAULT_CURRENCY)
            return GameDetails(
                name=details.get("name", "Unknown Game"),
                current_price=price["current"],
                original_price=price["original"],
                discount_percent=price["discount_percent"],
                is_on_sale=price["is_on_sale"],
                sale_end=None,
                currency=currency,
                cover_image=details.get("header_image", ""),
                store_id=app_id,
            )
        except requests.RequestException as e:
            logger.error("Steam API request failed for app %s: %s", app_id, e)
            return GameDetails(store_id=app_id)

    def get_current_price(self, url: str) -> Optional[float]:
        details = self.get_game_details(url)
        return details.current_price


class EpicFetcher(BaseFetcher):
    # Stable, auth-free storefront GraphQL endpoint. Returns title, price
    # (in minor units), currency and key images for a given search keyword.
    GRAPHQL_URL = "https://store.epicgames.com/graphql"
    SEARCH_QUERY = """
    query($country: String!, $locale: String!, $slug: String!) {
      Catalog {
        searchStore(country: $country, locale: $locale, count: 10, keywords: $slug) {
          elements {
            title
            productSlug
            urlSlug
            namespace
            seller { name }
            price(country: $country) {
              totalPrice { currencyCode discountPrice originalPrice }
            }
            keyImages { type url }
          }
        }
      }
    }
    """
    # Preferred cover image types, most -> least square/portrait friendly.
    COVER_PREFERENCE = ("Thumbnail", "OfferImageTall", "OfferImageWide", "DieselGameBox")
    # Try native INR first (no exchange-rate dependency); fall back to USD.
    COUNTRY_ATTEMPTS = (("IN", "en-US"), ("US", "en-US"))

    def _search(self, slug: str, country: str, locale: str) -> Optional[dict]:
        try:
            resp = requests.post(
                self.GRAPHQL_URL,
                json={
                    "query": self.SEARCH_QUERY,
                    "variables": {"country": country, "locale": locale, "slug": slug},
                },
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as e:
            logger.error("Epic GraphQL request failed (country=%s, slug=%s): %s", country, slug, e)
            return None
        if "errors" in payload:
            logger.error("Epic GraphQL returned errors (country=%s): %s", country, payload["errors"])
            return None
        try:
            return payload["data"]["Catalog"]["searchStore"]
        except (KeyError, TypeError) as e:
            logger.error("Epic GraphQL unexpected response shape: %s", e)
            return None

    def _match_element(self, elements: list, slug: str):
        if not elements:
            return None, False
        for el in elements:
            for key in ("urlSlug", "productSlug"):
                v = el.get(key)
                if v and (v == slug or v.rstrip("/").lower().endswith("/" + slug)):
                    return el, True
        # No exact match — search returned the closest product, use it.
        return elements[0], False

    def _pick_cover(self, element: dict) -> str:
        imgs = element.get("keyImages") or []
        by_type = {i.get("type"): i.get("url") for i in imgs if i.get("url")}
        for preferred in self.COVER_PREFERENCE:
            if by_type.get(preferred):
                return by_type[preferred]
        for url in by_type.values():
            return url
        return ""

    def _parse_price(self, element: dict) -> dict:
        """Return current/original/discount for an Epic element.

        Epic reports discountPrice + originalPrice (minor units). If Epic does
        not provide a percentage we compute it ourselves.
        """
        price_info = element.get("price") or {}
        total = price_info.get("totalPrice")
        if not total:
            return {
                "current": None, "original": None,
                "discount_percent": 0, "is_on_sale": False,
            }
        currency = total.get("currencyCode", "USD")
        original_cents = total.get("originalPrice")
        current_cents = total.get("discountPrice", original_cents)

        current = current_cents / 100.0 if current_cents is not None else None
        original = original_cents / 100.0 if original_cents is not None else None

        discount_percent = price_info.get("discountPercentage")
        is_on_sale = (
            original is not None
            and current is not None
            and original > current
        )
        if discount_percent is None and is_on_sale and original:
            discount_percent = round((original - current) / original * 100)

        return {
            "current": current,
            "original": original,
            "discount_percent": int(discount_percent or 0),
            "is_on_sale": is_on_sale,
        }

    def get_game_details(self, url: str) -> GameDetails:
        slug = extract_epic_slug(url)
        if not slug:
            logger.warning("Epic: could not extract slug from URL: %s", url)
            return GameDetails()
        logger.info("Epic: extracted slug=%s from %s", slug, url)

        for country, locale in self.COUNTRY_ATTEMPTS:
            search = self._search(slug, country, locale)
            if not search:
                continue
            elements = search.get("elements") or []
            logger.info("Epic: country=%s returned %d elements", country, len(elements))
            element, exact = self._match_element(elements, slug)
            if not element:
                continue
            logger.info("Epic: matched '%s' (exact=%s)", element.get("title"), exact)

            name = element.get("title") or slug
            price = self._parse_price(element)
            currency = (element.get("price") or {}).get("totalPrice", {}).get("currencyCode", "INR")

            # Normalize both current and original to INR for app-wide consistency.
            if currency != "INR" and price["current"] is not None:
                converted_current = convert_price(price["current"], currency, "INR")
                converted_original = None
                if price["original"] is not None:
                    converted_original = convert_price(price["original"], currency, "INR")
                if converted_current is not None:
                    price["current"] = converted_current
                    price["original"] = converted_original
                    currency = "INR"
                else:
                    logger.warning("Epic: INR conversion failed; keeping %s %s", price["current"], currency)

            cover = self._pick_cover(element)
            logger.info("Epic: price=%s %s | cover=%s", price["current"], currency, bool(cover))
            return GameDetails(
                name=name,
                current_price=price["current"],
                original_price=price["original"],
                discount_percent=price["discount_percent"],
                is_on_sale=price["is_on_sale"],
                sale_started=None,
                sale_last_seen=None,
                sale_end=None,
                currency=currency,
                cover_image=cover,
                store_id=slug,
            )

        logger.error("Epic: no matching product found for slug=%s", slug)
        return GameDetails(store_id=slug)

    def get_current_price(self, url: str) -> Optional[float]:
        return self.get_game_details(url).current_price


class GOGFetcher(BaseFetcher):
    def get_game_details(self, url: str) -> GameDetails:
        game_id = extract_gog_game_id(url)
        if not game_id:
            return GameDetails()
        try:
            api_url = f"https://api.gog.com/products/{game_id}?expand=description"
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            name = data.get("title", "Unknown Game")
            cover = ""
            images = data.get("images", {})
            if images.get("logo"):
                cover = images["logo"]
                if cover.startswith("//"):
                    cover = "https:" + cover
            price = self._fetch_price(game_id)
            currency = price.get("currency", "USD")
            current = price.get("current")
            original = price.get("original")
            discount_percent = price.get("discount_percent", 0)
            is_on_sale = price.get("is_on_sale", False)
            if current is not None and currency != "INR":
                current = usd_to_inr(current)
                if original is not None:
                    original = usd_to_inr(original)
                currency = "INR"
            return GameDetails(
                name=name,
                current_price=current,
                original_price=original,
                discount_percent=discount_percent,
                is_on_sale=is_on_sale,
                sale_started=None,
                sale_last_seen=None,
                sale_end=None,
                currency=currency,
                cover_image=cover,
                store_id=str(game_id),
            )
        except requests.RequestException as e:
            logger.error("GOG API request failed for %s: %s", url, e)
            return GameDetails(store_id=str(game_id))

    def _fetch_price(self, product_id: str) -> dict:
        """Return base (original) + final (current) price from GOG.

        GOG prices response has currency keys (e.g. USD) each carrying
        basePrice/finalPrice; we compute the discount percent if needed.
        """
        try:
            api_url = f"https://api.gog.com/products/{product_id}/prices"
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            usd = data.get("USD") or {}
            base_price = usd.get("basePrice")
            final_price = usd.get("finalPrice", base_price)
            original = float(base_price) if base_price is not None else None
            current = float(final_price) if final_price is not None else None
            is_on_sale = original is not None and current is not None and original > current
            discount_percent = usd.get("discountPercent")
            if discount_percent is None and is_on_sale and original:
                discount_percent = round((original - current) / original * 100)
            return {
                "current": current,
                "original": original,
                "discount_percent": int(discount_percent or 0),
                "is_on_sale": is_on_sale,
                "currency": "USD",
            }
        except (requests.RequestException, KeyError, TypeError) as e:
            logger.error("GOG price fetch failed for product %s: %s", product_id, e)
            return {"current": None, "original": None, "discount_percent": 0, "is_on_sale": False, "currency": "USD"}

    def get_current_price(self, url: str) -> Optional[float]:
        return self.get_game_details(url).current_price


FETCHER_MAP = {
    "steam": SteamFetcher,
    "epic": EpicFetcher,
    "gog": GOGFetcher,
}


def get_fetcher(store: str) -> BaseFetcher:
    fetcher_cls = FETCHER_MAP.get(store)
    if not fetcher_cls:
        raise ValueError(f"Unsupported store: {store}")
    return fetcher_cls()


def fetch_game_details(store: str, url: str) -> GameDetails:
    return get_fetcher(store).get_game_details(url)


def fetch_current_price(store: str, url: str) -> Optional[float]:
    return get_fetcher(store).get_current_price(url)
