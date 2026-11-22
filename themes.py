import logging
import random
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
        "btn_primary_bg": "#c2185b",
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
        "btn_primary_bg": "#047857",
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
        "btn_primary_bg": "#9333ea",
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
        "btn_primary_bg": "#b45309",
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


# Sample / reference dashboard styling tokens
DASHBOARD_STYLE = {
    "background": "#F7F5EF",
    "surface": "#FFFEFA",
    "surface_secondary": "#E9EEE6",
    "text": "#172B25",
    "text_muted": "#68766E",
    "primary": "#1E5B45",
    "primary_hover": "#174735",
    "accent": "#FF7A45",
    "highlight": "#F4C95D",
    "border": "#DFE5DB",
    "card_radius": "22px",
    "button_radius": "14px",
    "shadow": "0 12px 32px rgba(27, 54, 42, 0.07)",
}


def get_theme(theme_id: str) -> dict[str, Any]:
    return THEMES.get(theme_id, THEMES["midnight_gamer"])


def get_dashboard_tokens(theme: dict[str, Any]) -> dict[str, str]:
    """Extract or compute dashboard design tokens for a given theme dict with sensible fallbacks."""
    return {
        "background": theme.get("background") or theme.get("bg_body") or "#0f172a",
        "surface": theme.get("surface") or theme.get("bg_card") or "#1e293b",
        "surface_secondary": theme.get("surface_secondary") or theme.get("bg_card_elevated") or theme.get("bg_sidebar") or "#334155",
        "text": theme.get("text") or theme.get("text_primary") or "#f8fafc",
        "text_muted": theme.get("text_muted") or "#94a3b8",
        "primary": theme.get("primary") or theme.get("btn_primary_bg") or theme.get("accent_primary") or "#6366f1",
        "primary_hover": theme.get("primary_hover") or theme.get("border_hover") or theme.get("accent_secondary") or "#4f46e5",
        "accent": theme.get("accent") or theme.get("accent_primary") or theme.get("sale_color") or "#818cf8",
        "highlight": theme.get("highlight") or theme.get("warning_color") or theme.get("sale_color") or "#f4c95d",
        "border": theme.get("border") or theme.get("border_color") or "#3b4f73",
        "card_radius": theme.get("card_radius") or "12px",
        "button_radius": theme.get("button_radius") or "8px",
        "shadow": theme.get("shadow") or theme.get("shadow_card") or "0 8px 24px rgba(15, 23, 42, 0.5)",
    }


def generate_dashboard_css(
    theme: dict[str, Any],
    particle_css: str = "",
) -> str:
    """Expose one theme's real tokens and paint the entire Streamlit app with an original playful gaming identity."""
    t = theme
    font_family = t.get("font_family") or "'Fredoka', 'Quicksand', 'Inter', -apple-system, sans-serif"
    mode = t.get("mode") or "dark"

    def token(key: str, fallback: str) -> str:
        value = t.get(key)
        return str(value) if value not in (None, "") else fallback

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Quicksand:wght@500;600;700&family=Inter:wght@400;500;600;700;800;900&display=swap');

    :root {{
        --theme-mode: {mode};
        --theme-bg-body: {token("bg_body", "#0f172a")};
        --theme-bg-sidebar: {token("bg_sidebar", "#162032")};
        --theme-bg-card: {token("bg_card", "#27354a")};
        --theme-bg-card-elevated: {token("bg_card_elevated", "#405575")};
        --theme-bg-input: {token("bg_input", "#1c283c")};
        --theme-text-primary: {token("text_primary", "#f8fafc")};
        --theme-text-secondary: {token("text_secondary", "#cbd5e1")};
        --theme-text-muted: {token("text_muted", "#94a3b8")};
        --theme-border-color: {token("border_color", "#3b4f73")};
        --theme-border-subtle: {token("border_subtle", "#273752")};
        --theme-border-hover: {token("border_hover", "#818cf8")};
        --theme-accent-primary: {token("accent_primary", "#818cf8")};
        --theme-accent-secondary: {token("accent_secondary", "#38bdf8")};
        --theme-accent-bg: {token("accent_bg", "rgba(129, 140, 248, 0.22)")};
        --theme-sale: {token("sale_color", "#4ade80")};
        --theme-sale-bg: {token("sale_bg", "rgba(74, 222, 128, 0.22)")};
        --theme-warning: {token("warning_color", "#ef4444")};
        --theme-btn-primary-bg: {token("btn_primary_bg", "#6366f1")};
        --theme-btn-primary-text: {token("btn_primary_text", "#ffffff")};
        --theme-btn-secondary-bg: {token("btn_secondary_bg", "#32445e")};
        --theme-btn-secondary-text: {token("btn_secondary_text", "#f8fafc")};
        --theme-shadow-card: {token("shadow_card", "0 8px 24px rgba(15, 23, 42, 0.5)")};
        --theme-shadow-hover: {token("shadow_hover", "0 12px 32px rgba(129, 140, 248, 0.35)")};
        --theme-card-radius: {token("card_radius", "20px")};
        --theme-button-radius: {token("button_radius", "14px")};
        --theme-input-radius: {token("input_radius", "14px")};
        --theme-font-family: {font_family};

        --dashboard-bg: var(--theme-bg-body);
        --dashboard-surface: var(--theme-bg-card);
        --dashboard-surface-secondary: var(--theme-bg-card-elevated);
        --dashboard-text: var(--theme-text-primary);
        --dashboard-muted: var(--theme-text-muted);
        --dashboard-primary: var(--theme-btn-primary-bg);
        --dashboard-primary-hover: var(--theme-border-hover);
        --dashboard-accent: var(--theme-accent-primary);
        --dashboard-highlight: var(--theme-sale);
        --dashboard-border: var(--theme-border-color);
        --dashboard-card-radius: var(--theme-card-radius);
        --dashboard-button-radius: var(--theme-button-radius);
        --dashboard-shadow: var(--theme-shadow-card);
    }}

    /* Global App Container */
    html, body, .stApp {{
        color-scheme: {mode};
        font-family: var(--theme-font-family) !important;
    }}

    .stApp, [data-testid="stAppViewContainer"], .stAppViewContainer, section.main, .main, [data-testid="stMain"], div[data-testid="stAppViewMain"] {{
        background: var(--theme-bg-body) !important;
        color: var(--theme-text-primary) !important;
        font-family: var(--theme-font-family) !important;
        transition: background 0.3s ease, color 0.3s ease;
    }}

    .block-container {{
        background: transparent !important;
        padding: 1.5rem 1.5rem 3.5rem !important;
        max-width: 1400px !important;
        margin: 0 auto;
    }}

    #MainMenu, footer {{ display: none !important; }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        z-index: 100 !important;
    }}
    button[data-testid="stSidebarCollapseButton"], button[data-testid="baseButton-headerNoPadding"] {{
        color: var(--theme-text-primary) !important;
        background: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 12px !important;
        box-shadow: 0 3px 0 rgba(0,0,0,0.12) !important;
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {{
        color: var(--theme-text-primary) !important;
        font-family: 'Fredoka', 'Quicksand', 'Inter', -apple-system, sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        margin: 0 0 0.5rem 0;
    }}

    p, span, div, label, .stMarkdown p, .stMarkdown li, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{
        color: var(--theme-text-primary);
        font-family: var(--theme-font-family);
    }}

    .text-muted, .sub-text, .empty-sub {{
        color: var(--theme-text-muted) !important;
    }}

    /* ── PLAYFUL TACTILE 3D BUTTONS (skribbl-inspired) ── */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"],
    div.stFormSubmitButton > button {{
        background: var(--theme-btn-primary-bg) !important;
        color: var(--theme-btn-primary-text) !important;
        border: 2px solid var(--theme-btn-primary-bg) !important;
        border-radius: var(--theme-button-radius, 14px) !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        padding: 9px 20px !important;
        min-height: 42px !important;
        box-shadow: 0 4px 0 rgba(0,0,0,0.22) !important;
        cursor: pointer !important;
        transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.15s ease, border-color 0.15s ease !important;
    }}

    div.stButton > button[kind="primary"] *,
    div.stButton > button[data-testid="baseButton-primary"] *,
    div.stFormSubmitButton > button * {{
        color: var(--theme-btn-primary-text) !important;
        font-weight: 800 !important;
    }}

    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    div.stFormSubmitButton > button:hover {{
        background: var(--theme-border-hover) !important;
        border-color: var(--theme-border-hover) !important;
        color: var(--theme-btn-primary-text) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 0 rgba(0,0,0,0.26), var(--theme-shadow-hover) !important;
    }}

    div.stButton > button[kind="primary"]:active,
    div.stButton > button[data-testid="baseButton-primary"]:active,
    div.stFormSubmitButton > button:active {{
        transform: translateY(2px) !important;
        box-shadow: 0 1px 0 rgba(0,0,0,0.22) !important;
    }}

    div.stButton > button,
    div.stButton > button[kind="secondary"],
    div.stDownloadButton > button,
    div.stLinkButton > a {{
        background: var(--theme-btn-secondary-bg) !important;
        color: var(--theme-btn-secondary-text) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: var(--theme-button-radius, 14px) !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        padding: 8px 18px !important;
        min-height: 40px !important;
        box-shadow: 0 3px 0 rgba(0,0,0,0.14) !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.15s ease, border-color 0.15s ease !important;
    }}

    div.stButton > button *,
    div.stDownloadButton > button *,
    div.stLinkButton > a * {{
        color: inherit !important;
        font-weight: 700 !important;
    }}

    div.stButton > button:hover,
    div.stDownloadButton > button:hover,
    div.stLinkButton > a:hover {{
        background: var(--theme-bg-card-elevated) !important;
        border-color: var(--theme-border-hover) !important;
        color: var(--theme-text-primary) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 0 rgba(0,0,0,0.18) !important;
    }}

    div.stButton > button:active,
    div.stDownloadButton > button:active,
    div.stLinkButton > a:active {{
        transform: translateY(2px) !important;
        box-shadow: 0 1px 0 rgba(0,0,0,0.14) !important;
    }}

    /* ── FORM INPUTS & DROPDOWNS ── */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        background: var(--theme-bg-input) !important;
        color: var(--theme-text-primary) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: var(--theme-input-radius, 14px) !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
        font-family: var(--theme-font-family) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--theme-accent-primary) !important;
        box-shadow: 0 0 0 3px var(--theme-accent-bg) !important;
    }}

    .stTextInput input::placeholder {{
        color: var(--theme-text-muted) !important;
    }}

    div[data-baseweb="select"] > div {{
        background-color: var(--theme-bg-input) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: var(--theme-input-radius, 14px) !important;
        color: var(--theme-text-primary) !important;
    }}

    div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] svg {{
        color: var(--theme-text-primary) !important;
        fill: var(--theme-text-primary) !important;
    }}

    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"], [data-baseweb="popover"] > div,
    [data-testid="stPopoverBody"], div[data-testid="stPopover"] {{
        background-color: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 16px !important;
        color: var(--theme-text-primary) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important;
    }}

    [data-baseweb="option"], li[role="option"] {{
        background-color: var(--theme-bg-card) !important;
        color: var(--theme-text-primary) !important;
        font-family: var(--theme-font-family) !important;
    }}

    [data-baseweb="option"]:hover, [data-baseweb="option"][aria-selected="true"], li[role="option"]:hover {{
        background-color: var(--theme-bg-card-elevated) !important;
        color: var(--theme-accent-primary) !important;
    }}

    /* ── EXPANDERS ── */
    [data-testid="stExpander"], details[data-testid="stExpander"] {{
        background-color: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 18px !important;
        color: var(--theme-text-primary) !important;
        box-shadow: 0 3px 0 rgba(0,0,0,0.08) !important;
        margin-bottom: 14px !important;
    }}

    summary[data-testid="stExpanderSummary"], [data-testid="stExpanderSummary"] {{
        background-color: var(--theme-bg-card) !important;
        color: var(--theme-text-primary) !important;
        border-radius: 18px !important;
    }}

    summary[data-testid="stExpanderSummary"]:hover {{
        background-color: var(--theme-bg-card-elevated) !important;
    }}

    summary[data-testid="stExpanderSummary"] span, summary[data-testid="stExpanderSummary"] p {{
        color: var(--theme-text-primary) !important;
        font-weight: 700 !important;
    }}

    /* ── RADIO BUTTONS & TABS ── */
    div[data-testid="stRadio"] label {{
        background: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 14px !important;
        color: var(--theme-text-secondary) !important;
        font-weight: 600 !important;
        padding: 6px 14px !important;
        transition: all 0.15s ease !important;
    }}

    div[data-testid="stRadio"] label:hover {{
        border-color: var(--theme-border-hover) !important;
        color: var(--theme-text-primary) !important;
    }}

    div[data-testid="stRadio"] label:has(input:checked) {{
        background: var(--theme-accent-bg) !important;
        border-color: var(--theme-accent-primary) !important;
        color: var(--theme-accent-primary) !important;
        font-weight: 800 !important;
        box-shadow: 0 2px 0 var(--theme-accent-primary) !important;
    }}

    /* ── SIDEBAR NAVIGATION ── */
    section[data-testid="stSidebar"], div[data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] > div {{
        background: var(--theme-bg-sidebar) !important;
        color: var(--theme-text-primary) !important;
        border-right: 2px solid var(--theme-border-color) !important;
    }}

    .sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 4px 14px;
        margin-bottom: 14px;
        border-bottom: 2px solid var(--theme-border-color);
    }}

    .sidebar-brand-icon {{
        font-size: 26px;
        transition: transform 0.25s ease;
        display: inline-block;
    }}

    .sidebar-brand:hover .sidebar-brand-icon {{
        transform: scale(1.2) rotate(-8deg);
    }}

    .sidebar-brand-title {{
        font-size: 19px;
        font-weight: 900;
        color: var(--theme-text-primary) !important;
        letter-spacing: -0.03em;
        font-family: 'Fredoka', 'Inter', sans-serif !important;
        line-height: 1.1;
    }}

    .sidebar-brand-subtitle {{
        font-size: 11px;
        color: var(--theme-text-muted) !important;
        font-weight: 600;
        margin-top: 2px;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {{
        gap: 6px !important;
        width: 100% !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {{
        background: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 14px !important;
        padding: 9px 13px !important;
        color: var(--theme-text-secondary) !important;
        font-weight: 700;
        font-size: 13.5px;
        cursor: pointer;
        display: flex;
        align-items: center;
        width: 100% !important;
        margin: 0 !important;
        box-shadow: 0 3px 0 rgba(0,0,0,0.08) !important;
        transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {{
        background: var(--theme-bg-card-elevated) !important;
        border-color: var(--theme-border-hover) !important;
        color: var(--theme-text-primary) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 0 rgba(0,0,0,0.12) !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {{
        background: var(--theme-accent-bg) !important;
        border-color: var(--theme-accent-primary) !important;
        color: var(--theme-accent-primary) !important;
        font-weight: 800;
        box-shadow: 0 3px 0 var(--theme-accent-primary) !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {{
        display: none !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:last-child {{
        width: 100% !important;
        color: inherit !important;
    }}

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {{
        font-size: 13.5px !important;
        margin: 0 !important;
        color: inherit !important;
        font-weight: inherit !important;
        white-space: nowrap !important;
    }}

    .sidebar-status-card {{
        background: var(--theme-bg-card) !important;
        border: 2px solid var(--theme-border-color) !important;
        border-radius: 16px !important;
        padding: 12px 14px;
        margin-top: 18px;
        box-shadow: 0 3px 0 rgba(0,0,0,0.08) !important;
    }}

    /* ── GAMING LOBBY COMPONENTS ── */
    .lobby-hero {{
        background: var(--theme-bg-card);
        border: 2.5px solid var(--theme-border-color);
        border-radius: 24px;
        padding: 26px 30px 22px;
        margin-bottom: 22px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 6px 0 rgba(0,0,0,0.12), var(--theme-shadow-card);
    }}

    .lobby-hero-title {{
        font-size: 30px;
        font-weight: 900;
        color: var(--theme-text-primary);
        line-height: 1.2;
        letter-spacing: -0.03em;
        font-family: 'Fredoka', 'Inter', sans-serif !important;
        margin: 0 0 6px 0;
    }}

    .lobby-hero-sub {{
        font-size: 14.5px;
        color: var(--theme-text-secondary);
        font-weight: 500;
        margin: 0 0 16px 0;
        line-height: 1.4;
    }}

    .lobby-chips {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 14px;
    }}

    .lobby-chip {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: var(--theme-bg-card-elevated);
        border: 2px solid var(--theme-border-color);
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 800;
        color: var(--theme-text-primary);
        box-shadow: 0 2px 0 rgba(0,0,0,0.08);
    }}

    .arcade-pad-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
    }}

    .arcade-pad {{
        background: var(--theme-bg-card);
        border: 2.5px solid var(--theme-border-color);
        border-radius: 18px;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1);
        transition: all 0.2s cubic-bezier(0.16,1,0.3,1);
        cursor: pointer;
    }}

    .arcade-pad:hover {{
        transform: translateY(-3px);
        border-color: var(--theme-border-hover);
        box-shadow: 0 7px 0 rgba(0,0,0,0.14), var(--theme-shadow-hover);
    }}

    .arcade-icon {{
        font-size: 24px;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--theme-accent-bg);
        border-radius: 12px;
        flex-shrink: 0;
    }}

    .arcade-label {{
        font-size: 13.5px;
        font-weight: 800;
        color: var(--theme-text-primary);
        font-family: 'Fredoka', 'Inter', sans-serif !important;
        margin-bottom: 2px;
    }}

    .arcade-sub {{
        font-size: 11px;
        color: var(--theme-text-muted);
        font-weight: 600;
    }}

    .stat-pods-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
    }}

    .stat-pod {{
        background: var(--theme-bg-card);
        border: 2.5px solid var(--theme-border-color);
        border-radius: 20px;
        padding: 16px 18px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }}

    .stat-pod:hover {{
        transform: translateY(-3px);
        border-color: var(--theme-border-hover);
        box-shadow: 0 7px 0 rgba(0,0,0,0.14);
    }}

    .stat-pod-icon {{
        font-size: 24px;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--theme-accent-bg);
        border-radius: 12px;
        flex-shrink: 0;
    }}

    .stat-pod-label {{
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--theme-text-muted);
        margin-bottom: 2px;
    }}

    .stat-pod-val {{
        font-size: 24px;
        font-weight: 900;
        color: var(--theme-text-primary);
        font-family: 'Fredoka', 'Inter', sans-serif !important;
        line-height: 1;
    }}

    .stat-pod-val.sale {{ color: var(--theme-sale) !important; }}
    .stat-pod-val.accent {{ color: var(--theme-accent-primary) !important; }}

    /* ── GAME CARDS (skribbl-inspired rounded bubbly cards) ── */
    .game-card, .game-card-container, .game-card-wrapper, .search-result-card {{
        background: var(--theme-bg-card) !important;
        border: 2.5px solid var(--theme-border-color) !important;
        border-radius: 22px !important;
        padding: 18px 20px !important;
        margin-bottom: 18px !important;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1), var(--theme-shadow-card) !important;
        transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.2s ease,
                    box-shadow 0.2s ease !important;
    }}

    .game-card:hover, .game-card-container:hover, .game-card-wrapper:hover, .search-result-card:hover {{
        transform: translateY(-4px) !important;
        border-color: var(--theme-border-hover) !important;
        box-shadow: 0 8px 0 rgba(0,0,0,0.14), var(--theme-shadow-hover) !important;
    }}

    .game-card-wrapper.on-sale {{
        border-left: 6px solid var(--theme-sale) !important;
    }}

    .card-layout-flex {{
        display: flex;
        gap: 18px;
        align-items: flex-start;
    }}

    .card-art-col {{
        flex: 0 0 190px;
        max-width: 190px;
    }}

    .card-art-wrap {{
        overflow: hidden;
        border-radius: 14px;
        aspect-ratio: 16 / 9;
        background: var(--theme-bg-card-elevated);
        border: 1.5px solid var(--theme-border-subtle);
        position: relative;
    }}

    .card-art-img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.35s ease;
    }}

    .game-card-wrapper:hover .card-art-img {{
        transform: scale(1.06) rotate(-0.5deg);
    }}

    .card-info-col {{
        flex: 1;
        min-width: 0;
    }}

    .card-title-row {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 6px;
        flex-wrap: wrap;
    }}

    .card-game-title {{
        font-size: 18px;
        font-weight: 800;
        color: var(--theme-text-primary);
        font-family: 'Fredoka', 'Inter', sans-serif !important;
        line-height: 1.3;
    }}

    /* ── BADGES & TAGS ── */
    .store-tag {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 8px;
        border: 1.5px solid var(--theme-border-color);
        background: var(--theme-bg-card-elevated);
        color: var(--theme-text-primary);
    }}

    .store-tag.steam {{
        border-color: #0ea5e9;
        color: #0284c7;
        background: rgba(14, 165, 233, 0.15);
    }}

    .store-tag.epic {{
        border-color: #8b5cf6;
        color: #7c3aed;
        background: rgba(139, 92, 246, 0.15);
    }}

    .store-tag.gog {{
        border-color: #f59e0b;
        color: #d97706;
        background: rgba(245, 158, 11, 0.15);
    }}

    .disc-tag, .flame-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: #ffffff !important;
        border-radius: 999px;
        padding: 3px 10px;
        font-size: 12px;
        font-weight: 900;
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.35);
        animation: pulseDeal 2.5s infinite;
    }}

    .target-met-badge {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: linear-gradient(135deg, #10b981, #059669);
        color: #ffffff !important;
        border-radius: 999px;
        padding: 4px 12px;
        font-weight: 800;
        font-size: 11px;
        animation: pulseDeal 2s infinite;
    }}

    .owned-badge {{
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #ffffff !important;
        border-radius: 999px;
        padding: 4px 12px;
        font-weight: 800;
        font-size: 11px;
    }}

    .lowest-price-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: var(--theme-sale-bg);
        border: 1.5px solid var(--theme-sale);
        color: var(--theme-sale);
        border-radius: 8px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 700;
    }}

    .best-deal-callout {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: var(--theme-sale) !important;
        background: var(--theme-sale-bg) !important;
        border: 1.5px solid var(--theme-sale) !important;
        border-radius: 10px !important;
        padding: 6px 14px !important;
    }}

    .price-orig-strike {{
        font-size: 13px !important;
        color: var(--theme-text-muted) !important;
        text-decoration: line-through !important;
        margin-left: 8px !important;
    }}

    .compare-section {{
        background: var(--theme-bg-card-elevated);
        border: 1.5px solid var(--theme-border-color);
        border-radius: 14px;
        padding: 12px 16px;
        margin: 10px 0;
    }}

    .compare-columns-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }}

    .compare-store-item {{
        display: flex;
        flex-direction: column;
    }}

    .compare-price-val {{
        font-size: 18px;
        font-weight: 800;
        color: var(--theme-text-primary);
        margin-top: 4px;
        font-family: 'Fredoka', 'Inter', sans-serif;
    }}

    .compare-price-val.sale {{
        color: var(--theme-sale) !important;
    }}

    /* ── EMPTY STATES ── */
    .empty-box {{
        text-align: center !important;
        padding: 44px 24px !important;
        background: var(--theme-bg-card) !important;
        border: 2.5px dashed var(--theme-border-color) !important;
        border-radius: 22px !important;
        color: var(--theme-text-muted) !important;
        box-shadow: 0 4px 0 rgba(0,0,0,0.06) !important;
    }}

    .empty-icon {{
        font-size: 46px !important;
        margin-bottom: 10px !important;
        animation: floatGamer 3s infinite ease-in-out;
    }}

    .empty-title {{
        font-size: 18px !important;
        font-weight: 800 !important;
        color: var(--theme-text-primary) !important;
        margin-bottom: 6px !important;
        font-family: 'Fredoka', 'Inter', sans-serif !important;
    }}

    .empty-sub {{
        font-size: 13.5px !important;
        color: var(--theme-text-secondary) !important;
        max-width: 460px;
        margin: 0 auto;
        line-height: 1.5;
    }}

    /* ── CELEBRATION BANNER ── */
    .celebration-banner {{
        background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(6,182,212,0.18));
        border: 2px solid var(--theme-sale);
        border-radius: 18px;
        padding: 14px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 16px rgba(16,185,129,0.2);
        animation: confettiPop 0.5s ease-out;
    }}

    /* ── SUMMARY STAT CARDS ── */
    .summary-cards-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
        margin-bottom: 22px;
    }}

    .sum-card {{
        background: var(--theme-bg-card) !important;
        border: 2.5px solid var(--theme-border-color) !important;
        border-radius: 18px !important;
        padding: 14px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 0 rgba(0,0,0,0.08) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }}

    .sum-card:hover {{
        transform: translateY(-2px) !important;
        border-color: var(--theme-border-hover) !important;
        box-shadow: 0 6px 0 rgba(0,0,0,0.12) !important;
    }}

    .sum-icon {{
        font-size: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: var(--theme-accent-bg) !important;
        color: var(--theme-accent-primary) !important;
    }}

    .sum-info {{
        display: flex;
        flex-direction: column;
    }}

    .sum-label {{
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--theme-text-muted) !important;
        margin-bottom: 2px;
    }}

    .sum-val {{
        font-size: 20px;
        font-weight: 900;
        color: var(--theme-text-primary) !important;
        font-family: 'Fredoka', 'Inter', sans-serif !important;
    }}

    .sum-val.sale {{ color: var(--theme-sale) !important; }}
    .sum-val.accent {{ color: var(--theme-accent-primary) !important; }}

    /* ── ANIMATIONS ── */
    @keyframes pulseDeal {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}

    @keyframes floatGamer {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-5px); }}
    }}

    @keyframes confettiPop {{
        0% {{ transform: scale(0.9); opacity: 0; }}
        70% {{ transform: scale(1.03); }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}

    /* ── RESPONSIVENESS ── */
    @media (max-width: 900px) {{
        .card-layout-flex {{
            flex-direction: column;
            gap: 12px;
        }}
        .card-art-col {{
            flex: 0 0 100%;
            max-width: 100%;
        }}
        .arcade-pad-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .stat-pods-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .summary-cards-container {{
            grid-template-columns: repeat(2, 1fr);
        }}
    }}

    @media (max-width: 600px) {{
        .block-container {{
            padding: 0.75rem 0.75rem 2rem !important;
        }}
        .lobby-hero {{
            padding: 20px 16px;
        }}
        .lobby-hero-title {{
            font-size: 24px;
        }}
        .arcade-pad-grid {{
            grid-template-columns: 1fr;
        }}
        .stat-pods-grid {{
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        .summary-cards-container {{
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        div.stButton > button {{
            width: 100% !important;
            min-height: 44px !important;
        }}
        body, html, .stApp {{
            overflow-x: hidden !important;
            max-width: 100vw !important;
        }}
    }}

    {particle_css}
    </style>
    """


def generate_theme_css(theme_id: str) -> str:
    t = get_theme(theme_id)
    tokens = get_dashboard_tokens(t)

    # Particle Animations CSS
    particle_css = ""
    if t.get("particle_type") == "sakura":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            [data-testid="stAppViewContainer"]::before {
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
        accent_color = tokens["accent"]
        particle_css = f"""
        @media not (prefers-reduced-motion: reduce) {{
            [data-testid="stAppViewContainer"]::before {{
                content: '✦';
                position: fixed;
                top: 20%;
                right: 10%;
                font-size: 14px;
                color: {accent_color};
                opacity: 0.5;
                animation: starTwinkle 4s ease-in-out infinite alternate;
                pointer-events: none;
                z-index: 0;
            }}
            @keyframes starTwinkle {{
                0% {{ opacity: 0.15; transform: scale(0.8); }}
                100% {{ opacity: 0.85; transform: scale(1.3); }}
            }}
        }}
        """
    elif t.get("particle_type") == "embers":
        particle_css = """
        @media not (prefers-reduced-motion: reduce) {
            [data-testid="stAppViewContainer"]::before {
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
            [data-testid="stAppViewContainer"]::before {
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

    return generate_dashboard_css(t, particle_css=particle_css)



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


# ── Dedicated Email Themes Registry ─────────────────────────────────
EMAIL_THEMES: dict[str, dict[str, Any]] = {
    "sakura_dream": {
        "id": "sakura_dream",
        "name": "Sakura Dream",
        "mode": "light",
        "bg_body": "#fff0f5",
        "bg_container": "#fdf7fa",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#fce4ec",
        "border_color": "#f8c8dc",
        "border_subtle": "#fce4ec",
        "text_primary": "#2d1732",
        "text_secondary": "#5c3d64",
        "text_muted": "#886791",
        "accent": "#ff85a2",
        "sale_color": "#e04870",
        "sale_bg": "rgba(224, 72, 112, 0.12)",
        "btn_bg": "#ff85a2",
        "btn_text": "#ffffff",
        "swatch_colors": ["#fff0f5", "#ffffff", "#ff85a2", "#2d1732"],
    },
    "wuxia_ink": {
        "id": "wuxia_ink",
        "name": "Wuxia / Ink & Jade",
        "mode": "light",
        "bg_body": "#f5efe6",
        "bg_container": "#f9f6f0",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f3ece0",
        "border_color": "#d6cebf",
        "border_subtle": "#e7e0d3",
        "text_primary": "#1c1917",
        "text_secondary": "#44403c",
        "text_muted": "#78716c",
        "accent": "#00a86b",
        "sale_color": "#00a86b",
        "sale_bg": "rgba(0, 168, 107, 0.12)",
        "btn_bg": "#00a86b",
        "btn_text": "#ffffff",
        "swatch_colors": ["#f5efe6", "#ffffff", "#00a86b", "#1c1917"],
    },
    "cozy_forest": {
        "id": "cozy_forest",
        "name": "Cozy Forest",
        "mode": "light",
        "bg_body": "#f4f7f2",
        "bg_container": "#f9faf7",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#eaf2e8",
        "border_color": "#cddcd2",
        "border_subtle": "#dfebd4",
        "text_primary": "#1c2e24",
        "text_secondary": "#3e5749",
        "text_muted": "#688574",
        "accent": "#52796f",
        "sale_color": "#407a52",
        "sale_bg": "rgba(64, 122, 82, 0.12)",
        "btn_bg": "#52796f",
        "btn_text": "#ffffff",
        "swatch_colors": ["#f4f7f2", "#ffffff", "#52796f", "#1c2e24"],
    },
    "arcane_library": {
        "id": "arcane_library",
        "name": "Wizarding / Arcane Library",
        "mode": "light",
        "bg_body": "#f7f1e3",
        "bg_container": "#fbf8f1",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f5ebd7",
        "border_color": "#dfd2bc",
        "border_subtle": "#ede3d1",
        "text_primary": "#2b1810",
        "text_secondary": "#54382b",
        "text_muted": "#856251",
        "accent": "#9f1239",
        "sale_color": "#15803d",
        "sale_bg": "rgba(21, 128, 61, 0.12)",
        "btn_bg": "#9f1239",
        "btn_text": "#faf3e0",
        "swatch_colors": ["#f7f1e3", "#ffffff", "#9f1239", "#2b1810"],
    },
    "celestial": {
        "id": "celestial",
        "name": "Celestial Constellation",
        "mode": "light",
        "bg_body": "#f0f4f8",
        "bg_container": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#e4eef7",
        "border_color": "#cbd5e1",
        "border_subtle": "#e2e8f0",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "accent": "#6366f1",
        "sale_color": "#0284c7",
        "sale_bg": "rgba(2, 132, 199, 0.12)",
        "btn_bg": "#4f46e5",
        "btn_text": "#ffffff",
        "swatch_colors": ["#f0f4f8", "#ffffff", "#6366f1", "#0f172a"],
    },
    "minimal": {
        "id": "minimal",
        "name": "Minimal",
        "mode": "light",
        "bg_body": "#ffffff",
        "bg_container": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_card_elevated": "#f1f5f9",
        "border_color": "#e2e8f0",
        "border_subtle": "#f1f5f9",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "text_muted": "#64748b",
        "accent": "#2563eb",
        "sale_color": "#16a34a",
        "sale_bg": "rgba(22, 163, 74, 0.12)",
        "btn_bg": "#2563eb",
        "btn_text": "#ffffff",
        "swatch_colors": ["#ffffff", "#ffffff", "#2563eb", "#0f172a"],
    },
    "midnight_gamer": {
        "id": "midnight_gamer",
        "name": "Midnight Gamer",
        "mode": "dark",
        "bg_body": "#0f172a",
        "bg_container": "#1e293b",
        "bg_card": "#27354a",
        "bg_card_elevated": "#32445e",
        "border_color": "#3b4f73",
        "border_subtle": "#273752",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "accent": "#818cf8",
        "sale_color": "#4ade80",
        "sale_bg": "rgba(74, 222, 128, 0.22)",
        "btn_bg": "#6366f1",
        "btn_text": "#ffffff",
        "swatch_colors": ["#0f172a", "#27354a", "#818cf8", "#f8fafc"],
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "mode": "dark",
        "bg_body": "#08070d",
        "bg_container": "#13111c",
        "bg_card": "#1a1726",
        "bg_card_elevated": "#252136",
        "border_color": "#433b63",
        "border_subtle": "#252038",
        "text_primary": "#f0f6fc",
        "text_secondary": "#dcd2f8",
        "text_muted": "#b1a0e3",
        "accent": "#00f0ff",
        "sale_color": "#ff007f",
        "sale_bg": "rgba(255, 0, 127, 0.25)",
        "btn_bg": "#00b4d8",
        "btn_text": "#050408",
        "swatch_colors": ["#08070d", "#1a1726", "#00f0ff", "#f0f6fc"],
    },
    "gothic_academia": {
        "id": "gothic_academia",
        "name": "Gothic / Dark Academia",
        "mode": "dark",
        "bg_body": "#0f0d10",
        "bg_container": "#1c181e",
        "bg_card": "#27212b",
        "bg_card_elevated": "#342d3a",
        "border_color": "#4e4354",
        "border_subtle": "#2c2630",
        "text_primary": "#f7f0e6",
        "text_secondary": "#ebdfcf",
        "text_muted": "#cca99a",
        "accent": "#d4af37",
        "sale_color": "#d4af37",
        "sale_bg": "rgba(212, 175, 55, 0.25)",
        "btn_bg": "#800f2f",
        "btn_text": "#f7f0e6",
        "swatch_colors": ["#0f0d10", "#27212b", "#d4af37", "#f7f0e6"],
    },
    "aurora": {
        "id": "aurora",
        "name": "Aurora",
        "mode": "dark",
        "bg_body": "#090d16",
        "bg_container": "#131b2e",
        "bg_card": "#1a253d",
        "bg_card_elevated": "#253456",
        "border_color": "rgba(139, 92, 246, 0.3)",
        "border_subtle": "rgba(139, 92, 246, 0.15)",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "accent": "#8b5cf6",
        "sale_color": "#22c55e",
        "sale_bg": "rgba(34, 197, 94, 0.2)",
        "btn_bg": "#7c3aed",
        "btn_text": "#ffffff",
        "swatch_colors": ["#090d16", "#1a253d", "#8b5cf6", "#f8fafc"],
    },
}


def get_email_theme(theme_name: str, app_theme_id: str = "midnight_gamer") -> dict[str, Any]:
    """Resolves email theme token mapping cleanly for any selected theme name."""
    if theme_name == "Use application theme":
        target_id = app_theme_id
    else:
        # Match by name or ID
        target_id = None
        for eid, eth in EMAIL_THEMES.items():
            if eth["name"].lower() == theme_name.lower() or eid.lower() == theme_name.lower():
                target_id = eid
                break
        if not target_id:
            for tid, t in THEMES.items():
                if t["name"].lower() == theme_name.lower() or tid.lower() == theme_name.lower():
                    target_id = tid
                    break
        if not target_id:
            target_id = "midnight_gamer"

    if target_id in EMAIL_THEMES:
        return EMAIL_THEMES[target_id]

    if target_id in THEMES:
        t = THEMES[target_id]
        is_light = (t.get("mode") == "light")
        return {
            "id": t["id"],
            "name": t["name"],
            "mode": t.get("mode", "dark"),
            "bg_body": "#fff0f5" if is_light else (t.get("bg_body", "#0f172a") if not t.get("bg_body", "").startswith("linear") else "#0f172a"),
            "bg_container": t.get("bg_sidebar", "#fdf7fa" if is_light else "#1e293b"),
            "bg_card": t.get("bg_card", "#ffffff" if is_light else "#27354a"),
            "bg_card_elevated": t.get("bg_card_elevated", "#fce4ec" if is_light else "#32445e"),
            "border_color": t.get("border_color", "#f8c8dc" if is_light else "#3b4f73"),
            "border_subtle": t.get("border_subtle", "#fce4ec" if is_light else "#273752"),
            "text_primary": t.get("text_primary", "#2d1732" if is_light else "#f8fafc"),
            "text_secondary": t.get("text_secondary", "#5c3d64" if is_light else "#cbd5e1"),
            "text_muted": t.get("text_muted", "#886791" if is_light else "#94a3b8"),
            "accent": t.get("accent_primary", "#ff85a2" if is_light else "#818cf8"),
            "sale_color": t.get("sale_color", "#e04870" if is_light else "#4ade80"),
            "sale_bg": t.get("sale_bg", "rgba(224, 72, 112, 0.12)" if is_light else "rgba(74, 222, 128, 0.22)"),
            "btn_bg": t.get("btn_primary_bg", "#ff85a2" if is_light else "#6366f1"),
            "btn_text": t.get("btn_primary_text", "#ffffff"),
            "swatch_colors": [
                t.get("bg_sidebar", "#fff0f5" if is_light else "#0f172a"),
                t.get("bg_card", "#ffffff" if is_light else "#27354a"),
                t.get("accent_primary", "#ff85a2" if is_light else "#818cf8"),
                t.get("text_primary", "#2d1732" if is_light else "#f8fafc"),
            ],
        }

    return EMAIL_THEMES["midnight_gamer"]

