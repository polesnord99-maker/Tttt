"""Accès SQLite asynchrone et initialisation du schéma."""
from __future__ import annotations
import aiosqlite
from pathlib import Path
from config import DATABASE_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS guild_config (
 guild_id INTEGER NOT NULL, key TEXT NOT NULL, value TEXT,
 updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 PRIMARY KEY (guild_id, key)
);
CREATE TABLE IF NOT EXISTS panels (
 guild_id INTEGER NOT NULL, panel_type TEXT NOT NULL, channel_id INTEGER,
 message_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1,
 PRIMARY KEY (guild_id, panel_type)
);
CREATE TABLE IF NOT EXISTS tickets (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL,
 user_id INTEGER NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open', claimed_by INTEGER,
 staff_channel_id INTEGER, staff_message_id INTEGER,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 closed_at TEXT, closed_by INTEGER, close_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(guild_id,user_id,status);
CREATE TABLE IF NOT EXISTS ticket_messages (
 id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL REFERENCES tickets(id),
 author_id INTEGER NOT NULL, direction TEXT NOT NULL, content TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS ticket_notes (
 id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL REFERENCES tickets(id),
 author_id INTEGER NOT NULL, note TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS absences (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 start_at TEXT NOT NULL, end_at TEXT NOT NULL, reason TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending', decision_by INTEGER, decision_at TEXT,
 decision_reason TEXT, actual_end_at TEXT,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_absences_active ON absences(guild_id,user_id,status);
CREATE TABLE IF NOT EXISTS service_sessions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
 started_at TEXT NOT NULL, ended_at TEXT, started_by INTEGER NOT NULL,
 ended_by INTEGER, end_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_service_per_user
 ON service_sessions(guild_id,user_id) WHERE ended_at IS NULL;
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, actor_id INTEGER,
 target_id INTEGER, event TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
"""

class Database:
    def __init__(self, path: str | None = None):
        self.path = path or DATABASE_PATH
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA foreign_keys=ON")
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    def db(self) -> aiosqlite.Connection:
        if self.conn is None:
            raise RuntimeError("Base de données non initialisée")
        return self.conn

    async def get_config(self, guild_id: int, key: str, default=None):
        cur = await self.db().execute(
            "SELECT value FROM guild_config WHERE guild_id=? AND key=?", (guild_id, key))
        row = await cur.fetchone()
        return row["value"] if row else default

    async def set_config(self, guild_id: int, key: str, value):
        await self.db().execute("""INSERT INTO guild_config(guild_id,key,value)
            VALUES(?,?,?) ON CONFLICT(guild_id,key) DO UPDATE SET
            value=excluded.value, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
            (guild_id, key, None if value is None else str(value)))
        await self.db().commit()

    async def audit(self, guild_id: int, actor_id: int | None, target_id: int | None,
                    event: str, details: str = ""):
        await self.db().execute(
            "INSERT INTO audit_logs(guild_id,actor_id,target_id,event,details) VALUES(?,?,?,?,?)",
            (guild_id, actor_id, target_id, event, details[:1500]))
        await self.db().commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None
