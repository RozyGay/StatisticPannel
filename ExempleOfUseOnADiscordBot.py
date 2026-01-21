import os,random,aiohttp,discord
from discord import app_commands
from discord.ext import commands
from typing import Optional,List,Dict

DISCORD_TOKEN="YOUR TOKEN OF DISCORD BOT HERE"
SUPABASE_URL="YOUR SUBABASE URL"
SUPABASE_KEY="YOUR SUBABASE KEY"

HEADERS={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}"}

LOCALES={
    "en":{
        "stats_title":"📊 Player Statistics","steam_id":"🆔 Steam ID","kills":"⚔️ Kills","deaths":"💀 Deaths","kdr":"📈 K/D Ratio","playtime":"⏱️ Playtime","last_seen":"🕐 Last Seen Online","no_player_nick":"```❌ No player found with nickname: {nick}```","no_player_steam":"```❌ No player found with SteamID: {steam}```","top_title":"🏆 Top 5 — {cat}","no_data":"📭 No data available","server_title":"🌐 Global Server Statistics","total_kills":"⚔️ Total Kills","total_deaths":"💀 Total Deaths","total_playtime":"⏱️ Total Playtime","total_players":"👥 Registered Players","lang_set":"✅ Language set to **English**","h":"h","m":"m","s":"s","kills_word":"kills","deaths_word":"deaths","cat_playtime":"Playtime","cat_kills":"Kills","cat_deaths":"Deaths","cat_kdr":"K/D Ratio","footer":"Requested by {user}","compare_title":"⚔️ Player Comparison","vs":"VS","winner":"🏆 Winner","tie":"🤝 It's a tie!","no_second":"❌ Second player not found","random_title":"🎲 Random Player","help_title":"📖 Available Commands","help_desc":"```/track_player — Search player by nickname\n/track_steamid — Search player by SteamID\n/top — Show top 5 players\n/server_stats — Global statistics\n/compare — Compare two players\n/random_player — Random player stats\n/language — Change language\n/help — This message```"
    },
    "ru":{
        "stats_title":"📊 Статистика игрока","steam_id":"🆔 Steam ID","kills":"⚔️ Убийства","deaths":"💀 Смерти","kdr":"📈 K/D Соотношение","playtime":"⏱️ Время в игре","last_seen":"🕐 Последний визит","no_player_nick":"```❌ Игрок с ником не найден: {nick}```","no_player_steam":"```❌ Игрок со SteamID не найден: {steam}```","top_title":"🏆 Топ 5 — {cat}","no_data":"📭 Данные отсутствуют","server_title":"🌐 Глобальная статистика сервера","total_kills":"⚔️ Всего убийств","total_deaths":"💀 Всего смертей","total_playtime":"⏱️ Общее время игры","total_players":"👥 Зарегистрировано игроков","lang_set":"✅ Язык установлен: **Русский**","h":"ч","m":"м","s":"с","kills_word":"убийств","deaths_word":"смертей","cat_playtime":"Времени","cat_kills":"Убийствам","cat_deaths":"Смертям","cat_kdr":"K/D Соотношению","footer":"Запросил {user}","compare_title":"⚔️ Сравнение игроков","vs":"ПРОТИВ","winner":"🏆 Победитель","tie":"🤝 Ничья!","no_second":"❌ Второй игрок не найден","random_title":"🎲 Случайный игрок","help_title":"📖 Доступные команды","help_desc":"```/track_player — Поиск игрока по нику\n/track_steamid — Поиск по SteamID\n/top — Топ 5 игроков\n/server_stats — Общая статистика\n/compare — Сравнить двух игроков\n/random_player — Случайный игрок\n/language — Сменить язык\n/help — Это сообщение```"
    }
}

COLORS={"stats":0x5865F2,"top":0xFEE75C,"server":0x57F287,"error":0xED4245,"compare":0xEB459E,"random":0x9B59B6,"help":0x3498DB}

user_langs:Dict[int,str]={}
session:Optional[aiohttp.ClientSession]=None

def L(uid:int,key:str,**kw)->str:return LOCALES[user_langs.get(uid,"en")].get(key,"???").format(**kw)if kw else LOCALES[user_langs.get(uid,"en")].get(key,"???")

def fmt_time(sec:int,uid:int)->str:h,m,s=sec//3600,(sec%3600)//60,sec%60;lc=user_langs.get(uid,"en");return f"{h}{LOCALES[lc]['h']} {m}{LOCALES[lc]['m']} {s}{LOCALES[lc]['s']}"

def calc_kdr(k:int,d:int)->float:return k/d if d>0 else float(k)

def make_bar(val:int,max_val:int,length:int=10)->str:filled=int((val/max_val)*length)if max_val>0 else 0;return "█"*filled+"░"*(length-filled)

def make_embed(title:str,color:int,uid:int,desc:str=None)->discord.Embed:e=discord.Embed(title=title,description=desc,color=color,timestamp=discord.utils.utcnow());e.set_footer(text=L(uid,"footer",user="User"),icon_url="https://cdn.discordapp.com/embed/avatars/0.png");return e

intents=discord.Intents.default()
bot=commands.Bot(command_prefix="!",intents=intents)

@bot.event
async def on_ready():await bot.tree.sync();print(f"✨ {bot.user} is online!")

@bot.event
async def on_connect():
    global session
    if session is None:session=aiohttp.ClientSession()

@bot.event
async def on_disconnect():
    global session
    if session:await session.close();session=None

async def db_get(path:str)->List[dict]:
    async with session.get(f"{SUPABASE_URL}/rest/v1/{path}",headers=HEADERS)as r:return await r.json()if r.status==200 else[]

async def db_count(tbl:str)->int:return len(await db_get(f"{tbl}?select=steam_id"))

async def ac_players(inter:discord.Interaction,cur:str):
    if not cur:return[]
    async with session.get(f"{SUPABASE_URL}/rest/v1/player_stats?nickname=ilike.%25{cur}%25&select=nickname&limit=10",headers=HEADERS)as r:
        if r.status!=200:return[]
        data=await r.json()
    return[app_commands.Choice(name=f"🎮 {p['nickname']}",value=p["nickname"])for p in data if"nickname"in p][:10]

def build_stats_embed(p:dict,uid:int,clr:int)->discord.Embed:
    k,d,pt=p.get("kills",0),p.get("deaths",0),p.get("total_play_seconds",0)
    kdr=calc_kdr(k,d)
    e=make_embed(f"{L(uid,'stats_title')}",clr,uid)
    e.add_field(name="👤 Nickname",value=f"```{p.get('nickname','Unknown')}```",inline=False)
    e.add_field(name=L(uid,"steam_id"),value=f"`{p.get('steam_id','N/A')}`",inline=False)
    e.add_field(name=L(uid,"kills"),value=f"```yaml\n{k}```",inline=True)
    e.add_field(name=L(uid,"deaths"),value=f"```yaml\n{d}```",inline=True)
    e.add_field(name=L(uid,"kdr"),value=f"```fix\n{kdr:.2f}```",inline=True)
    e.add_field(name=L(uid,"playtime"),value=f"```{fmt_time(pt,uid)}```",inline=True)
    e.add_field(name=L(uid,"last_seen"),value=f"```{p.get('last_seen_utc','N/A')}```",inline=True)
    e.add_field(name="📊 Performance",value=f"`{make_bar(k,k+d,20)}` {k}/{k+d}",inline=False)
    return e

@bot.tree.command(name="language",description="🌐 Change bot language / Сменить язык бота")
@app_commands.choices(lang=[app_commands.Choice(name="🇬🇧 English",value="en"),app_commands.Choice(name="🇷🇺 Русский",value="ru")])
async def language(inter:discord.Interaction,lang:app_commands.Choice[str]):
    user_langs[inter.user.id]=lang.value
    e=discord.Embed(title="🌐 Language / Язык",description=L(inter.user.id,"lang_set"),color=0x5865F2)
    await inter.response.send_message(embed=e,ephemeral=True)

@bot.tree.command(name="help",description="📖 Show all commands / Показать все команды")
async def help_cmd(inter:discord.Interaction):
    uid=inter.user.id
    e=make_embed(L(uid,"help_title"),COLORS["help"],uid,L(uid,"help_desc"))
    e.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await inter.response.send_message(embed=e)

@bot.tree.command(name="track_player",description="🔍 Find player by nickname / Найти игрока по нику")
@app_commands.autocomplete(nickname=ac_players)
async def track_player(inter:discord.Interaction,nickname:str):
    await inter.response.defer()
    uid=inter.user.id
    data=await db_get(f"player_stats?nickname=ilike.%25{nickname}%25&select=*")
    if not data:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_player_nick",nick=nickname),color=COLORS["error"]));return
    await inter.followup.send(embed=build_stats_embed(data[0],uid,COLORS["stats"]))

@bot.tree.command(name="track_steamid",description="🔍 Find player by SteamID / Найти игрока по SteamID")
async def track_steamid(inter:discord.Interaction,steamid:str):
    await inter.response.defer()
    uid=inter.user.id
    data=await db_get(f"player_stats?steam_id=eq.{steamid}&select=*")
    if not data:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_player_steam",steam=steamid),color=COLORS["error"]));return
    await inter.followup.send(embed=build_stats_embed(data[0],uid,COLORS["stats"]))

@bot.tree.command(name="top",description="🏆 Show top 5 players / Показать топ 5 игроков")
@app_commands.choices(category=[app_commands.Choice(name="⏱️ Playtime",value="playtime"),app_commands.Choice(name="⚔️ Kills",value="kills"),app_commands.Choice(name="💀 Deaths",value="deaths"),app_commands.Choice(name="📈 K/D Ratio",value="kdr")])
async def top(inter:discord.Interaction,category:app_commands.Choice[str]):
    await inter.response.defer()
    uid,cat=inter.user.id,category.value
    cat_names={"playtime":L(uid,"cat_playtime"),"kills":L(uid,"cat_kills"),"deaths":L(uid,"cat_deaths"),"kdr":L(uid,"cat_kdr")}
    medals=["🥇","🥈","🥉","4️⃣","5️⃣"]
    if cat=="playtime":data=await db_get("player_stats?select=nickname,total_play_seconds&order=total_play_seconds.desc&limit=5");lines=[f"{medals[i]} **{p['nickname']}**\n└ `{fmt_time(p['total_play_seconds'],uid)}`"for i,p in enumerate(data)]
    elif cat=="kills":data=await db_get("player_stats?select=nickname,kills&order=kills.desc&limit=5");lines=[f"{medals[i]} **{p['nickname']}**\n└ `{p['kills']} {L(uid,'kills_word')}`"for i,p in enumerate(data)]
    elif cat=="deaths":data=await db_get("player_stats?select=nickname,deaths&order=deaths.desc&limit=5");lines=[f"{medals[i]} **{p['nickname']}**\n└ `{p['deaths']} {L(uid,'deaths_word')}`"for i,p in enumerate(data)]
    else:data=await db_get("player_stats?select=nickname,kills,deaths");pls=sorted([(p.get("nickname","?"),calc_kdr(p.get("kills",0),p.get("deaths",0)))for p in data],key=lambda x:x[1],reverse=True)[:5];lines=[f"{medals[i]} **{n}**\n└ `KDR: {k:.2f}`"for i,(n,k)in enumerate(pls)]
    e=make_embed(L(uid,"top_title",cat=cat_names.get(cat,cat)),COLORS["top"],uid,"\n\n".join(lines)if lines else L(uid,"no_data"))
    await inter.followup.send(embed=e)

@bot.tree.command(name="server_stats",description="🌐 Show global statistics / Показать глобальную статистику")
async def server_stats(inter:discord.Interaction):
    await inter.response.defer()
    uid=inter.user.id
    data=await db_get("player_stats?select=kills,deaths,total_play_seconds")
    if not data:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_data"),color=COLORS["error"]));return
    tk,td,tp=sum(p.get("kills",0)for p in data),sum(p.get("deaths",0)for p in data),sum(p.get("total_play_seconds",0)for p in data)
    pc=await db_count("player_stats")
    e=make_embed(L(uid,"server_title"),COLORS["server"],uid)
    e.add_field(name=L(uid,"total_kills"),value=f"```yaml\n{tk:,}```",inline=True)
    e.add_field(name=L(uid,"total_deaths"),value=f"```yaml\n{td:,}```",inline=True)
    e.add_field(name=L(uid,"total_playtime"),value=f"```{fmt_time(tp,uid)}```",inline=False)
    e.add_field(name=L(uid,"total_players"),value=f"```yaml\n{pc:,}```",inline=False)
    e.add_field(name="📊 Kill/Death Balance",value=f"`{make_bar(tk,tk+td,25)}`\n⚔️ {tk:,} vs 💀 {td:,}",inline=False)
    await inter.followup.send(embed=e)

@bot.tree.command(name="compare",description="⚔️ Compare two players / Сравнить двух игроков")
@app_commands.autocomplete(player1=ac_players,player2=ac_players)
async def compare(inter:discord.Interaction,player1:str,player2:str):
    await inter.response.defer()
    uid=inter.user.id
    d1,d2=await db_get(f"player_stats?nickname=ilike.%25{player1}%25&select=*"),await db_get(f"player_stats?nickname=ilike.%25{player2}%25&select=*")
    if not d1:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_player_nick",nick=player1),color=COLORS["error"]));return
    if not d2:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_second"),color=COLORS["error"]));return
    p1,p2=d1[0],d2[0]
    k1,d1_,k2,d2_=p1.get("kills",0),p1.get("deaths",0),p2.get("kills",0),p2.get("deaths",0)
    kdr1,kdr2=calc_kdr(k1,d1_),calc_kdr(k2,d2_)
    w=p1.get("nickname","?")if kdr1>kdr2 else(p2.get("nickname","?")if kdr2>kdr1 else None)
    e=make_embed(L(uid,"compare_title"),COLORS["compare"],uid)
    e.add_field(name=f"🔴 {p1.get('nickname','?')}",value=f"```yaml\n⚔️ {k1}\n💀 {d1_}\n📈 {kdr1:.2f}```",inline=True)
    e.add_field(name=f"⚡ {L(uid,'vs')}",value="```\n───────```",inline=True)
    e.add_field(name=f"🔵 {p2.get('nickname','?')}",value=f"```yaml\n⚔️ {k2}\n💀 {d2_}\n📈 {kdr2:.2f}```",inline=True)
    e.add_field(name=L(uid,"winner")if w else"",value=f"**🎖️ {w}**"if w else L(uid,"tie"),inline=False)
    await inter.followup.send(embed=e)

@bot.tree.command(name="random_player",description="🎲 Get random player stats / Случайный игрок")
async def random_player(inter:discord.Interaction):
    await inter.response.defer()
    uid=inter.user.id
    data=await db_get("player_stats?select=*")
    if not data:await inter.followup.send(embed=discord.Embed(description=L(uid,"no_data"),color=COLORS["error"]));return
    p=random.choice(data)
    e=build_stats_embed(p,uid,COLORS["random"])
    e.title=f"🎲 {L(uid,'random_title')}"
    await inter.followup.send(embed=e)

if __name__=="__main__":bot.run(DISCORD_TOKEN)
