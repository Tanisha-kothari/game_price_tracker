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

    def _extract_price(self, details: dict) -> tuple[Optional[float], str]:
        price_info = details.get("price_overview")
        if not price_info:
            logger.info("No price info for Steam app")
            return (None, self.DEFAULT_CURRENCY)
        price = price_info.get("final", 0) / 100.0
        currency = price_info.get("currency", self.DEFAULT_CURRENCY)
        return (price, currency)

    def get_game_details(self, url: str) -> GameDetails:
        app_id = extract_steam_app_id(url)
        if not app_id:
            return GameDetails()
        try:
            details = self._fetch_details(app_id)
            if not details:
                return GameDetails(store_id=app_id)
            price, currency = self._extract_price(details)
            return GameDetails(
                name=details.get("name", "Unknown Game"),
                current_price=price,
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

    def _parse_price(self, element: dict):
        price_info = element.get("price") or {}
        total = price_info.get("totalPrice")
        if not total:
            return None, "INR"
        currency = total.get("currencyCode", "USD")
        cents = total.get("discountPrice")
        if cents is None:
            cents = total.get("originalPrice")
        if cents is None:
            return None, currency
        return cents / 100.0, currency

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
            current_price, currency = self._parse_price(element)

            # Normalize to INR for app-wide consistency. Native INR (country=IN)
            # needs no conversion; otherwise convert the fetched currency.
            if currency != "INR" and current_price is not None:
                converted = convert_price(current_price, currency, "INR")
                if converted is not None:
                    current_price, currency = converted, "INR"
                else:
                    logger.warning("Epic: INR conversion failed; keeping %s %s", current_price, currency)

            cover = self._pick_cover(element)
            logger.info("Epic: price=%s %s | cover=%s", current_price, currency, bool(cover))
            return GameDetails(
                name=name,
                current_price=current_price,
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
            price_data = self._fetch_price(game_id)
            current_price = price_data.get("price")
            currency = price_data.get("currency", "USD")
            if current_price is not None and currency != "INR":
                current_price = usd_to_inr(current_price)
                currency = "INR"
            return GameDetails(
                name=name,
                current_price=current_price,
                currency=currency,
                cover_image=cover,
                store_id=str(game_id),
            )
        except requests.RequestException as e:
            logger.error("GOG API request failed for %s: %s", url, e)
            return GameDetails(store_id=str(game_id))

    def _fetch_price(self, product_id: str) -> dict:
        try:
            api_url = f"https://api.gog.com/products/{product_id}/prices"
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            usd = data.get("USD") or {}
            base_price = usd.get("basePrice", usd.get("finalPrice"))
            if base_price is not None:
                return {"price": float(base_price), "currency": "USD"}
            return {"price": None, "currency": "USD"}
        except (requests.RequestException, KeyError, TypeError) as e:
            logger.error("GOG price fetch failed for product %s: %s", product_id, e)
            return {"price": None, "currency": "USD"}

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
