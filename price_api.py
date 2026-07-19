import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import requests

from utils import (
    extract_steam_app_id, extract_gog_game_id, extract_epic_slug,
    parse_price, usd_to_inr,
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
    currency: str = "USD"
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
    def get_game_details(self, url: str) -> GameDetails:
        app_id = extract_steam_app_id(url)
        if not app_id:
            return GameDetails()
        try:
            api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=in&l=en"
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            app_data = data.get(app_id, {})
            if not app_data.get("success"):
                logger.warning("Steam API returned success=false for app %s", app_id)
                return GameDetails(store_id=app_id)
            details = app_data.get("data", {})
            name = details.get("name", "Unknown Game")
            cover = details.get("header_image", "")
            price_info = details.get("price_overview", {})
            if price_info:
                current_price = price_info.get("final", 0) / 100.0
                currency = price_info.get("currency", "USD")
                if currency != "INR":
                    current_price = usd_to_inr(current_price)
                    currency = "INR"
            else:
                current_price = None
                currency = "INR"
            return GameDetails(
                name=name,
                current_price=current_price,
                currency=currency,
                cover_image=cover,
                store_id=app_id,
            )
        except requests.RequestException as e:
            logger.error("Steam API request failed for %s: %s", url, e)
            return GameDetails(store_id=app_id)

    def get_current_price(self, url: str) -> Optional[float]:
        return self.get_game_details(url).current_price


class EpicFetcher(BaseFetcher):
    def get_game_details(self, url: str) -> GameDetails:
        slug = extract_epic_slug(url)
        if not slug:
            return GameDetails()
        try:
            api_url = "https://store-content.ak.epicgames.com/api/en-US/content/products/" + slug
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            name = data.get("title", slug)
            pages = data.get("pages", [])
            cover = ""
            for page in pages:
                for item in page.get("data", {}).get("slides", []):
                    img = item.get("background", {})
                    if isinstance(img, dict) and img.get("url"):
                        cover = img["url"]
                        break
            price_data = self._fetch_price(slug)
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
                store_id=slug,
            )
        except requests.RequestException as e:
            logger.error("Epic API request failed for %s: %s", url, e)
            return GameDetails(store_id=slug)

    def _fetch_price(self, slug: str) -> dict:
        try:
            api_url = f"https://store-content.ak.epicgames.com/api/en-US/content/products/{slug}"
            resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            for page in data.get("pages", []):
                offer = page.get("data", {}).get("offer", {})
                if offer:
                    price_data = offer.get("price", {})
                    if price_data:
                        total = price_data.get("totalPrice", {})
                        if total:
                            return {
                                "price": total.get("discountPrice", total.get("originalPrice", 0)) / 100.0,
                                "currency": total.get("currencyCode", "USD"),
                            }
            return {"price": None, "currency": "USD"}
        except (requests.RequestException, KeyError, TypeError) as e:
            logger.error("Epic price fetch failed for %s: %s", slug, e)
            return {"price": None, "currency": "USD"}

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
    fetcher = get_fetcher(store)
    return fetcher.get_game_details(url)


def fetch_current_price(store: str, url: str) -> Optional[float]:
    fetcher = get_fetcher(store)
    return fetcher.get_current_price(url)
