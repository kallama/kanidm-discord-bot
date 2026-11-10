import pytest

from bot.config import Settings

REQUIRED = {"DISCORD_TOKEN": "t", "KANIDM_URL": "https://idm.example.com/", "KANIDM_TOKEN": "k"}
OPTIONAL = [
    "KANIDM_GROUP",
    "DISCORD_ROLE",
    "DISCORD_REQUIRE_ROLE",
    "DB_PATH",
    "ENABLE_POSIX",
    "HEARTBEAT_URL",
    "HEARTBEAT_SECONDS",
]


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in OPTIONAL:
        monkeypatch.delenv(key, raising=False)
    for key, value in REQUIRED.items():
        monkeypatch.setenv(key, value)


def test_defaults() -> None:
    settings = Settings.from_env()
    assert settings.kanidm_url == "https://idm.example.com"
    assert settings.kanidm_group is None
    assert settings.enable_posix is False
    assert settings.heartbeat_seconds == 60


def test_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KANIDM_TOKEN")
    with pytest.raises(SystemExit, match="KANIDM_TOKEN"):
        Settings.from_env()


@pytest.mark.parametrize("value", ["abc", "0", "-5", "1.5"])
def test_bad_heartbeat_seconds(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("HEARTBEAT_SECONDS", value)
    with pytest.raises(SystemExit, match="HEARTBEAT_SECONDS"):
        Settings.from_env()


def test_empty_heartbeat_seconds_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HEARTBEAT_SECONDS", "")
    assert Settings.from_env().heartbeat_seconds == 60
