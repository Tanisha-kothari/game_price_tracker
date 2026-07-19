import os
import logging
from typing import Optional

import streamlit as st

from utils import (
    detect_store, is_valid_url, generate_game_id, format_price,
    today_str, now_str, games_to_csv, history_to_csv,
    extract_steam_app_id, extract_gog_game_id, extract_epic_slug,
)
from database import (
    load_games, load_history, add_game, remove_game, get_game_by_id,
)
from price_api import fetch_game_details
from github_manager import GitHubManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("app")

st.set_page_config(
    page_title="Game Price Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .block-container { padding: 1.5rem 2rem !important; max-width: 1200px; }
    h1, h2, h3 { color: #f1f5f9 !important; }
    .stTextInput>div>div>input {
        background-color: #1e293b; color: #f1f5f9; border: 1px solid #334155;
        border-radius: 8px; padding: 10px 14px;
    }
    .stTextInput>div>div>input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.3); }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white; border: none; border-radius: 8px; padding: 8px 20px;
        font-weight: 600; transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.4);
    }
    .stButton>button[kind="secondary"] {
        background: #1e293b; color: #f1f5f9; border: 1px solid #334155;
    }
    div[data-testid="stNotification"] { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }
    .game-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155; border-radius: 16px; padding: 20px;
        margin-bottom: 16px; transition: all 0.3s;
    }
    .game-card:hover { border-color: #3b82f6; box-shadow: 0 4px 20px rgba(59,130,246,0.15); }
    .game-card img { border-radius: 12px; width: 100%; max-height: 200px; object-fit: cover; }
    .game-title { font-size: 18px; font-weight: 700; color: #f1f5f9; margin: 8px 0 4px; }
    .game-store { font-size: 13px; color: #64748b; margin-bottom: 12px; }
    .price-row { display: flex; justify-content: space-between; margin: 4px 0; }
    .price-label { color: #94a3b8; font-size: 13px; }
    .price-value { color: #f1f5f9; font-weight: 600; font-size: 14px; }
    .price-drop { color: #22c55e; }
    .price-lowest { color: #22c55e; }
    .price-target-met { color: #22c55e; }
    .stDownloadButton>button {
        background: #1e293b; color: #f1f5f9; border: 1px solid #334155;
        border-radius: 8px; padding: 8px 20px; font-weight: 500;
    }
    @media (max-width: 640px) {
        .block-container { padding: 1rem !important; }
        .game-card { padding: 14px; }
    }
</style>
"""


def init_github() -> Optional[GitHubManager]:
    token = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
    owner = st.secrets.get("REPO_OWNER", os.environ.get("REPO_OWNER", ""))
    repo = st.secrets.get("REPO_NAME", os.environ.get("REPO_NAME", ""))

    gh = GitHubManager(token, owner, repo)

    # Debug the exact URL being used
    st.write("GitHub URL:", gh._base_url)

    if not gh.test_connection():
        st.error("Cannot connect to GitHub.")
        return None

    return gh


def load_games_from_github(gh: GitHubManager) -> list[dict]:
    try:
        content = gh.get_file_content("games.json")
        if content is None:
            return []
        return load_games(content)
    except Exception as e:
        logger.error("Failed to load games: %s", e)
        st.error(f"Failed to load games: {e}")
        return []


def load_history_from_github(gh: GitHubManager) -> dict:
    try:
        content = gh.get_file_content("history.json")
        if content is None:
            return {}
        return load_history(content)
    except Exception as e:
        logger.error("Failed to load history: %s", e)
        return {}


def render_game_card(game: dict, gh: GitHubManager, games: list[dict]):
    game_id = game["id"]
    store = game["store"]
    name = game.get("name", "Unknown")
    current = game.get("current_price")
    lowest = game.get("lowest_price")
    target = game.get("target_price")
    currency = game.get("currency", "USD")
    last_checked = game.get("last_checked", "Never")
    cover = game.get("cover_image", "")
    url = game.get("url", "")

    store_labels = {"steam": "Steam", "epic": "Epic Games", "gog": "GOG"}
    store_display = store_labels.get(store, store.title())

    with st.container():
        st.markdown('<div class="game-card">', unsafe_allow_html=True)
        cols = st.columns([1, 2, 1])

        with cols[0]:
            if cover:
                st.image(cover, use_container_width=True)

        with cols[1]:
            st.markdown(f'<div class="game-title">{name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="game-store">{store_display}</div>', unsafe_allow_html=True)

            st.markdown(
                f'<div class="price-row"><span class="price-label">Current</span>'
                f'<span class="price-value">{format_price(current, currency)}</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="price-row"><span class="price-label">Lowest</span>'
                f'<span class="price-value price-lowest">{format_price(lowest, currency)}</span></div>',
                unsafe_allow_html=True,
            )

            if target is not None:
                target_met = current is not None and current <= target
                met_class = "price-target-met" if target_met else ""
                st.markdown(
                    f'<div class="price-row"><span class="price-label">Target</span>'
                    f'<span class="price-value {met_class}">{format_price(target, currency)}'
                    f'{" ✅" if target_met else ""}</span></div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div class="price-row"><span class="price-label">Last checked</span>'
                f'<span class="price-value">{last_checked}</span></div>',
                unsafe_allow_html=True,
            )

        with cols[2]:
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🗑️", key=f"del_{game_id}", help="Delete game"):
                    updated = remove_game(games, game_id)
                    try:
                        gh.save_games(
                            updated,
                            f"Remove {name} from tracker"
                        )
                        st.success(f"Removed {name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to remove: {e}")

            with c2:
                if st.button("🔄", key=f"ref_{game_id}", help="Refresh price"):
                    with st.spinner(f"Checking {name}..."):
                        try:
                            details = fetch_game_details(store, url)
                            for g in games:
                                if g["id"] == game_id:
                                    g["current_price"] = details.current_price
                                    g["currency"] = details.currency
                                    g["last_checked"] = today_str()
                                    if details.current_price is not None:
                                        old_low = g.get("lowest_price")
                                        if old_low is None or details.current_price < old_low:
                                            g["lowest_price"] = details.current_price
                                    break
                            gh.save_games(games, f"Refresh price for {name}")
                            st.success(f"{name}: {format_price(details.current_price, details.currency)}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Refresh failed: {e}")

            with c3:
                if url:
                    st.link_button("🔗", url, help="Open store page")

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("🎮 Game Price Tracker")

    gh = init_github()
    if gh is None:
        return

    if "games" not in st.session_state:
        st.session_state.games = load_games_from_github(gh)

    games = st.session_state.games

    with st.expander("➕ Add New Game", expanded=True):
        url_col, price_col, btn_col = st.columns([3, 1, 1])
        with url_col:
            game_url = st.text_input("Game URL", placeholder="https://store.steampowered.com/app/...", label_visibility="collapsed")
        with price_col:
            target_price_input = st.text_input("Target Price (optional)", placeholder="e.g. 9.99", label_visibility="collapsed")
        with btn_col:
            st.write("")
            st.write("")
            add_clicked = st.button("Add Game", type="primary", use_container_width=True)

        if add_clicked:
            if not game_url.strip():
                st.warning("Please enter a game URL.")
            elif not is_valid_url(game_url):
                st.error("Invalid URL. Please enter a valid game store URL.")
            else:
                store = detect_store(game_url)
                if not store:
                    st.error("Unsupported store. Supported: Steam, Epic Games, GOG.")
                else:
                    with st.spinner("Fetching game details..."):
                        try:
                            details = fetch_game_details(store, game_url.strip())
                            store_id = details.store_id
                            if not store_id:
                                st.error("Could not identify the game from the URL.")
                            else:
                                game_id = generate_game_id(store, store_id)
                                if get_game_by_id(games, game_id):
                                    st.warning("This game is already in your tracker.")
                                else:
                                    target_price = None
                                    if target_price_input.strip():
                                        try:
                                            target_price = float(target_price_input.strip())
                                        except ValueError:
                                            st.warning("Invalid target price, ignoring.")

                                    game_entry = {
                                        "id": game_id,
                                        "name": details.name,
                                        "store": store,
                                        "url": game_url.strip(),
                                        "current_price": details.current_price,
                                        "target_price": target_price,
                                        "lowest_price": details.current_price,
                                        "last_checked": today_str(),
                                        "currency": details.currency,
                                        "cover_image": details.cover_image,
                                    }
                                    updated, added = add_game(games, game_entry)
                                    if added:
                                        gh.save_games(updated, f"Add {details.name} to tracker")
                                        st.session_state.games = updated
                                        st.success(f"{details.name} added! Current price: {format_price(details.current_price, details.currency)}")
                                        st.rerun()
                        except Exception as e:
                            logger.exception("Failed to add game")
                            st.error(f"Error adding game: {e}")

    action_cols = st.columns([1, 1, 1, 3])
    with action_cols[0]:
        if st.button("🔄 Refresh All", use_container_width=True):
            with st.spinner("Refreshing all prices..."):
                try:
                    from price_api import fetch_game_details as fetch_details
                    changed = 0
                    for g in games:
                        try:
                            details = fetch_details(g["store"], g["url"])
                            g["current_price"] = details.current_price
                            g["currency"] = details.currency
                            g["last_checked"] = today_str()
                            if details.current_price is not None:
                                old_low = g.get("lowest_price")
                                if old_low is None or details.current_price < old_low:
                                    g["lowest_price"] = details.current_price
                            changed += 1
                        except Exception:
                            continue
                    gh.save_games(games, "chore: refresh all prices")
                    st.session_state.games = games
                    st.success(f"Refreshed prices for {changed}/{len(games)} game(s).")
                    st.rerun()
                except Exception as e:
                    st.error(f"Refresh failed: {e}")

    with action_cols[1]:
        if games:
            csv_data = games_to_csv(games)
            st.download_button(
                "📥 Export CSV",
                csv_data,
                "games.csv",
                "text/csv",
                use_container_width=True,
            )

    with action_cols[2]:
        if st.button("📋 Export JSON", use_container_width=True):
            import json
            games_json = json.dumps(games, indent=2, ensure_ascii=False)
            st.download_button(
                "Download games.json",
                games_json,
                "games.json",
                "application/json",
                use_container_width=True,
            )

    st.markdown("---")
    st.subheader(f"📌 Tracked Games ({len(games)})")

    if not games:
        st.info("No games tracked yet. Add a game URL above to get started!")
    else:
        for game in games:
            render_game_card(game, gh, games)


if __name__ == "__main__":
    main()
