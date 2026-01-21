
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=220&section=header&text=StatisticPannel&fontSize=65&fontColor=ffffff&animation=twinkling" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/downloads/Konoaru384/StatisticPannel/total?color=0af&label=Downloads" />
  <img src="https://img.shields.io/github/v/release/Konoaru384/StatisticPannel?label=Latest%20Release" />
  <img src="https://img.shields.io/github/stars/Konoaru384/StatisticPannel?label=Stars&color=yellow" />
  <img src="https://img.shields.io/github/repo-size/Konoaru384/StatisticPannel?label=Repository%20Size" />
</p>

<h1 align="center">StatisticPannel Plugin</h1>

<p align="center" style="color: #888; font-size: 18px;">
StatisticPannel is an EXILED plugin that tracks player statistics (playtime, kills, deaths, KDR, last seen) and automatically syncs them to Subabase (Supabase).  
It can be used anywhere Subabase is available — websites, dashboards, external tools, and more.
</p>

<hr>

<h2 align="center">Created by</h2>

<table align="center">
  <tr>
    <td align="center" style="padding: 10px;">
      <strong>Konoaru</strong><br>
      <a href="https://github.com/Konoaru384">github.com/Konoaru384</a>
    </td>
  </tr>
</table>

---

# 📌 Core Features

<table>
  <tr>
    <th align="left">Feature</th>
    <th align="left">Description</th>
  </tr>

  <tr>
    <td>Player Statistics Tracking</td>
    <td>Tracks kills, deaths, KDR, total playtime, nickname updates, and last seen time.</td>
  </tr>

  <tr>
    <td>Subabase Sync</td>
    <td>Automatically sends all player statistics to your Subabase database.</td>
  </tr>

  <tr>
    <td>Web Integration</td>
    <td>Can be used anywhere Subabase works — websites, dashboards, external tools, etc.</td>
  </tr>

  <tr>
    <td>Example Website Included</td>
    <td>An example HTML file (<b>ExempleOfUseOnWebsite.html</b>) shows how to display stats on your own site.</td>
  </tr>
</table>

---

# 📥 Installation

1. Download the latest release from GitHub:  
   👉 https://github.com/Konoaru384/StatisticPannel

2. Put **StatisticPannel.dll** into:  
   ```
   EXILED/Plugins
   ```

3. Unzip **dependencies.zip** and put **Newtonsoft.Json.dll** into:  
   ```
   EXILED/Plugins/dependencies
   ```

4. Restart your server.

5. Configure the plugin using the generated config file.

---

# 🛠️ Subabase (Supabase) Setup Guide

StatisticPannel requires a Subabase (Supabase) database to store player statistics.

## 1. Create a Subabase Account

1. Go to: https://supabase.com  
2. Click **Start your project**  
3. Log in  
4. Create a new project  
5. Choose a password and region  
6. Wait for initialization  

---

## 2. Get Your Subabase URL + API Key

Inside your Subabase project:

1. Go to **Project Settings**  
2. Open **API**  
3. Copy:

- **Project URL** → used as `SupabaseUrl`
- **anon public key** → used as `SupabaseKey`

These must be placed in your plugin config.

---

## 3. Create the Required Database Table

Go to **SQL Editor** in Subabase and paste:

```sql
create table if not exists player_stats (
    steam_id text primary key,
    nickname text not null,
    total_play_seconds integer not null default 0,
    kills integer not null default 0,
    deaths integer not null default 0,
    last_seen_utc timestamptz not null default now()
);
```

Run the query.

---

# ⚙️ Configuration File

Your config will look like this:

```yaml
is_enabled: true
debug: false

supabase_url: "YOUR_SUBABASE_URL_HERE"
supabase_key: "YOUR_SUBABASE_KEY_HERE"
```

### Explanation:

| Field | Description |
|-------|-------------|
| `supabase_url` | Your Subabase project URL |
| `supabase_key` | Your public anon API key |
| `is_enabled` | Enables or disables the plugin |
| `debug` | Enables debug logs |

---

# 🌐 Using StatisticPannel on a Website

StatisticPannel can be used **anywhere Subabase works**, including:

- Google Sites  
- Custom HTML websites  
- GitHub Pages  
- Vercel / Netlify  
- Any JavaScript environment  

An example file is included:

```
ExempleOfUseOnWebsite.html
```

This file shows how to:

- Fetch player stats  
- Display top playtime, kills, deaths, KDR  
- Search players  
- Build a full statistics dashboard  

### Want to see a live example?

👉 https://sites.google.com/view/speed-dark-rp/statistique-joueur?authuser=0

---

# 💬 Support

For help or questions:

- Discord: **realkonoaru**  
- Discord Server: https://discord.gg/Bbx28xhrKE  
- EXILED Community also available

---

# 📄 License

This project is licensed under the MIT License.  
https://choosealicense.com/licenses/mit/

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=140&section=footer" />
</p>
