from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class UserMap:
    """Persistent Discord ID -> Kanidm username mapping backed by a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            self._data = json.loads(self._path.read_text())
            log.info("Loaded %d user mapping(s) from %s", len(self._data), self._path)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2) + "\n")

    def set(self, discord_id: int, username: str) -> None:
        self._data[str(discord_id)] = username
        self._save()

    def get(self, discord_id: int) -> str | None:
        return self._data.get(str(discord_id))

    def has(self, discord_id: int) -> bool:
        return str(discord_id) in self._data
