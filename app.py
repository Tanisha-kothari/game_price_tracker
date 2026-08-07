import os
import logging
from typing import Optional

import streamlit as st

from utils import (
    detect_store, is_valid_url, generate_game_id,
    today_str, games_to_csv, games_to_json, history_to_csv,
    format_price, render_sparkline_svg,
)
from database import (
    load_games, load_history, add_game, remove_game, get_game_by_id,
    migrate_games, migrate_history, apply_price_update,
    get_price_currency, is_target_met, detect_price_change,
    get_history_prices, build_game_from_details,
)
from price_api import fetch_game_details
from github_manager import GitHubManager
from scheduler import start_daily_report_scheduler
from budget_planner import BudgetPlanner, BudgetOptions, BudgetPlannerError, PlanResult, combo_key

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

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; box-sizing: border-box; }

    .stApp {
        background: radial-gradient(ellipse at 15% 20%, #111827 0%, #030712 45%, #020617 100%);
        color: #f1f5f9;
    }

    .block-container {
        padding: 1.5rem 2rem 3rem !important;
        max-width: 1300px !important;
    }

    #MainMenu, footer, header { visibility: hidden; }

    h1, h2, h3, h4, h5, h6 { color: #f1f5f9 !important; letter-spacing: -0.02em; }

    .stTextInput>div>div>input {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(12px);
        color: #f1f5f9 !important;
        border: 1px solid rgba(99, 102, 241, 0.18) !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        font-size: 15px !important;
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .stTextInput>div>div>input:focus {
        border-color: rgba(139, 92, 246, 0.55) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12) !important;
    }
    .stTextInput>div>div>input::placeholder { color: #64748b; }

    div.stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 4px 18px rgba(59, 130, 246, 0.28) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px rgba(59, 130, 246, 0.38) !important;
    }
    div.stButton > button:active { transform: translateY(0) !important; }

    div.stButton > button[kind="secondary"] {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        color: #e2e8f0 !important;
        box-shadow: none !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(30, 41, 59, 0.9) !important;
        border-color: rgba(99, 102, 241, 0.35) !important;
    }

    div.stDownloadButton > button {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    div.stDownloadButton > button:hover {
        background: rgba(30, 41, 59, 0.9) !important;
        border-color: rgba(99, 102, 241, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    .hero-section {
        text-align: center;
        padding: 36px 28px 28px;
        margin-bottom: 28px;
        background: linear-gradient(135deg,
            rgba(124, 58, 237, 0.1) 0%,
            rgba(37, 99, 235, 0.06) 45%,
            rgba(16, 185, 129, 0.04) 100%);
        border-radius: 24px;
        border: 1px solid rgba(99, 102, 241, 0.12);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 25% 40%, rgba(124,58,237,0.08) 0%, transparent 55%),
                    radial-gradient(circle at 75% 60%, rgba(37,99,235,0.06) 0%, transparent 55%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 46px;
        font-weight: 900;
        background: linear-gradient(135deg, #c4b5fd, #93c5fd, #6ee7b7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 8px;
        letter-spacing: -0.03em;
        position: relative;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 17px;
        font-weight: 400;
        margin-bottom: 24px;
        position: relative;
    }
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        position: relative;
    }
    .dash-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 16px;
        padding: 16px 18px;
        text-align: left;
        transition: transform 0.25s ease, border-color 0.25s ease;
    }
    .dash-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.25);
    }
    .dash-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
        margin-bottom: 6px;
    }
    .dash-value {
        font-size: 20px;
        font-weight: 700;
        color: #f1f5f9;
    }
    .dash-value.ok { color: #22c55e; }
    .dash-value.warn { color: #f59e0b; }

    .add-game-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.85), rgba(2,6,23,0.9));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.14);
        border-radius: 20px;
        padding: 26px 28px;
        margin-bottom: 24px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.25);
    }
    .add-game-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 18px;
        color: #f1f5f9;
    }

    .toolbar {
        display: flex;
        gap: 10px;
        margin-bottom: 28px;
        flex-wrap: wrap;
        align-items: stretch;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 18px;
        color: #f1f5f9;
    }

    .game-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.88), rgba(2,6,23,0.95));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 20px;
        padding: 22px;
        margin-bottom: 18px;
        transition: transform 0.3s cubic-bezier(0.4,0,0.2,1), box-shadow 0.3s ease, border-color 0.3s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
    }
    .game-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7c3aed, #2563eb, #06b6d4);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .game-card:hover::before { opacity: 1; }
    .game-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.22);
        box-shadow: 0 16px 48px rgba(0,0,0,0.35);
    }

    .game-cover-wrap img {
        border-radius: 14px;
        width: 100%;
        aspect-ratio: 460 / 215;
        object-fit: cover;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        transition: transform 0.35s ease;
    }
    .game-card:hover .game-cover-wrap img { transform: scale(1.02); }

    .game-name {
        font-size: 22px;
        font-weight: 800;
        color: #f1f5f9;
        margin: 0 0 8px;
        line-height: 1.25;
    }

    .store-badge {
        display: inline-block;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 5px 14px;
        border-radius: 100px;
        margin-bottom: 14px;
    }
    .store-badge.steam { background: rgba(27,40,56,0.95); color: #66c0f4; border: 1px solid rgba(102,192,244,0.25); }
    .store-badge.epic { background: rgba(18,18,18,0.95); color: #ffffff; border: 1px solid rgba(255,255,255,0.12); }
    .store-badge.gog { background: rgba(43,43,43,0.95); color: #d2b48c; border: 1px solid rgba(210,180,140,0.25); }

    .price-row {
        display: flex;
        align-items: flex-end;
        gap: 28px;
        margin: 14px 0 10px;
        flex-wrap: wrap;
    }
    .price-block .label {
        color: #64748b;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .price-current {
        font-size: 32px;
        font-weight: 900;
        color: #f8fafc;
        letter-spacing: -0.02em;
        line-height: 1;
    }
    .price-lowest {
        font-size: 18px;
        font-weight: 700;
        color: #22c55e;
    }
    .price-target {
        font-size: 16px;
        font-weight: 600;
        color: #cbd5e1;
    }
    .price-target.met { color: #22c55e; }
    .price-meta {
        font-size: 13px;
        color: #64748b;
        margin-top: 6px;
    }

    .status-badges {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 10px 0 6px;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 100px;
        letter-spacing: 0.3px;
    }
    .status-badge.target { background: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }
    .status-badge.drop { background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }
    .status-badge.low { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }

    .sparkline-wrap {
        margin-top: 8px;
        opacity: 0.85;
    }

    .card-actions {
        display: flex;
        gap: 8px;
        margin-top: 16px;
        flex-wrap: wrap;
    }

    .empty-state {
        text-align: center;
        padding: 72px 32px;
        background: rgba(15,23,42,0.45);
        border-radius: 20px;
        border: 1px dashed rgba(99,102,241,0.2);
    }
    .empty-icon { font-size: 72px; margin-bottom: 16px; opacity: 0.5; }
    .empty-title { font-size: 24px; font-weight: 800; color: #94a3b8; margin-bottom: 8px; }
    .empty-sub { font-size: 15px; color: #64748b; }

    div[data-testid="stNotification"] { border-radius: 12px !important; }
    .stAlert { border-radius: 12px !important; }

    @media (max-width: 1024px) {
        .dashboard-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px) {
        .block-container { padding: 1rem !important; }
        .hero-title { font-size: 30px !important; }
        .dashboard-grid { grid-template-columns: 1fr 1fr; }
        .game-name { font-size: 18px; }
        .price-current { font-size: 26px; }
        .add-game-card { padding: 18px; }
        .hero-section { padding: 24px 16px; }
    }

    /* ── View switcher ─────────────────────────────────── */
    div[data-testid="stRadio"] > div {
        gap: 6px;
    }
    div[data-testid="stRadio"] label {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(99, 102, 241, 0.18);
        border-radius: 12px;
        padding: 8px 16px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: rgba(139, 92, 246, 0.4);
        color: #e2e8f0;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.25), rgba(37, 99, 235, 0.18));
        border-color: rgba(139, 92, 246, 0.55);
        color: #f1f5f9;
    }

    /* ── Budget planner UI ─────────────────────────────── */
    .planner-card {
        background: linear-gradient(145deg, rgba(15,23,42,0.88), rgba(2,6,23,0.95));
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .planner-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
    }
    .planner-pill {
        flex: 1 1 auto;
        min-width: 140px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 14px;
        padding: 14px 18px;
        text-align: center;
    }
    .planner-pill .label {
        color: #64748b;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .planner-pill .value {
        color: #f1f5f9;
        font-size: 22px;
        font-weight: 800;
        margin-top: 2px;
    }
    .planner-pill .value.green  { color: #22c55e; }
    .planner-pill .value.amber  { color: #f59e0b; }
    .planner-pill .value.red    { color: #ef4444; }
    .planner-pill .value.violet { color: #8b5cf6; }

    .planner-game-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 4px;
        border-bottom: 1px solid rgba(51, 65, 85, 0.25);
    }
    .planner-game-row:last-child { border-bottom: none; }
    .planner-game-index {
        width: 28px; height: 28px;
        flex: 0 0 28px;
        border-radius: 50%;
        background: rgba(124, 58, 237, 0.2);
        color: #c4b5fd;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 700;
    }
    .planner-game-name { color: #f1f5f9; font-weight: 600; font-size: 15px; flex: 1; }
    .planner-game-price { color: #22c55e; font-weight: 700; font-size: 15px; white-space: nowrap; }
    .planner-notice {
        color: #94a3b8; font-size: 13px; margin-top: 12px; padding: 12px;
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-radius: 12px;
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


def load_data_from_github(gh: GitHubManager) -> tuple[list[dict], dict, bool]:
    """Load games and history, migrate, and persist if needed."""
    migrated = False
    try:
        content = gh.get_file_content("games.json")
        games = load_games(content) if content else []
    except Exception as e:
        logger.error("Failed to load games: %s", e)
        st.error("Failed to load games from GitHub.")
        return [], {}, False

    try:
        hist_content = gh.get_file_content("history.json")
        history = load_history(hist_content) if hist_content else {}
    except Exception as e:
        logger.error("Failed to load history: %s", e)
        history = {}

    games, games_changed = migrate_games(games)
    history, history_changed = migrate_history(history, games)

    if games_changed:
        try:
            gh.save_games(games, "chore: migrate price data model")
            logger.info("Saved migrated games to GitHub")
            migrated = True
        except Exception as e:
            logger.error("Failed to save migrated games: %s", e)

    if history_changed:
        try:
            gh.save_history(history, "chore: migrate history currency")
            logger.info("Saved migrated history to GitHub")
            migrated = True
        except Exception as e:
            logger.error("Failed to save migrated history: %s", e)

    return games, history, migrated


def get_last_sync(games: list[dict]) -> str:
    if not games:
        return "—"
    dates = [g.get("last_checked") for g in games if g.get("last_checked")]
    return max(dates) if dates else "—"


def notification_status() -> tuple[str, str]:
    email = os.environ.get("EMAIL_ADDRESS") or st.secrets.get("EMAIL_ADDRESS", "")
    password = os.environ.get("EMAIL_PASSWORD") or st.secrets.get("EMAIL_PASSWORD", "")
    if email and password:
        return "Configured", "ok"
    return "Not configured", "warn"


def render_store_badge(store: str) -> str:
    labels = {"steam": "STEAM", "epic": "EPIC GAMES", "gog": "GOG"}
    label = labels.get(store, store.upper())
    return f'<span class="store-badge {store}">{label}</span>'


def render_status_badges(
    game: dict,
    history: dict,
    current: Optional[float],
    current_currency: str,
) -> str:
    badges = []
    target = game.get("target_price")
    target_currency = get_price_currency(game, "target_price")

    if is_target_met(current, current_currency, target, target_currency):
        badges.append('<span class="status-badge target">✅ Target reached</span>')

    diff = detect_price_change(history, game["id"], current, current_currency)
    if diff is not None and diff < 0:
        badges.append('<span class="status-badge drop">▼ Price dropped</span>')

    lowest = game.get("lowest_price")
    lowest_currency = get_price_currency(game, "lowest_price")
    if (
        current is not None
        and lowest is not None
        and current_currency == lowest_currency
        and abs(current - lowest) < 0.01
        and len(get_history_prices(history, game["id"])) >= 2
    ):
        badges.append('<span class="status-badge low">★ New lowest</span>')

    if not badges:
        return ""
    return f'<div class="status-badges">{"".join(badges)}</div>'


def render_game_card(game: dict, gh: GitHubManager, games: list[dict], history: dict):
    game_id = game["id"]
    store = game["store"]
    name = game.get("name", "Unknown")
    current = game.get("current_price")
    lowest = game.get("lowest_price")
    target = game.get("target_price")
    current_currency = get_price_currency(game, "current_price")
    lowest_currency = get_price_currency(game, "lowest_price")
    target_currency = get_price_currency(game, "target_price")
    last_checked = game.get("last_checked", "Never")
    cover = game.get("cover_image", "")
    url = game.get("url", "")

    current_display = format_price(current, current_currency)
    lowest_display = format_price(lowest, lowest_currency)
    target_display = format_price(target, target_currency) if target is not None else "Not set"
    target_met = is_target_met(current, current_currency, target, target_currency)

    hist_prices = get_history_prices(history, game_id)
    sparkline = render_sparkline_svg(hist_prices[-12:]) if len(hist_prices) >= 2 else ""
    status_html = render_status_badges(game, history, current, current_currency)

    cover_html = (
        f'<div class="game-cover-wrap"><img src="{cover}" alt="{name}"></div>'
        if cover else '<div class="game-cover-wrap" style="background:rgba(30,41,59,0.5);border-radius:14px;aspect-ratio:460/215;"></div>'
    )

    st.markdown('<div class="game-card">', unsafe_allow_html=True)

    cols = st.columns([1.1, 2.2])

    with cols[0]:
        st.markdown(cover_html, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f'<div class="game-name">{name}</div>', unsafe_allow_html=True)
        st.markdown(render_store_badge(store), unsafe_allow_html=True)

        st.markdown(
            f'<div class="price-row">'
            f'<div class="price-block">'
            f'<div class="label">Current</div>'
            f'<div class="price-current">{current_display}</div>'
            f'</div>'
            f'<div class="price-block">'
            f'<div class="label">Lowest</div>'
            f'<div class="price-lowest">{lowest_display}</div>'
            f'</div>'
            f'<div class="price-block">'
            f'<div class="label">Target</div>'
            f'<div class="price-target {"met" if target_met else ""}">{target_display}</div>'
            f'</div>'
            f'</div>'
            f'{status_html}'
            f'<div class="price-meta">Last checked: {last_checked}</div>'
            f'{"<div class=\"sparkline-wrap\">" + sparkline + "</div>" if sparkline else ""}',
            unsafe_allow_html=True,
        )

        btn_cols = st.columns([1, 1, 1, 2])
        with btn_cols[0]:
            if st.button("🔄 Refresh", key=f"ref_{game_id}", use_container_width=True):
                with st.spinner("Checking..."):
                    try:
                        details = fetch_game_details(store, url)
                        for g in games:
                            if g["id"] == game_id:
                                apply_price_update(g, details.current_price, details.currency)
                                break
                        gh.save_games(games, f"Refresh price for {name}")
                        st.session_state.games = games
                        st.success(f"{name}: {format_price(details.current_price, details.currency)}")
                        st.rerun()
                    except Exception:
                        st.error("Refresh failed.")
        with btn_cols[1]:
            if st.button("🗑 Delete", key=f"del_{game_id}", use_container_width=True):
                updated = remove_game(games, game_id)
                try:
                    gh.save_games(updated, f"Remove {name} from tracker")
                    st.session_state.games = updated
                    st.success(f"Removed {name}")
                    st.rerun()
                except Exception:
                    st.error("Failed to remove.")
        with btn_cols[2]:
            if url:
                st.link_button("🔗 Store", url, use_container_width=True)

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
            if not details.store_id:
                st.error("Could not identify the game from the URL.")
                return
            game_id = generate_game_id(store, details.store_id)
            if get_game_by_id(games, game_id):
                st.warning("This game is already in your tracker.")
                return
            target_price = None
            if target_input.strip():
                try:
                    target_price = float(target_input.strip())
                except ValueError:
                    st.warning("Invalid target price, ignoring.")
            game_entry = build_game_from_details(
                details, game_url.strip(), store, target_price,
            )
            game_entry["id"] = game_id
            updated, added = add_game(games, game_entry)
            if added:
                gh.save_games(updated, f"Add {details.name} to tracker")
                st.session_state.games = updated
                st.success(
                    f"**{details.name}** added! "
                    f"Current price: {format_price(details.current_price, details.currency)}"
                )
                st.rerun()
        except Exception:
            logger.exception("Failed to add game")
            st.error("Error adding game. Check the URL and try again.")


def handle_refresh_all(games: list[dict], gh: GitHubManager):
    with st.spinner("Refreshing all prices..."):
        changed = 0
        for g in games:
            try:
                details = fetch_game_details(g["store"], g["url"])
                apply_price_update(g, details.current_price, details.currency)
                changed += 1
            except Exception:
                continue
        gh.save_games(games, "chore: refresh all prices")
        st.session_state.games = games
        st.success(f"Refreshed prices for {changed}/{len(games)} game(s).")
        st.rerun()


PLANNER_VIEW = "💰 Smart Budget Planner"
TRACKER_VIEW = "🎮 Tracked Games"


def render_budget_planner(games: list[dict]):
    """Renders the Smart Budget Planner section (separate view from the tracker)."""
    priceable = [g for g in games if g.get("current_price") is not None]
    name_to_id = {g["name"]: g["id"] for g in priceable}
    id_to_game = {g["id"]: g for g in priceable}

    st.markdown(
        '<div class="section-title">💰 Smart Budget Planner</div>',
        unsafe_allow_html=True,
    )

    if not priceable:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">💰</div>'
            '<div class="empty-title">No priced games to plan with</div>'
            '<div class="empty-sub">Track some games first — the planner draws from your '
            "tracked games' current prices.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Inputs ──────────────────────────────────────────────
    bcol, ccol = st.columns(2)
    with bcol:
        budget = st.number_input("Budget (₹)", min_value=1, step=100, value=3000)
    with ccol:
        count = st.number_input(
            "Games to buy", min_value=1,
            max_value=len(priceable), step=1,
            value=min(3, len(priceable)),
        )

    mcol, fcol = st.columns([2, 1.4])
    with mcol:
        must_names = st.multiselect("Must include (optional)", list(name_to_id.keys()))
    with fcol:
        flex = st.checkbox("Flexible budget", help="Allow the total to exceed the budget by a small percentage.")
        flex_pct = st.slider("Flexibility %", 0, 100, 10, disabled=not flex) if flex else 0

    def _current_options() -> BudgetOptions:
        return BudgetOptions(
            budget=float(budget),
            count=int(count),
            must_include_ids=tuple(name_to_id[n] for n in must_names),
            flex_pct=float(flex_pct if flex else 0),
        )

    # Fingerprint of the inputs, to tell when settings changed.
    fingerprint = (float(budget), int(count), tuple(sorted(name_to_id[n] for n in must_names)), float(flex_pct if flex else 0))

    ss = st.session_state
    # Reset cached plan whenever the inputs change.
    if ss.get("planner.fp") != fingerprint:
        ss["planner.fp"] = fingerprint
        ss["planner.excluded"] = set()
        ss["planner.result"] = None
        ss["planner.error"] = None

    gcol, rcol, _ = st.columns([1, 1, 3])
    with gcol:
        generate_clicked = st.button("⚡ Generate", type="primary", use_container_width=True)
    with rcol:
        refresh_clicked = st.button("🔄 Refresh", use_container_width=True)

    # ── Action handling ─────────────────────────────────────
    plan: Optional[PlanResult] = None
    if generate_clicked:
        ss["planner.excluded"] = set()
        try:
            planner = BudgetPlanner(priceable, _current_options())
            plan = planner.generate(exclude=set())
            ss["planner.excluded"].add(combo_key(tuple(plan.games)))
            ss["planner.result"] = plan
            ss["planner.error"] = None
        except BudgetPlannerError as e:
            ss["planner.result"] = None
            ss["planner.error"] = str(e)

    elif refresh_clicked and ss.get("planner.result") is not None:
        try:
            planner = BudgetPlanner(priceable, _current_options())
            plan = planner.generate(exclude=ss["planner.excluded"])
            ss["planner.excluded"].add(combo_key(tuple(plan.games)))
            ss["planner.result"] = plan
            ss["planner.error"] = None
        except BudgetPlannerError as e:
            ss["planner.error"] = str(e)

    # Show errors, then the current (or newly chosen) plan.
    if ss.get("planner.error"):
        st.error(ss["planner.error"])

    result = plan if plan is not None else ss.get("planner.result")
    if result is None:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">🗒️</div>'
            '<div class="empty-title">Set your budget and hit Generate</div>'
            '<div class="empty-sub">The planner finds combinations of tracked games '
            "that fit your budget.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Render the plan ───────────────────────────────────────
    rows = ""
    for i, g in enumerate(result.games, start=1):
        rows += (
            f'<div class="planner-game-row">'
            f'<div class="planner-game-index">{i}</div>'
            f'<div class="planner-game-name">{g["name"]} '
            f'{render_store_badge(g.get("store", ""))}</div>'
            f'<div class="planner-game-price">{format_price(g.get("current_price"), get_price_currency(g, "current_price"))}</div>'
            f"</div>"
        )

    over = result.is_over_budget
    remaining_display = format_price(result.remaining, "INR")
    if over:
        total_value = f'<div class="value amber">over by {format_price(result.over_amount, "INR")}</div>'
    else:
        total_value = f'<div class="value green">{remaining_display}</div>'

    only_one = result.combos_count <= 1
    notice = f'<p style="color:#64748b;font-size:12px;margin-top:10px;">{result.combos_count} valid combination(s) found. ' \
             f'{"Only one combination fits these settings, so Refresh will show the same plan." if only_one else "Use Refresh for a different combination."}</p>'

    st.markdown(
        f'<div class="planner-card">'
        f'<div class="planner-summary">'
        f'<div class="planner-pill"><div class="label">Budget</div>'
        f'<div class="value">{format_price(result.budget, "INR")}</div></div>'
        f'<div class="planner-pill"><div class="label">Allowed</div>'
        f'<div class="value violet">{format_price(result.allowed, "INR")}</div></div>'
        f'<div class="planner-pill"><div class="label">Total Cost</div>'
        f'<div class="value">{format_price(result.total, "INR")}</div></div>'
        f'<div class="planner-pill"><div class="label">{"Over Budget" if over else "Remaining"}</div>'
        f'{total_value}</div>'
        f"</div>"
        f"{rows}"
        f"{notice}"
        f"</div>",
        unsafe_allow_html=True,
    )


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    gh = init_github()
    if gh is None:
        return

    if "scheduler_started" not in st.session_state:
        st.session_state.scheduler_started = True
        email_addr = os.environ.get("EMAIL_ADDRESS") or st.secrets.get("EMAIL_ADDRESS", "")
        email_pwd = os.environ.get("EMAIL_PASSWORD") or st.secrets.get("EMAIL_PASSWORD", "")
        email_to = os.environ.get("EMAIL_TO") or st.secrets.get("EMAIL_TO", email_addr)
        report_time = os.environ.get("EMAIL_REPORT_TIME") or st.secrets.get("EMAIL_REPORT_TIME", "11:05")
        smtp_server = os.environ.get("SMTP_SERVER") or st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT") or st.secrets.get("SMTP_PORT", "587"))
        if email_addr and email_pwd:
            start_daily_report_scheduler(
                gh, email_addr, email_pwd,
                to_address=email_to, send_time=report_time,
                smtp_server=smtp_server, smtp_port=smtp_port,
            )
        else:
            logger.info("Email not configured; daily report scheduler disabled")

    if "games" not in st.session_state or "history" not in st.session_state:
        games, history, _ = load_data_from_github(gh)
        st.session_state.games = games
        st.session_state.history = history
    else:
        games = st.session_state.games
        history = st.session_state.history

    games = st.session_state.games
    history = st.session_state.history

    # ── View switcher ────────────────────────────────────────
    view = st.radio(
        "", [TRACKER_VIEW, PLANNER_VIEW],
        horizontal=True, label_visibility="collapsed",
        key="app_view",
    )
    if view == PLANNER_VIEW:
        render_budget_planner(games)
        return

    last_sync = get_last_sync(games)
    notify_label, notify_class = notification_status()

    st.markdown(
        f'<div class="hero-section">'
        f'<div class="hero-title"> Game Price Tracker</div>'
        f'<div class="hero-subtitle">Track prices across Steam, Epic Games and GOG.</div>'
        f'<div class="dashboard-grid">'
        f'<div class="dash-card"><div class="dash-label">Tracked Games</div>'
        f'<div class="dash-value">{len(games)}</div></div>'
        f'<div class="dash-card"><div class="dash-label">Last Sync</div>'
        f'<div class="dash-value">{last_sync}</div></div>'
        f'<div class="dash-card"><div class="dash-label">GitHub Status</div>'
        f'<div class="dash-value ok">Connected</div></div>'
        f'<div class="dash-card"><div class="dash-label">Notification Status</div>'
        f'<div class="dash-value {notify_class}">{notify_label}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="add-game-card">'
        '<div class="add-game-title">➕ Add New Game</div>',
        unsafe_allow_html=True,
    )

    url_col, price_col, btn_col = st.columns([3.2, 1, 0.9])
    with url_col:
        game_url = st.text_input(
            "Game URL",
            placeholder="https://store.steampowered.com/app/730/...",
            label_visibility="collapsed",
        )
    with price_col:
        target_price_input = st.text_input(
            "Target Price (₹)",
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

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        if st.button("🔄 Refresh All", use_container_width=True, type="primary"):
            handle_refresh_all(games, gh)
    with ac2:
        if games:
            st.download_button(
                "📥 Export CSV",
                games_to_csv(games),
                "games.csv",
                "text/csv",
                use_container_width=True,
            )
    with ac3:
        if games:
            st.download_button(
                "📋 Export JSON",
                games_to_json(games),
                "games.json",
                "application/json",
                use_container_width=True,
            )
    with ac4:
        if history:
            st.download_button(
                "📈 Export History",
                history_to_csv(history),
                "history.csv",
                "text/csv",
                use_container_width=True,
            )

    st.markdown(
        f'<div class="section-title">📌 Tracked Games ({len(games)})</div>',
        unsafe_allow_html=True,
    )

    if not games:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-icon">🎮</div>'
            '<div class="empty-title">No games are being tracked yet</div>'
            '<div class="empty-sub">Paste a Steam, Epic, or GOG URL above to start tracking.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for game in games:
            render_game_card(game, gh, games, history)


if __name__ == "__main__":
    main()
