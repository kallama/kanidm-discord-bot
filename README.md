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

Each Discord account can only register once — a local mapping file prevents duplicates. I don't like the idea of a mapping file or sqlite db, but don't see a current way to store the users Discord ID as a Kanidm attribute

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
| `USERMAP_PATH` | no | `data/usermap.json` | Path to the Discord ID to Kanidm Person UUID mapping file |
| `ENABLE_POSIX` | no | `false` | Enable POSIX account attributes for new users |

Enabling POSIX attributes and having a POSIX password is required for the user to LDAP login

## Container

```bash
docker build -t kanidm-discord-bot -f Containerfile .
docker run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

Or with Podman:

```bash
podman build -t kanidm-discord-bot -f Containerfile .
podman run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

The `-v ./data:/app/data` bind mount persists the usermap file across container restarts. Or use `compose.yaml`:

```bash
docker compose up -d
```

## Project structure

```
bot/
├── __main__.py      # Entry point, Discord bot setup
├── config.py        # Settings from environment variables
├── kanidm.py        # Async Kanidm REST API client
├── usermap.py       # Discord ID → Kanidm Person UUID mapping
└── cogs/
    └── register.py  # /register slash command and modal
```
