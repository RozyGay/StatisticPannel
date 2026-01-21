import os
import random
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

DISCORD_TOKEN = "YOUR TOKEN OF DISCORD BOT HERE"
SUPABASE_URL = "YOUR SUBABASE URL"
SUPABASE_KEY = "YOUR SUBABASE KEY"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def format_playtime(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
session: Optional[aiohttp.ClientSession] = None

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot ready as {bot.user}")

@bot.event
async def on_connect():
    global session
    if session is None:
        session = aiohttp.ClientSession()

@bot.event
async def on_disconnect():
    global session
    if session:
        await session.close()
        session = None

async def supabase_get(path: str) -> List[dict]:
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    async with session.get(url, headers=HEADERS) as resp:
        if resp.status == 200:
            return await resp.json()
        return []

async def supabase_count(table: str) -> int:
    data = await supabase_get(f"{table}?select=steam_id")
    return len(data)

async def autocomplete_players(interaction: discord.Interaction, current: str):
    if not current:
        return []
    url = f"{SUPABASE_URL}/rest/v1/player_stats?nickname=ilike.%25{current}%25&select=nickname&limit=5"
    async with session.get(url, headers=HEADERS) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    return [
        app_commands.Choice(name=p["nickname"], value=p["nickname"])
        for p in data if "nickname" in p
    ]

@bot.tree.command(name="track_player", description="Show statistics of a player by nickname")
@app_commands.autocomplete(nickname=autocomplete_players)
async def track_player(interaction: discord.Interaction, nickname: str):
    await interaction.response.defer()
    data = await supabase_get(f"player_stats?nickname=ilike.%25{nickname}%25&select=*")
    if not data:
        await interaction.followup.send(f"No player found with nickname `{nickname}`.")
        return

    p = data[0]
    kills = p.get("kills", 0)
    deaths = p.get("deaths", 0)
    kdr = kills / deaths if deaths > 0 else kills

    embed = discord.Embed(title=f"Stats of {p.get('nickname','?')}", color=discord.Color.blue())
    embed.add_field(name="Steam ID", value=p.get("steam_id","N/A"), inline=False)
    embed.add_field(name="Kills", value=str(kills), inline=True)
    embed.add_field(name="Deaths", value=str(deaths), inline=True)
    embed.add_field(name="KDR", value=f"{kdr:.2f}", inline=True)
    embed.add_field(name="Playtime", value=format_playtime(p.get("total_play_seconds",0)), inline=False)
    embed.add_field(name="Last Seen", value=str(p.get("last_seen_utc","N/A")), inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="track_steamid", description="Show statistics of a player by SteamID")
async def track_steamid(interaction: discord.Interaction, steamid: str):
    await interaction.response.defer()
    data = await supabase_get(f"player_stats?steam_id=eq.{steamid}&select=*")
    if not data:
        await interaction.followup.send(f"No player found with SteamID `{steamid}`.")
        return

    p = data[0]
    kills = p.get("kills", 0)
    deaths = p.get("deaths", 0)
    kdr = kills / deaths if deaths > 0 else kills

    embed = discord.Embed(title=f"Stats of {p.get('nickname','?')}", color=discord.Color.green())
    embed.add_field(name="Steam ID", value=p.get("steam_id","N/A"), inline=False)
    embed.add_field(name="Kills", value=str(kills), inline=True)
    embed.add_field(name="Deaths", value=str(deaths), inline=True)
    embed.add_field(name="KDR", value=f"{kdr:.2f}", inline=True)
    embed.add_field(name="Playtime", value=format_playtime(p.get("total_play_seconds",0)), inline=False)
    embed.add_field(name="Last Seen", value=str(p.get("last_seen_utc","N/A")), inline=False)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="top", description="Show the top players")
@app_commands.choices(category=[
    app_commands.Choice(name="Playtime", value="playtime"),
    app_commands.Choice(name="Kills", value="kills"),
    app_commands.Choice(name="Deaths", value="deaths"),
    app_commands.Choice(name="KDR", value="kdr"),
])
async def top(interaction: discord.Interaction, category: app_commands.Choice[str]):
    await interaction.response.defer()
    cat = category.value

    if cat == "playtime":
        data = await supabase_get("player_stats?select=nickname,total_play_seconds&order=total_play_seconds.desc&limit=5")
        lines = [f"**{p['nickname']}** — {format_playtime(p['total_play_seconds'])}" for p in data]

    elif cat == "kills":
        data = await supabase_get("player_stats?select=nickname,kills&order=kills.desc&limit=5")
        lines = [f"**{p['nickname']}** — {p['kills']} kills" for p in data]

    elif cat == "deaths":
        data = await supabase_get("player_stats?select=nickname,deaths&order=deaths.desc&limit=5")
        lines = [f"**{p['nickname']}** — {p['deaths']} deaths" for p in data]

    else:
        data = await supabase_get("player_stats?select=nickname,kills,deaths")
        players = []
        for p in data:
            k = p.get("kills", 0)
            d = p.get("deaths", 0)
            kdr = k / d if d > 0 else k
            players.append((p.get("nickname","?"), kdr))
        players.sort(key=lambda x: x[1], reverse=True)
        lines = [f"**{name}** — KDR {kdr:.2f}" for name, kdr in players[:5]]

    embed = discord.Embed(title=f"Top {cat}", description="\n".join(lines) or "No data.", color=discord.Color.purple())
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="server_stats", description="Show global server statistics")
async def server_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    data = await supabase_get("player_stats?select=kills,deaths,total_play_seconds")
    if not data:
        await interaction.followup.send("No data found.")
        return

    total_kills = sum(p.get("kills", 0) for p in data)
    total_deaths = sum(p.get("deaths", 0) for p in data)
    total_playtime = sum(p.get("total_play_seconds", 0) for p in data)
    total_players = await supabase_count("player_stats")

    embed = discord.Embed(title="Server Statistics", color=discord.Color.gold())
    embed.add_field(name="Total Kills", value=str(total_kills))
    embed.add_field(name="Total Deaths", value=str(total_deaths))
    embed.add_field(name="Total Playtime", value=format_playtime(total_playtime), inline=False)
    embed.add_field(name="Total Registered Players", value=str(total_players), inline=False)

    await interaction.followup.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
