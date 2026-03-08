from __future__ import annotations

import asyncio
import logging

import discord
from dotenv import load_dotenv

from bot.config import Settings
from bot.kanidm import KanidmClient
from bot.usermap import UserMap

log = logging.getLogger(__name__)


class Bot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)
        self.settings = settings
        self.kanidm = KanidmClient(settings.kanidm_url, settings.kanidm_token)
        self.usermap: UserMap  # initialized in setup_hook

    async def setup_hook(self) -> None:
        self.usermap = await UserMap.connect(self.settings.db_path)

        from bot.cogs.register import register

        self.tree.add_command(register)
        synced = await self.tree.sync()
        log.info("Synced %d command(s)", len(synced))

        if self.settings.heartbeat_url:
            from bot.cogs.heartbeat import Heartbeat

            self._heartbeat = Heartbeat(self)

    async def on_ready(self) -> None:
        assert self.user is not None
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)

    async def close(self) -> None:
        if hasattr(self, "_heartbeat"):
            await self._heartbeat.teardown()
        if hasattr(self, "usermap"):
            await self.usermap.close()
        await self.kanidm.close()
        await super().close()


async def main() -> None:
    load_dotenv()
    settings = Settings.from_env()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if settings.heartbeat_url:
        heartbeat_host = settings.heartbeat_url.split("//")[-1].split("/")[0]

        class _HeartbeatFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                return heartbeat_host not in record.getMessage()

        logging.getLogger("httpx").addFilter(_HeartbeatFilter())

    bot = Bot(settings)
    try:
        await bot.start(settings.discord_token)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
