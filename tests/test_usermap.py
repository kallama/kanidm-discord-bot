import asyncio
import sqlite3
from pathlib import Path

import pytest

from bot.usermap import UserMap


def test_roundtrip(tmp_path: Path) -> None:
    async def run() -> None:
        usermap = await UserMap.connect(tmp_path / "sub" / "bot.db")
        try:
            assert await usermap.count() == 0
            assert not await usermap.has(1)
            await usermap.set(1, "uuid-1")
            assert await usermap.has(1)
            assert await usermap.get(1) == "uuid-1"
            assert await usermap.count() == 1
            with pytest.raises(sqlite3.IntegrityError):
                await usermap.set(1, "uuid-2")
        finally:
            await usermap.close()

    asyncio.run(run())
