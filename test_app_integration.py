import os
import json
import pytest
import database
from database import (
    load_purchased_games,
    dump_purchased_games,
    add_purchased_game,
    update_purchased_game,
    remove_purchased_game,
    calculate_total_spending,
    is_game_purchased,
    get_purchased_game_by_title_store,
)

def test_full_purchased_games_lifecycle(tmp_path):
    json_path = tmp_path / "purchased_games.json"
    
    # 1. Start with empty
    games = load_purchased_games("")
    assert len(games) == 0
    assert calculate_total_spending(games) == 0.0

    # 2. Add Steam game with price
    entry_steam = {
        "title": "The Elder Scrolls V: Skyrim Special Edition",
        "store": "Steam",
        "url": "https://store.steampowered.com/app/489830",
        "cover": "https://cdn.akamai.steamstatic.com/cover.jpg",
        "purchase_date": "2026-08-25",
        "purchase_price": 449.0,
        "currency": "INR"
    }
    games = add_purchased_game(games, entry_steam)
    assert len(games) == 1
    assert is_game_purchased(games, "The Elder Scrolls V: Skyrim Special Edition", "Steam")
    assert not is_game_purchased(games, "The Elder Scrolls V: Skyrim Special Edition", "Epic Games")
    assert calculate_total_spending(games) == 449.0

    # 3. Add Epic Games game without price (optional price)
    entry_epic = {
        "title": "The Elder Scrolls V: Skyrim Special Edition",
        "store": "Epic Games",
        "url": "https://store.epicgames.com/p/skyrim",
        "cover": "https://epic.com/cover.jpg",
        "purchase_date": "2026-08-26",
        "purchase_price": None,
        "currency": "INR"
    }
    games = add_purchased_game(games, entry_epic)
    assert len(games) == 2
    # Verify price calculation ignores None and does NOT treat as zero
    assert calculate_total_spending(games) == 449.0

    # 4. Save to JSON and reload
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(dump_purchased_games(games))

    with open(json_path, "r", encoding="utf-8") as f:
        reloaded = load_purchased_games(f.read())
    assert len(reloaded) == 2
    assert reloaded[0]["purchase_price"] == 449.0
    assert reloaded[1]["purchase_price"] is None

    # 5. Edit purchase details (update price for epic version, update date for steam version)
    epic_item = get_purchased_game_by_title_store(reloaded, "The Elder Scrolls V: Skyrim Special Edition", "Epic Games")
    assert epic_item is not None
    reloaded = update_purchased_game(reloaded, epic_item["id"], {"purchase_price": 399.0, "purchase_date": "2026-08-27"})
    assert calculate_total_spending(reloaded) == 848.0

    # 6. Clear purchase price on Epic item
    reloaded = update_purchased_game(reloaded, epic_item["id"], {"purchase_price": None})
    assert calculate_total_spending(reloaded) == 449.0

    # 7. Remove item from library
    steam_item = get_purchased_game_by_title_store(reloaded, "The Elder Scrolls V: Skyrim Special Edition", "Steam")
    assert steam_item is not None
    reloaded = remove_purchased_game(reloaded, steam_item["id"])
    assert len(reloaded) == 1
    assert not is_game_purchased(reloaded, "The Elder Scrolls V: Skyrim Special Edition", "Steam")
    assert is_game_purchased(reloaded, "The Elder Scrolls V: Skyrim Special Edition", "Epic Games")

def test_app_imports_and_compiles():
    import app
    assert hasattr(app, "render_my_library_view")
    assert hasattr(app, "render_mark_as_purchased_popover")
    assert hasattr(app, "load_purchased_games_data")
    assert hasattr(app, "save_purchased_games_data")
