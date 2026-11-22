"""Discord Bot for GameTracker.

Provides rich gaming-assistant slash commands:
- /tracked: Show all tracked games with prices and sale badges
- /game <name>: Show deep details, cover art, discount, and direct store button
- /owned: Show purchased games in My Library
- /deals: Show currently discounted tracked games sorted by highest discount
- /search <query>: Search tracked collection
- /refresh: Trigger price refresh (guarded by authorization & cooldown)
- /help: Display all available commands
"""
from __future__ import annotations

import os
import sys
import logging
from typing import Any, Optional, Sequence

import discord
from discord import app_commands
from discord.ext import commands

from bot_service import get_service, GameTrackerService

logger = logging.getLogger("discord_bot")

DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes


def get_authorized_user_ids() -> set[int]:
    """Load authorized Discord user IDs from environment variables or Streamlit secrets."""
    raw = os.environ.get("DISCORD_AUTHORIZED_USERS", "")
    if not raw:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                raw = str(st.secrets.get("DISCORD_AUTHORIZED_USERS", ""))
        except Exception:
            pass

    user_ids: set[int] = set()
    for item in raw.replace(",", " ").split():
        item = item.strip()
        if item.isdigit():
            user_ids.add(int(item))
    return user_ids


class StoreButtonView(discord.ui.View):
    """Interactive button linking to the game's store page."""

    def __init__(self, store: str, url: str):
        super().__init__(timeout=None)
        if url and (url.startswith("http://") or url.startswith("https://")):
            emoji_map = {
                "steam": "🎮",
                "epic": "⚡",
                "gog": "👾",
            }
            emoji = emoji_map.get(store.lower(), "🛒")
            label = f"Open on {store.capitalize()}" if store else "Open Store"
            self.add_item(discord.ui.Button(label=label, url=url, emoji=emoji))


def build_tracked_embed(games: Sequence[dict[str, Any]]) -> discord.Embed:
    """Format tracked games into a clean, game-themed Discord embed."""
    embed = discord.Embed(
        title="🎮 GameTracker — Tracked Games Radar",
        description=f"Currently tracking **{len(games)}** game listing(s) across connected stores.",
        color=discord.Color.blurple(),
    )
    if not games:
        embed.description = "No games are currently being tracked. Add games from the web dashboard!"
        return embed

    # Display up to 25 fields (Discord max fields per embed is 25)
    for g in games[:25]:
        name = g.get("name") or g.get("title") or "Unknown Game"
        store = (g.get("store") or "Store").capitalize()
        price = g.get("current_price_str") or "N/A"
        lowest = g.get("lowest_price_str") or "N/A"
        discount = g.get("discount_percent") or 0
        is_sale = bool(g.get("is_on_sale") or (discount and float(discount) > 0))

        status_str = f"🔥 **ON SALE (-{discount}%)**" if is_sale else "🟢 Regular Price"
        val = f"**Store:** {store}\n**Price:** {price} *(Low: {lowest})*\n**Status:** {status_str}"
        embed.add_field(name=f"🕹️ {name}", value=val, inline=True)

    if len(games) > 25:
        embed.set_footer(text=f"Showing 25 of {len(games)} total tracked games.")
    else:
        embed.set_footer(text="GameTracker Radar · Powered by GameTracker Bot")
    return embed


def build_game_embed(game: dict[str, Any]) -> tuple[discord.Embed, Optional[discord.ui.View]]:
    """Format single game details into a rich Discord embed with direct store button."""
    name = game.get("name", "Unknown Game")
    store = (game.get("store") or "Store").capitalize()
    c_price = game.get("current_price_str", "N/A")
    low_price = game.get("lowest_price_str", "N/A")
    orig_price = game.get("original_price_str")
    discount = game.get("discount_percent", 0)
    is_sale = game.get("is_on_sale", False)
    last_checked = game.get("last_checked", "Unknown")
    url = game.get("url", "")
    cover = game.get("cover_image", "")

    color = discord.Color.red() if is_sale else discord.Color.blue()
    embed = discord.Embed(
        title=f"🎮 {name}",
        url=url if url else None,
        color=color,
    )
    if cover and cover.startswith("http"):
        embed.set_thumbnail(url=cover)

    embed.add_field(name="Store", value=f"🏷️ {store}", inline=True)
    embed.add_field(name="Current Price", value=f"💰 **{c_price}**", inline=True)
    embed.add_field(name="Lowest Recorded", value=f"📉 {low_price}", inline=True)

    if is_sale:
        embed.add_field(name="Discount", value=f"🔥 **-{discount}% OFF**", inline=True)
        if orig_price:
            embed.add_field(name="Original Price", value=f"~~{orig_price}~~", inline=True)
        embed.add_field(name="Status", value="🎉 **ON SALE NOW!**", inline=True)
    else:
        embed.add_field(name="Status", value="🟢 Regular Price", inline=True)

    if game.get("target_price"):
        embed.add_field(name="Target Price", value=f"🎯 {game.get('target_price_str')}", inline=True)

    embed.add_field(name="Last Checked", value=f"⏱️ {last_checked}", inline=False)
    embed.set_footer(text="GameTracker · Your Personal Loot Radar")

    view = StoreButtonView(store, url) if url else None
    return embed, view


def build_owned_embed(purchased: Sequence[dict[str, Any]]) -> discord.Embed:
    """Format purchased games into an attractive Loot Vault embed."""
    embed = discord.Embed(
        title="📚 My Library — Loot Vault",
        description=f"You own **{len(purchased)}** purchased game(s) in your personal library.",
        color=discord.Color.green(),
    )
    if not purchased:
        embed.description = "Your Loot Vault is empty. Mark games as purchased on GameTracker to log your collection!"
        return embed

    for p in purchased[:25]:
        name = p.get("name", "Unknown Game")
        store = (p.get("store") or "Store").capitalize()
        p_date = p.get("purchase_date", "Unknown")
        p_price = p.get("purchase_price_str", "Not recorded")
        val = f"**Store:** {store}\n**Acquired:** {p_date}\n**Purchase Price:** {p_price}"
        embed.add_field(name=f"📦 {name}", value=val, inline=True)

    if len(purchased) > 25:
        embed.set_footer(text=f"Showing 25 of {len(purchased)} owned games.")
    else:
        embed.set_footer(text="GameTracker Loot Vault")
    return embed


def build_deals_embed(deals: Sequence[dict[str, Any]]) -> discord.Embed:
    """Format active deals into a high-visibility sales embed sorted by discount."""
    embed = discord.Embed(
        title="🔥 GameTracker — Current Hot Deals",
        description=f"Found **{len(deals)}** active deal(s) across your tracked games radar!",
        color=discord.Color.gold(),
    )
    if not deals:
        embed.description = "No tracked games are currently on sale. Check back soon for new price drops!"
        return embed

    for d in deals[:25]:
        name = d.get("name", "Unknown Game")
        store = (d.get("store") or "Store").capitalize()
        price = d.get("current_price_str", "N/A")
        lowest = d.get("lowest_price_str", "N/A")
        discount = d.get("discount_percent", 0)

        val = f"**Store:** {store}\n**Discount:** 🔥 **-{discount}%**\n**Sale Price:** **{price}** *(Low: {lowest})*"
        embed.add_field(name=f"⚡ {name}", value=val, inline=True)

    if len(deals) > 25:
        embed.set_footer(text=f"Showing top 25 deals out of {len(deals)} total discounts.")
    else:
        embed.set_footer(text="GameTracker Deals · Sorted by Highest Discount")
    return embed


def build_search_embed(query: str, matches: Sequence[dict[str, Any]]) -> discord.Embed:
    """Format search results into an embed."""
    embed = discord.Embed(
        title=f"🔍 Search Results for '{query}'",
        description=f"Found **{len(matches)}** matching tracked game(s).",
        color=discord.Color.teal(),
    )
    if not matches:
        embed.description = f"No tracked games matched '**{query}**'. Try searching by partial title or store."
        return embed

    for m in matches[:25]:
        name = m.get("name", "Unknown Game")
        store = (m.get("store") or "Store").capitalize()
        price = m.get("current_price_str", "N/A")
        discount = m.get("discount_percent", 0)
        status = f"🔥 -{discount}%" if m.get("is_on_sale") else "🟢 Regular"
        val = f"**Store:** {store} · **Price:** {price} ({status})"
        embed.add_field(name=f"🎮 {name}", value=val, inline=True)

    return embed


def build_help_embed() -> discord.Embed:
    """Format Discord slash command help documentation."""
    embed = discord.Embed(
        title="🤖 GameTracker Bot — Command Guide",
        description="Your personal gaming assistant for tracking store deals, prices, and your game library.",
        color=discord.Color.purple(),
    )
    commands_list = [
        ("`/tracked`", "List all games currently on your radar with prices and store badges."),
        ("`/game <name>`", "View deep details, store links, artwork, and lowest price for a specific game."),
        ("`/owned`", "Browse your personal Loot Vault (purchased games, dates, and spending)."),
        ("`/deals`", "See all games currently on sale, sorted by highest discount percentage."),
        ("`/search <query>`", "Search your tracked games collection by name, store, or tag."),
        ("`/refresh`", "Request an immediate price refresh (protected by authorized user role & 5-min cooldown)."),
        ("`/help`", "Display this command guide."),
    ]
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.set_footer(text="GameTracker Bot · Stay updated on the lowest game prices!")
    return embed


def create_discord_bot(
    service: Optional[GameTrackerService] = None,
    authorized_users: Optional[set[int]] = None,
) -> commands.Bot:
    """Instantiate and configure the Discord bot with slash commands."""
    svc = service or get_service()
    auth_users = authorized_users if authorized_users is not None else get_authorized_user_ids()

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready() -> None:
        logger.info("GameTracker Discord Bot logged in as %s (ID: %s)", bot.user, bot.user.id if bot.user else "N/A")
        try:
            synced = await bot.tree.sync()
            logger.info("Successfully synced %d application slash commands.", len(synced))
        except Exception as e:
            logger.error("Failed to sync slash commands: %s", e)

    @bot.tree.command(name="tracked", description="Show all games currently being tracked on your radar.")
    async def slash_tracked(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        games = svc.get_tracked_games()
        # Enrich games with formatted strings
        enriched = []
        for g in games:
            details = svc.get_game_details(g.get("name") or g.get("id", ""))
            enriched.append(details or g)
        embed = build_tracked_embed(enriched)
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="game", description="Show full details, discount, and links for a specific game.")
    @app_commands.describe(name="The name or title of the game to look up")
    async def slash_game(interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        details = svc.get_game_details(name)
        if not details:
            await interaction.followup.send(
                f"❌ Could not find '**{name}**' in your tracked games radar. Use `/tracked` or `/search` to find games.",
                ephemeral=True,
            )
            return

        embed, view = build_game_embed(details)
        if view:
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed)

    @bot.tree.command(name="owned", description="Show games in your personal Loot Vault (My Library).")
    async def slash_owned(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        purchased = svc.get_purchased_games()
        embed = build_owned_embed(purchased)
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="deals", description="Show all currently discounted games sorted by highest discount.")
    async def slash_deals(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        deals = svc.get_active_deals()
        embed = build_deals_embed(deals)
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="search", description="Search tracked games by title, store, or tag.")
    @app_commands.describe(query="Keywords to search for")
    async def slash_search(interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()
        matches = svc.search_tracked_games(query)
        embed = build_search_embed(query, matches)
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="refresh", description="Request an application-wide price refresh across all stores.")
    async def slash_refresh(interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        user_id = interaction.user.id
        is_auth = (user_id in auth_users) if auth_users else True  # If no IDs configured, allow server admins / users

        res = svc.refresh_all_prices(
            requester_id=f"discord_{user_id}",
            is_authorized=is_auth,
            cooldown_seconds=DEFAULT_COOLDOWN_SECONDS,
        )

        if not res.get("success"):
            status = res.get("status")
            if status == "unauthorized":
                await interaction.followup.send(
                    f"🚫 **Access Denied**: Only authorized GameTracker operators can trigger application-wide price refreshes.",
                    ephemeral=True,
                )
            elif status == "cooldown":
                remaining = res.get("remaining_seconds", 0)
                mins = (remaining // 60) + 1
                await interaction.followup.send(
                    f"⏳ **Cooldown Active**: Price refresh was executed recently. Please wait approximately **{mins} minute(s)** ({remaining}s) before trying again.",
                    ephemeral=True,
                )
            elif status == "busy":
                await interaction.followup.send(
                    "⚠️ **Busy**: A price refresh job is currently in progress. Please wait a moment.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(f"❌ {res.get('message', 'Refresh failed.')}", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔄 Price Refresh Completed!",
            description=res.get("message", "All prices refreshed successfully."),
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="help", description="Show all supported GameTracker bot commands.")
    async def slash_help(interaction: discord.Interaction) -> None:
        embed = build_help_embed()
        await interaction.response.send_message(embed=embed)

    return bot


def run_bot() -> None:
    """Run the Discord bot directly from CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                token = str(st.secrets.get("DISCORD_BOT_TOKEN", ""))
        except Exception:
            pass

    if not token or token.strip().lower() in ("placeholder", "your_discord_bot_token"):
        logger.error("DISCORD_BOT_TOKEN is not set or contains a placeholder. Exiting.")
        sys.exit(1)

    bot = create_discord_bot()
    bot.run(token)


if __name__ == "__main__":
    run_bot()
