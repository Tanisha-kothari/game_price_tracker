import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

PERSONALITY_LEVELS = ["Subtle", "Playful", "Chaotic"]

THEMES: dict[str, dict[str, Any]] = {
    "midnight_gamer": {
        "id": "midnight_gamer",
        "name": "Midnight Gamer",
        "icon": "🌙",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #1e293b 0%, #334155 50%, #0f172a 100%)",
        "bg_sidebar": "#162032",
        "bg_card": "linear-gradient(145deg, #27354a 0%, #32445e 100%)",
        "bg_card_elevated": "#405575",
        "bg_input": "#1c283c",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "border_color": "#3b4f73",
        "border_subtle": "#273752",
        "border_hover": "#818cf8",
        "accent_primary": "#818cf8",
        "accent_secondary": "#38bdf8",
        "accent_bg": "rgba(129, 140, 248, 0.22)",
        "sale_color": "#4ade80",
        "sale_bg": "rgba(74, 222, 128, 0.22)",
        "warning_color": "#ef4444",
        "btn_primary_bg": "#6366f1",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#32445e",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(15, 23, 42, 0.5)",
        "shadow_hover": "0 12px 32px rgba(129, 140, 248, 0.35)",
        "card_radius": "12px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "🏆 BEST DEAL",
        "tracked_label": "TRACKED",
        "buy_button_prefix": "VIEW GAME",
    },
    "sakura_dream": {
        "id": "sakura_dream",
        "name": "Sakura Dream",
        "icon": "🌸",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #fff0f5 0%, #fdf7fa 50%, #f7e8f0 100%)",
        "bg_sidebar": "#faebf3",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#fce4ec",
        "bg_input": "#ffffff",
        "text_primary": "#2d1732",
        "text_secondary": "#5c3d64",
        "text_muted": "#886791",
        "border_color": "#f8c8dc",
        "border_subtle": "#fce4ec",
        "border_hover": "#ff85a2",
        "accent_primary": "#ff85a2",
        "accent_secondary": "#c084fc",
        "accent_bg": "rgba(255, 133, 162, 0.15)",
        "sale_color": "#e04870",
        "sale_bg": "rgba(224, 72, 112, 0.12)",
        "warning_color": "#ff4d6d",
        "btn_primary_bg": "#ff85a2",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#fce4ec",
        "btn_secondary_text": "#2d1732",
        "shadow_card": "0 6px 20px rgba(255, 133, 162, 0.15)",
        "shadow_hover": "0 10px 28px rgba(255, 133, 162, 0.3)",
        "card_radius": "16px",
        "button_radius": "10px",
        "input_radius": "10px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "sakura",
        "best_deal_label": "🌸 SAKURA OFFER",
        "tracked_label": "GARDEN",
        "buy_button_prefix": "CLAIM OFFER",
    },
    "ua_night": {
        "id": "ua_night",
        "name": "U.A. Night",
        "icon": "⚔️",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #0b132b 0%, #1c2541 60%, #070d1e 100%)",
        "bg_sidebar": "#091024",
        "bg_card": "linear-gradient(145deg, #1c2541 0%, #29375e 100%)",
        "bg_card_elevated": "#3a4b7c",
        "bg_input": "#141c33",
        "text_primary": "#f8fafc",
        "text_secondary": "#d5e4f5",
        "text_muted": "#a6c2e2",
        "border_color": "#3a4b7c",
        "border_subtle": "#1d2b4e",
        "border_hover": "#ff3b4b",
        "accent_primary": "#ff3b4b",
        "accent_secondary": "#00f5d4",
        "accent_bg": "rgba(255, 59, 75, 0.25)",
        "sale_color": "#00f5d4",
        "sale_bg": "rgba(0, 245, 212, 0.25)",
        "warning_color": "#ffb703",
        "btn_primary_bg": "#ff3b4b",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#29375e",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(11, 19, 43, 0.5)",
        "shadow_hover": "0 12px 32px rgba(255, 59, 75, 0.4)",
        "card_radius": "8px",
        "button_radius": "6px",
        "input_radius": "6px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "💥 PLUS ULTRA DEAL",
        "tracked_label": "HERO DOSSIER",
        "buy_button_prefix": "PLUS ULTRA → VIEW",
    },
    "cosmic_romance": {
        "id": "cosmic_romance",
        "name": "Cosmic Romance",
        "icon": "🌌",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #0d0b1d 0%, #1a1636 60%, #090714 100%)",
        "bg_sidebar": "#0b0918",
        "bg_card": "linear-gradient(145deg, #231d45 0%, #2f275c 100%)",
        "bg_card_elevated": "#3f347a",
        "bg_input": "#191433",
        "text_primary": "#f8fafc",
        "text_secondary": "#e0d6f7",
        "text_muted": "#bdaee6",
        "border_color": "#473b88",
        "border_subtle": "#2c2457",
        "border_hover": "#00e5ff",
        "accent_primary": "#00e5ff",
        "accent_secondary": "#a855f7",
        "accent_bg": "rgba(0, 229, 255, 0.25)",
        "sale_color": "#a855f7",
        "sale_bg": "rgba(168, 85, 247, 0.25)",
        "warning_color": "#ff4081",
        "btn_primary_bg": "#a855f7",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#2f275c",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(13, 11, 29, 0.6)",
        "shadow_hover": "0 12px 32px rgba(0, 229, 255, 0.4)",
        "card_radius": "14px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "stars",
        "best_deal_label": "✦ BEST OFFER",
        "tracked_label": "SIGNAL DECK",
        "buy_button_prefix": "✦ ENGAGE LINK",
    },
    "wuxia_ink": {
        "id": "wuxia_ink",
        "name": "Wuxia / Ink & Jade",
        "icon": "🪷",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f5efe6 0%, #f9f6f0 50%, #eee5d8 100%)",
        "bg_sidebar": "#eae2d5",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f3ece0",
        "bg_input": "#ffffff",
        "text_primary": "#1c1917",
        "text_secondary": "#44403c",
        "text_muted": "#78716c",
        "border_color": "#d6cebf",
        "border_subtle": "#e7e0d3",
        "border_hover": "#00a86b",
        "accent_primary": "#00a86b",
        "accent_secondary": "#c59b27",
        "accent_bg": "rgba(0, 168, 107, 0.12)",
        "sale_color": "#00a86b",
        "sale_bg": "rgba(0, 168, 107, 0.12)",
        "warning_color": "#e11d48",
        "btn_primary_bg": "#00a86b",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#f3ece0",
        "btn_secondary_text": "#1c1917",
        "shadow_card": "0 6px 20px rgba(28, 25, 23, 0.06)",
        "shadow_hover": "0 10px 28px rgba(0, 168, 107, 0.2)",
        "card_radius": "8px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Georgia', serif",
        "particle_type": "none",
        "best_deal_label": "江湖 · BEST DEAL",
        "tracked_label": "江湖 · TRACKED",
        "buy_button_prefix": "ENTER STORE",
    },
    "arcane_library": {
        "id": "arcane_library",
        "name": "Wizarding / Arcane Library",
        "icon": "📚",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f7f1e3 0%, #fbf8f1 50%, #f0e6d2 100%)",
        "bg_sidebar": "#ebe1cd",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f5ebd7",
        "bg_input": "#ffffff",
        "text_primary": "#2b1810",
        "text_secondary": "#54382b",
        "text_muted": "#856251",
        "border_color": "#dfd2bc",
        "border_subtle": "#ede3d1",
        "border_hover": "#9f1239",
        "accent_primary": "#9f1239",
        "accent_secondary": "#c59b27",
        "accent_bg": "rgba(159, 18, 57, 0.12)",
        "sale_color": "#15803d",
        "sale_bg": "rgba(21, 128, 61, 0.12)",
        "warning_color": "#f43f5e",
        "btn_primary_bg": "#9f1239",
        "btn_primary_text": "#faf3e0",
        "btn_secondary_bg": "#f5ebd7",
        "btn_secondary_text": "#2b1810",
        "shadow_card": "0 6px 20px rgba(43, 24, 16, 0.08)",
        "shadow_hover": "0 10px 28px rgba(159, 18, 57, 0.2)",
        "card_radius": "10px",
        "button_radius": "6px",
        "input_radius": "6px",
        "font_family": "'Georgia', serif",
        "particle_type": "embers",
        "best_deal_label": "✨ ARCANE BARGAIN",
        "tracked_label": "GRIMOIRE",
        "buy_button_prefix": "INSPECT SPELL",
    },
    "cozy_forest": {
        "id": "cozy_forest",
        "name": "Cozy Forest",
        "icon": "🌿",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f4f7f2 0%, #f9faf7 50%, #e9f0e6 100%)",
        "bg_sidebar": "#e3ede0",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#eaf2e8",
        "bg_input": "#ffffff",
        "text_primary": "#1c2e24",
        "text_secondary": "#3e5749",
        "text_muted": "#688574",
        "border_color": "#cddcd2",
        "border_subtle": "#dfebd4",
        "border_hover": "#52796f",
        "accent_primary": "#52796f",
        "accent_secondary": "#68904d",
        "accent_bg": "rgba(82, 121, 111, 0.12)",
        "sale_color": "#407a52",
        "sale_bg": "rgba(64, 122, 82, 0.12)",
        "warning_color": "#d97706",
        "btn_primary_bg": "#52796f",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#eaf2e8",
        "btn_secondary_text": "#1c2e24",
        "shadow_card": "0 6px 20px rgba(28, 46, 36, 0.06)",
        "shadow_hover": "0 10px 28px rgba(82, 121, 111, 0.2)",
        "card_radius": "14px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "leaves",
        "best_deal_label": "🍃 COZY BARGAIN",
        "tracked_label": "SANCTUARY",
        "buy_button_prefix": "VISIT HAVEN",
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "icon": "🕶️",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #08070d 0%, #13111c 60%, #050408 100%)",
        "bg_sidebar": "#07060a",
        "bg_card": "linear-gradient(145deg, #1a1726 0%, #252136 100%)",
        "bg_card_elevated": "#342e4c",
        "bg_input": "#12101c",
        "text_primary": "#f0f6fc",
        "text_secondary": "#dcd2f8",
        "text_muted": "#b1a0e3",
        "border_color": "#433b63",
        "border_subtle": "#252038",
        "border_hover": "#00f0ff",
        "accent_primary": "#00f0ff",
        "accent_secondary": "#ff007f",
        "accent_bg": "rgba(0, 240, 255, 0.25)",
        "sale_color": "#ff007f",
        "sale_bg": "rgba(255, 0, 127, 0.25)",
        "warning_color": "#ff9900",
        "btn_primary_bg": "#00b4d8",
        "btn_primary_text": "#050408",
        "btn_secondary_bg": "#252136",
        "btn_secondary_text": "#f0f6fc",
        "shadow_card": "0 6px 20px rgba(8, 7, 13, 0.7)",
        "shadow_hover": "0 0 24px rgba(0, 240, 255, 0.45)",
        "card_radius": "2px",
        "button_radius": "2px",
        "input_radius": "2px",
        "font_family": "'Consolas', 'Courier New', monospace",
        "particle_type": "none",
        "best_deal_label": "⚡ SIGNAL DETECTED",
        "tracked_label": "NET GRID",
        "buy_button_prefix": "EXECUTE PROTOCOL",
    },
    "gothic_academia": {
        "id": "gothic_academia",
        "name": "Gothic / Dark Academia",
        "icon": "🕯️",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #0f0d10 0%, #1c181e 60%, #0a080b 100%)",
        "bg_sidebar": "#0c0a0d",
        "bg_card": "linear-gradient(145deg, #27212b 0%, #342d3a 100%)",
        "bg_card_elevated": "#483f50",
        "bg_input": "#1e1a22",
        "text_primary": "#f7f0e6",
        "text_secondary": "#ebdfcf",
        "text_muted": "#cca99a",
        "border_color": "#4e4354",
        "border_subtle": "#2c2630",
        "border_hover": "#d4af37",
        "accent_primary": "#d4af37",
        "accent_secondary": "#800f2f",
        "accent_bg": "rgba(212, 175, 55, 0.25)",
        "sale_color": "#d4af37",
        "sale_bg": "rgba(212, 175, 55, 0.25)",
        "warning_color": "#800f2f",
        "btn_primary_bg": "#800f2f",
        "btn_primary_text": "#f7f0e6",
        "btn_secondary_bg": "#342d3a",
        "btn_secondary_text": "#f7f0e6",
        "shadow_card": "0 8px 24px rgba(15, 13, 16, 0.7)",
        "shadow_hover": "0 12px 32px rgba(212, 175, 55, 0.35)",
        "card_radius": "6px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Georgia', serif",
        "particle_type": "none",
        "best_deal_label": "📜 ARCHIVE OFFER",
        "tracked_label": "ARCHIVE",
        "buy_button_prefix": "CONSULT ARCHIVE",
    },
    "pastel_gamer": {
        "id": "pastel_gamer",
        "name": "Pastel Gamer",
        "icon": "☁️",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f5f0ff 0%, #faf5ff 50%, #eee0ff 100%)",
        "bg_sidebar": "#efe2fe",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f3e8ff",
        "bg_input": "#ffffff",
        "text_primary": "#3b1d54",
        "text_secondary": "#664086",
        "text_muted": "#9370b8",
        "border_color": "#e9d5ff",
        "border_subtle": "#f3e8ff",
        "border_hover": "#c084fc",
        "accent_primary": "#c084fc",
        "accent_secondary": "#38bdf8",
        "accent_bg": "rgba(192, 132, 252, 0.15)",
        "sale_color": "#0284c7",
        "sale_bg": "rgba(2, 132, 199, 0.12)",
        "warning_color": "#f472b6",
        "btn_primary_bg": "#c084fc",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#f3e8ff",
        "btn_secondary_text": "#3b1d54",
        "shadow_card": "0 6px 20px rgba(192, 132, 252, 0.12)",
        "shadow_hover": "0 10px 28px rgba(192, 132, 252, 0.3)",
        "card_radius": "16px",
        "button_radius": "10px",
        "input_radius": "10px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "☁️ COMFY OFFER",
        "tracked_label": "COZY CORNER",
        "buy_button_prefix": "TAKE A LOOK",
    },
    "retro_arcade": {
        "id": "retro_arcade",
        "name": "Retro Arcade",
        "icon": "🕹️",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #180b2d 0%, #261245 60%, #100720 100%)",
        "bg_sidebar": "#130824",
        "bg_card": "linear-gradient(145deg, #301757 0%, #3c1d6d 100%)",
        "bg_card_elevated": "#522895",
        "bg_input": "#240f42",
        "text_primary": "#f9fafb",
        "text_secondary": "#e4daf7",
        "text_muted": "#baa4ed",
        "border_color": "#532797",
        "border_subtle": "#31165c",
        "border_hover": "#2dd4bf",
        "accent_primary": "#2dd4bf",
        "accent_secondary": "#ff923c",
        "accent_bg": "rgba(45, 212, 191, 0.25)",
        "sale_color": "#ff923c",
        "sale_bg": "rgba(255, 146, 60, 0.25)",
        "warning_color": "#f72585",
        "btn_primary_bg": "#2dd4bf",
        "btn_primary_text": "#100720",
        "btn_secondary_bg": "#3c1d6d",
        "btn_secondary_text": "#f9fafb",
        "shadow_card": "0 6px 20px rgba(24, 11, 45, 0.6)",
        "shadow_hover": "0 8px 28px rgba(45, 212, 191, 0.4)",
        "card_radius": "6px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Courier New', monospace",
        "particle_type": "none",
        "best_deal_label": "🕹️ HIGH SCORE DEAL",
        "tracked_label": "ARCADE CABINET",
        "buy_button_prefix": "INSERT COIN → BUY",
    },
    "alchemist": {
        "id": "alchemist",
        "name": "Alchemist Workshop",
        "icon": "⚗️",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f6f0e6 0%, #faf6f0 50%, #ece2d0 100%)",
        "bg_sidebar": "#e8dccb",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f4e8d7",
        "bg_input": "#ffffff",
        "text_primary": "#362215",
        "text_secondary": "#614431",
        "text_muted": "#8e6f59",
        "border_color": "#dfcdb5",
        "border_subtle": "#ede0cf",
        "border_hover": "#d97706",
        "accent_primary": "#d97706",
        "accent_secondary": "#10b981",
        "accent_bg": "rgba(217, 119, 6, 0.12)",
        "sale_color": "#059669",
        "sale_bg": "rgba(5, 150, 105, 0.12)",
        "warning_color": "#ef4444",
        "btn_primary_bg": "#d97706",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#f4e8d7",
        "btn_secondary_text": "#362215",
        "shadow_card": "0 6px 20px rgba(54, 34, 21, 0.08)",
        "shadow_hover": "0 10px 28px rgba(217, 119, 6, 0.2)",
        "card_radius": "10px",
        "button_radius": "6px",
        "input_radius": "6px",
        "font_family": "'Georgia', serif",
        "particle_type": "embers",
        "best_deal_label": "🧪 TRANSMUTED DEAL",
        "tracked_label": "LABORATORY",
        "buy_button_prefix": "EXAMINE REAGENT",
    },
    "celestial": {
        "id": "celestial",
        "name": "Celestial Constellation",
        "icon": "✨",
        "mode": "light",
        "bg_body": "linear-gradient(135deg, #f0f4f8 0%, #f8fafc 50%, #e2ecf5 100%)",
        "bg_sidebar": "#dbe5f0",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#e4eef7",
        "bg_input": "#ffffff",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "border_color": "#cbd5e1",
        "border_subtle": "#e2e8f0",
        "border_hover": "#6366f1",
        "accent_primary": "#6366f1",
        "accent_secondary": "#0284c7",
        "accent_bg": "rgba(99, 102, 241, 0.12)",
        "sale_color": "#0284c7",
        "sale_bg": "rgba(2, 132, 199, 0.12)",
        "warning_color": "#f43f5e",
        "btn_primary_bg": "#4f46e5",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#e4eef7",
        "btn_secondary_text": "#0f172a",
        "shadow_card": "0 6px 20px rgba(15, 23, 42, 0.06)",
        "shadow_hover": "0 10px 28px rgba(99, 102, 241, 0.2)",
        "card_radius": "14px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "stars",
        "best_deal_label": "🌌 CELESTIAL ALIGNMENT",
        "tracked_label": "OBSERVATORY",
        "buy_button_prefix": "NAVIGATE TO STORE",
    },
    "icebound": {
        "id": "icebound",
        "name": "Icebound Realm",
        "icon": "❄️",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #0b1524 0%, #14243b 60%, #070e19 100%)",
        "bg_sidebar": "#08101c",
        "bg_card": "linear-gradient(145deg, #182e4a 0%, #213c61 100%)",
        "bg_card_elevated": "#2d5182",
        "bg_input": "#12243b",
        "text_primary": "#f8fafc",
        "text_secondary": "#daebf9",
        "text_muted": "#a6cdf0",
        "border_color": "#2e5285",
        "border_subtle": "#172d4c",
        "border_hover": "#22d3ee",
        "accent_primary": "#22d3ee",
        "accent_secondary": "#38bdf8",
        "accent_bg": "rgba(34, 211, 238, 0.25)",
        "sale_color": "#22d3ee",
        "sale_bg": "rgba(34, 211, 238, 0.25)",
        "warning_color": "#ef4444",
        "btn_primary_bg": "#0284c7",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#213c61",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(11, 21, 36, 0.5)",
        "shadow_hover": "0 12px 32px rgba(34, 211, 238, 0.4)",
        "card_radius": "10px",
        "button_radius": "6px",
        "input_radius": "6px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "❄️ FROZEN PRICE",
        "tracked_label": "FROST VAULT",
        "buy_button_prefix": "UNFREEZE DEAL",
    },
    "survival_horror": {
        "id": "survival_horror",
        "name": "Survival Horror",
        "icon": "🩸",
        "mode": "dark",
        "bg_body": "linear-gradient(135deg, #14141a 0%, #202029 60%, #0d0d11 100%)",
        "bg_sidebar": "#101015",
        "bg_card": "linear-gradient(145deg, #262630 0%, #323240 100%)",
        "bg_card_elevated": "#464658",
        "bg_input": "#1b1b22",
        "text_primary": "#f4f4f5",
        "text_secondary": "#e3d3d5",
        "text_muted": "#bc9e9e",
        "border_color": "#4a4a5b",
        "border_subtle": "#252530",
        "border_hover": "#f43f5e",
        "accent_primary": "#f43f5e",
        "accent_secondary": "#fb7185",
        "accent_bg": "rgba(244, 63, 94, 0.25)",
        "sale_color": "#f43f5e",
        "sale_bg": "rgba(244, 63, 94, 0.25)",
        "warning_color": "#f59e0b",
        "btn_primary_bg": "#be123c",
        "btn_primary_text": "#f4f4f5",
        "btn_secondary_bg": "#323240",
        "btn_secondary_text": "#f4f4f5",
        "shadow_card": "0 8px 24px rgba(20, 20, 26, 0.6)",
        "shadow_hover": "0 12px 32px rgba(244, 63, 94, 0.4)",
        "card_radius": "6px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "⚠ SLASHED PRICE",
        "tracked_label": "SURVIVAL KIT",
        "buy_button_prefix": "ENTER STORE",
    },
}


def get_theme(theme_id: str) -> dict[str, Any]:
    return THEMES.get(theme_id, THEMES["midnight_gamer"])


def generate_theme_css(theme_id: str) -> str:
    t = get_theme(theme_id)

    # Particle Animations CSS
    particle_css = ""
    if t.get("particle_type") == "sakura":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            .main-view-container::before {
                content: '🌸';
                position: fixed;
                top: -20px;
                right: 15%;
                font-size: 20px;
                opacity: 0.45;
                animation: sakuraFall 12s linear infinite;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes sakuraFall {
                0% { transform: translateY(0) rotate(0deg); opacity: 0.45; }
                100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
            }
        }
        """
    elif t.get("particle_type") == "stars":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            .main-view-container::before {
                content: '✦';
                position: fixed;
                top: 20%;
                right: 10%;
                font-size: 14px;
                color: """ + t["accent_primary"] + """;
                opacity: 0.5;
                animation: starTwinkle 4s ease-in-out infinite alternate;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes starTwinkle {
                0% { opacity: 0.15; transform: scale(0.8); }
                100% { opacity: 0.85; transform: scale(1.3); }
            }
        }
        """
    elif t.get("particle_type") == "embers":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            .main-view-container::before {
                content: '✨';
                position: fixed;
                bottom: 10%;
                left: 12%;
                font-size: 14px;
                opacity: 0.4;
                animation: emberRise 8s ease-in-out infinite;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes emberRise {
                0% { transform: translateY(0); opacity: 0.15; }
                100% { transform: translateY(-80vh); opacity: 0.7; }
            }
        }
        """
    elif t.get("particle_type") == "leaves":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            .main-view-container::before {
                content: '🍃';
                position: fixed;
                top: 10%;
                left: 8%;
                font-size: 16px;
                opacity: 0.4;
                animation: leafSway 10s ease-in-out infinite alternate;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes leafSway {
                0% { transform: translateX(0) rotate(0deg); }
                100% { transform: translateX(80px) rotate(45deg); }
            }
        }
        """

    return f"""
    <style>
    /* ── Global Theme CSS Design System Variables ────────────────── */
    :root {{
        --theme-mode: {t["mode"]};
        --theme-bg-body: {t["bg_body"]};
        --theme-bg-sidebar: {t["bg_sidebar"]};
        --theme-bg-card: {t["bg_card"]};
        --theme-bg-card-elevated: {t["bg_card_elevated"]};
        --theme-bg-input: {t["bg_input"]};
        --theme-text-primary: {t["text_primary"]};
        --theme-text-secondary: {t["text_secondary"]};
        --theme-text-muted: {t["text_muted"]};
        --theme-border-color: {t["border_color"]};
        --theme-border-subtle: {t["border_subtle"]};
        --theme-border-hover: {t["border_hover"]};
        --theme-accent-primary: {t["accent_primary"]};
        --theme-accent-secondary: {t["accent_secondary"]};
        --theme-accent-bg: {t["accent_bg"]};
        --theme-sale: {t["sale_color"]};
        --theme-sale-bg: {t["sale_bg"]};
        --theme-warning: {t["warning_color"]};
        --theme-btn-primary-bg: {t["btn_primary_bg"]};
        --theme-btn-primary-text: {t["btn_primary_text"]};
        --theme-btn-secondary-bg: {t["btn_secondary_bg"]};
        --theme-btn-secondary-text: {t["btn_secondary_text"]};
        --theme-shadow-card: {t["shadow_card"]};
        --theme-shadow-hover: {t["shadow_hover"]};
        --theme-card-radius: {t["card_radius"]};
        --theme-button-radius: {t["button_radius"]};
        --theme-input-radius: {t["input_radius"]};
        --theme-font-family: {t["font_family"]};
    }}

    /* Global App Container */
    .stApp, [data-testid="stAppViewContainer"], .stAppViewContainer, section.main, .main, [data-testid="stMain"], div[data-testid="stAppViewMain"] {{
        background: {t["bg_body"]} !important;
        color: {t["text_primary"]} !important;
        font-family: {t["font_family"]} !important;
        transition: background 0.35s ease-in-out, color 0.35s ease-in-out;
    }}

    .block-container {{
        background: transparent !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"], section[data-testid="stSidebar"] {{
        background: {t["bg_sidebar"]} !important;
        border-right: 1px solid {t["border_color"]} !important;
    }}
    .sidebar-brand-title {{
        color: {t["text_primary"]} !important;
        font-family: {t["font_family"]} !important;
    }}
    .sidebar-brand-subtitle {{
        color: {t["text_muted"]} !important;
    }}
    .sidebar-status-card {{
        background: {t["bg_card"]} !important;
        border: 1px solid {t["border_color"]} !important;
        border-radius: {t["card_radius"]} !important;
    }}

    /* Cards Treatment */
    .game-card-container, .summary-card, .dashboard-metric-box, .search-hero-box {{
        background: {t["bg_card"]} !important;
        border: 1px solid {t["border_color"]} !important;
        border-radius: {t["card_radius"]} !important;
        box-shadow: {t["shadow_card"]} !important;
        transition: transform 0.25s cubic-bezier(0.2, 0, 0.2, 1), border-color 0.25s ease, box-shadow 0.25s ease !important;
    }}

    .game-card-container:hover {{
        transform: translateY(-3px) scale(1.01) !important;
        border-color: {t["border_hover"]} !important;
        box-shadow: {t["shadow_hover"]} !important;
    }}

    /* Text Colors */
    h1, h2, h3, h4, .card-title, .sum-val {{
        color: {t["text_primary"]} !important;
        font-family: {t["font_family"]} !important;
    }}

    p, span, div, label {{
        color: {t["text_secondary"]};
    }}

    .sum-label, .card-sub, .empty-sub {{
        color: {t["text_muted"]} !important;
    }}

    /* Sale Badges */
    .sale-badge {{
        background: {t["sale_bg"]} !important;
        color: {t["sale_color"]} !important;
        border: 1px solid {t["sale_color"]} !important;
        border-radius: 6px !important;
        font-weight: 800 !important;
    }}

    /* Buttons */
    .stButton > button[kind="primary"], .stButton > button[type="primary"] {{
        background: {t["btn_primary_bg"]} !important;
        color: {t["btn_primary_text"]} !important;
        border: none !important;
        border-radius: {t["button_radius"]} !important;
        font-weight: 700 !important;
        transition: transform 0.15s ease, opacity 0.15s ease, box-shadow 0.15s ease !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        opacity: 0.92 !important;
        transform: translateY(-1px) !important;
    }}

    .stButton > button[kind="secondary"], .stButton > button[type="secondary"] {{
        background: {t["btn_secondary_bg"]} !important;
        color: {t["btn_secondary_text"]} !important;
        border: 1px solid {t["border_color"]} !important;
        border-radius: {t["button_radius"]} !important;
        font-weight: 600 !important;
    }}

    /* Inputs & Selectboxes */
    .stTextInput > div > div > input, .stSelectbox > div > div {{
        background: {t["bg_input"]} !important;
        color: {t["text_primary"]} !important;
        border: 1px solid {t["border_color"]} !important;
        border-radius: {t["input_radius"]} !important;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {t["accent_primary"]} !important;
        box-shadow: 0 0 0 2px {t["accent_bg"]} !important;
    }}

    {particle_css}
    </style>
    """


def get_contextual_message(
    event_type: str,
    theme_id: str = "midnight_gamer",
    personality_level: str = "Subtle",
    **kwargs: Any,
) -> str:
    """Generate theme-aware, personality-tailored contextual messages."""
    t = get_theme(theme_id)
    disc = kwargs.get("discount_percent", 0)

    if event_type == "sale" and disc >= 65 and theme_id == "ua_night":
        return f"💥 PLUS ULTRA! {disc}% OFF!"
    if event_type == "sale" and theme_id == "sakura_dream":
        return "🌸 A little price drop appeared..."
    if event_type == "sale" and theme_id == "cosmic_romance":
        return "✦ A new opportunity has appeared."
    if event_type == "sale" and theme_id == "arcane_library":
        return "✨ A fortunate bargain has appeared."
    if event_type == "sale" and theme_id == "cyberpunk":
        return "⚠ PRICE SIGNAL DETECTED"
    if event_type == "sale" and theme_id == "icebound":
        return f"❄️ PRICE FROZEN — {disc}% OFF"
    if event_type == "sale" and theme_id == "survival_horror":
        return "⚠ Something has changed."

    if event_type == "wallet_safe":
        if personality_level == "Chaotic":
            return "Your wallet is safe... for now. Stay vigilant!"
        elif personality_level == "Playful":
            return "No suspiciously good deals detected right now."
        return "✦ Everything is under control."

    if event_type == "sale":
        if disc >= 90:
            if personality_level == "Chaotic":
                return "🚨 WHAT ARE YOU WAITING FOR?! IT'S ALMOST FREE!"
            elif personality_level == "Playful":
                return "🚨 90%+ OFF! Is this a typo?!"
            return "🔥 Extreme Deal Detected!"

        if disc >= 75:
            if personality_level == "Chaotic":
                return "🚨 Okay, NOW we're talking. Instant buy energy."
            elif personality_level == "Playful":
                return "👀 That's looking very tempting!"
            return "🔥 Major discount available."

        if disc >= 50:
            if personality_level == "Chaotic":
                return "🔥 50%+ discount! Half price gaming!"
            elif personality_level == "Playful":
                return "🔥 That's a pretty good deal!"
            return "🔥 Deal detected."

        if personality_level == "Chaotic":
            return "Someone dropped the price!"
        elif personality_level == "Playful":
            return "Price drop spotted!"
        return "Price drop active."

    if event_type == "price_increase":
        if personality_level == "Chaotic":
            return "💀 They raised it! Your wallet has suffered a setback."
        elif personality_level == "Playful":
            return "That price went the wrong direction..."
        return "Price increased."

    if event_type == "refreshing":
        if theme_id == "alchemist":
            return "🧪 Brewing price data..."
        if personality_level == "Chaotic":
            return "🔍 Hunting for bargains across the net..."
        return "Refreshing price data..."

    if event_type == "refresh_complete":
        if theme_id == "alchemist":
            return "✨ The prices have been revealed."
        if personality_level == "Chaotic":
            return "✓ Hunt complete. Target acquired."
        return "✓ Refresh complete."

    if event_type == "empty_tracker":
        if theme_id == "cozy_forest":
            return "🍃 Nothing urgent. Your wishlist is peaceful."
        if theme_id == "gothic_academia":
            return "Your collection awaits."
        if personality_level == "Chaotic":
            return "🎮 It's awfully quiet here... Add a game before your wishlist gathers dust!"
        return "No games tracked yet."

    if event_type == "empty_search":
        if personality_level == "Chaotic":
            return "🔍 Nothing found. Even the internet couldn't find that one."
        return "No search results found."

    return ""
