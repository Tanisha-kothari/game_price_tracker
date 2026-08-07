"""Sale detection — maintainable strategy using calendar metadata.

Uses a JSON-based sale calendar file (sale_calendar.json) that can be
updated without code changes. Falls back to page-scraping when available.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

SALE_CALENDAR_PATH = os.path.join(os.path.dirname(__file__), "..", "sale_calendar.json")


@dataclass
class SaleEvent:
    name: str
    store: str
    months: list[int] = field(default_factory=list)
    approximate: bool = True  # True = estimated dates


DEFAULT_CALENDAR: list[dict] = [
    {
        "name": "Steam Summer Sale",
        "store": "steam",
        "start_month": 6,
        "end_month": 7,
        "approximate": True,
    },
    {
        "name": "Steam Winter Sale",
        "store": "steam",
        "start_month": 12,
        "end_month": 1,
        "approximate": True,
    },
    {
        "name": "Steam Autumn Sale",
        "store": "steam",
        "start_month": 11,
        "end_month": 11,
        "approximate": True,
    },
    {
        "name": "Steam Spring Sale",
        "store": "steam",
        "start_month": 3,
        "end_month": 3,
        "approximate": True,
    },
    {
        "name": "Steam Halloween Sale",
        "store": "steam",
        "start_month": 10,
        "end_month": 10,
        "approximate": True,
    },
    {
        "name": "Epic Mega Sale",
        "store": "epic",
        "start_month": 5,
        "end_month": 6,
        "approximate": True,
    },
    {
        "name": "Epic Holiday Sale",
        "store": "epic",
        "start_month": 12,
        "end_month": 1,
        "approximate": True,
    },
    {
        "name": "Golden Week Sale",
        "store": "steam",
        "start_month": 4,
        "end_month": 5,
        "approximate": True,
    },
    {
        "name": "GOG Summer Sale",
        "store": "gog",
        "start_month": 6,
        "end_month": 7,
        "approximate": True,
    },
    {
        "name": "GOG Winter Sale",
        "store": "gog",
        "start_month": 12,
        "end_month": 1,
        "approximate": True,
    },
]


class SaleDetector:
    """Detects active sales using calendar metadata + optional live data."""

    def __init__(self, calendar_path: Optional[str] = None):
        self.calendar_path = calendar_path or SALE_CALENDAR_PATH
        self._calendar: list[dict] = []
        self._load_calendar()

    def _load_calendar(self) -> None:
        """Load calendar from JSON file, falling back to defaults."""
        try:
            if os.path.exists(self.calendar_path):
                with open(self.calendar_path, "r") as f:
                    self._calendar = json.load(f)
                logger.info("Loaded sale calendar from %s", self.calendar_path)
                return
        except Exception as e:
            logger.warning("Failed to load sale calendar: %s", e)

        # Fall back to defaults
        self._calendar = DEFAULT_CALENDAR
        # Save default calendar for user editing
        try:
            os.makedirs(os.path.dirname(self.calendar_path) or ".", exist_ok=True)
            with open(self.calendar_path, "w") as f:
                json.dump(DEFAULT_CALENDAR, f, indent=2)
            logger.info("Created default sale calendar at %s", self.calendar_path)
        except Exception as e:
            logger.warning("Could not save default sale calendar: %s", e)

    def detect_sale(self, store: str) -> Optional[str]:
        """Detect currently active sale for a given store.

        Returns sale name or None if no known sale is active.
        """
        today = date.today()
        current_month = today.month

        for sale in self._calendar:
            if sale.get("store") != store:
                continue
            start = sale.get("start_month")
            end = sale.get("end_month")
            if start is None or end is None:
                continue

            # Handle cross-year sales (e.g. Dec -> Jan)
            if start <= end:
                if start <= current_month <= end:
                    return sale["name"]
            else:
                # Cross-year: e.g. start=12, end=1
                if current_month >= start or current_month <= end:
                    return sale["name"]

        return None

    def get_upcoming_sales(self, store: str, months_ahead: int = 3) -> list[dict]:
        """Get upcoming sales for a store within the next N months."""
        today = date.today()
        current_month = today.month
        current_year = today.year
        upcoming = []

        for sale in self._calendar:
            if sale.get("store") != store:
                continue
            start = sale.get("start_month")
            if start is None:
                continue
            # Calculate months until start
            if start >= current_month:
                months_until = start - current_month
            else:
                months_until = (12 - current_month) + start

            if 0 <= months_until <= months_ahead:
                upcoming.append({
                    "name": sale["name"],
                    "months_until": months_until,
                    "approximate": sale.get("approximate", True),
                })

        return sorted(upcoming, key=lambda x: x["months_until"])

    def is_discount_sale(self, store: str, discount_percent: int) -> Optional[str]:
        """Check if a given discount level corresponds to a known sale."""
        if discount_percent <= 0:
            return None
        sale = self.detect_sale(store)
        if sale:
            return sale
        # Deep discount but no known sale event
        if discount_percent >= 50:
            return "Major Discount"
        if discount_percent >= 25:
            return "Discount"
        return None
