import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

PERSONALITY_LEVELS = ["Subtle", "Playful", "Chaotic"]

THEMES: dict[str, dict[str, Any]] = {
    "midnight_gamer": {
        "id": "midnight_gamer",
        "name": "Midnight Gamer",
        "icon": "🌙",
        "bg_body": "radial-gradient(ellipse at top, #111827 0%, #0d121f 60%, #080b12 100%)",
        "bg_sidebar": "#090d16",
        "bg_card": "#121827",
        "bg_card_elevated": "#1a2238",
        "bg_input": "#0d121f",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "border_color": "#1f293d",
        "border_subtle": "#162032",
        "border_hover": "#374151",
        "accent_primary": "#6366f1",
        "accent_secondary": "#818cf8",
        "accent_bg": "rgba(99, 102, 241, 0.12)",
        "sale_color": "#4ade80",
        "sale_bg": "rgba(74, 222, 128, 0.12)",
        "warning_color": "#ef4444",
        "btn_primary_bg": "#4f46e5",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#1e293b",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 20px rgba(0, 0, 0, 0.3)",
        "shadow_hover": "0 12px 28px rgba(99, 102, 241, 0.2)",
        "card_radius": "10px",
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
        "bg_body": "radial-gradient(circle at 80% 20%, rgba(255, 183, 197, 0.09) 0%, transparent 45%), radial-gradient(circle at 10% 80%, rgba(226, 160, 255, 0.07) 0%, transparent 45%), linear-gradient(135deg, #130816 0%, #170b1a 60%, #200f24 100%)",
        "bg_sidebar": "#0e0611",
        "bg_card": "linear-gradient(145deg, #251429 0%, #2e1a33 100%)",
        "bg_card_elevated": "#361e3b",
        "bg_input": "#1d0e21",
        "text_primary": "#fdf0f5",
        "text_secondary": "#e5c5d3",
        "text_muted": "#c9a9b6",
        "border_color": "#3d2342",
        "border_subtle": "#2c1730",
        "border_hover": "#ffb7c5",
        "accent_primary": "#ffb7c5",
        "accent_secondary": "#e2a0ff",
        "accent_bg": "rgba(255, 183, 197, 0.15)",
        "sale_color": "#e2a0ff",
        "sale_bg": "rgba(226, 160, 255, 0.15)",
        "warning_color": "#ff6b8b",
        "btn_primary_bg": "#db7093",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#2e1a33",
        "btn_secondary_text": "#fdf0f5",
        "shadow_card": "0 8px 24px rgba(37, 20, 41, 0.4)",
        "shadow_hover": "0 12px 32px rgba(255, 183, 197, 0.25)",
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
        "icon": "💥",
        "bg_body": "linear-gradient(135deg, #070d1e 0%, #0a1128 60%, #101a3b 100%)",
        "bg_sidebar": "#050814",
        "bg_card": "linear-gradient(145deg, #121e3d 0%, #17264a 100%)",
        "bg_card_elevated": "#1e305e",
        "bg_input": "#0b132c",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#a0aec0",
        "border_color": "#1e2d5a",
        "border_subtle": "#142042",
        "border_hover": "#e63946",
        "accent_primary": "#e63946",
        "accent_secondary": "#00f5d4",
        "accent_bg": "rgba(230, 57, 70, 0.15)",
        "sale_color": "#00f5d4",
        "sale_bg": "rgba(0, 245, 212, 0.15)",
        "warning_color": "#ffb703",
        "btn_primary_bg": "#e63946",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#1e2d5a",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 20px rgba(0, 0, 0, 0.4)",
        "shadow_hover": "0 10px 28px rgba(230, 57, 70, 0.3)",
        "card_radius": "6px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "💥 PLUS ULTRA DEAL",
        "tracked_label": "HERO DOSSIER",
        "buy_button_prefix": "PLUS ULTRA → VIEW",
    },
    "cosmic_romance": {
        "id": "cosmic_romance",
        "name": "Cosmic Romance",
        "icon": "✦",
        "bg_body": "radial-gradient(ellipse at 50% 10%, rgba(124, 58, 237, 0.12) 0%, transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(0, 229, 255, 0.08) 0%, transparent 50%), linear-gradient(135deg, #05070e 0%, #080b14 60%, #0e1322 100%)",
        "bg_sidebar": "#030408",
        "bg_card": "rgba(16, 22, 38, 0.85)",
        "bg_card_elevated": "rgba(24, 34, 58, 0.9)",
        "bg_input": "#0a0e1a",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#a3b3d1",
        "border_color": "#1d2840",
        "border_subtle": "#141c2e",
        "border_hover": "#00e5ff",
        "accent_primary": "#00e5ff",
        "accent_secondary": "#a855f7",
        "accent_bg": "rgba(0, 229, 255, 0.15)",
        "sale_color": "#a855f7",
        "sale_bg": "rgba(168, 85, 247, 0.15)",
        "warning_color": "#ff4081",
        "btn_primary_bg": "#7c3aed",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#161e33",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(5, 7, 14, 0.6)",
        "shadow_hover": "0 12px 32px rgba(0, 229, 255, 0.25)",
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
        "icon": "江湖",
        "bg_body": "radial-gradient(circle at 50% 30%, rgba(0, 168, 107, 0.05) 0%, transparent 70%), linear-gradient(135deg, #07080a 0%, #0b0c10 60%, #12141a 100%)",
        "bg_sidebar": "#050507",
        "bg_card": "linear-gradient(145deg, #16181d 0%, #1c1e24 100%)",
        "bg_card_elevated": "#252830",
        "bg_input": "#101115",
        "text_primary": "#f4f1ea",
        "text_secondary": "#d5ceb8",
        "text_muted": "#9a9a91",
        "border_color": "#2c2e35",
        "border_subtle": "#1e2025",
        "border_hover": "#00a86b",
        "accent_primary": "#00a86b",
        "accent_secondary": "#d4af37",
        "accent_bg": "rgba(0, 168, 107, 0.15)",
        "sale_color": "#00c985",
        "sale_bg": "rgba(0, 201, 133, 0.15)",
        "warning_color": "#c0392b",
        "btn_primary_bg": "#008552",
        "btn_primary_text": "#f4f1ea",
        "btn_secondary_bg": "#1c1e24",
        "btn_secondary_text": "#f4f1ea",
        "shadow_card": "0 8px 20px rgba(0, 0, 0, 0.5)",
        "shadow_hover": "0 10px 28px rgba(0, 168, 107, 0.25)",
        "card_radius": "6px",
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
        "icon": "✨",
        "bg_body": "radial-gradient(circle at 30% 20%, rgba(212, 175, 55, 0.06) 0%, transparent 50%), linear-gradient(135deg, #0f050c 0%, #150811 60%, #1f0d19 100%)",
        "bg_sidebar": "#0a0308",
        "bg_card": "linear-gradient(145deg, #22101c 0%, #2b1424 100%)",
        "bg_card_elevated": "#3a1c31",
        "bg_input": "#190a15",
        "text_primary": "#faf3e0",
        "text_secondary": "#d9c5b2",
        "text_muted": "#b89b88",
        "border_color": "#3d1d32",
        "border_subtle": "#2a1322",
        "border_hover": "#d4af37",
        "accent_primary": "#d4af37",
        "accent_secondary": "#8b0000",
        "accent_bg": "rgba(212, 175, 55, 0.15)",
        "sale_color": "#27ae60",
        "sale_bg": "rgba(39, 174, 96, 0.15)",
        "warning_color": "#c0392b",
        "btn_primary_bg": "#8b0000",
        "btn_primary_text": "#faf3e0",
        "btn_secondary_bg": "#2b1424",
        "btn_secondary_text": "#faf3e0",
        "shadow_card": "0 8px 20px rgba(15, 5, 12, 0.5)",
        "shadow_hover": "0 10px 28px rgba(212, 175, 55, 0.25)",
        "card_radius": "8px",
        "button_radius": "6px",
        "input_radius": "6px",
        "font_family": "'Georgia', serif",
        "particle_type": "embers",
        "best_deal_label": "✨ ARCANE BARGAIN",
        "tracked_label": "GRIMOIRE",
        "buy_button_prefix": "INSPECT SPELL",
    },
    "cyberpunk": {
        "id": "cyberpunk",
        "name": "Cyberpunk",
        "icon": "⚙️",
        "bg_body": "repeating-linear-gradient(0deg, rgba(0,240,255,0.015) 0px, rgba(0,240,255,0.015) 1px, transparent 1px, transparent 4px), linear-gradient(135deg, #050608 0%, #08090c 60%, #0e1017 100%)",
        "bg_sidebar": "#030405",
        "bg_card": "#11131a",
        "bg_card_elevated": "#181b24",
        "bg_input": "#0a0c10",
        "text_primary": "#f0f6fc",
        "text_secondary": "#c5d1de",
        "text_muted": "#8b949e",
        "border_color": "#1e2230",
        "border_subtle": "#141720",
        "border_hover": "#00f0ff",
        "accent_primary": "#00f0ff",
        "accent_secondary": "#ff0055",
        "accent_bg": "rgba(0, 240, 255, 0.15)",
        "sale_color": "#ff0055",
        "sale_bg": "rgba(255, 0, 85, 0.15)",
        "warning_color": "#ff9900",
        "btn_primary_bg": "#00a8b5",
        "btn_primary_text": "#08090c",
        "btn_secondary_bg": "#181b24",
        "btn_secondary_text": "#f0f6fc",
        "shadow_card": "0 4px 16px rgba(0, 0, 0, 0.6)",
        "shadow_hover": "0 0 16px rgba(0, 240, 255, 0.3)",
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
        "icon": "📜",
        "bg_body": "linear-gradient(135deg, #050506 0%, #09090b 60%, #101014 100%)",
        "bg_sidebar": "#040405",
        "bg_card": "#141417",
        "bg_card_elevated": "#1f1f24",
        "bg_input": "#0e0e10",
        "text_primary": "#f4f4f5",
        "text_secondary": "#d4d4d8",
        "text_muted": "#a1a1aa",
        "border_color": "#27272a",
        "border_subtle": "#1c1c1f",
        "border_hover": "#991b1b",
        "accent_primary": "#991b1b",
        "accent_secondary": "#ca8a04",
        "accent_bg": "rgba(153, 27, 27, 0.15)",
        "sale_color": "#ca8a04",
        "sale_bg": "rgba(202, 138, 4, 0.15)",
        "warning_color": "#b91c1c",
        "btn_primary_bg": "#7f1d1d",
        "btn_primary_text": "#f4f4f5",
        "btn_secondary_bg": "#1a1a1f",
        "btn_secondary_text": "#f4f4f5",
        "shadow_card": "0 8px 24px rgba(0, 0, 0, 0.6)",
        "shadow_hover": "0 10px 28px rgba(153, 27, 27, 0.25)",
        "card_radius": "4px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Georgia', serif",
        "particle_type": "none",
        "best_deal_label": "📜 ARCHIVE OFFER",
        "tracked_label": "ARCHIVE",
        "buy_button_prefix": "CONSULT ARCHIVE",
    },
    "cozy_forest": {
        "id": "cozy_forest",
        "name": "Cozy Forest",
        "icon": "🍃",
        "bg_body": "radial-gradient(circle at 70% 30%, rgba(104, 144, 77, 0.08) 0%, transparent 50%), linear-gradient(135deg, #08120c 0%, #0d1912 60%, #13241a 100%)",
        "bg_sidebar": "#050b07",
        "bg_card": "#16281e",
        "bg_card_elevated": "#213b2c",
        "bg_input": "#101e16",
        "text_primary": "#f5f2eb",
        "text_secondary": "#cdd9d0",
        "text_muted": "#9eb3a4",
        "border_color": "#243e2e",
        "border_subtle": "#1a2d21",
        "border_hover": "#68904d",
        "accent_primary": "#68904d",
        "accent_secondary": "#8bc34a",
        "accent_bg": "rgba(104, 144, 77, 0.15)",
        "sale_color": "#8bc34a",
        "sale_bg": "rgba(139, 195, 74, 0.15)",
        "warning_color": "#d97706",
        "btn_primary_bg": "#486b32",
        "btn_primary_text": "#f5f2eb",
        "btn_secondary_bg": "#1d3326",
        "btn_secondary_text": "#f5f2eb",
        "shadow_card": "0 8px 20px rgba(8, 18, 12, 0.4)",
        "shadow_hover": "0 12px 28px rgba(104, 144, 77, 0.2)",
        "card_radius": "14px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "leaves",
        "best_deal_label": "🍃 COZY BARGAIN",
        "tracked_label": "SANCTUARY",
        "buy_button_prefix": "VISIT HAVEN",
    },
    "retro_arcade": {
        "id": "retro_arcade",
        "name": "Retro Arcade",
        "icon": "🕹️",
        "bg_body": "repeating-linear-gradient(90deg, rgba(45,212,191,0.01) 0px, rgba(45,212,191,0.01) 2px, transparent 2px, transparent 20px), linear-gradient(135deg, #0b0614 0%, #120a1f 60%, #1b0f2e 100%)",
        "bg_sidebar": "#07040c",
        "bg_card": "#1e1333",
        "bg_card_elevated": "#2a1a47",
        "bg_input": "#150c24",
        "text_primary": "#f9fafb",
        "text_secondary": "#cbd5e1",
        "text_muted": "#a78bfa",
        "border_color": "#332154",
        "border_subtle": "#23163a",
        "border_hover": "#2dd4bf",
        "accent_primary": "#2dd4bf",
        "accent_secondary": "#fb923c",
        "accent_bg": "rgba(45, 212, 191, 0.15)",
        "sale_color": "#fb923c",
        "sale_bg": "rgba(251, 146, 60, 0.15)",
        "warning_color": "#f43f5e",
        "btn_primary_bg": "#0d9488",
        "btn_primary_text": "#f9fafb",
        "btn_secondary_bg": "#261940",
        "btn_secondary_text": "#f9fafb",
        "shadow_card": "0 6px 18px rgba(0, 0, 0, 0.5)",
        "shadow_hover": "0 8px 24px rgba(45, 212, 191, 0.3)",
        "card_radius": "4px",
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
        "icon": "🧪",
        "bg_body": "radial-gradient(circle at 40% 60%, rgba(217, 119, 6, 0.08) 0%, transparent 50%), linear-gradient(135deg, #0c0705 0%, #150d0a 60%, #1f130f 100%)",
        "bg_sidebar": "#080403",
        "bg_card": "#231713",
        "bg_card_elevated": "#30201a",
        "bg_input": "#1a100d",
        "text_primary": "#fbf3eb",
        "text_secondary": "#d9c7bb",
        "text_muted": "#bfa89b",
        "border_color": "#3d2821",
        "border_subtle": "#2a1c17",
        "border_hover": "#d97706",
        "accent_primary": "#d97706",
        "accent_secondary": "#10b981",
        "accent_bg": "rgba(217, 119, 6, 0.15)",
        "sale_color": "#10b981",
        "sale_bg": "rgba(16, 185, 129, 0.15)",
        "warning_color": "#dc2626",
        "btn_primary_bg": "#b45309",
        "btn_primary_text": "#fbf3eb",
        "btn_secondary_bg": "#2c1e18",
        "btn_secondary_text": "#fbf3eb",
        "shadow_card": "0 8px 20px rgba(12, 7, 5, 0.5)",
        "shadow_hover": "0 10px 28px rgba(217, 119, 6, 0.25)",
        "card_radius": "8px",
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
        "icon": "🌌",
        "bg_body": "radial-gradient(circle at 50% 20%, rgba(129, 140, 248, 0.1) 0%, transparent 60%), linear-gradient(135deg, #030408 0%, #05070d 60%, #090e1a 100%)",
        "bg_sidebar": "#020305",
        "bg_card": "#0c101c",
        "bg_card_elevated": "#141a2e",
        "bg_input": "#080b14",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#8fa4c7",
        "border_color": "#182238",
        "border_subtle": "#101726",
        "border_hover": "#818cf8",
        "accent_primary": "#818cf8",
        "accent_secondary": "#38bdf8",
        "accent_bg": "rgba(129, 140, 248, 0.15)",
        "sale_color": "#38bdf8",
        "sale_bg": "rgba(56, 189, 248, 0.15)",
        "warning_color": "#f43f5e",
        "btn_primary_bg": "#4f46e5",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#121829",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 24px rgba(3, 4, 8, 0.6)",
        "shadow_hover": "0 12px 32px rgba(129, 140, 248, 0.25)",
        "card_radius": "12px",
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
        "bg_body": "linear-gradient(135deg, #04070b 0%, #060b12 60%, #0b1420 100%)",
        "bg_sidebar": "#020407",
        "bg_card": "#0d1724",
        "bg_card_elevated": "#142336",
        "bg_input": "#09101a",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbe1f5",
        "text_muted": "#8baac9",
        "border_color": "#182a40",
        "border_subtle": "#101d2c",
        "border_hover": "#38bdf8",
        "accent_primary": "#38bdf8",
        "accent_secondary": "#22d3ee",
        "accent_bg": "rgba(56, 189, 248, 0.15)",
        "sale_color": "#22d3ee",
        "sale_bg": "rgba(34, 211, 238, 0.15)",
        "warning_color": "#ef4444",
        "btn_primary_bg": "#0284c7",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#122033",
        "btn_secondary_text": "#f8fafc",
        "shadow_card": "0 8px 20px rgba(4, 7, 11, 0.5)",
        "shadow_hover": "0 10px 28px rgba(56, 189, 248, 0.25)",
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
        "bg_body": "linear-gradient(135deg, #050506 0%, #09090b 60%, #111114 100%)",
        "bg_sidebar": "#030304",
        "bg_card": "#121215",
        "bg_card_elevated": "#1c1c21",
        "bg_input": "#0d0d0f",
        "text_primary": "#e4e4e7",
        "text_secondary": "#a1a1aa",
        "text_muted": "#71717a",
        "border_color": "#242429",
        "border_subtle": "#18181b",
        "border_hover": "#991b1b",
        "accent_primary": "#991b1b",
        "accent_secondary": "#ef4444",
        "accent_bg": "rgba(153, 27, 27, 0.15)",
        "sale_color": "#ef4444",
        "sale_bg": "rgba(239, 68, 68, 0.15)",
        "warning_color": "#f59e0b",
        "btn_primary_bg": "#7f1d1d",
        "btn_primary_text": "#e4e4e7",
        "btn_secondary_bg": "#18181c",
        "btn_secondary_text": "#e4e4e7",
        "shadow_card": "0 8px 24px rgba(0, 0, 0, 0.7)",
        "shadow_hover": "0 10px 28px rgba(153, 27, 27, 0.3)",
        "card_radius": "4px",
        "button_radius": "4px",
        "input_radius": "4px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "⚠ SLASHED PRICE",
        "tracked_label": "SURVIVAL KIT",
        "buy_button_prefix": "ENTER STORE",
    },
    "pastel_gamer": {
        "id": "pastel_gamer",
        "name": "Pastel Gamer",
        "icon": "☁️",
        "bg_body": "linear-gradient(135deg, #0e0c15 0%, #14121e 60%, #1c1929 100%)",
        "bg_sidebar": "#09080e",
        "bg_card": "#201c30",
        "bg_card_elevated": "#2d2745",
        "bg_input": "#181524",
        "text_primary": "#faf5ff",
        "text_secondary": "#dbd3ed",
        "text_muted": "#b8adcf",
        "border_color": "#332d4a",
        "border_subtle": "#252038",
        "border_hover": "#c084fc",
        "accent_primary": "#c084fc",
        "accent_secondary": "#38bdf8",
        "accent_bg": "rgba(192, 132, 252, 0.15)",
        "sale_color": "#38bdf8",
        "sale_bg": "rgba(56, 189, 248, 0.15)",
        "warning_color": "#f472b6",
        "btn_primary_bg": "#9333ea",
        "btn_primary_text": "#ffffff",
        "btn_secondary_bg": "#28233c",
        "btn_secondary_text": "#faf5ff",
        "shadow_card": "0 8px 20px rgba(14, 12, 21, 0.4)",
        "shadow_hover": "0 12px 28px rgba(192, 132, 252, 0.25)",
        "card_radius": "14px",
        "button_radius": "8px",
        "input_radius": "8px",
        "font_family": "'Inter', -apple-system, sans-serif",
        "particle_type": "none",
        "best_deal_label": "☁️ COMFY OFFER",
        "tracked_label": "COZY CORNER",
        "buy_button_prefix": "TAKE A LOOK",
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
                opacity: 0.35;
                animation: sakuraFall 12s linear infinite;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes sakuraFall {
                0% { transform: translateY(0) rotate(0deg); opacity: 0.35; }
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
                opacity: 0.4;
                animation: starTwinkle 4s ease-in-out infinite alternate;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes starTwinkle {
                0% { opacity: 0.1; transform: scale(0.8); }
                100% { opacity: 0.75; transform: scale(1.3); }
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
                opacity: 0.3;
                animation: emberRise 8s ease-in-out infinite;
                pointer-events: none;
                z-index: 0;
            }
            @keyframes emberRise {
                0% { transform: translateY(0); opacity: 0.1; }
                100% { transform: translateY(-80vh); opacity: 0.6; }
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
                opacity: 0.3;
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
    .stApp {{
        background: {t["bg_body"]} !important;
        color: {t["text_primary"]} !important;
        font-family: {t["font_family"]} !important;
        transition: background 0.35s ease-in-out, color 0.35s ease-in-out;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
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
