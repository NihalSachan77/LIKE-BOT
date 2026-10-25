import sqlite3
import secrets
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).with_name("nxt_like_bot.sqlite3")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, joined_at TEXT);
        CREATE TABLE IF NOT EXISTS premium(user_id INTEGER PRIMARY KEY, expires_at TEXT);
        CREATE TABLE IF NOT EXISTS redeem_keys(code TEXT PRIMARY KEY, days INTEGER NOT NULL, revoked INTEGER DEFAULT 0, used_by INTEGER, used_at TEXT);
        CREATE TABLE IF NOT EXISTS usage(user_id INTEGER NOT NULL, day TEXT NOT NULL, count INTEGER DEFAULT 0, PRIMARY KEY(user_id, day));
        CREATE TABLE IF NOT EXISTS channels(channel TEXT PRIMARY KEY, invite TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS autolikes(user_id INTEGER PRIMARY KEY, player_uid TEXT NOT NULL, enabled INTEGER DEFAULT 1, last_run TEXT);
        """)

def now():
    return datetime.now(timezone.utc)

def upsert_user(uid, username, first_name):
    with connect() as c:
        c.execute("INSERT INTO users VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name", (uid, username, first_name, now().isoformat()))

def plan_for(uid):
    with connect() as c:
        row = c.execute("SELECT expires_at FROM premium WHERE user_id=?", (uid,)).fetchone()
    if row:
        try:
            if datetime.fromisoformat(row["expires_at"]) > now():
                return "premium"
        except ValueError:
            pass
    return "free"

def premium_expiry(uid):
    with connect() as c:
        row = c.execute("SELECT expires_at FROM premium WHERE user_id=?", (uid,)).fetchone()
    if row and plan_for(uid) == "premium":
        return row["expires_at"][:10]
    return None

def grant_premium(uid, days):
    days = max(1, min(days, 3650))
    base = now()
    with connect() as c:
        row = c.execute("SELECT expires_at FROM premium WHERE user_id=?", (uid,)).fetchone()
        if row:
            try:
                old = datetime.fromisoformat(row["expires_at"])
                if old > base: base = old
            except ValueError: pass
        expiry = base + timedelta(days=days)
        c.execute("INSERT INTO premium VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at", (uid, expiry.isoformat()))

def remove_premium(uid):
    with connect() as c:
        c.execute("DELETE FROM premium WHERE user_id=?", (uid,))

def generate_key(days):
    alphabet = string.ascii_uppercase + string.digits
    key = "NXT-" + "".join(secrets.choice(alphabet) for _ in range(16))
    with connect() as c:
        c.execute("INSERT INTO redeem_keys(code,days) VALUES(?,?)", (key, max(1, min(days, 3650))))
    return key

def redeem_key(uid, key):
    with connect() as c:
        row = c.execute("SELECT days,revoked,used_by FROM redeem_keys WHERE code=?", (key.upper(),)).fetchone()
        if not row or row["revoked"] or row["used_by"] is not None:
            return False
        days = row["days"]
        c.execute("UPDATE redeem_keys SET used_by=?,used_at=? WHERE code=?", (uid, now().isoformat(), key.upper()))
    grant_premium(uid, days)
    return True

def revoke_key(key):
    with connect() as c:
        c.execute("UPDATE redeem_keys SET revoked=1 WHERE code=?", (key.upper(),))

def usage_today(uid):
    day = now().date().isoformat()
    with connect() as c:
        row = c.execute("SELECT count FROM usage WHERE user_id=? AND day=?", (uid, day)).fetchone()
    return row["count"] if row else 0

def record_usage(uid):
    day = now().date().isoformat()
    with connect() as c:
        c.execute("INSERT INTO usage(user_id,day,count) VALUES(?,?,1) ON CONFLICT(user_id,day) DO UPDATE SET count=count+1", (uid, day))

def add_channel(channel, invite=""):
    with connect() as c:
        c.execute("INSERT INTO channels(channel,invite) VALUES(?,?) ON CONFLICT(channel) DO UPDATE SET invite=excluded.invite", (channel, invite))

def remove_channel(channel):
    with connect() as c:
        c.execute("DELETE FROM channels WHERE channel=?", (channel,))

def list_channels():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT channel,invite FROM channels ORDER BY channel").fetchall()]

def clear_channels():
    with connect() as c:
        c.execute("DELETE FROM channels")

def set_setting(key, value):
    with connect() as c:
        c.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

def get_setting(key, default=None):
    with connect() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default

def user_count():
    with connect() as c:
        return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

def premium_count():
    with connect() as c:
        rows = c.execute("SELECT user_id,expires_at FROM premium").fetchall()
    return sum(1 for r in rows if datetime.fromisoformat(r["expires_at"]) > now())

def all_user_ids():
    with connect() as c:
        return [r[0] for r in c.execute("SELECT user_id FROM users").fetchall()]


def set_autolike(user_id, player_uid):
    with connect() as c:
        c.execute("INSERT INTO autolikes(user_id,player_uid,enabled,last_run) VALUES(?,?,1,NULL) ON CONFLICT(user_id) DO UPDATE SET player_uid=excluded.player_uid, enabled=1", (user_id, player_uid))

def stop_autolike(user_id):
    with connect() as c:
        c.execute("UPDATE autolikes SET enabled=0 WHERE user_id=?", (user_id,))

def get_autolike(user_id):
    with connect() as c:
        row = c.execute("SELECT user_id,player_uid,enabled,last_run FROM autolikes WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None

def active_autolikes():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT user_id,player_uid,enabled,last_run FROM autolikes WHERE enabled=1").fetchall()]

def mark_autolike_run(user_id):
    with connect() as c:
        c.execute("UPDATE autolikes SET last_run=? WHERE user_id=?", (now().isoformat(), user_id))
