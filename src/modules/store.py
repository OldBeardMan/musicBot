"""The bot's small SQLite store: pets and the last known state of Long Kitten Nation accounts."""
import sqlite3
import time


class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS pets (
                user_id  TEXT PRIMARY KEY,
                count    INTEGER NOT NULL DEFAULT 0,
                last_at  REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS lkn_members (
                discord_id TEXT PRIMARY KEY,
                status     TEXT NOT NULL,
                mc_name    TEXT
            );
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self.db.commit()

    # ------------------------------------------------------------ pets

    def pet(self, user_id: int, cooldown: float):
        """Counts one pet. Returns (user_count, total) or None while the user is on cooldown."""
        uid, now = str(user_id), time.time()
        row = self.db.execute("SELECT count, last_at FROM pets WHERE user_id = ?", (uid,)).fetchone()
        if row and now - row[1] < cooldown:
            return None
        self.db.execute(
            "INSERT INTO pets (user_id, count, last_at) VALUES (?, 1, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET count = count + 1, last_at = excluded.last_at",
            (uid, now),
        )
        self.db.commit()
        return self.user_pets(user_id), self.total_pets()

    def user_pets(self, user_id: int) -> int:
        row = self.db.execute("SELECT count FROM pets WHERE user_id = ?", (str(user_id),)).fetchone()
        return row[0] if row else 0

    def total_pets(self) -> int:
        return self.db.execute("SELECT COALESCE(SUM(count), 0) FROM pets").fetchone()[0]

    def top_petters(self, limit: int = 10):
        return self.db.execute("SELECT user_id, count FROM pets ORDER BY count DESC LIMIT ?", (limit,)).fetchall()

    # ------------------------------------------------------------ Long Kitten Nation

    def lkn_known(self) -> dict:
        return {r[0]: (r[1], r[2]) for r in self.db.execute("SELECT discord_id, status, mc_name FROM lkn_members")}

    def lkn_save(self, members: list):
        self.db.execute("DELETE FROM lkn_members")
        self.db.executemany(
            "INSERT INTO lkn_members (discord_id, status, mc_name) VALUES (?, ?, ?)",
            [(m["discord_id"], m["status"], m.get("mc_name")) for m in members],
        )
        self.db.commit()

    def get_meta(self, key: str):
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def set_meta(self, key: str, value: str):
        self.db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
        self.db.commit()
