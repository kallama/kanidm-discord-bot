from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    discord_token: str
    kanidm_url: str
    kanidm_token: str
    kanidm_group: str | None = None
    discord_role: str | None = None
    discord_require_role: str | None = None
    usermap_path: str = "data/usermap.json"
    enable_posix: bool = False
    heartbeat_url: str | None = None
    heartbeat_seconds: int = 60

    @classmethod
    def from_env(cls) -> Settings:
        required = {"DISCORD_TOKEN", "KANIDM_URL", "KANIDM_TOKEN"}
        missing = sorted(v for v in required if not os.environ.get(v))
        if missing:
            raise SystemExit(f"Missing required env vars: {', '.join(missing)}")

        return cls(
            discord_token=os.environ["DISCORD_TOKEN"],
            kanidm_url=os.environ["KANIDM_URL"].rstrip("/"),
            kanidm_token=os.environ["KANIDM_TOKEN"],
            kanidm_group=os.environ.get("KANIDM_GROUP") or None,
            discord_role=os.environ.get("DISCORD_ROLE") or None,
            discord_require_role=os.environ.get("DISCORD_REQUIRE_ROLE") or None,
            usermap_path=os.environ.get("USERMAP_PATH", "data/usermap.json"),
            enable_posix=os.environ.get("ENABLE_POSIX", "").lower() == "true",
            heartbeat_url=os.environ.get("HEARTBEAT_URL") or None,
            heartbeat_seconds=int(os.environ.get("HEARTBEAT_SECONDS", "60")),
        )
