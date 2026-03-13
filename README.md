# Kanidm Discord Bot

A Discord bot that lets users self-register [Kanidm](https://kanidm.com) accounts via a `/register` slash command.

## Vibe-Code Warning

This was vibe-coded with Claude Opus 4.6 as a personal project.

## What it does

1. User runs `/register` in Discord
2. A modal collects username, email, and name
3. The bot creates a Kanidm account, enables POSIX if ENABLE_POSIX is true, adds user to KANIDM_GROUP if set
4. The user receives a credential reset link to set up their passkey, and UNIX password if ENABLE_POSIX is true
5. Discord role DISCORD_ROLE is assigned to the user if set

Each Discord account can only register once — a local SQLite database prevents duplicates. I don't like the idea of a mapping file or sqlite db, but don't see a current way to store the users Discord ID as a Kanidm attribute

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A Kanidm instance with a service account token (the account must be a member of `idm_people_admins`, `idm_group_admins`, and `idm_unix_admins` at minimum)
- A Discord bot token with the `applications.commands` and `guilds.members` scopes

### Install and run

```bash
uv sync
cp .env.example .env  # fill in your values
uv run python -m bot
```

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | yes | | Discord bot token |
| `KANIDM_URL` | yes | | Kanidm base URL (e.g. `https://idm.example.com`) |
| `KANIDM_TOKEN` | yes | | Kanidm service account Bearer token |
| `KANIDM_GROUP` | no | | Kanidm group to add new users to (skipped if unset) |
| `DISCORD_ROLE` | no | | Discord role to assign after registration (skipped if unset) |
| `DISCORD_REQUIRE_ROLE` | no | | If set, only members with this Discord role can use `/register` |
| `DB_PATH` | no | `data/bot.db` | Path to SQLite database for Discord ID → Kanidm UUID mappings |
| `ENABLE_POSIX` | no | `false` | Enable POSIX account attributes for new users |
| `HEARTBEAT_URL` | no | | URL to GET periodically as an uptime heartbeat (disabled if unset) |
| `HEARTBEAT_SECONDS` | no | `60` | Interval in seconds between heartbeat pings |

Enabling POSIX attributes and having a POSIX password is required for the user to LDAP login

## Container

The container defaults to UID/GID 1000. To override, set `BOT_UID` and `BOT_GID` in your `.env` file:

```
BOT_UID=1001
BOT_GID=1001
```

### Docker Compose (recommended)

By default, `compose.yaml` uses a named volume (`bot-data`) which is managed by Docker/Podman automatically — no extra setup needed:

```bash
docker compose up -d
```

### Standalone container

Using a named volume:

```bash
docker run --env-file .env -v bot-data:/app/data ghcr.io/kallama/kanidm-discord-bot:latest
```

### Using a bind mount

If you prefer a bind mount to keep the database on the host filesystem, ensure the data directory exists and is writable by the configured UID/GID (default 1000):

```bash
mkdir -p data && chown 1000:1000 data
```

If using custom `BOT_UID`/`BOT_GID`, match the ownership:

```bash
mkdir -p data && chown $BOT_UID:$BOT_GID data
```

Then override the volume in your run command:

```bash
docker run --env-file .env -v ./data:/app/data ghcr.io/kallama/kanidm-discord-bot:latest
```

Or in `compose.yaml`, replace the volumes section:

```yaml
    volumes:
      - ./data:/app/data
```

### Building from source

```bash
docker build -t kanidm-discord-bot -f Containerfile .
```

```bash
docker compose up --build
```

## Project structure

```
bot/
├── __main__.py      # Entry point, Discord bot setup
├── config.py        # Settings from environment variables
├── kanidm.py        # Async Kanidm REST API client
├── usermap.py       # Discord ID → Kanidm Person UUID mapping
└── cogs/
    ├── heartbeat.py # Periodic uptime heartbeat pings
    └── register.py  # /register slash command and modal
```
