import json
import pytest
from database import (
    load_purchased_games,
    dump_purchased_games,
    add_purchased_game,
    update_purchased_game,
    remove_purchased_game,
    get_purchased_game,
    get_purchased_game_by_title_store,
    is_game_purchased,
    calculate_total_spending,
)

def test_load_and_dump_purchased_games():
    raw_json = json.dumps([
        {
            "id": "p1",
            "title": "Skyrim Special Edition",
            "store": "Steam",
            "url": "https://store.steampowered.com/app/489830",
            "cover": "https://cover.jpg",
            "purchase_date": "2026-08-25",
            "purchase_price": 449.0,
            "currency": "INR",
        },
        {
            "id": "p2",
            "title": "Witcher 3",
            "store": "Epic",
            "url": "https://epicgames.com/p/witcher3",
            "cover": "https://cover2.jpg",
            "purchase_date": "2026-08-20",
            "purchase_price": None,
            "currency": "INR",
        }
    ])
    
    games = load_purchased_games(raw_json)
    assert len(games) == 2
    assert games[0]["title"] == "Skyrim Special Edition"
    assert games[0]["purchase_price"] == 449.0
    assert games[1]["purchase_price"] is None
    
    dumped = dump_purchased_games(games)
    parsed = json.loads(dumped)
    assert len(parsed) == 2
    assert parsed[1]["purchase_price"] is None

def test_add_and_duplicate_protection():
    games = []
    entry1 = {
        "title": "Skyrim Special Edition",
        "store": "Steam",
        "url": "https://store.steampowered.com/app/489830",
        "cover": "https://cover.jpg",
        "purchase_date": "2026-08-25",
        "purchase_price": 449.0,
        "currency": "INR",
    }
    games = add_purchased_game(games, entry1)
    assert len(games) == 1
    assert is_game_purchased(games, "Skyrim Special Edition", "Steam")
    assert not is_game_purchased(games, "Skyrim Special Edition", "Epic Games")

    # Epic version is separate record
    entry2 = {
        "title": "Skyrim Special Edition",
        "store": "Epic Games",
        "url": "https://epicgames.com/p/skyrim",
        "cover": "https://cover.jpg",
        "purchase_date": "2026-08-26",
        "purchase_price": 399.0,
        "currency": "INR",
    }
    games = add_purchased_game(games, entry2)
    assert len(games) == 2

    # Attempt duplicate Steam entry should update existing instead of creating duplicate
    entry1_dup = {
        "title": "Skyrim Special Edition",
        "store": "Steam",
        "purchase_price": 499.0,
    }
    games = add_purchased_game(games, entry1_dup)
    assert len(games) == 2
    steam_game = get_purchased_game_by_title_store(games, "Skyrim Special Edition", "Steam")
    assert steam_game["purchase_price"] == 499.0

def test_update_and_clear_price():
    games = [{
        "id": "p1",
        "title": "Cyberpunk 2077",
        "store": "Steam",
        "purchase_date": "2026-01-01",
        "purchase_price": 1499.0,
        "currency": "INR"
    }]
    
    # Update price and date
    games = update_purchased_game(games, "p1", {"purchase_price": 1299.0, "purchase_date": "2026-01-02"})
    assert games[0]["purchase_price"] == 1299.0
    assert games[0]["purchase_date"] == "2026-01-02"

    # Clear price to None
    games = update_purchased_game(games, "p1", {"purchase_price": None})
    assert games[0]["purchase_price"] is None

def test_remove_purchased_game():
    games = [
        {"id": "p1", "title": "Game 1", "store": "Steam"},
        {"id": "p2", "title": "Game 2", "store": "Epic"}
    ]
    games = remove_purchased_game(games, "p1")
    assert len(games) == 1
    assert games[0]["id"] == "p2"

def test_calculate_total_spending():
    games = [
        {"id": "p1", "purchase_price": 449.0},
        {"id": "p2", "purchase_price": None},
        {"id": "p3", "purchase_price": 1200.50},
    ]
    total = calculate_total_spending(games)
    assert total == 1649.50
