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
    migrate_games, migrate_history, apply_price_update, apply_game_update,
    get_price_currency, is_target_met, detect_price_change,
    get_history_prices, build_game_from_details, build_game_from_search_result,
    get_tracked_store_ids, get_tracked_stores_for_game, group_games_by_identity,
    store_filter_stats, filter_grouped_games,
)
from price_api import fetch_game_details
from search.engine import search_games, AggregatedGame
from stores import get_pricing
from utils import canonical_game_id
from github_manager import GitHubManager
from scheduler import start_daily_report_scheduler
from budget_planner import BudgetPlanner, BudgetOptions, BudgetPlannerError, PlanResult, combo_key
from report import build_daily_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("app")

st.set_page_config(
    page_title="GameTracker — Price & Sale Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Compact Modern Dark Gaming Dashboard CSS ─────────────────────────
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    *, *::before, *::after {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-sizing: border-box;
    }

    .stApp {
        background-color: #090d16 !important;
        color: #e2e8f0 !important;
    }

    .block-container {
        padding: 1.25rem 2rem 3rem !important;
        max-width: 1280px !important;
        margin: 0 auto;
    }

    #MainMenu, footer { display: none !important; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 100 !important;
    }
    button[data-testid="stSidebarCollapseButton"], button[data-testid="baseButton-headerNoPadding"] {
        color: #94a3b8 !important;
        background: #121827 !important;
        border: 1px solid #1f293d !important;
        border-radius: 6px !important;
    }
    button[data-testid="stSidebarCollapseButton"]:hover {
        color: #f8fafc !important;
        background: #1a2238 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        margin: 0 0 0.5rem 0;
    }

    /* ── Persistent Left Sidebar Navigation ─────────────────── */
    section[data-testid="stSidebar"] {
        background-color: #0d121f !important;
        border-right: 1px solid #1a2337 !important;
        min-width: 230px !important;
        max-width: 250px !important;
        width: 240px !important;
        flex-shrink: 0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        background-color: #0d121f !important;
        padding: 1.1rem 0.85rem !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 2px 4px 12px;
        margin-bottom: 10px;
        border-bottom: 1px solid #1a2337;
    }
    .sidebar-brand-icon {
        font-size: 22px;
        display: inline-block;
        transition: transform 0.25s ease;
    }
    .sidebar-brand:hover .sidebar-brand-icon {
        transform: scale(1.15) rotate(-6deg);
    }
    .sidebar-brand-title {
        font-size: 17px;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -0.03em;
    }
    .sidebar-brand-subtitle {
        font-size: 11px;
        color: #64748b;
        font-weight: 500;
    }

    /* ── Sidebar Navigation Links ───────────────────────────── */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] {
        width: 100% !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        gap: 3px !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 9px 12px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 13.5px;
        cursor: pointer;
        display: flex;
        align-items: center;
        width: 100% !important;
        margin: 0 !important;
        transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background: #151c2e;
        color: #f8fafc;
        border-color: #1a2337;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background: #1a2238;
        border-color: #4f46e5;
        color: #f8fafc;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
    }
    /* Hide the small default radio circle so it looks like a clean nav button */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:last-child {
        width: 100% !important;
        color: inherit !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
        font-size: 13.5px !important;
        margin: 0 !important;
        color: inherit !important;
        font-weight: inherit !important;
        white-space: nowrap !important;
    }

    .sidebar-status-card {
        background: #121827;
        border: 1px solid #1a2337;
        border-radius: 8px;
        padding: 10px 12px;
        margin-top: 20px;
    }

    /* ── Form Inputs ────────────────────────────────────────── */
    .stTextInput input, .stNumberInput input {
        background: #121827 !important;
        color: #f8fafc !important;
        border: 1px solid #1f293d !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        transition: all 0.2s ease;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        background: #182035 !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }
    .stTextInput input::placeholder { color: #64748b; }

    div[data-baseweb="select"] > div {
        background-color: #121827 !important;
        border: 1px solid #1f293d !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-size: 13px !important;
    }

    /* ── Non-Wrapping Buttons with Comfortable Padding ──────── */
    div.stButton > button {
        background: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        min-height: 38px !important;
        white-space: nowrap !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div.stButton > button:hover {
        background: #334155 !important;
        border-color: #64748b !important;
        color: #ffffff !important;
        transform: translateY(-1.5px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Primary CTA */
    div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
        background: #4f46e5 !important;
        border: 1px solid #6366f1 !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35) !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stButton > button[data-testid="baseButton-primary"]:hover {
        background: #4338ca !important;
        border-color: #818cf8 !important;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.5) !important;
    }

    /* Secondary / Delete */
    div.stButton > button[kind="secondary"] {
        background: #121827 !important;
        border: 1px solid #334155 !important;
        color: #94a3b8 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
    }

    div.stDownloadButton > button, div.stLinkButton > a {
        background: #121827 !important;
        border: 1px solid #1f293d !important;
        border-radius: 8px !important;
        color: #cbd5e1 !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        min-height: 38px !important;
        white-space: nowrap !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
    }
    div.stDownloadButton > button:hover, div.stLinkButton > a:hover {
        background: #1e293b !important;
        border-color: #475569 !important;
        color: #f8fafc !important;
        transform: translateY(-1px) !important;
    }

    /* ── Filter Segmented Tabs ──────────────────────────────── */
    .main-view-container div[data-testid="stRadio"] > div {
        gap: 6px;
        flex-wrap: wrap;
    }
    .main-view-container div[data-testid="stRadio"] label {
        background: #121827;
        border: 1px solid #1f293d;
        border-radius: 8px;
        padding: 6px 16px;
        color: #94a3b8;
        font-weight: 500;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .main-view-container div[data-testid="stRadio"] label:hover {
        color: #f8fafc;
        border-color: #475569;
        transform: translateY(-1px);
    }
    .main-view-container div[data-testid="stRadio"] label:has(input:checked) {
        background: #1a2238;
        border-color: #6366f1;
        color: #f8fafc;
        font-weight: 600;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }

    /* ── Compact Summary Cards Bar ──────────────────────────── */
    .summary-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
    }
    .sum-card {
        background: #121827;
        border: 1px solid #1f293d;
        border-radius: 10px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .sum-card:hover {
        transform: translateY(-2px);
        border-color: #334155;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
    }
    .sum-icon {
        font-size: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 38px;
        height: 38px;
        border-radius: 8px;
        background: #1a2238;
    }
    .sum-info {
        display: flex;
        flex-direction: column;
    }
    .sum-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 2px;
    }
    .sum-val {
        font-size: 20px;
        font-weight: 800;
        color: #f8fafc;
    }
    .sum-val.sale { color: #4ade80; }
    .sum-val.accent { color: #818cf8; }

    /* ── Unified Self-Contained Game Card ───────────────────── */
    .game-card-wrapper {
        background: #121827;
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 18px 20px 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.2s ease,
                    box-shadow 0.2s ease;
    }
    .game-card-wrapper:hover {
        transform: translateY(-2px);
        border-color: #334155;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .game-card-wrapper.on-sale {
        border-left: 4px solid #22c55e;
    }

    .card-layout-flex {
        display: flex;
        gap: 20px;
    }
    .card-art-col {
        flex: 0 0 200px;
        max-width: 200px;
    }
    .card-art-wrap {
        overflow: hidden;
        border-radius: 8px;
        aspect-ratio: 16 / 9;
        background-color: #0b0f19;
    }
    .card-art-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .game-card-wrapper:hover .card-art-img {
        transform: scale(1.04);
    }

    .card-info-col {
        flex: 1;
        min-width: 0;
    }
    .card-title-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 6px;
    }
    .card-game-title {
        font-size: 18px;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.3;
    }

    .store-tag {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        padding: 3px 8px;
        border-radius: 4px;
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
    }
    .store-tag.steam { color: #66c0f4; border-color: rgba(102, 192, 244, 0.25); }
    .store-tag.epic { color: #f8fafc; border-color: rgba(248, 250, 252, 0.25); }
    .store-tag.gog { color: #d2b48c; border-color: rgba(210, 180, 140, 0.25); }

    .disc-tag {
        display: inline-block;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 4px;
        padding: 2px 7px;
        font-size: 11px;
        font-weight: 700;
        margin-left: 6px;
    }
    .price-orig-strike {
        font-size: 13px;
        color: #64748b;
        text-decoration: line-through;
        margin-left: 8px;
    }

    /* ── Dual-Store Side-by-Side Comparison ─────────────────── */
    .compare-section {
        background: #0d121f;
        border: 1px solid #1a2337;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
    }
    .compare-columns-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
    .compare-store-item {
        display: flex;
        flex-direction: column;
    }
    .compare-price-val {
        font-size: 19px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }
    .compare-price-val.sale { color: #4ade80; }

    .best-deal-callout {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 700;
        color: #4ade80;
        background: rgba(34, 197, 94, 0.12);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-radius: 6px;
        padding: 6px 14px;
        margin-top: 8px;
    }

    /* ── Search Hero & Search Cards ─────────────────────────── */
    .search-hero-box {
        background: #121827;
        border: 1px solid #1f293d;
        border-radius: 12px;
        padding: 20px 22px;
        margin-bottom: 20px;
    }

    .search-result-card {
        background: #121827;
        border: 1px solid #1f293d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .search-result-card:hover {
        transform: translateY(-2px);
        border-color: #334155;
    }

    /* ── Empty State ────────────────────────────────────────── */
    .empty-box {
        text-align: center;
        padding: 48px 24px;
        background: #121827;
        border: 1px dashed #1f293d;
        border-radius: 12px;
        color: #94a3b8;
    }
    .empty-icon { font-size: 40px; margin-bottom: 8px; }
    .empty-title { font-size: 17px; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }
    .empty-sub { font-size: 13px; color: #64748b; }

    /* ── Mobile Layout ──────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container { padding: 0.75rem 1rem 2rem !important; }
        .summary-cards-container { grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-layout-flex { flex-direction: column; gap: 12px; }
        .card-art-col { flex: 0 0 100%; max-width: 100%; }
        .compare-columns-grid { grid-template-columns: 1fr; gap: 8px; }
        div.stButton > button { min-height: 42px !important; width: 100% !important; }
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
            migrated = True
        except Exception as e:
            logger.error("Failed to save migrated games: %s", e)

    if history_changed:
        try:
            gh.save_history(history, "chore: migrate history currency")
            migrated = True
        except Exception as e:
            logger.error("Failed to save migrated history: %s", e)

    return games, history, migrated


def get_last_sync(games: list[dict]) -> str:
    if not games:
        return "—"
    dates = [g.get("last_checked") for g in games if g.get("last_checked")]
    return max(dates) if dates else "—"


STORE_LABELS = {"steam": "Steam", "epic": "Epic Games", "gog": "GOG"}
STORE_TAGS = {"steam": "STEAM", "epic": "EPIC", "gog": "GOG"}


def render_store_tag(store: str) -> str:
    tag = STORE_TAGS.get(store, store.upper())
    return f'<span class="store-tag {store}">{tag}</span>'


def _best_search_result(results: list) -> Optional[dict]:
    if not results:
        return None
    standard = [r for r in results if getattr(r, "edition", "") == "Standard"]
    return standard[0] if standard else results[0]


def _store_matches_filter(store: str, store_filter: str) -> bool:
    if store_filter in ("All", "All Games"):
        return True
    if store_filter == "Steam":
        return store == "steam"
    if store_filter == "Epic Games":
        return store == "epic"
    return True


def handle_track_from_search(
    games: list[dict],
    store: str,
    store_id: str,
    name: str,
    gh: GitHubManager,
    target_price: Optional[float] = None,
):
    listing_id = generate_game_id(store, store_id)
    if get_game_by_id(games, listing_id):
        st.warning(f"Already tracking **{name}** on {STORE_LABELS.get(store, store)}.")
        return
    with st.spinner(f"Adding {name} on {STORE_LABELS.get(store, store)}..."):
        try:
            from stores import get_store

            store_impl = get_store(store)
            default_url = store_impl.build_url(store_id) if store_impl else ""
            if store == "epic":
                default_url = f"https://store.epicgames.com/p/{store_id}"
            elif store == "steam":
                default_url = f"https://store.steampowered.com/app/{store_id}"

            url = default_url
            details = fetch_game_details(store, url)
            resolved_store_id = details.store_id or store_id
            listing_id = generate_game_id(store, resolved_store_id)

            if get_game_by_id(games, listing_id):
                st.warning(f"Already tracking **{details.name or name}** on {STORE_LABELS.get(store, store)}.")
                return

            game_entry = build_game_from_details(details, url, store, target_price)
            game_entry["id"] = listing_id
            game_entry["name"] = details.name if details.name and details.name != "Unknown Game" else name
            game_entry["game_id"] = canonical_game_id(game_entry["name"])

            updated, added = add_game(games, game_entry)
            if added:
                gh.save_games(updated, f"Add {game_entry['name']} ({store}) to tracker")
                st.session_state.games = updated
                price = game_entry.get("current_price")
                currency = get_price_currency(game_entry, "current_price")
                logger.info("Tracked '%s' on %s (id=%s)", game_entry['name'], store, listing_id)
                st.success(
                    f"**{game_entry['name']}** on {STORE_LABELS.get(store, store)} added! "
                    f"Price: {format_price(price, currency)}"
                )
                st.rerun()
        except Exception as e:
            logger.exception("Failed to track from search: %s", e)
            st.error("Could not add this game. Try again or paste the store URL.")


def render_search_result_card(
    agg: AggregatedGame,
    games: list[dict],
    gh: GitHubManager,
    store_filter: str,
):
    canonical_id = canonical_game_id(agg.canonical_name)
    tracked_stores = get_tracked_stores_for_game(games, canonical_id)

    store_results: dict[str, object] = {}
    for store, results in agg.results.items():
        if not _store_matches_filter(store, store_filter):
            continue
        best = _best_search_result(results)
        if best:
            store_results[store] = best

    if not store_results:
        return

    cover = ""
    for r in store_results.values():
        if getattr(r, "cover_image", ""):
            cover = r.cover_image
            break

    availability = []
    if "steam" in store_results:
        availability.append('<span style="color:#66c0f4;font-weight:600;">Steam</span>')
    if "epic" in store_results:
        availability.append('<span style="color:#f8fafc;font-weight:600;">Epic Games</span>')
    if "gog" in store_results:
        availability.append('<span style="color:#d2b48c;font-weight:600;">GOG</span>')
    avail_html = '<span style="color:#64748b;margin-right:4px;">Available on:</span> ' + " · ".join(availability)

    store_rows_html = ""
    for store, result in store_results.items():
        price_display = format_price(result.current_price, result.currency)
        discount = result.discount_percent or 0
        sale_cls = " style=\"color:#4ade80;font-weight:700;\"" if discount > 0 else ""
        discount_html = f'<span class="disc-tag">-{discount}%</span>' if discount > 0 else ""
        store_rows_html += (
            f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid #1a2337;font-size:13px;">'
            f'<span style="font-weight:600;color:#94a3b8;">{STORE_LABELS.get(store, store)}</span>'
            f'<span{sale_cls}>{price_display}{discount_html}</span>'
            f'</div>'
        )

    cover_html = (
        f'<div class="card-art-wrap"><img src="{cover}" alt="{agg.canonical_name}" class="card-art-img"></div>'
        if cover else
        '<div class="card-art-wrap" style="background:#0b0f19;"></div>'
    )

    st.markdown(
        f'<div class="search-result-card">'
        f'<div class="card-layout-flex">'
        f'<div class="card-art-col">{cover_html}</div>'
        f'<div class="card-info-col">'
        f'<div style="font-size:16px;font-weight:700;color:#f8fafc;margin-bottom:4px;">{agg.canonical_name}</div>'
        f'<div style="font-size:11px;color:#94a3b8;margin-bottom:10px;">{avail_html}</div>'
        f'{store_rows_html}'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    btn_cols = st.columns([1.5, 1.5, 3])
    col_idx = 0
    for store, result in store_results.items():
        if col_idx < 2:
            with btn_cols[col_idx]:
                label = STORE_LABELS.get(store, store)
                if store in tracked_stores:
                    st.markdown(
                        f'<div style="color:#4ade80;font-size:12px;font-weight:600;padding:8px 0;">✓ Already tracking on {label}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(f"Track on {label}", key=f"track_{canonical_id}_{store}", use_container_width=True):
                        handle_track_from_search(
                            games, store, result.store_id, result.name, gh,
                        )
            col_idx += 1


def render_store_comparison_box(listings: list[dict]) -> str:
    """Renders a clean, side-by-side comparison block for games available on both Steam & Epic."""
    steam = next((g for g in listings if g.get("store") == "steam"), None)
    epic = next((g for g in listings if g.get("store") == "epic"), None)
    compared = [g for g in (steam, epic) if g is not None]
    if len(compared) < 2:
        return ""

    s_price = format_price(steam.get("current_price"), get_price_currency(steam, "current_price"))
    e_price = format_price(epic.get("current_price"), get_price_currency(epic, "current_price"))
    s_orig = steam.get("original_price")
    e_orig = epic.get("original_price")
    s_disc = steam.get("discount_percent") or 0
    e_disc = epic.get("discount_percent") or 0

    s_cur = steam.get("current_price")
    e_cur = epic.get("current_price")

    s_orig_html = f'<span class="price-orig-strike">{format_price(s_orig, get_price_currency(steam, "original_price"))}</span>' if s_orig and s_orig > (s_cur or 0) else ""
    e_orig_html = f'<span class="price-orig-strike">{format_price(e_orig, get_price_currency(epic, "original_price"))}</span>' if e_orig and e_orig > (e_cur or 0) else ""

    s_disc_html = f'<span class="disc-tag">-{s_disc}%</span>' if s_disc > 0 else ""
    e_disc_html = f'<span class="disc-tag">-{e_disc}%</span>' if e_disc > 0 else ""

    winner_html = ""
    if s_cur is not None and e_cur is not None:
        if s_cur < e_cur:
            diff = e_cur - s_cur
            curr = get_price_currency(steam, "current_price")
            winner_html = (
                f'<div class="best-deal-callout">'
                f'🏆 <strong>BEST DEAL:</strong> Steam (Save {format_price(diff, curr)})'
                f'</div>'
            )
        elif e_cur < s_cur:
            diff = s_cur - e_cur
            curr = get_price_currency(epic, "current_price")
            winner_html = (
                f'<div class="best-deal-callout">'
                f'🏆 <strong>BEST DEAL:</strong> Epic Games (Save {format_price(diff, curr)})'
                f'</div>'
            )
        else:
            winner_html = (
                f'<div class="best-deal-callout" style="color:#94a3b8;border-color:#1a2337;background:#0d121f;">'
                f'⚖️ Same price on Steam and Epic Games'
                f'</div>'
            )

    return (
        f'<div class="compare-section">'
        f'<div class="compare-columns-grid">'
        f'<div class="compare-store-item">'
        f'<div><span class="store-tag steam">STEAM</span></div>'
        f'<div class="compare-price-val{" sale" if s_disc > 0 else ""}">{s_price}{s_orig_html}{s_disc_html}</div>'
        f'</div>'
        f'<div class="compare-store-item">'
        f'<div><span class="store-tag epic">EPIC GAMES</span></div>'
        f'<div class="compare-price-val{" sale" if e_disc > 0 else ""}">{e_price}{e_orig_html}{e_disc_html}</div>'
        f'</div>'
        f'</div>'
        f'{winner_html}'
        f'</div>'
    )


def render_game_card(
    listings: list[dict],
    gh: GitHubManager,
    games: list[dict],
    history: dict,
):
    """Renders a self-contained, beautifully styled product card with generous button sizing."""
    is_multi = len(listings) > 1
    primary_game = listings[0]
    name = primary_game.get("name", "Unknown")
    for g in listings:
        if len(g.get("name", "")) > len(name):
            name = g["name"]

    cover = next((g.get("cover_image") for g in listings if g.get("cover_image")), "")
    on_sale_any = any(g.get("is_on_sale") for g in listings)
    last_checked = max((g.get("last_checked", "Never") for g in listings), default="Never")

    cover_html = (
        f'<div class="card-art-wrap"><img src="{cover}" alt="{name}" class="card-art-img"></div>'
        if cover else
        '<div class="card-art-wrap" style="background:#0b0f19;"></div>'
    )

    stores_badges = " ".join(render_store_tag(g["store"]) for g in listings)

    if is_multi:
        middle_html = render_store_comparison_box(listings)
    else:
        g = primary_game
        current = g.get("current_price")
        currency = get_price_currency(g, "current_price")
        lowest = g.get("lowest_price")
        lowest_curr = get_price_currency(g, "lowest_price")
        orig = g.get("original_price")
        disc = g.get("discount_percent") or 0
        is_sale = bool(g.get("is_on_sale"))

        price_disp = format_price(current, currency)
        orig_html = f'<span class="price-orig-strike">{format_price(orig, currency)}</span>' if is_sale and orig and orig > (current or 0) else ""
        disc_html = f'<span class="disc-tag">-{disc}%</span>' if is_sale and disc > 0 else ""

        target_val = g.get("target_price")
        target_str = ""
        if target_val is not None:
            target_met = is_target_met(current, currency, target_val, get_price_currency(g, "target_price"))
            color = "#4ade80" if target_met else "#94a3b8"
            target_str = f' · Target: <span style="color:{color};font-weight:600;">{format_price(target_val, get_price_currency(g, "target_price"))}</span>'

        middle_html = (
            f'<div style="display:flex;align-items:baseline;gap:20px;margin:10px 0 6px;">'
            f'<div><span style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Price</span><br>'
            f'<span style="font-size:20px;font-weight:800;color:{"#4ade80" if is_sale else "#f8fafc"};">{price_disp}{orig_html}{disc_html}</span></div>'
            f'<div><span style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:600;">Lowest Recorded</span><br>'
            f'<span style="font-size:15px;font-weight:600;color:#94a3b8;">{format_price(lowest, lowest_curr)}</span></div>'
            f'</div>'
            f'<div style="font-size:12px;color:#64748b;margin-bottom:8px;">Checked: {last_checked}{target_str}</div>'
        )

    # Sparkline chart
    hist_prices = get_history_prices(history, primary_game["id"])
    sparkline = render_sparkline_svg(hist_prices[-10:], width=110, height=22) if len(hist_prices) >= 2 else ""
    sparkline_html = f'<div style="margin:4px 0 8px;">{sparkline}</div>' if sparkline else ""

    st.markdown(
        f'<div class="game-card-wrapper{" on-sale" if on_sale_any else ""}">'
        f'<div class="card-layout-flex">'
        f'<div class="card-art-col">{cover_html}</div>'
        f'<div class="card-info-col">'
        f'<div class="card-title-row">'
        f'<span class="card-game-title">{name}</span>'
        f'<div>{stores_badges}</div>'
        f'</div>'
        f'{middle_html}'
        f'{sparkline_html}'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Action buttons with generous widths
    if is_multi:
        steam_g = next((g for g in listings if g.get("store") == "steam"), None)
        epic_g = next((g for g in listings if g.get("store") == "epic"), None)

        b_cols = st.columns([1.4, 1.4, 1.4, 1.4, 1.1])
        with b_cols[0]:
            if steam_g and st.button("🔄 Refresh Steam", key=f"ref_{steam_g['id']}", use_container_width=True):
                with st.spinner("Checking Steam..."):
                    try:
                        details = fetch_game_details("steam", steam_g["url"])
                        apply_game_update(steam_g, details)
                        gh.save_games(games, f"Refresh Steam price for {name}")
                        st.session_state.games = games
                        st.success("Steam price refreshed!")
                        st.rerun()
                    except Exception:
                        st.error("Steam refresh failed.")
        with b_cols[1]:
            if steam_g and steam_g.get("url"):
                st.link_button("🔗 Open Steam", steam_g["url"], use_container_width=True)
        with b_cols[2]:
            if epic_g and st.button("🔄 Refresh Epic", key=f"ref_{epic_g['id']}", use_container_width=True):
                with st.spinner("Checking Epic Games..."):
                    try:
                        details = fetch_game_details("epic", epic_g["url"])
                        apply_game_update(epic_g, details)
                        gh.save_games(games, f"Refresh Epic price for {name}")
                        st.session_state.games = games
                        st.success("Epic price refreshed!")
                        st.rerun()
                    except Exception:
                        st.error("Epic refresh failed.")
        with b_cols[3]:
            if epic_g and epic_g.get("url"):
                st.link_button("🔗 Open Epic", epic_g["url"], use_container_width=True)
        with b_cols[4]:
            if st.button("🗑 Delete", key=f"del_all_{primary_game['id']}", use_container_width=True, type="secondary"):
                for g in listings:
                    games = remove_game(games, g["id"])
                gh.save_games(games, f"Remove {name} from tracker")
                st.session_state.games = games
                st.success(f"Removed {name}")
                st.rerun()
    else:
        g = primary_game
        gid = g["id"]
        store_lbl = STORE_LABELS.get(g["store"], g["store"])
        b_cols = st.columns([1.3, 1.6, 1.1, 2.5])
        with b_cols[0]:
            if st.button("🔄 Refresh", key=f"ref_{gid}", use_container_width=True):
                with st.spinner(f"Checking {store_lbl}..."):
                    try:
                        details = fetch_game_details(g["store"], g["url"])
                        apply_game_update(g, details)
                        if details.current_price is not None:
                            gh.save_games(games, f"Refresh price for {name}")
                            st.session_state.games = games
                            st.success(f"{store_lbl}: {format_price(details.current_price, details.currency)}")
                        else:
                            st.warning(f"{store_lbl}: Kept last known price.")
                        st.rerun()
                    except Exception:
                        st.error(f"{store_lbl} refresh failed.")
        with b_cols[1]:
            if g.get("url"):
                st.link_button(f"🔗 Open {store_lbl}", g["url"], use_container_width=True)
        with b_cols[2]:
            if st.button("🗑 Delete", key=f"del_{gid}", use_container_width=True, type="secondary"):
                updated = remove_game(games, gid)
                try:
                    gh.save_games(updated, f"Remove {name} from tracker")
                    st.session_state.games = updated
                    st.success(f"Removed {name}")
                    st.rerun()
                except Exception:
                    st.error("Failed to remove.")


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
                    f"Price: {format_price(details.current_price, details.currency)}"
                )
                st.rerun()
        except Exception:
            logger.exception("Failed to add game")
            st.error("Error adding game. Check the URL and try again.")


def handle_refresh_all(games: list[dict], gh: GitHubManager):
    with st.spinner("Refreshing all prices across stores..."):
        ok = 0
        failed = 0
        for g in games:
            try:
                details = fetch_game_details(g["store"], g["url"])
                apply_game_update(g, details)
                if details.current_price is not None:
                    ok += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
                continue
        gh.save_games(games, "chore: refresh all prices")
        st.session_state.games = games
        msg = f"Refreshed {ok}/{len(games)} listing(s)."
        if failed:
            msg += f" {failed} store(s) kept last known prices."
        st.success(msg)
        st.rerun()


# ── View 1: 🏠 Dashboard ─────────────────────────────────────────────
def render_dashboard_view(games: list[dict], history: dict, gh: GitHubManager):
    on_sale_games = [g for g in games if g.get("is_on_sale")]
    unique_games = len(group_games_by_identity(games))
    store_stats = store_filter_stats(games)
    last_sync = get_last_sync(games)

    st.markdown(
        f'<div class="summary-cards-container">'
        f'<div class="sum-card"><div class="sum-icon">🎮</div><div class="sum-info"><div class="sum-label">Tracked Games</div><div class="sum-val">{unique_games}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon">🔥</div><div class="sum-info"><div class="sum-label">On Sale</div><div class="sum-val sale">{len(on_sale_games)}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#66c0f4;">●</div><div class="sum-info"><div class="sum-label">Steam</div><div class="sum-val">{store_stats["steam"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#f8fafc;">●</div><div class="sum-info"><div class="sum-label">Epic Games</div><div class="sum-val">{store_stats["epic"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#818cf8;">✨</div><div class="sum-info"><div class="sum-label">Both Stores</div><div class="sum-val accent">{store_stats["both"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#94a3b8;">⏱️</div><div class="sum-info"><div class="sum-label">Last Synced</div><div class="sum-val" style="font-size:15px;color:#94a3b8;">{last_sync}</div></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Primary Search Box on Dashboard
    st.markdown('<div class="search-hero-box"><div style="font-size:16px;font-weight:700;color:#f8fafc;margin-bottom:10px;">🔍 Search & Track Games Across Stores</div>', unsafe_allow_html=True)
    s_col, btn_col = st.columns([4, 1.2])
    with s_col:
        dash_search_query = st.text_input(
            "Search for a game to track",
            placeholder="Search The Witcher 3, Cyberpunk 2077, Hogwarts Legacy...",
            label_visibility="collapsed",
            key="dash_search_query_input",
        )
    with btn_col:
        dash_search_clicked = st.button("Search Stores", type="primary", use_container_width=True, key="dash_search_btn")

    if dash_search_clicked and dash_search_query.strip():
        with st.spinner("Searching storefronts..."):
            try:
                st.session_state.search_results = search_games(dash_search_query.strip(), limit=6)
                st.session_state.last_searched_query = dash_search_query.strip()
            except Exception:
                logger.exception("Search failed")
                st.session_state.search_results = []
                st.error("Search failed. Please try again.")

    dash_results: list[AggregatedGame] = st.session_state.get("search_results", [])
    if dash_results:
        st.markdown(f'<div style="font-size:15px;font-weight:700;color:#f8fafc;margin:16px 0 10px;">Results for "{st.session_state.get("last_searched_query", "")}"</div>', unsafe_allow_html=True)
        for agg in dash_results:
            render_search_result_card(agg, games, gh, "All")

    with st.expander("Can't find your game? Add a store URL manually", expanded=False):
        st.markdown('<div style="font-size:13px;color:#94a3b8;margin-bottom:8px;">Paste a direct Steam, Epic Games, or GOG store URL:</div>', unsafe_allow_html=True)
        url_c, pr_c, add_c = st.columns([3.2, 1, 1.2])
        with url_c:
            m_url = st.text_input("Store URL input", placeholder="https://store.steampowered.com/app/...", label_visibility="collapsed", key="dash_manual_url")
        with pr_c:
            m_target = st.text_input("Target price (₹)", placeholder="Target (₹)", label_visibility="collapsed", key="dash_manual_target")
        with add_c:
            if st.button("Add URL", type="primary", use_container_width=True, key="dash_manual_add_btn"):
                handle_add_game(games, m_url, m_target, gh)

    st.markdown('</div>', unsafe_allow_html=True)

    # Top Active Deals Preview
    st.markdown('<div style="font-size:17px;font-weight:800;color:#f8fafc;margin:24px 0 12px;">🔥 Top Active Deals</div>', unsafe_allow_html=True)
    if on_sale_games:
        grouped = group_games_by_identity(on_sale_games)
        for gid, listings in list(grouped.items())[:3]:
            render_game_card(listings, gh, games, history)
    else:
        st.markdown('<div class="empty-box"><div class="empty-icon">🏷️</div><div class="empty-title">No active sales right now</div><div class="empty-sub">When games in your library go on sale, they will be highlighted here.</div></div>', unsafe_allow_html=True)


# ── View 2: 🔍 Search Games ──────────────────────────────────────────
def render_search_view(games: list[dict], gh: GitHubManager):
    st.markdown('<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:12px;">🔍 Search & Add Games</div>', unsafe_allow_html=True)
    st.markdown('<div class="search-hero-box">', unsafe_allow_html=True)
    s_col, btn_col = st.columns([4, 1.2])
    with s_col:
        search_query = st.text_input(
            "Search for games, editions, stores...",
            placeholder="Search for games, editions, stores...",
            label_visibility="collapsed",
            key="main_search_query_input",
        )
    with btn_col:
        search_clicked = st.button("Search Games", type="primary", use_container_width=True, key="search_page_btn")

    search_store_filter = st.radio(
        "Search filter store options",
        ["All", "Steam", "Epic Games"],
        horizontal=True,
        label_visibility="collapsed",
        key="search_page_store_filter",
    )

    if search_clicked and search_query.strip():
        with st.spinner("Searching storefronts..."):
            try:
                st.session_state.search_results = search_games(search_query.strip(), limit=8)
                st.session_state.last_searched_query = search_query.strip()
            except Exception:
                logger.exception("Search failed")
                st.session_state.search_results = []
                st.error("Search failed. Please try again.")

    with st.expander("Can't find your game? Add a store URL manually", expanded=False):
        st.markdown('<div style="font-size:13px;color:#94a3b8;margin-bottom:8px;">Paste a direct Steam, Epic Games, or GOG product URL:</div>', unsafe_allow_html=True)
        url_col, price_col, add_btn_col = st.columns([3.2, 1, 1.2])
        with url_col:
            game_url = st.text_input("Game URL input", placeholder="https://store.steampowered.com/app/...", label_visibility="collapsed", key="add_game_url_search_page")
        with price_col:
            target_price_input = st.text_input("Target price input", placeholder="Target (₹)", label_visibility="collapsed", key="add_target_price_search_page")
        with add_btn_col:
            if st.button("Add URL", type="primary", use_container_width=True, key="add_url_btn_search_page"):
                handle_add_game(games, game_url, target_price_input, gh)

    st.markdown('</div>', unsafe_allow_html=True)

    results: list[AggregatedGame] = st.session_state.get("search_results", [])
    last_query = st.session_state.get("last_searched_query", "")
    if results:
        st.markdown(f'<div style="font-size:15px;font-weight:700;color:#f8fafc;margin:18px 0 10px;">Results for "{last_query}" ({len(results)})</div>', unsafe_allow_html=True)
        for agg in results:
            render_search_result_card(agg, games, gh, search_store_filter)
    elif last_query and search_clicked:
        st.info(f"No games found matching **'{last_query}'**.")


# ── View 3: 🎮 Tracked Games ─────────────────────────────────────────
def render_tracked_games_view(games: list[dict], history: dict, gh: GitHubManager):
    unique_games = len(group_games_by_identity(games))
    on_sale_games = [g for g in games if g.get("is_on_sale")]
    store_stats = store_filter_stats(games)
    last_sync = get_last_sync(games)

    st.markdown(
        f'<div class="summary-cards-container">'
        f'<div class="sum-card"><div class="sum-icon">🎮</div><div class="sum-info"><div class="sum-label">Tracked Games</div><div class="sum-val">{unique_games}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon">🔥</div><div class="sum-info"><div class="sum-label">On Sale</div><div class="sum-val sale">{len(on_sale_games)}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#66c0f4;">●</div><div class="sum-info"><div class="sum-label">Steam</div><div class="sum-val">{store_stats["steam"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#f8fafc;">●</div><div class="sum-info"><div class="sum-label">Epic Games</div><div class="sum-val">{store_stats["epic"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#818cf8;">✨</div><div class="sum-info"><div class="sum-label">Both Stores</div><div class="sum-val accent">{store_stats["both"]}</div></div></div>'
        f'<div class="sum-card"><div class="sum-icon" style="color:#94a3b8;">⏱️</div><div class="sum-info"><div class="sum-label">Last Synced</div><div class="sum-val" style="font-size:15px;color:#94a3b8;">{last_sync}</div></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    f_col1, f_col2 = st.columns([3, 1.5])
    with f_col1:
        store_list_filter = st.radio(
            "Filter games by store availability",
            ["All Games", "Steam", "Epic Games", "Both Stores"],
            horizontal=True,
            label_visibility="collapsed",
            key="tracked_store_filter_radio",
        )
    with f_col2:
        sort_choice = st.selectbox(
            "Sort library games by",
            [
                "Last Updated", "Price", "Discount", "Name",
            ],
            label_visibility="collapsed",
            key="tracked_sort_choice_select",
        )

    def _apply_filter_and_sort(games_list: list[dict]) -> list[dict]:
        out = list(games_list)
        if sort_choice == "Discount":
            out.sort(key=lambda g: (g.get("discount_percent") or 0), reverse=True)
        elif sort_choice == "Price":
            out.sort(key=lambda g: (g.get("current_price") if g.get("current_price") is not None else float("inf")))
        elif sort_choice == "Name":
            out.sort(key=lambda g: g.get("name", "").lower())
        elif sort_choice == "Last Updated":
            out.sort(key=lambda g: g.get("last_checked", ""), reverse=True)
        return out

    filter_map = {"All Games": "All", "Steam": "Steam", "Epic Games": "Epic Games", "Both Stores": "Steam + Epic"}
    filtered_groups = filter_grouped_games(games, filter_map.get(store_list_filter, "All"))
    display_groups: list[list[dict]] = []
    for gid, listings in filtered_groups.items():
        filtered_listings = _apply_filter_and_sort(listings)
        if not filtered_listings:
            continue
        display_groups.append(filtered_listings)

    if sort_choice == "Discount":
        display_groups.sort(key=lambda grp: max((g.get("discount_percent") or 0 for g in grp), default=0), reverse=True)
    elif sort_choice == "Price":
        display_groups.sort(key=lambda grp: min((g.get("current_price") for g in grp if g.get("current_price") is not None), default=float("inf")))
    elif sort_choice == "Name":
        display_groups.sort(key=lambda grp: grp[0].get("name", "").lower())
    elif sort_choice == "Last Updated":
        display_groups.sort(key=lambda grp: max(g.get("last_checked", "") for g in grp), reverse=True)

    if not games:
        st.markdown('<div class="empty-box"><div class="empty-icon">🎮</div><div class="empty-title">No games tracked yet</div><div class="empty-sub">Use Search Games in the sidebar to find and track titles.</div></div>', unsafe_allow_html=True)
    elif not display_groups:
        st.info("No tracked games match this store filter.")
    else:
        for listings in display_groups:
            render_game_card(listings, gh, games, history)


# ── View 4: 📈 Price History ─────────────────────────────────────────
def render_history_view(games: list[dict], history: dict):
    st.markdown('<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:12px;">📈 Price History & Trends</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;color:#94a3b8;margin-bottom:16px;">View historical price fluctuations and export tracking data.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if games:
            st.download_button("📥 Export Games (CSV)", games_to_csv(games), "games.csv", "text/csv", use_container_width=True)
    with c2:
        if games:
            st.download_button("📋 Export Games (JSON)", games_to_json(games), "games.json", "application/json", use_container_width=True)
    with c3:
        if history:
            st.download_button("📈 Export History (CSV)", history_to_csv(history), "history.csv", "text/csv", use_container_width=True)

    st.markdown('<div style="margin-top:24px;font-size:16px;font-weight:700;color:#f8fafc;margin-bottom:10px;">Historical Price Log</div>', unsafe_allow_html=True)
    if not games:
        st.markdown('<div class="empty-box"><div class="empty-title">No price history recorded yet</div></div>', unsafe_allow_html=True)
        return

    table_rows = ""
    for g in games:
        hist = get_history_prices(history, g["id"])
        spark = render_sparkline_svg(hist[-10:], width=90, height=22) if len(hist) >= 2 else "—"
        cur = format_price(g.get("current_price"), get_price_currency(g, "current_price"))
        low = format_price(g.get("lowest_price"), get_price_currency(g, "lowest_price"))
        table_rows += (
            f'<tr>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #1a2337;">{g.get("name", "Unknown")} {render_store_tag(g.get("store", ""))}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #1a2337;text-align:right;">{cur}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #1a2337;text-align:right;color:#4ade80;font-weight:600;">{low}</td>'
            f'<td style="padding:10px 8px;border-bottom:1px solid #1a2337;text-align:center;">{spark}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;margin:10px 0;font-size:13px;">'
        f'<thead><tr style="color:#64748b;font-size:11px;text-transform:uppercase;border-bottom:1px solid #1f293d;"><th style="text-align:left;padding:8px;">Game</th><th style="text-align:right;padding:8px;">Current Price</th><th style="text-align:right;padding:8px;">Lowest Recorded</th><th style="text-align:center;padding:8px;">Trend</th></tr></thead>'
        f'<tbody>{table_rows}</tbody>'
        f'</table>',
        unsafe_allow_html=True,
    )


# ── View 5: 🧮 Smart Calculator (Budget Combination Calculator) ──────
def render_smart_calculator(games: list[dict]):
    priceable = [g for g in games if g.get("current_price") is not None]
    name_to_id = {g["name"]: g["id"] for g in priceable}

    st.markdown('<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:8px;">🧮 Smart Calculator</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;color:#94a3b8;margin-bottom:16px;">Calculate the optimal combination of tracked games that fits within your budget.</div>', unsafe_allow_html=True)

    if not priceable:
        st.markdown('<div class="empty-box"><div class="empty-icon">🛒</div><div class="empty-title">No priced games available</div><div class="empty-sub">Track games first to calculate your budget combinations.</div></div>', unsafe_allow_html=True)
        return

    st.markdown('<div style="background:#121827;border:1px solid #1f293d;border-radius:10px;padding:18px;margin-bottom:20px;">', unsafe_allow_html=True)
    bcol, ccol = st.columns(2)
    with bcol:
        st.markdown('<div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">Total Budget (₹)</div>', unsafe_allow_html=True)
        budget = st.number_input("Budget in INR", min_value=1, step=100, value=3000, label_visibility="collapsed")
    with ccol:
        st.markdown('<div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">Number of Games to Buy</div>', unsafe_allow_html=True)
        count = st.number_input("Games count", min_value=1, max_value=len(priceable), step=1, value=min(3, len(priceable)), label_visibility="collapsed")

    mcol, fcol = st.columns([2, 1.4])
    with mcol:
        st.markdown('<div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">Must Include Game (Optional)</div>', unsafe_allow_html=True)
        must_names = st.multiselect("Must include games", list(name_to_id.keys()), label_visibility="collapsed")
    with fcol:
        st.markdown('<div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">Budget Flexibility</div>', unsafe_allow_html=True)
        flex = st.checkbox("Allow flexible budget (+10%)", value=True)
        flex_pct = 10.0 if flex else 0.0

    def _current_options() -> BudgetOptions:
        return BudgetOptions(
            budget=float(budget),
            count=int(count),
            must_include_ids=tuple(name_to_id[n] for n in must_names),
            flex_pct=float(flex_pct),
        )

    fingerprint = (float(budget), int(count), tuple(sorted(name_to_id[n] for n in must_names)), float(flex_pct))
    ss = st.session_state
    if ss.get("planner.fp") != fingerprint:
        ss["planner.fp"] = fingerprint
        ss["planner.excluded"] = set()
        ss["planner.result"] = None
        ss["planner.error"] = None

    btn_row1, btn_row2, _ = st.columns([1.6, 1.6, 3])
    with btn_row1:
        generate_clicked = st.button("⚡ Generate Combination", type="primary", use_container_width=True)
    with btn_row2:
        refresh_clicked = st.button("🔄 New Combination", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

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

    if ss.get("planner.error"):
        st.error(ss["planner.error"])

    result = plan if plan is not None else ss.get("planner.result")
    if result is None:
        return

    items_html = ""
    for i, g in enumerate(result.games, start=1):
        p_str = format_price(g.get("current_price"), get_price_currency(g, "current_price"))
        items_html += (
            f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1a2337;font-size:14px;">'
            f'<span><strong style="color:#64748b;margin-right:8px;">{i}.</strong> {g["name"]} {render_store_tag(g.get("store", ""))}</span>'
            f'<span style="font-weight:700;color:#f8fafc;">{p_str}</span>'
            f'</div>'
        )

    over = result.is_over_budget
    rem_label = "Over Budget" if over else "Remaining"
    rem_val = f"+{format_price(result.over_amount, 'INR')}" if over else format_price(result.remaining, "INR")

    st.markdown(
        f'<div style="background:#121827;border:1px solid #1f293d;border-radius:10px;padding:20px;">'
        f'<div style="font-size:16px;font-weight:700;color:#f8fafc;margin-bottom:14px;">Selected Game Combination ({len(result.games)} games)</div>'
        f'<div class="summary-cards-container">'
        f'<div class="sum-card"><div class="sum-info"><div class="sum-label">Budget</div><div class="sum-val">{format_price(result.budget, "INR")}</div></div></div>'
        f'<div class="sum-card"><div class="sum-info"><div class="sum-label">Total Cost</div><div class="sum-val">{format_price(result.total, "INR")}</div></div></div>'
        f'<div class="sum-card"><div class="sum-info"><div class="sum-label">{rem_label}</div><div class="sum-val {"sale" if not over else "accent"}">{rem_val}</div></div></div>'
        f'</div>'
        f'{items_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── View 6: 🔥 Deals ─────────────────────────────────────────────────
def render_deals_view(games: list[dict], history: dict, gh: GitHubManager):
    on_sale_games = [g for g in games if g.get("is_on_sale")]
    st.markdown(f'<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:8px;">🔥 Active Deals & Sales</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:14px;color:#94a3b8;margin-bottom:16px;">Currently tracking {len(on_sale_games)} active store discount(s).</div>', unsafe_allow_html=True)
    if not on_sale_games:
        st.markdown('<div class="empty-box"><div class="empty-icon">🔥</div><div class="empty-title">No active sales right now</div><div class="empty-sub">When games in your tracker go on sale, they will appear here.</div></div>', unsafe_allow_html=True)
        return

    grouped = group_games_by_identity(on_sale_games)
    for gid, listings in grouped.items():
        render_game_card(listings, gh, games, history)


# ── View 7: 📧 Reports ────────────────────────────────────────────────
def render_reports_view(games: list[dict], history: dict):
    st.markdown('<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:8px;">📧 Daily Price Reports</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;color:#94a3b8;margin-bottom:16px;">Daily email report summary and preview.</div>', unsafe_allow_html=True)
    report_html = build_daily_report(games, history)
    st.components.v1.html(report_html, height=650, scrolling=True)


# ── View 8: ⚙️ Settings ──────────────────────────────────────────────
def render_settings_view(games: list[dict], gh: GitHubManager):
    st.markdown('<div style="font-size:18px;font-weight:800;color:#f8fafc;margin-bottom:8px;">⚙️ Settings & Synchronization</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:14px;color:#94a3b8;margin-bottom:16px;">GitHub persistence and scheduler settings.</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#121827;border:1px solid #1f293d;border-radius:10px;padding:20px;">'
        f'<div style="font-size:15px;font-weight:700;color:#f8fafc;margin-bottom:8px;">GitHub Repository Connection</div>'
        f'<div style="font-size:13px;color:#94a3b8;line-height:1.6;margin-bottom:16px;">'
        f'Owner: <strong>{gh.owner}</strong><br>'
        f'Repository: <strong>{gh.repo}</strong><br>'
        f'Tracked listings file: <strong>games.json</strong><br>'
        f'Price history file: <strong>history.json</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Force Synchronize Data", type="primary"):
        with st.spinner("Syncing data to GitHub..."):
            gh.save_games(games, "chore: manual sync from dashboard")
            st.success("Synchronized successfully!")
    st.markdown('</div>', unsafe_allow_html=True)


# ── Main Application Orchestrator ────────────────────────────────────
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

    last_sync = get_last_sync(games)
    unique_games = len(group_games_by_identity(games))
    on_sale_count = len([g for g in games if g.get("is_on_sale")])

    # ── Compact Left Sidebar Navigation ──────────────────────
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            '<span class="sidebar-brand-icon">🎮</span>'
            '<div>'
            '<div class="sidebar-brand-title">GameTracker</div>'
            '<div class="sidebar-brand-subtitle">Price & Sale Tracker</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        nav_choice = st.radio(
            "Dashboard Navigation Menu",
            [
                "🏠 Dashboard",
                "🔍 Search Games",
                "🎮 Tracked Games",
                "📈 Price History",
                "🧮 Smart Calculator",
                "🔥 Deals",
                "📧 Reports",
                "⚙️ Settings",
            ],
            index=0,
            label_visibility="collapsed",
            key="main_sidebar_nav_choice",
        )

        st.markdown(
            f'<div class="sidebar-status-card">'
            f'<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Status</div>'
            f'<div style="font-size:13px;color:#f8fafc;margin-top:4px;">{unique_games} games ({on_sale_count} on sale)</div>'
            f'<div style="font-size:11px;color:#64748b;margin-top:2px;">Last synced: {last_sync}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Top Bar Header ───────────────────────────────────────
    tb_col1, tb_col2 = st.columns([3.5, 1.4])
    with tb_col1:
        st.markdown(
            f'<div style="font-size:22px;font-weight:800;color:#f8fafc;letter-spacing:-0.02em;">{nav_choice}</div>',
            unsafe_allow_html=True,
        )
    with tb_col2:
        if st.button("🔄 Refresh All Prices", type="primary", use_container_width=True, key="topbar_refresh_all"):
            handle_refresh_all(games, gh)

    # ── Main View Routing ────────────────────────────────────
    st.markdown('<div class="main-view-container">', unsafe_allow_html=True)
    if nav_choice == "🏠 Dashboard":
        render_dashboard_view(games, history, gh)
    elif nav_choice == "🔍 Search Games":
        render_search_view(games, gh)
    elif nav_choice == "🎮 Tracked Games":
        render_tracked_games_view(games, history, gh)
    elif nav_choice == "📈 Price History":
        render_history_view(games, history)
    elif nav_choice == "🧮 Smart Calculator":
        render_smart_calculator(games)
    elif nav_choice == "🔥 Deals":
        render_deals_view(games, history, gh)
    elif nav_choice == "📧 Reports":
        render_reports_view(games, history)
    elif nav_choice == "⚙️ Settings":
        render_settings_view(games, gh)
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
