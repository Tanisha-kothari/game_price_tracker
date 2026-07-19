import json
import logging
from copy import deepcopy
from typing import Optional

from utils import today_str

logger = logging.getLogger(__name__)

GAMES_FILE = "games.json"
HISTORY_FILE = "history.json"

DEFAULT_GAMES: list[dict] = []
DEFAULT_HISTORY: dict[str, dict[str, float]] = {}


def load_games(content: str) -> list[dict]:
    if not content.strip():
        return deepcopy(DEFAULT_GAMES)
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return deepcopy(DEFAULT_GAMES)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse games.json: %s", e)
        return deepcopy(DEFAULT_GAMES)


def load_history(content: str) -> dict[str, dict[str, float]]:
    if not content.strip():
        return deepcopy(DEFAULT_HISTORY)
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        return deepcopy(DEFAULT_HISTORY)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse history.json: %s", e)
        return deepcopy(DEFAULT_HISTORY)


def dump_games(games: list[dict]) -> str:
    return json.dumps(games, indent=2, ensure_ascii=False)


def dump_history(history: dict[str, dict[str, float]]) -> str:
    return json.dumps(history, indent=2, ensure_ascii=False)


def add_game(games: list[dict], game: dict) -> tuple[list[dict], bool]:
    game_id = game.get("id", "")
    for existing in games:
        if existing.get("id") == game_id:
            logger.warning("Duplicate game skipped: %s (%s)", game.get("name"), game_id)
            return games, False
    games.append(game)
    return games, True


def remove_game(games: list[dict], game_id: str) -> list[dict]:
    return [g for g in games if g.get("id") != game_id]


def update_game_price(games: list[dict], game_id: str, price: Optional[float],
                      currency: str = "USD") -> list[dict]:
    today = today_str()
    for game in games:
        if game.get("id") == game_id:
            game["current_price"] = price
            game["currency"] = currency
            game["last_checked"] = today
            lowest = game.get("lowest_price")
            if price is not None and (lowest is None or price < lowest):
                game["lowest_price"] = price
            break
    return games


def update_price_history(history: dict[str, dict[str, float]],
                         game_id: str, price: Optional[float]) -> dict[str, dict[str, float]]:
    today = today_str()
    if game_id not in history:
        history[game_id] = {}
    if price is not None:
        history[game_id][today] = price
    return history


def get_game_by_id(games: list[dict], game_id: str) -> Optional[dict]:
    for game in games:
        if game.get("id") == game_id:
            return game
    return None


def detect_price_change(history: dict[str, dict[str, float]],
                        game_id: str, current_price: Optional[float]) -> Optional[float]:
    if game_id not in history or not history[game_id]:
        return None
    sorted_dates = sorted(history[game_id].keys())
    if len(sorted_dates) < 2:
        return None
    prev_price = history[game_id][sorted_dates[-2]]
    if current_price is None:
        return None
    diff = current_price - prev_price
    if abs(diff) < 0.001:
        return None
    return diff


def get_lowest_price(games: list[dict], game_id: str) -> Optional[float]:
    for game in games:
        if game.get("id") == game_id:
            return game.get("lowest_price")
    return None
