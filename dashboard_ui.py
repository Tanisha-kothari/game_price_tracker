"""Theme-aware, game-lobby Streamlit UI for GameTracker inspired by playful gaming aesthetics.

Usage:
    from dashboard_ui import render_dashboard
    render_dashboard(games=games, theme=active_theme, stats=stats)
"""
from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence
import streamlit as st

from utils import format_price
from database import get_price_currency, is_target_met, apply_game_update, remove_game
from price_api import fetch_game_details
from themes import get_contextual_message, get_theme

DEFAULTS = {
    "background": "#0f172a", "surface": "#1e293b", "surface_alt": "#334155",
    "text": "#f8fafc", "muted": "#94a3b8", "primary": "#6366f1",
    "primary_hover": "#4f46e5", "accent": "#818cf8", "success": "#4ade80",
    "border": "#3b4f73", "radius": "20px",
    "shadow": "0 8px 24px rgba(15, 23, 42, 0.5)",
}

ALIASES = {
    "background": ("background", "bg", "background_color", "app_bg", "page_bg", "bg_body"),
    "surface": ("surface", "card", "card_bg", "secondary_background", "panel", "bg_card"),
    "surface_alt": ("surface_alt", "sidebar", "sidebar_bg", "secondary", "panel_alt", "bg_card_elevated"),
    "text": ("text", "text_color", "foreground", "primary_text", "text_primary"),
    "muted": ("muted", "text_muted", "secondary_text", "muted_text"),
    "primary": ("primary", "primary_color", "accent", "accent_color", "btn_primary_bg"),
    "primary_hover": ("primary_hover", "accent_hover", "hover_color", "border_hover"),
    "accent": ("highlight", "sale", "sale_color", "warning", "secondary_accent", "accent_primary"),
    "success": ("success", "success_color", "discount", "discount_color", "sale_color"),
    "border": ("border", "border_color", "outline"),
    "radius": ("radius", "card_radius", "border_radius"),
    "shadow": ("shadow", "card_shadow", "shadow_card"),
}


def _tokens(theme: Mapping[str, Any] | None) -> dict[str, str]:
    result = dict(DEFAULTS)
    theme = theme or {}
    for token, aliases in ALIASES.items():
        for key in aliases:
            if theme.get(key) not in (None, ""):
                result[token] = str(theme[key])
                break
    return result


def _css(t: Mapping[str, str]) -> str:
    # Retained for backwards compatibility if called elsewhere;
    # Global styling is handled by generate_theme_css.
    return ""


def _value(item: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if item.get(key) not in (None, ""):
            return item[key]
    return default


def _safe(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _money(value: Any, currency: str = "₹") -> str:
    if value in (None, ""):
        return "Price unavailable"
    try:
        n = float(value)
        return f"{currency}{n:,.0f}" if n.is_integer() else f"{currency}{n:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def _store_badge(store_name: str) -> str:
    s = str(store_name or "").lower()
    if "steam" in s:
        return '<span class="store-tag steam">🟦 Steam</span>'
    elif "epic" in s:
        return '<span class="store-tag epic">⚡ Epic Games</span>'
    elif "gog" in s:
        return '<span class="store-tag gog">🛡️ GOG</span>'
    return f'<span class="store-tag">🎮 {_safe(store_name or "Store")}</span>'


def _game_card_html(game: Mapping[str, Any], currency: str = "₹", is_owned: bool = False) -> str:
    title = _value(game, "name", "title", "game_name", default="Untitled Game")
    image = _value(game, "cover_image", "image", "cover", "image_url", "header_image")
    store = _value(game, "store", "store_name", default="")
    price = _value(game, "current_price", "price")
    regular = _value(game, "original_price", "regular_price")
    discount = _value(game, "discount_percent", "discount", "discount_percentage", default=0)
    lowest = _value(game, "lowest_price")
    target = _value(game, "target_price")
    genre = _value(game, "genre", "category", default="")
    is_sale = bool(game.get("is_on_sale") or (discount and float(discount) > 0))

    cover_html = (
        f'<div class="card-art-wrap"><img src="{_safe(image)}" alt="{_safe(title)}" class="card-art-img"></div>'
        if image else
        f'<div class="card-art-wrap" style="display:flex;align-items:center;justify-content:center;font-size:36px;">🎮</div>'
    )

    store_badge = _store_badge(store)
    
    # Badges
    badges_html = store_badge
    if is_owned:
        badges_html += ' <span class="owned-badge">🏆 IN LIBRARY</span>'
    elif is_sale and discount and float(discount) > 0:
        badges_html += f' <span class="disc-tag">🔥 -{int(float(discount))}%</span>'

    # Price row
    price_str = _money(price, currency) if price is not None else "Price unavailable"
    reg_str = f'<span class="price-orig-strike">{_money(regular, currency)}</span>' if regular and is_sale and float(regular) > (float(price) if price else 0) else ""
    
    lowest_html = ""
    if lowest is not None:
        is_lowest = (price is not None and float(price) <= float(lowest))
        lbl = "👑 Historic Low!" if is_lowest else f"Lowest: {_money(lowest, currency)}"
        lowest_html = f'<div class="lowest-price-badge">{lbl}</div>'

    # Target indicator
    target_html = ""
    if target is not None:
        try:
            t_val = float(target)
            if price is not None:
                p_val = float(price)
                if p_val <= t_val:
                    target_html = '<div style="margin-top:6px;"><span class="target-met-badge">🎯 TARGET REACHED!</span></div>'
                else:
                    target_html = f'<div style="font-size:11px;color:var(--theme-text-muted);margin-top:4px;">Target: {_money(t_val, currency)}</div>'
        except (ValueError, TypeError):
            pass

    genre_html = f'<span style="font-size:11px;color:var(--theme-text-muted);font-weight:600;margin-top:4px;">{_safe(genre)}</span>' if genre else ""

    return (
        f'<div class="game-card-wrapper{" on-sale" if is_sale else ""}">'
        f'<div class="card-layout-flex">'
        f'<div class="card-art-col">{cover_html}</div>'
        f'<div class="card-info-col">'
        f'<div class="card-title-row">'
        f'<div class="card-game-title">{_safe(title)}</div>'
        f'<div>{badges_html}</div>'
        f'</div>'
        f'{genre_html}'
        f'<div style="display:flex;align-items:baseline;gap:8px;margin:8px 0 6px;">'
        f'<span style="font-size:22px;font-weight:900;color:{"var(--theme-sale)" if is_sale else "var(--theme-text-primary)"};font-family:\'Fredoka\',\'Inter\',sans-serif;">{price_str}</span>'
        f'{reg_str}'
        f'</div>'
        f'{lowest_html}'
        f'{target_html}'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def render_dashboard(
    games: Sequence[Mapping[str, Any]] | None = None,
    theme: Mapping[str, Any] | None = None,
    stats: Mapping[str, Any] | None = None,
    purchased_games: Sequence[Mapping[str, Any]] | None = None,
    history: Mapping[str, Any] | None = None,
    gh: Any = None,
    on_search: Callable[[str], Any] | None = None,
    currency: str = "₹",
    title: str = "GameTracker",
    subtitle: str = "Your gaming lobby and personal loot radar.",
    page_size: int = 9,
) -> None:
    """Render the full, playful gaming lobby dashboard."""
    games_list = list(games or [])
    stats_dict = dict(stats or {})
    theme_dict = dict(theme or {})
    purchased_list = list(purchased_games or st.session_state.get("purchased_games", []))
    history_dict = dict(history or st.session_state.get("history", {}))

    theme_id = theme_dict.get("id", "midnight_gamer")
    theme_settings = st.session_state.get("theme_settings", {})
    personality_level = theme_settings.get("personality_level", "Playful")

    # Metrics
    tracked_count = stats_dict.get("tracked", len(games_list))
    on_sale_games = [
        g for g in games_list
        if bool(g.get("is_on_sale") or (g.get("discount_percent") and float(g.get("discount_percent") or 0) > 0))
    ]
    on_sale_count = len(on_sale_games)
    owned_count = len(purchased_list)

    # Max discount
    discounts = [float(g.get("discount_percent") or 0) for g in on_sale_games if g.get("discount_percent")]
    max_discount = int(max(discounts)) if discounts else 0

    # Target reached games
    target_met_games = []
    for g in games_list:
        t_price = g.get("target_price")
        c_price = g.get("current_price")
        if t_price is not None and c_price is not None:
            try:
                if float(c_price) <= float(t_price):
                    target_met_games.append(g)
            except (ValueError, TypeError):
                pass

    # ── CELEBRATION BANNER FOR TARGET MET ────────────────────────────
    if target_met_games:
        tg = target_met_games[0]
        t_name = _safe(tg.get("name") or tg.get("title") or "Tracked Game")
        t_price_str = _money(tg.get("current_price"), currency)
        st.markdown(
            f'<div class="celebration-banner">'
            f'<span style="font-size:28px;">🎉</span>'
            f'<div>'
            f'<div style="font-size:15px;font-weight:900;color:var(--theme-text-primary);letter-spacing:-0.02em;">'
            f'TARGET UNLOCKED: <strong>{t_name}</strong> is now down to {t_price_str}!'
            f'</div>'
            f'<div style="font-size:12px;color:var(--theme-text-secondary);">'
            f'The merchant price has dropped to or below your target! Grab it before the sale ends 🎯'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── GAMING LOBBY HERO ───────────────────────────────────────────
    context_msg = get_contextual_message(
        "sale" if on_sale_count > 0 else "wallet_safe",
        theme_id=theme_id,
        personality_level=personality_level,
        discount_percent=max_discount,
    )

    context_bubble = ""
    if context_msg:
        context_bubble = (
            f'<div style="display:inline-flex;align-items:center;gap:7px;background:var(--theme-accent-bg);'
            f'border:1.5px solid var(--theme-accent-primary);border-radius:12px;padding:6px 14px;'
            f'font-size:12.5px;font-weight:700;color:var(--theme-accent-primary);margin-top:10px;">'
            f'💬 <em>{_safe(context_msg)}</em>'
            f'</div>'
        )

    st.markdown(
        f'<div class="lobby-hero">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
        f'<span style="font-size:32px;display:inline-block;animation:floatGamer 3s infinite ease-in-out;">🕹️</span>'
        f'<div class="lobby-hero-title">WELCOME TO THE GAMING LOBBY, PLAYER 1!</div>'
        f'</div>'
        f'<div class="lobby-hero-sub">Your personal command center for tracking store loot, catching price drops, and building your collection.</div>'
        f'<div class="lobby-chips">'
        f'<span class="lobby-chip">🟢 RADAR ONLINE</span>'
        f'<span class="lobby-chip">⚡ 3 STORES CONNECTED</span>'
        f'<span class="lobby-chip">🎯 {len(target_met_games)} TARGETS REACHED</span>'
        + (f'<span class="lobby-chip">⏱️ REFRESHED: {_safe(stats_dict["last_automatic_refresh"])}</span>' if stats_dict.get("last_automatic_refresh") else '')
        + (f'<span class="lobby-chip">⏳ NEXT: {_safe(stats_dict["next_scheduled_refresh"])}</span>' if stats_dict.get("next_scheduled_refresh") else '')
        + f'</div>'
        f'{context_bubble}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── ARCADE JUMP PADS (Quick Navigation) ──────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;margin:20px 0 10px;">'
        '<span style="font-size:18px;">🕹️</span>'
        '<span style="font-size:15px;font-weight:900;text-transform:uppercase;letter-spacing:0.6px;color:var(--theme-text-primary);">LOBBY JUMP PADS</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🎮 Watchlist\n\nAll Tracked", use_container_width=True, key="jump_tracked"):
            st.session_state.main_sidebar_nav_choice = "🎮 Tracked Games"
            st.rerun()
    with col2:
        if st.button("🔍 Hunter\n\nSearch Store", use_container_width=True, key="jump_search"):
            st.session_state.main_sidebar_nav_choice = "🔍 Search Games"
            st.rerun()
    with col3:
        if st.button(f"📚 Loot Vault\n\n{owned_count} Owned", use_container_width=True, key="jump_library"):
            st.session_state.main_sidebar_nav_choice = "📚 My Library"
            st.rerun()
    with col4:
        if st.button("📈 Radar\n\nPrice Trends", use_container_width=True, key="jump_history"):
            st.session_state.main_sidebar_nav_choice = "📈 Price History"
            st.rerun()
    with col5:
        if st.button("🧮 Calculator\n\nSmart Planner", use_container_width=True, key="jump_calc"):
            st.session_state.main_sidebar_nav_choice = "🧮 Smart Calculator"
            st.rerun()
    with col6:
        if st.button(f"🔥 Hot Deals\n\n{on_sale_count} Active", type="primary", use_container_width=True, key="jump_deals"):
            st.session_state.main_sidebar_nav_choice = "🔥 Deals"
            st.rerun()

    # ── TRACKED GAME STATS (Arcade Stat Pods) ────────────────────────
    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="stat-pods-grid">'
        f'<div class="stat-pod">'
        f'<div class="stat-pod-icon">🎮</div>'
        f'<div><div class="stat-pod-label">GAMES IN RADAR</div><div class="stat-pod-val">{tracked_count}</div></div>'
        f'</div>'
        f'<div class="stat-pod">'
        f'<div class="stat-pod-icon" style="color:var(--theme-sale);">🔥</div>'
        f'<div><div class="stat-pod-label">ON SALE NOW</div><div class="stat-pod-val sale">{on_sale_count}</div></div>'
        f'</div>'
        f'<div class="stat-pod">'
        f'<div class="stat-pod-icon">📚</div>'
        f'<div><div class="stat-pod-label">LIBRARY LOOT</div><div class="stat-pod-val">{owned_count}</div></div>'
        f'</div>'
        f'<div class="stat-pod">'
        f'<div class="stat-pod-icon">💎</div>'
        f'<div><div class="stat-pod-label">TOP DISCOUNT</div><div class="stat-pod-val accent">-{max_discount}%</div></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── PROMINENT GAME SEARCH SECTION ────────────────────────────────
    st.markdown(
        '<div style="background:var(--theme-bg-card);border:2.5px solid var(--theme-border-color);'
        'border-radius:20px;padding:20px 22px;margin-bottom:26px;box-shadow:0 4px 0 rgba(0,0,0,0.1);">'
        '<div style="font-size:16px;font-weight:900;color:var(--theme-text-primary);margin-bottom:12px;display:flex;align-items:center;gap:8px;">'
        '<span>🎯</span> QUICK GAME RADAR & SEARCH'
        '</div>',
        unsafe_allow_html=True,
    )

    s_left, s_right = st.columns([4, 1.2])
    with s_left:
        search_q = st.text_input(
            "Search radar games",
            placeholder="Type a game title (e.g. Witcher, Elden Ring, Hades) or store name... 🎯",
            label_visibility="collapsed",
            key="dash_quick_search_input",
        )
    with s_right:
        search_btn = st.button("Search Radar 🔎", type="primary", use_container_width=True, key="dash_quick_search_btn")

    st.markdown('</div>', unsafe_allow_html=True)

    # Handle quick search redirection
    if search_btn and search_q.strip():
        # Match against tracked games
        matched_games = [g for g in games_list if search_q.strip().lower() in str(g.get("name") or g.get("title") or "").lower()]
        if not matched_games:
            st.info(f"'{search_q.strip()}' is not in your tracked watchlist yet.")
            col_s1, col_s2 = st.columns([1, 1.5])
            with col_s2:
                if st.button(f"🔍 Search Across Steam & Epic for '{search_q.strip()}' →", type="primary", use_container_width=True):
                    st.session_state.main_search_query_input = search_q.strip()
                    st.session_state.main_sidebar_nav_choice = "🔍 Search Games"
                    st.rerun()

    # ── GAMES CURRENTLY ON SALE ──────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin:28px 0 14px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:24px;">🔥</span>'
        '<div>'
        f'<div style="font-size:19px;font-weight:900;color:var(--theme-text-primary);letter-spacing:-0.02em;">GAMES CURRENTLY ON SALE ({on_sale_count})</div>'
        '<div style="font-size:12px;color:var(--theme-text-muted);">Hot discounts spotted across your tracked titles</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if on_sale_games:
        # Sort by discount percent descending
        sorted_sales = sorted(on_sale_games, key=lambda x: float(x.get("discount_percent") or 0), reverse=True)
        sale_display = sorted_sales[:6]

        cols_per_row = 3
        for i in range(0, len(sale_display), cols_per_row):
            row_items = sale_display[i : i + cols_per_row]
            row_cols = st.columns(cols_per_row)
            for idx, g in enumerate(row_items):
                with row_cols[idx]:
                    title_str = g.get("name") or g.get("title") or "Game"
                    gid = g.get("id", str(idx))
                    owned_this = any(p.get("title", "").lower() == title_str.lower() for p in purchased_list)

                    st.markdown(_game_card_html(g, currency=currency, is_owned=owned_this), unsafe_allow_html=True)
                    
                    # Quick action buttons
                    b1, b2 = st.columns([1.5, 1])
                    with b1:
                        if g.get("url"):
                            st.link_button("🔗 View Store", g["url"], use_container_width=True)
                    with b2:
                        if st.button("🔄 Refresh", key=f"dash_ref_{gid}", use_container_width=True):
                            with st.spinner("Checking price..."):
                                try:
                                    det = fetch_game_details(g.get("store", "steam"), g.get("url", ""))
                                    apply_game_update(g, det)
                                    if gh:
                                        gh.save_games(games_list, f"Refresh price for {title_str}")
                                    st.session_state.games = games_list
                                    st.success(f"Updated {title_str}!")
                                    st.rerun()
                                except Exception:
                                    st.error("Refresh failed.")
    else:
        st.markdown(
            '<div class="empty-box">'
            '<div class="empty-icon">🛡️</div>'
            '<div class="empty-title">The merchants are holding the line!</div>'
            '<div class="empty-sub">No active price drops right now on your tracked titles. Radar is scanning Steam, Epic Games, and GOG 24/7.</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── BEST DEALS SPOTLIGHT ─────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin:32px 0 14px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:24px;">🏆</span>'
        '<div>'
        '<div style="font-size:19px;font-weight:900;color:var(--theme-text-primary);letter-spacing:-0.02em;">BEST DEALS SPOTLIGHT</div>'
        '<div style="font-size:12px;color:var(--theme-text-muted);">The deepest discounts and all-time lowest price alerts</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Best deals: games with discount >= 50% or price == lowest_price
    deals_pool = []
    for g in games_list:
        cur_p = g.get("current_price")
        low_p = g.get("lowest_price")
        disc = float(g.get("discount_percent") or 0)
        is_hist_low = (cur_p is not None and low_p is not None and float(cur_p) <= float(low_p))
        if disc >= 50 or is_hist_low:
            deals_pool.append((g, disc, is_hist_low))

    deals_pool.sort(key=lambda x: (x[2], x[1]), reverse=True)
    best_deals = [x[0] for x in deals_pool[:3]]

    if best_deals:
        b_cols = st.columns(len(best_deals))
        for idx, g in enumerate(best_deals):
            with b_cols[idx]:
                title_str = g.get("name") or g.get("title") or "Game"
                owned_this = any(p.get("title", "").lower() == title_str.lower() for p in purchased_list)
                st.markdown(_game_card_html(g, currency=currency, is_owned=owned_this), unsafe_allow_html=True)
                if g.get("url"):
                    st.link_button("Claim Deal →", g["url"], type="primary", use_container_width=True, key=f"best_deal_btn_{idx}")
    else:
        st.markdown(
            '<div class="empty-box">'
            '<div class="empty-icon">💎</div>'
            '<div class="empty-title">Deep discounts are being scouted</div>'
            '<div class="empty-sub">When games hit 50%+ discounts or historical lowest prices, they\'ll appear in this spotlight!</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── RECENTLY PURCHASED GAMES (Recent Loot Trophies) ──────────────
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin:32px 0 14px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:24px;">📚</span>'
        '<div>'
        f'<div style="font-size:19px;font-weight:900;color:var(--theme-text-primary);letter-spacing:-0.02em;">RECENT LOOT VAULT ({owned_count} TROPHIES)</div>'
        '<div style="font-size:12px;color:var(--theme-text-muted);">Games added to your personal trophy collection</div>'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if purchased_list:
        recent_purchased = sorted(purchased_list, key=lambda x: x.get("purchase_date") or "", reverse=True)[:3]
        p_cols = st.columns(len(recent_purchased))
        for idx, item in enumerate(recent_purchased):
            with p_cols[idx]:
                p_title = _safe(item.get("title", "Game"))
                p_store = _store_badge(item.get("store", ""))
                p_date = _safe(item.get("purchase_date", "Recently"))
                p_price = _money(item.get("purchase_price"), currency) if item.get("purchase_price") is not None else "Price logged"
                p_cover = item.get("cover") or ""

                img_html = f'<img src="{_safe(p_cover)}" alt="{p_title}" class="card-art-img">' if p_cover else '<div style="font-size:32px;text-align:center;padding:20px;">🏆</div>'

                st.markdown(
                    f'<div class="game-card-wrapper">'
                    f'<div class="card-art-wrap" style="margin-bottom:10px;">{img_html}</div>'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
                    f'<div class="card-game-title" style="font-size:15px;">{p_title}</div>'
                    f'<span class="owned-badge">🏆 OWNED</span>'
                    f'</div>'
                    f'<div style="font-size:12px;color:var(--theme-text-muted);margin-bottom:4px;">{p_store} · Purchased {p_date}</div>'
                    f'<div style="font-size:16px;font-weight:900;color:var(--theme-text-primary);font-family:\'Fredoka\',sans-serif;">{p_price}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        col_v1, col_v2, col_v3 = st.columns([1, 1.5, 1])
        with col_v2:
            if st.button("Browse Entire Loot Vault →", type="secondary", use_container_width=True, key="dash_open_library"):
                st.session_state.main_sidebar_nav_choice = "📚 My Library"
                st.rerun()
    else:
        st.markdown(
            '<div class="empty-box">'
            '<div class="empty-icon">📚</div>'
            '<div class="empty-title">Your Loot Vault is waiting!</div>'
            '<div class="empty-sub">When you buy a game, mark it as purchased to track your personal collection, total spending, and trophies!</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    last_auto = stats_dict.get("last_automatic_refresh")
    next_auto = stats_dict.get("next_scheduled_refresh")
    footer_bits = []
    if stats_dict.get("last_synced"):
        footer_bits.append(f"Radar last synced: {_safe(stats_dict['last_synced'])}")
    if last_auto:
        footer_bits.append(f"Last automatic refresh: {_safe(last_auto)}")
    if next_auto:
        footer_bits.append(f"Next scheduled refresh: {_safe(next_auto)}")

    if footer_bits:
        st.markdown(
            f'<div style="text-align:center;font-size:12px;color:var(--theme-text-muted);margin-top:28px;">'
            f'{" &nbsp;•&nbsp; ".join(footer_bits)}'
            f'</div>',
            unsafe_allow_html=True,
        )
