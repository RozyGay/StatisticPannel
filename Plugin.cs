using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using Exiled.API.Features;
using Exiled.API.Interfaces;
using Exiled.Events.EventArgs.Player;
using Exiled.Events.EventArgs.Server;
using Newtonsoft.Json;

namespace StatisticPanel
{
    public class StatsPlugin : Plugin<StatsConfig>
    {
        public override string Name => "StatisticPanel";
        public override string Author => "Konoara";
        public override Version Version => new Version(1, 0, 0);
        public override Version RequiredExiledVersion => new Version(9, 10, 0);

        private string DataPath;
        private Dictionary<string, PlayerStats> stats = new Dictionary<string, PlayerStats>();
        private static readonly HttpClient httpClient = new HttpClient();

        public override void OnEnabled()
        {
            DataPath = Path.Combine(Paths.Plugins, "StatisticPanel", "stats.json");
            Directory.CreateDirectory(Path.GetDirectoryName(DataPath));

            if (File.Exists(DataPath))
                stats = JsonConvert.DeserializeObject<Dictionary<string, PlayerStats>>(File.ReadAllText(DataPath))
                        ?? new Dictionary<string, PlayerStats>();

            Exiled.Events.Handlers.Player.Died += OnPlayerDied;
            Exiled.Events.Handlers.Player.Verified += OnPlayerJoin;
            Exiled.Events.Handlers.Player.Left += OnPlayerLeft;
            Exiled.Events.Handlers.Server.RoundEnded += OnRoundEnded;

            base.OnEnabled();
            Log.Info("StatisticPanel connected to Supabase");
        }

        public override void OnDisabled()
        {
            Exiled.Events.Handlers.Player.Died -= OnPlayerDied;
            Exiled.Events.Handlers.Player.Verified -= OnPlayerJoin;
            Exiled.Events.Handlers.Player.Left -= OnPlayerLeft;
            Exiled.Events.Handlers.Server.RoundEnded -= OnRoundEnded;

            SaveStats();
            base.OnDisabled();
        }

        private void OnPlayerJoin(VerifiedEventArgs ev)
        {
            string id = GetSteamId(ev.Player);

            if (!stats.ContainsKey(id))
            {
                stats[id] = new PlayerStats
                {
                    Nickname = ev.Player.Nickname,
                    LastJoin = DateTime.Now
                };
            }
            else
            {
                stats[id].Nickname = ev.Player.Nickname;
                stats[id].LastJoin = DateTime.Now;
            }

            SendStatsToSupabase(id, stats[id]);
        }

        private void OnPlayerLeft(LeftEventArgs ev)
        {
            string id = GetSteamId(ev.Player);

            if (stats.TryGetValue(id, out PlayerStats ps))
            {
                ps.TotalPlaySeconds += (int)(DateTime.Now - ps.LastJoin).TotalSeconds;
                ps.LastSeenUtc = DateTime.UtcNow;
                SendStatsToSupabase(id, ps);
            }

            SaveStats();
        }

        private void OnPlayerDied(DiedEventArgs ev)
        {
            string victimId = GetSteamId(ev.Player);

            if (!stats.ContainsKey(victimId))
                stats[victimId] = new PlayerStats { Nickname = ev.Player.Nickname };

            stats[victimId].Deaths++;
            stats[victimId].LastSeenUtc = DateTime.UtcNow;

            if (ev.Attacker != null && ev.Attacker != ev.Player)
            {
                string killerId = GetSteamId(ev.Attacker);

                if (!stats.ContainsKey(killerId))
                    stats[killerId] = new PlayerStats { Nickname = ev.Attacker.Nickname };

                stats[killerId].Kills++;
                stats[killerId].LastSeenUtc = DateTime.UtcNow;

                SendStatsToSupabase(killerId, stats[killerId]);
            }

            SaveStats();
            SendStatsToSupabase(victimId, stats[victimId]);
        }

        private void OnRoundEnded(RoundEndedEventArgs ev)
        {
            SaveStats();

            foreach (var kvp in stats)
                SendStatsToSupabase(kvp.Key, kvp.Value);
        }

        private string GetSteamId(Player p) => p.UserId.Replace("@steam", "");

        private void SaveStats()
        {
            File.WriteAllText(DataPath, JsonConvert.SerializeObject(stats, Formatting.Indented));
        }

        private async void SendStatsToSupabase(string steamId, PlayerStats ps)
        {
            if (string.IsNullOrWhiteSpace(Config.SupabaseUrl) || string.IsNullOrWhiteSpace(Config.SupabaseKey))
            {
                Log.Warn("Supabase configuration missing");
                return;
            }

            try
            {
                var json = JsonConvert.SerializeObject(new
                {
                    steam_id = steamId,
                    nickname = ps.Nickname,
                    total_play_seconds = ps.TotalPlaySeconds,
                    kills = ps.Kills,
                    deaths = ps.Deaths,
                    last_seen_utc = ps.LastSeenUtc.ToString("o")
                });

                var content = new StringContent(json, Encoding.UTF8, "application/json");
                var request = new HttpRequestMessage(HttpMethod.Post, $"{Config.SupabaseUrl}/rest/v1/player_stats?on_conflict=steam_id");
                request.Content = content;
                request.Headers.Add("apikey", Config.SupabaseKey);
                request.Headers.Add("Authorization", $"Bearer {Config.SupabaseKey}");
                request.Headers.Add("Prefer", "resolution=merge-duplicates");

                var response = await httpClient.SendAsync(request);

                if (!response.IsSuccessStatusCode)
                    Log.Warn($"Supabase error: {response.StatusCode} - {await response.Content.ReadAsStringAsync()}");
            }
            catch (Exception ex)
            {
                Log.Error($"Supabase HTTP error: {ex.Message}");
            }
        }
    }

    public class PlayerStats
    {
        public string Nickname { get; set; } = "Unknown";
        public int Kills { get; set; }
        public int Deaths { get; set; }
        public int TotalPlaySeconds { get; set; }
        public DateTime LastJoin { get; set; } = DateTime.Now;
        public DateTime LastSeenUtc { get; set; } = DateTime.UtcNow;
    }

    public class StatsConfig : IConfig
    {
        public bool IsEnabled { get; set; } = true;
        public bool Debug { get; set; } = false;

        public string SupabaseUrl { get; set; } = "";
        public string SupabaseKey { get; set; } = "";
    }
}
