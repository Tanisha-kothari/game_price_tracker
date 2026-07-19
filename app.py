import os
import json
import logging
from typing import Optional

import streamlit as st

from utils import (
    detect_store, is_valid_url, generate_game_id, format_price,
    today_str, games_to_csv, history_to_csv, display_price_inr,
    get_display_price, format_inr, usd_to_inr,
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp {
        background: radial-gradient(ellipse at 20% 50%, #0f172a 0%, #020617 100%);
        color: #f1f5f9;
    }

    .block-container {
        padding: 1.2rem 1.5rem !important;
        max-width: 1100px;
    }

    h1, h2, h3, h4, h5, h6 { color: #f1f5f9 !important; letter-spacing: -0.02em; }

    .stTextInput>div>div>input {
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(8px);
        color: #f1f5f9 !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.25s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15) !important;
    }
    .stTextInput>div>div>input::placeholder { color: #64748b; }

    div.stButton > button {
        background: linear-gradient(135deg, #7c3aed, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.25) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }
    div.stButton > button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        color: #e2e8f0 !important;
        box-shadow: none !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(51, 65, 85, 0.9) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }

    div.stDownloadButton > button {
        background: rgba(30, 41, 59, 0.8) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.25s ease !important;
    }
    div.stDownloadButton > button:hover {
        background: rgba(51, 65, 85, 0.9) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    .hero-section {
        text-align: center;
        padding: 28px 20px 20px;
        margin-bottom: 20px;
        background: linear-gradient(135deg,
            rgba(124, 58, 237, 0.08) 0%,
            rgba(59, 130, 246, 0.05) 50%,
            rgba(16, 185, 129, 0.03) 100%);
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.08);
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(124,58,237,0.06) 0%, transparent 50%),
                    radial-gradient(circle at 70% 50%, rgba(59,130,246,0.04) 0%, transparent 50%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 40px;
        font-weight: 900;
        background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 6px;
        letter-spacing: -0.03em;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 16px;
        font-weight: 400;
        margin-bottom: 18px;
    }
    .hero-badges {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 100px;
        padding: 8px 18px;
        font-size: 13px;
        color: #cbd5e1;
        font-weight: 500;
    }
    .hero-badge strong { color: #f1f5f9; }

    .add-game-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.9));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 130, 246, 0.12);
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    .add-game-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 16px;
        color: #f1f5f9;
    }

    .action-bar {
        display: flex;
        gap: 10px;
        margin-bottom: 24px;
        flex-wrap: wrap;
    }

    .game-card {
        background: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(59, 130, 246, 0.08);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
    }
    .game-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7c3aed, #3b82f6, #06b6d4);
        opacity: 0;
        transition: opacity 0.35s ease;
    }
    .game-card:hover::before { opacity: 1; }
    .game-card:hover {
        transform: translateY(-4px);
        border-color: rgba(59, 130, 246, 0.2);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }

    .game-card img {
        border-radius: 14px;
        width: 100%;
        max-height: 180px;
        object-fit: cover;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        transition: transform 0.35s ease;
    }
    .game-card:hover img { transform: scale(1.01); }

    .game-name {
        font-size: 20px;
        font-weight: 700;
        color: #f1f5f9;
        margin: 10px 0 6px;
        line-height: 1.3;
    }

    .store-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        padding: 4px 14px;
        border-radius: 100px;
        margin-bottom: 14px;
    }
    .store-badge.steam { background: rgba(27,40,56,0.9); color: #66c0f4; border: 1px solid rgba(102,192,244,0.2); }
    .store-badge.epic { background: rgba(18,18,18,0.9); color: #ffffff; border: 1px solid rgba(255,255,255,0.1); }
    .store-badge.gog { background: rgba(43,43,43,0.9); color: #d2b48c; border: 1px solid rgba(210,180,140,0.2); }

    .price-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px 20px;
        margin: 12px 0;
    }
    .price-label { color: #64748b; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .price-value { color: #f1f5f9; font-size: 18px; font-weight: 700; }
    .price-value.lowest { color: #22c55e; }
    .price-value.target { color: #f1f5f9; }
    .price-value.target-met { color: #22c55e; }
    .price-value.current { font-size: 24px; }

    .target-reached-badge {
        display: inline-block;
        background: rgba(34,197,94,0.15);
        color: #22c55e;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 100px;
        border: 1px solid rgba(34,197,94,0.2);
        margin-top: 4px;
    }

    .card-actions {
        display: flex;
        gap: 8px;
        margin-top: 14px;
        flex-wrap: wrap;
    }
    .card-actions .stButton>button {
        padding: 6px 16px !important;
        font-size: 13px !important;
        border-radius: 10px !important;
        min-width: 0 !important;
    }

    .empty-state {
        text-align: center;
        padding: 60px 20px;
        background: rgba(30,41,59,0.4);
        border-radius: 18px;
        border: 1px dashed rgba(59,130,246,0.15);
    }
    .empty-icon { font-size: 64px; margin-bottom: 12px; opacity: 0.6; }
    .empty-title { font-size: 22px; font-weight: 700; color: #94a3b8; margin-bottom: 6px; }
    .empty-sub { font-size: 15px; color: #64748b; }

    div[data-testid="stNotification"] { border-radius: 12px !important; }

    hr { border-color: rgba(59,130,246,0.08) !important; margin: 8px 0 !important; }

    .stAlert { border-radius: 12px !important; }
    div[data-baseweb="notification"] { border-radius: 12px !important; }

    @media (max-width: 640px) {
        .block-container { padding: 0.8rem !important; }
        .hero-title { font-size: 28px !important; }
        .game-name { font-size: 17px; }
        .price-value.current { font-size: 20px; }
        .price-grid { grid-template-columns: 1fr; }
        .game-card { padding: 14px; }
        .add-game-card { padding: 16px; }
        .hero-section { padding: 20px 14px; }
    }
</style>
"""


def init_github() -> Optional[GitHubManager]:
    token = st.secrets.get("GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", ""))
    owner = st.secrets.get("REPO_OWNER", os.environ.get("REPO_OWNER", ""))
    repo = st.secrets.get("REPO_NAME", os.environ.get("REPO_NAME", ""))
    if not token or not owner or not repo:
        st.error("GitHub secrets not configured. Set GITHUB_TOKEN, REPO_OWNER, REPO_NAME in Streamlit Secrets.")
        return None
    gh = GitHubManager(token, owner, repo)
    if not gh.test_connection():
        st.error("Cannot connect to GitHub. Check your token and repository settings.")
        return None
    return gh


def load_games_from_github(gh: GitHubManager) -> list[dict]:
    try:
        content = gh.get_file_content("games.json")
        return load_games(content) if content else []
    except Exception as e:
        logger.error("Failed to load games: %s", e)
        st.error("Failed to load games from GitHub.")
        return []


def update_game_after_refresh(games: list[dict], game_id: str, details) -> None:
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


def render_store_badge(store: str) -> str:
    labels = {"steam": "STEAM", "epic": "EPIC GAMES", "gog": "GOG"}
    label = labels.get(store, store.upper())
    return f'<span class="store-badge {store}">{label}</span>'


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

    current_display = display_price_inr(current, currency)
    lowest_display = display_price_inr(lowest, currency)
    target_display = display_price_inr(target, currency) if target is not None else None

    target_met = current is not None and target is not None and current <= target

    with st.container():
        st.markdown('<div class="game-card">', unsafe_allow_html=True)

        cols = st.columns([1, 1.6, 0.7])

        with cols[0]:
            if cover:
                st.image(cover, use_container_width=True)

        with cols[1]:
            st.markdown(f'<div class="game-name">{name}</div>', unsafe_allow_html=True)
            st.markdown(render_store_badge(store), unsafe_allow_html=True)

            st.markdown(
                f'<div class="price-grid">'
                f'<div class="price-item">'
                f'<div class="price-label">Current</div>'
                f'<div class="price-value current">{current_display}</div>'
                f'</div>'
                f'<div class="price-item">'
                f'<div class="price-label">Lowest</div>'
                f'<div class="price-value lowest">{lowest_display}</div>'
                f'</div>'
                f'<div class="price-item">'
                f'<div class="price-label">Target</div>'
                f'<div class="price-value {"target-met" if target_met else "target"}">'
                f'{target_display if target_display else "Not set"}'
                f'</div>'
                f'</div>'
                f'<div class="price-item">'
                f'<div class="price-label">Last Checked</div>'
                f'<div class="price-value" style="font-size:14px;color:#94a3b8;">{last_checked}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if target_met:
                st.markdown('<span class="target-reached-badge">\u2705 Target Reached</span>', unsafe_allow_html=True)

        with cols[2]:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("\U0001f504", key=f"ref_{game_id}", help="Refresh price"):
                    with st.spinner("Checking..."):
                        try:
                            details = fetch_game_details(store, url)
                            update_game_after_refresh(games, game_id, details)
                            gh.save_games(games, f"Refresh price for {name}")
                            st.success(f"{name}: {display_price_inr(details.current_price, details.currency)}")
                            st.rerun()
                        except Exception:
                            st.error("Refresh failed.")

            with c2:
                if st.button("\U0001f5d1", key=f"del_{game_id}", help="Remove game"):
                    updated = remove_game(games, game_id)
                    try:
                        gh.save_games(updated, f"Remove {name} from tracker")
                        st.success(f"Removed {name}")
                        st.rerun()
                    except Exception:
                        st.error("Failed to remove.")

            if url:
                st.link_button("\U0001f517", url, help="Open store page")

        st.markdown("</div>", unsafe_allow_html=True)


def handle_add_game(games: list[dict], game_url: str, target_input: str, gh: GitHubManager):
    if not game_url.strip():
        st.warning("Please enter a game URL.")
        return
    if not is_valid_url(game_url):
        st.error("Invalid URL. Please enter a valid game store URL.")
        return
    store = detect_store(game_url)
    if not store:
        st.error("Unsupported store. Supported: Steam, Epic Games, GOG.")
        return
    with st.spinner("Fetching game details..."):
        try:
            details = fetch_game_details(store, game_url.strip())
            store_id = details.store_id
            if not store_id:
                st.error("Could not identify the game from the URL.")
                return
            game_id = generate_game_id(store, store_id)
            if get_game_by_id(games, game_id):
                st.warning("This game is already in your tracker.")
                return
            target_price = None
            if target_input.strip():
                try:
                    target_price = float(target_input.strip())
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
                st.success(f"**{details.name}** added! Current price: {display_price_inr(details.current_price, details.currency)}")
                st.rerun()
        except Exception as e:
            logger.exception("Failed to add game")
            st.error("Error adding game. Check the URL and try again.")


def handle_refresh_all(games: list[dict], gh: GitHubManager):
    with st.spinner("Refreshing all prices..."):
        changed = 0
        for g in games:
            try:
                details = fetch_game_details(g["store"], g["url"])
                update_game_after_refresh(games, g["id"], details)
                changed += 1
            except Exception:
                continue
        gh.save_games(games, "chore: refresh all prices")
        st.session_state.games = games
        st.success(f"Refreshed prices for {changed}/{len(games)} game(s).")
        st.rerun()


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    gh = init_github()
    if gh is None:
        return

    if "games" not in st.session_state:
        st.session_state.games = load_games_from_github(gh)

    games = st.session_state.games

    last_refresh = "Today" if games else "\u2014"

    st.markdown(
        f'<div class="hero-section">'
        f'<div class="hero-title">\U0001f3ae Game Price Tracker</div>'
        f'<div class="hero-subtitle">Track prices across Steam, Epic Games &amp; GOG</div>'
        f'<div class="hero-badges">'
        f'<span class="hero-badge">\U0001f4ca <strong>{len(games)}</strong> games tracked</span>'
        f'<span class="hero-badge">\U0001f4c5 Last refresh: <strong>{last_refresh}</strong></span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="add-game-card">'
        '<div class="add-game-title">\u2795 Add New Game</div>',
        unsafe_allow_html=True,
    )

    url_col, price_col, btn_col = st.columns([3, 1, 0.9])
    with url_col:
        game_url = st.text_input(
            "Game URL",
            placeholder="https://store.steampowered.com/app/730/...",
            label_visibility="collapsed",
        )
    with price_col:
        target_price_input = st.text_input(
            "Target Price (\u20b9)",
            placeholder="e.g. 999",
            label_visibility="collapsed",
        )
    with btn_col:
        st.write("")
        st.write("")
        add_clicked = st.button("Add Game", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if add_clicked:
        handle_add_game(games, game_url, target_price_input, gh)

    st.markdown('<div class="action-bar">', unsafe_allow_html=True)

    ac1, ac2, ac3, ac4 = st.columns([1, 1, 1, 3])
    with ac1:
        if st.button("\U0001f504 Refresh All", use_container_width=True, type="primary"):
            handle_refresh_all(games, gh)
    with ac2:
        if games:
            csv_data = games_to_csv(games)
            st.download_button(
                "\U0001f4e5 Export CSV",
                csv_data,
                "games.csv",
                "text/csv",
                use_container_width=True,
            )
    with ac3:
        if games:
            enriched = []
            for g in games:
                entry = dict(g)
                entry["price_inr"] = display_price_inr(g.get("current_price"), g.get("currency", "USD"))
                entry["lowest_inr"] = display_price_inr(g.get("lowest_price"), g.get("currency", "USD"))
                enriched.append(entry)
            games_json = json.dumps(enriched, indent=2, ensure_ascii=False)
            st.download_button(
                "\U0001f4cb Export JSON",
                games_json,
                "games.json",
                "application/json",
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<h3 style="font-size:20px;font-weight:700;margin-bottom:16px;">'
        f'\U0001f4cc Tracked Games ({len(games)})</h3>',
        unsafe_allow_html=True,
    )

    if not games:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">\U0001f3ae</div>'
            '<div class="empty-title">No games are being tracked yet</div>'
            '<div class="empty-sub">Add your first game above \u2191</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for game in games:
            render_game_card(game, gh, games)


if __name__ == "__main__":
    main()
