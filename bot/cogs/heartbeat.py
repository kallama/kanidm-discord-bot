from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx
from discord.ext import tasks

if TYPE_CHECKING:
    from bot.__main__ import Bot

log = logging.getLogger(__name__)


class Heartbeat:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.url: str = bot.settings.heartbeat_url  # type: ignore[assignment]
        self._client = httpx.AsyncClient(timeout=10)
        self._consecutive_failures = 0
        self.beat.change_interval(seconds=bot.settings.heartbeat_seconds)
        self.beat.start()

    async def teardown(self) -> None:
        self.beat.cancel()
        await self._client.aclose()

    @tasks.loop()
    async def beat(self) -> None:
        try:
            resp = await self._client.get(self.url)
            log.debug("Heartbeat %s → %d", self.url, resp.status_code)
            if self._consecutive_failures:
                log.info("Heartbeat recovered after %d failures", self._consecutive_failures)
            self._consecutive_failures = 0
        except Exception as exc:
            self._consecutive_failures += 1
            if self._consecutive_failures <= 3:
                log.warning("Heartbeat failed (%d): %s", self._consecutive_failures, exc)
            else:
                log.warning("Heartbeat still failing (%d consecutive)", self._consecutive_failures)

    @beat.before_loop
    async def before_beat(self) -> None:
        await self.bot.wait_until_ready()
