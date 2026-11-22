import pytest
import themes
from themes import THEMES, get_theme, generate_theme_css, get_email_theme, get_contextual_message
import dashboard_ui
import app


def test_all_15_themes_exist():
    expected_themes = [
        "midnight_gamer", "sakura_dream", "ua_night", "cosmic_romance",
        "wuxia_ink", "arcane_library", "cozy_forest", "cyberpunk",
        "gothic_academia", "pastel_gamer", "retro_arcade", "alchemist",
        "celestial", "icebound", "survival_horror"
    ]
    for tid in expected_themes:
        assert tid in THEMES, f"Missing theme: {tid}"


def test_light_and_dark_mode_backgrounds():
    for tid, t in THEMES.items():
        mode = t.get("mode")
        assert mode in ("light", "dark"), f"Theme {tid} has invalid mode: {mode}"
        text_primary = t.get("text_primary", "")
        bg_card = str(t.get("bg_card", ""))

        if mode == "light":
            # Light themes must have light card and dark text
            assert text_primary.startswith("#"), f"{tid} missing hex text_primary"
            # Light backgrounds should not be dark
            assert "#0" not in bg_card and "#1" not in bg_card and "#2" not in bg_card, f"Light theme {tid} has dark card: {bg_card}"
        else:
            # Dark themes must have light text and dark background
            assert text_primary.startswith("#"), f"{tid} missing hex text_primary"
            # Dark text should be bright (#f, #e, #d, #c)
            assert any(text_primary.lower().startswith(p) for p in ("#f", "#e", "#d", "#c")), f"Dark theme {tid} text not light: {text_primary}"


def test_contrast_ratios_across_themes():
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c*2 for c in hex_str])
        if len(hex_str) >= 6:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return (128, 128, 128)

    def luminance(rgb):
        vals = [x / 255.0 for x in rgb]
        lum = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
        return 0.2126 * lum[0] + 0.7152 * lum[1] + 0.0722 * lum[2]

    def contrast_ratio(c1, c2):
        l1 = luminance(hex_to_rgb(c1))
        l2 = luminance(hex_to_rgb(c2))
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    for tid, t in THEMES.items():
        text = t.get("text_primary", "#ffffff")
        card = t.get("bg_card")
        if "linear" in str(card):
            card = t.get("bg_card_elevated") or t.get("bg_sidebar")
        btn_bg = t.get("btn_primary_bg", "#6366f1")
        btn_text = t.get("btn_primary_text", "#ffffff")

        cr_text = contrast_ratio(text, card)
        cr_btn = contrast_ratio(btn_text, btn_bg)

        # Card text must be high contrast (at least 5.0)
        assert cr_text >= 5.0, f"Theme {tid} text contrast too low: {cr_text:.2f}"
        # Primary button must have good readability
        assert cr_btn >= 3.5, f"Theme {tid} button contrast too low: {cr_btn:.2f}"


def test_generate_theme_css_all_themes():
    for tid in THEMES:
        css = generate_theme_css(tid)
        assert "<style>" in css
        assert "</style>" in css
        assert ":root" in css
        assert "--theme-bg-body:" in css
        assert "--theme-text-primary:" in css
        assert "--theme-btn-primary-bg:" in css
        assert "--theme-border-color:" in css
        assert "game-card-wrapper" in css
        assert "lobby-hero" in css
        assert "stat-pod" in css
        assert "Fredoka" in css
        # Check that no hardcoded #ffffff or #1a0a3d overrides the entire app
        assert ".stApp, [data-testid=\"stAppViewContainer\"" in css


def test_email_themes_remain_separate():
    for eid, eth in themes.EMAIL_THEMES.items():
        assert "id" in eth
        assert "name" in eth
        assert "bg_body" in eth
        assert "text_primary" in eth

    eth_sakura = get_email_theme("Sakura Dream")
    assert eth_sakura["mode"] == "light"
    eth_midnight = get_email_theme("Midnight Gamer")
    assert eth_midnight["mode"] == "dark"


def test_contextual_messages():
    for tid in THEMES:
        msg_sale = get_contextual_message("sale", theme_id=tid, personality_level="Playful", discount_percent=75)
        assert isinstance(msg_sale, str)
        msg_safe = get_contextual_message("wallet_safe", theme_id=tid, personality_level="Playful")
        assert isinstance(msg_safe, str)


def test_dashboard_ui_helpers_and_card():
    sample_game = {
        "id": "steam_12345",
        "name": "Hades II",
        "store": "steam",
        "current_price": 999.0,
        "original_price": 1499.0,
        "discount_percent": 33,
        "lowest_price": 899.0,
        "target_price": 1000.0,
        "is_on_sale": True,
        "url": "https://store.steampowered.com/app/1145350",
        "cover_image": "https://cdn.akamai.steamstatic.com/cover.jpg",
    }
    card_html = dashboard_ui._game_card_html(sample_game, currency="₹", is_owned=False)
    assert "Hades II" in card_html
    assert "Steam" in card_html
    assert "₹999" in card_html
    assert "TARGET REACHED" in card_html
    assert "game-card-wrapper" in card_html
    assert "disc-tag" in card_html

    # Test owned game badge
    owned_card_html = dashboard_ui._game_card_html(sample_game, currency="₹", is_owned=True)
    assert "IN LIBRARY" in owned_card_html


def test_app_views_and_gamification():
    # Verify all major view handlers exist
    assert hasattr(app, "render_dashboard_view")
    assert hasattr(app, "render_search_view")
    assert hasattr(app, "render_tracked_games_view")
    assert hasattr(app, "render_my_library_view")
    assert hasattr(app, "render_history_view")
    assert hasattr(app, "render_smart_calculator")
    assert hasattr(app, "render_deals_view")
    assert hasattr(app, "render_reports_view")
    assert hasattr(app, "render_settings_view")
    assert hasattr(app, "render_store_tag")
    assert hasattr(app, "render_game_card")

    # Verify store tags have playful styling
    steam_tag = app.render_store_tag("steam")
    assert "store-tag steam" in steam_tag
    epic_tag = app.render_store_tag("epic")
    assert "store-tag epic" in epic_tag
    gog_tag = app.render_store_tag("gog")
    assert "store-tag gog" in gog_tag
