from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS usermap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kanidm_uuid TEXT NOT NULL UNIQUE,
    discord_id TEXT NOT NULL UNIQUE
)
"""


class UserMap:
    """Persistent Discord ID -> Kanidm UUID mapping backed by SQLite."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    @classmethod
    async def connect(cls, path: str | Path) -> UserMap:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        db = await aiosqlite.connect(path)
        await db.execute(_SCHEMA)
        await db.commit()
        async with db.execute("SELECT COUNT(*) FROM usermap") as cursor:
            row = await cursor.fetchone()
        log.info("Opened usermap at %s (%d mapping(s))", path, row[0] if row else 0)
        return cls(db)

    async def close(self) -> None:
        await self._db.close()

    async def set(self, discord_id: int, uuid: str) -> None:
        await self._db.execute(
            "INSERT INTO usermap (discord_id, kanidm_uuid) VALUES (?, ?)",
            (str(discord_id), uuid),
        )
        await self._db.commit()

    async def get(self, discord_id: int) -> str | None:
        async with self._db.execute(
            "SELECT kanidm_uuid FROM usermap WHERE discord_id = ?",
            (str(discord_id),),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def count(self) -> int:
        async with self._db.execute("SELECT COUNT(*) FROM usermap") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def has(self, discord_id: int) -> bool:
        async with self._db.execute(
            "SELECT 1 FROM usermap WHERE discord_id = ?",
            (str(discord_id),),
        ) as cursor:
            return await cursor.fetchone() is not None
