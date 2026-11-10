# Kanidm Discord Bot

## Quick start

```bash
uv sync                    # install dependencies
cp .env.example .env       # fill in values
uv run python -m bot       # start the bot
```

## Architecture

- `bot/__main__.py` — Entry point. Loads config, creates the Discord bot and Kanidm client, syncs slash commands on ready.
- `bot/config.py` — `Settings` frozen dataclass loaded from env vars.
- `bot/kanidm.py` — Async HTTP client wrapping the Kanidm REST API (httpx + Bearer auth).
- `bot/usermap.py` — SQLite-backed Discord ID to Kanidm UUID mapping (prevents duplicate registrations).
- `bot/cogs/heartbeat.py` — Periodic uptime heartbeat pings.
- `bot/cogs/register.py` — `/register` slash command that opens a modal, creates a Kanidm account, and assigns a Discord role.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | yes | | Discord bot token |
| `KANIDM_URL` | yes | | Kanidm base URL (e.g. `https://idm.example.com`) |
| `KANIDM_TOKEN` | yes | | Kanidm service account Bearer token |
| `KANIDM_GROUP` | no | | Kanidm group to add new users to (skipped if unset) |
| `DISCORD_ROLE` | no | | Discord role (name or ID) to assign after registration (skipped if unset) |
| `DISCORD_REQUIRE_ROLE` | no | | If set, only members with this Discord role (name or ID) can use `/register` |
| `DB_PATH` | no | `data/bot.db` | Path to SQLite database for Discord ID → Kanidm UUID mappings |
| `ENABLE_POSIX` | no | `false` | Enable POSIX account attributes for new users |
| `HEARTBEAT_URL` | no | | URL to GET periodically as an uptime heartbeat (disabled if unset) |
| `HEARTBEAT_SECONDS` | no | `60` | Interval in seconds between heartbeat pings |


## Container build

The container runs as UID/GID 1000. Ensure the data directory exists and is writable:

```bash
mkdir -p data
```

```bash
docker build -t kanidm-discord-bot -f Containerfile .
docker run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

```bash
podman build -t kanidm-discord-bot -f Containerfile .
podman run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

## Releasing

Run `./release.sh` from a clean, up-to-date `main`. It:

1. Refuses to run if the tree is dirty, the branch isn't `main`, `main` is behind `origin`, or `uv.lock` is stale
2. Runs `ruff check`, `ruff format --check`, and `pytest`
3. Bumps `version` in `pyproject.toml` (CalVer: `YYYY.MM.patch`; patch restarts at `0` each month, e.g. `2026.03.0`) and runs `uv lock`
4. Commits only `pyproject.toml` and `uv.lock` as `release <version>`, tags `<version>` (no `v` prefix), and pushes `main` plus that tag atomically

GitHub Actions (`.github/workflows/release.yaml`) then:
- Validates the tag matches `pyproject.toml` version
- Builds the container and pushes to GHCR
- Creates a GitHub Release with auto-generated notes

## Future considerations

### Cloudflare Workers deployment

The bot could be rewritten as a Cloudflare Worker for serverless/zero-ops hosting:

- Requires a TypeScript rewrite (Workers don't run Python)
- Switch from Discord gateway (WebSocket) to the HTTP interactions model
- Usermap storage moves from local SQLite to Cloudflare KV
- Ed25519 signature verification required for incoming interactions
- Free tier covers 100k requests/day with KV included
