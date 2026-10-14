#!/usr/bin/env python3
"""Live game statistics for ukgames.games.

nginx passes /api/event and /api/stats here (127.0.0.1:8082).

POST /api/event   Bumper Brawl reports what happens in the game (GameStats.cs). The body is one JSON object:
                    e  event: session_start (the game opened), heartbeat (every minute while it is open),
                       room_created (a player created a game), match_start, match_end (sent by whoever runs the match),
                       step (a player's step into play, once per launch: see STEPS)
                    s  random id the game makes on each launch (not stored on disk, not tied to an account)
                    p  platform (crazygames, itch, web, android, ios, desktop, server)
                    v  game version
                    a  where the player is: menu or match (heartbeat); the step's name (step)
                    m  map, g  game mode, n  players in the match, or which finished match (step match_done),
                    d  match length in seconds
                    t  milliseconds the game took to load (session_start)
                    r  days since the device first played, 0 = a new player (session_start; -1 or missing = unknown)
                    f  1 on the device's first launch of the UTC day (session_start)
GET  /api/funnel  per-day counts of the steps, new and returning players and loading time (last FUNNEL_DAYS days).
GET  /api/stats   the numbers the website's live ticker shows (site.js), cached for a few seconds.

Counters are kept per day (UTC) and in total in SQLite (STATS_DB). Who is online is only kept in memory: a session
counts as online while its heartbeats keep coming. IP addresses are used only in memory for the rate limit.
If GA_MEASUREMENT_ID and GA_API_SECRET are set (systemd EnvironmentFile=/etc/ukgames-stats.env), the game events are
also sent to Google Analytics through the Measurement Protocol, so the secret never ships inside the game.
Python standard library only.
"""

import json
import os
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = int(os.environ.get("STATS_PORT", "8082"))
STATS_DB = os.environ.get("STATS_DB", "/var/lib/ukgames-stats/stats.db")
# Our own game servers share one address; they are not rate limited.
TRUSTED_IPS = set(filter(None, os.environ.get("TRUSTED_IPS", "127.0.0.1,194.5.159.67").split(",")))
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "")
GA_API_SECRET = os.environ.get("GA_API_SECRET", "")

MAX_BODY_BYTES = 2048
ONLINE_SECONDS = 150          # a session is online while a heartbeat came within this time (they come every 60 s)
EVENTS_PER_IP_10_MIN = 120    # a phone sends about 12; a whole school behind one address still fits
STATS_CACHE_SECONDS = 5
RECENT_KEPT = 30
RECENT_SHOWN = 8
MAX_MATCH_SECONDS = 3600
MAX_PLAYERS = 16
MAX_LOAD_MS = 600000
MAX_DAYS = 3650
FUNNEL_DAYS = 14
NET_INTERFACE = os.environ.get("NET_INTERFACE", "eth0")
NET_SAMPLE_SECONDS = 60

EVENTS = {"session_start", "heartbeat", "room_created", "match_start", "match_end", "step"}
# A player's way into play, in order (GameStats.STEP_*). match_done comes with n = 1, 2, 3, 5 or 10.
STEPS = ("menu", "connecting", "connected", "connect_failed", "map_loaded", "in_match", "match_done")
MATCH_MILESTONES = {1, 2, 3, 5, 10}
# Days after the first launch that count as a return (return_d1 today / new_players yesterday = D1 retention).
RETURN_DAYS = {1, 7, 30}
FUNNEL_PREFIXES = ("step:", "sessions", "new_players", "returning", "return_d", "active_devices", "load_")
PLATFORMS = {"crazygames", "itch", "web", "android", "ios", "desktop", "server"}
SESSION_PATTERN = re.compile(r"^[0-9a-f]{16,32}$")
LABEL_PATTERN = re.compile(r"[^A-Za-z0-9 ._'-]")

_lock = threading.Lock()
_recent_ips = {}   # ip -> [event times within the last 10 minutes]
_online = {}       # session -> (last heartbeat time, where: menu/match, platform)
_net_rate = {"in": 0.0, "out": 0.0}   # bits per second over the last sample
_cache = {"time": 0.0, "body": b""}
_ga_queue = queue.Queue(maxsize=1000)


def log(text):
    print(text, flush=True)


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def label(value, limit=40):
    return LABEL_PATTERN.sub("", str(value or ""))[:limit].strip()


def number(value, low, high):
    try:
        return max(low, min(high, int(float(value))))
    except (TypeError, ValueError):
        return 0


# ---------- Storage ----------

def connect():
    os.makedirs(os.path.dirname(STATS_DB), exist_ok=True)
    db = sqlite3.connect(STATS_DB, check_same_thread=False)
    db.execute("CREATE TABLE IF NOT EXISTS counters (day TEXT, key TEXT, value INTEGER, PRIMARY KEY (day, key))")
    db.execute("CREATE TABLE IF NOT EXISTS recent (time INTEGER, data TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER)")
    db.commit()
    return db


_db = connect()


def add(key, amount=1):
    """Adds to today's counter and the all-time one (day 'all')."""
    for day in (today(), "all"):
        _db.execute("INSERT INTO counters (day, key, value) VALUES (?, ?, ?) "
                    "ON CONFLICT (day, key) DO UPDATE SET value = value + excluded.value", (day, key, amount))


def raise_to(key, value):
    """Keeps the highest value seen today and ever (peak players online)."""
    for day in (today(), "all"):
        _db.execute("INSERT INTO counters (day, key, value) VALUES (?, ?, ?) "
                    "ON CONFLICT (day, key) DO UPDATE SET value = MAX(value, excluded.value)", (day, key, value))


def counters(day):
    return dict(_db.execute("SELECT key, value FROM counters WHERE day = ?", (day,)).fetchall())


def add_recent(entry):
    _db.execute("INSERT INTO recent (time, data) VALUES (?, ?)", (entry["t"], json.dumps(entry)))
    _db.execute("DELETE FROM recent WHERE rowid NOT IN (SELECT rowid FROM recent ORDER BY time DESC LIMIT ?)",
                (RECENT_KEPT,))


# ---------- Server traffic ----------

def read_net_bytes():
    """Total bytes received and sent on the network interface since boot, or None if it can't be read."""
    try:
        with open("/proc/net/dev", encoding="ascii") as f:
            for line in f:
                name, _, rest = line.partition(":")
                if name.strip() == NET_INTERFACE:
                    fields = rest.split()
                    return int(fields[0]), int(fields[8])
    except (OSError, ValueError, IndexError):
        pass
    return None


def net_sampler():
    """Every minute adds the traffic since the last look to today's and the all-time counters, and keeps the
    current speed in memory. The kernel counters restart at zero on a reboot, which shows as a smaller number."""
    row = lambda key: _db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    saved_rx, saved_tx = row("net_rx"), row("net_tx")
    last = (saved_rx[0], saved_tx[0]) if saved_rx and saved_tx else None
    last_time = time.time()
    if last is None:
        last = read_net_bytes()   # first run: start counting from now, not from boot
    while True:
        time.sleep(NET_SAMPLE_SECONDS)
        current, now = read_net_bytes(), time.time()
        if current is None:
            continue
        rx = current[0] - last[0] if last and current[0] >= last[0] else current[0]
        tx = current[1] - last[1] if last and current[1] >= last[1] else current[1]
        seconds = max(1.0, now - last_time)
        with _lock:
            add("net_rx", rx)
            add("net_tx", tx)
            _db.execute("INSERT INTO meta (key, value) VALUES ('net_rx', ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value", (current[0],))
            _db.execute("INSERT INTO meta (key, value) VALUES ('net_tx', ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value", (current[1],))
            _db.commit()
            _net_rate["in"], _net_rate["out"] = rx * 8 / seconds, tx * 8 / seconds
        last, last_time = current, now


def month_counters():
    prefix = time.strftime("%Y-%m-", time.gmtime())
    rows = _db.execute("SELECT key, SUM(value) FROM counters WHERE day LIKE ? AND key IN ('net_rx', 'net_tx') GROUP BY key",
                       (prefix + "%",)).fetchall()
    return dict(rows)


# ---------- Events ----------

def is_rate_limited(ip):
    if ip in TRUSTED_IPS:
        return False
    now = time.time()
    times = [t for t in _recent_ips.get(ip, []) if now - t < 600]
    _recent_ips[ip] = times
    if len(times) >= EVENTS_PER_IP_10_MIN:
        return True
    times.append(now)
    return False


def online_counts(now):
    for session, (seen, _, _) in list(_online.items()):
        if now - seen > ONLINE_SECONDS:
            del _online[session]
    in_match = sum(1 for _, where, _ in _online.values() if where == "match")
    return len(_online), in_match


def record(event):
    """Called with _lock held."""
    name, now = event["e"], time.time()
    if name == "session_start":
        add("sessions")
        add("sessions:" + event["p"])
        if event["t"] > 0:
            add("load_ms:" + event["p"], event["t"])
            add("load_count:" + event["p"])
        # Once per device and day: how many played today, how many are new, how many came back.
        if event["r"] >= 0 and event["f"] == 1:
            add("active_devices:" + event["p"])
            if event["r"] == 0:
                add("new_players")
                add("new_players:" + event["p"])
            else:
                add("returning")
                if event["r"] in RETURN_DAYS:
                    add(f"return_d{event['r']}")
                    add(f"return_d{event['r']}:" + event["p"])
    if name == "step":
        key = "step:" + event["a"] + (f":{event['n']}" if event["a"] == "match_done" else "")
        add(key)
        add(key + ":" + event["p"])
    if name in ("session_start", "heartbeat") and event["p"] != "server":
        _online[event["s"]] = (now, "match" if event["a"] == "match" else "menu", event["p"])
        raise_to("peak_online", online_counts(now)[0])
    if name == "room_created":
        add("rooms")
    if name == "match_start":
        add("matches_started")
    if name == "match_end":
        add("matches")
        add("player_minutes", round(event["n"] * event["d"] / 60))
        if event["m"]:
            add("map:" + event["m"])
        if event["g"]:
            add("mode:" + event["g"])
    if name in ("room_created", "match_end"):
        add_recent({"t": int(now), "e": name, "m": event["m"], "g": event["g"], "n": event["n"], "d": event["d"]})
    _db.commit()
    _cache["time"] = 0.0


def parse_event(data):
    if not isinstance(data, dict):
        return None
    event = {
        "e": str(data.get("e", "")),
        "s": str(data.get("s", "")).lower(),
        "p": str(data.get("p", "")).lower(),
        "v": label(data.get("v"), 20),
        "a": label(data.get("a"), 20).lower(),
        "m": label(data.get("m")),
        "g": label(data.get("g"), 20).upper(),
        "n": number(data.get("n"), 0, MAX_PLAYERS),
        "d": number(data.get("d"), 0, MAX_MATCH_SECONDS),
        "t": number(data.get("t"), 0, MAX_LOAD_MS),
        # Older builds don't send it: unknown, not a new player.
        "r": number(data.get("r"), -1, MAX_DAYS) if "r" in data else -1,
        "f": 1 if data.get("f") == 1 else 0,
    }
    if event["e"] not in EVENTS or not SESSION_PATTERN.match(event["s"]):
        return None
    if event["e"] == "step" and (event["a"] not in STEPS
                                 or (event["a"] == "match_done" and event["n"] not in MATCH_MILESTONES)):
        return None
    if event["p"] not in PLATFORMS:
        event["p"] = "web"
    return event


# ---------- Google Analytics (optional) ----------

def forward_to_ga(event):
    if not GA_MEASUREMENT_ID or not GA_API_SECRET or event["e"] == "heartbeat":
        return
    params = {"platform": event["p"], "game_version": event["v"], "engagement_time_msec": 1}
    if event["m"]:
        params["map"] = event["m"]
    if event["g"]:
        params["mode"] = event["g"]
    if event["e"] in ("match_start", "match_end"):
        params["players"] = event["n"]
    if event["e"] == "match_end":
        params["duration_sec"] = event["d"]
    if event["e"] == "step":
        params["step"] = event["a"]
        if event["a"] == "match_done":
            params["match_number"] = event["n"]
    if event["e"] == "session_start":
        params["load_ms"] = event["t"]
        params["days_since_first"] = event["r"]
    payload = {"client_id": event["s"], "events": [{"name": "bb_" + event["e"], "params": params}]}
    try:
        _ga_queue.put_nowait(payload)
    except queue.Full:
        pass


def ga_sender():
    url = ("https://www.google-analytics.com/mp/collect?measurement_id=" + GA_MEASUREMENT_ID
           + "&api_secret=" + GA_API_SECRET)
    while True:
        payload = _ga_queue.get()
        try:
            request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                             headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(request, timeout=10).close()
        except Exception as ex:  # a lost analytics event is not worth more than a log line
            log(f"GA send failed: {ex}")


# ---------- Summary for the website ----------

def build_stats():
    now = time.time()
    online, in_match = online_counts(now)
    day, total = counters(today()), counters("all")
    maps = sorted(((k[4:], v) for k, v in day.items() if k.startswith("map:")), key=lambda kv: -kv[1])
    recent = [json.loads(row[0]) for row in
              _db.execute("SELECT data FROM recent ORDER BY time DESC LIMIT ?", (RECENT_SHOWN,)).fetchall()]
    month = month_counters()
    gb = lambda b: round(b / 1e9, 2)
    return {
        "net": {
            "mbps_in": round(_net_rate["in"] / 1e6, 2),
            "mbps_out": round(_net_rate["out"] / 1e6, 2),
            "today_gb": gb(day.get("net_rx", 0) + day.get("net_tx", 0)),
            "month_gb": gb(month.get("net_rx", 0) + month.get("net_tx", 0)),
            "total_gb": gb(total.get("net_rx", 0) + total.get("net_tx", 0)),
        },
        "online": online,
        "in_match": in_match,
        "today": {
            "matches": day.get("matches", 0),
            "rooms": day.get("rooms", 0),
            "sessions": day.get("sessions", 0),
            "player_minutes": day.get("player_minutes", 0),
            "peak_online": day.get("peak_online", 0),
            "top_map": maps[0][0] if maps else "",
        },
        "total": {
            "matches": total.get("matches", 0),
            "rooms": total.get("rooms", 0),
            "sessions": total.get("sessions", 0),
            "player_minutes": total.get("player_minutes", 0),
            "peak_online": total.get("peak_online", 0),
        },
        "recent": recent,
        "now": int(now),
    }


def build_funnel():
    """The steps and player counts of the last FUNNEL_DAYS days, newest first, with D1 retention where yesterday had
    new players."""
    days = []
    for i in range(FUNNEL_DAYS):
        day = time.strftime("%Y-%m-%d", time.gmtime(time.time() - i * 86400))
        values = {k: v for k, v in counters(day).items() if k.startswith(FUNNEL_PREFIXES)}
        days.append({"day": day, "counts": values})
    for today_entry, yesterday_entry in zip(days, days[1:]):
        new_yesterday = yesterday_entry["counts"].get("new_players", 0)
        if new_yesterday:
            today_entry["d1_retention"] = round(today_entry["counts"].get("return_d1", 0) / new_yesterday, 4)
    return {"days": days, "steps": list(STEPS), "now": int(time.time())}


class Handler(BaseHTTPRequestHandler):
    server_version = "ukgames-stats"

    def log_message(self, fmt, *args):
        pass  # no per-request access log: nginx keeps one

    def reply(self, status, body, cache_seconds=0):
        if isinstance(body, dict):
            body = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", f"public, max-age={cache_seconds}" if cache_seconds else "no-store")
        # The game runs on CrazyGames' and itch.io's pages, so its requests come from their addresses.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.reply(204, b"")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/funnel":
            with _lock:
                body = build_funnel()
            return self.reply(200, body, 60)
        if path != "/api/stats":
            return self.reply(404, {"ok": False, "error": "not_found"})
        with _lock:
            if time.time() - _cache["time"] > STATS_CACHE_SECONDS:
                _cache["body"] = json.dumps(build_stats(), separators=(",", ":")).encode("utf-8")
                _cache["time"] = time.time()
            body = _cache["body"]
        return self.reply(200, body, STATS_CACHE_SECONDS)

    def do_POST(self):
        if self.path.split("?")[0] != "/api/event":
            return self.reply(404, {"ok": False, "error": "not_found"})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            return self.reply(413, {"ok": False, "error": "too_large"})
        try:
            # Sent as text/plain by the game, so browsers don't ask first (CORS preflight); the body is JSON anyway.
            event = parse_event(json.loads(self.rfile.read(length).decode("utf-8", errors="replace")))
        except ValueError:
            event = None
        if event is None:
            return self.reply(400, {"ok": False, "error": "invalid"})
        ip = self.headers.get("X-Real-IP") or self.client_address[0]
        with _lock:
            is_limited = is_rate_limited(ip)
            error = None
            if not is_limited:
                try:
                    record(event)
                except sqlite3.Error as ex:
                    error = str(ex)
        if is_limited:
            return self.reply(429, {"ok": False, "error": "rate_limited"})
        if error:
            log(f"store failed: {error}")
            return self.reply(500, {"ok": False, "error": "store_failed"})
        forward_to_ga(event)
        return self.reply(200, {"ok": True})


def main():
    if GA_MEASUREMENT_ID and GA_API_SECRET:
        threading.Thread(target=ga_sender, daemon=True).start()
    threading.Thread(target=net_sampler, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log(f"stats server on {HOST}:{PORT}, db {STATS_DB}, Google Analytics {'on' if GA_API_SECRET else 'off'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
