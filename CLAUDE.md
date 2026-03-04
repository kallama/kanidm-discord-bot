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
- `bot/usermap.py` — JSON-file-backed Discord ID to Kanidm username mapping (prevents duplicate registrations).
- `bot/cogs/register.py` — `/register` slash command that opens a modal, creates a Kanidm account, and assigns a Discord role.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DISCORD_TOKEN` | yes | | Discord bot token |
| `KANIDM_URL` | yes | | Kanidm base URL (e.g. `https://idm.example.com`) |
| `KANIDM_TOKEN` | yes | | Kanidm service account Bearer token |
| `KANIDM_GROUP` | no | | Kanidm group to add new users to (skipped if unset) |
| `DISCORD_ROLE` | no | | Discord role to assign after registration (skipped if unset) |
| `DISCORD_REQUIRE_ROLE` | no | | If set, only members with this Discord role can use `/register` |
| `USERMAP_PATH` | no | `data/usermap.json` | Path to Discord ID → Kanidm username mapping file |
| `ENABLE_POSIX` | no | `false` | Enable POSIX account attributes for new users |


## Container build

```bash
docker build -t kanidm-discord-bot -f Containerfile .
docker run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

```bash
podman build -t kanidm-discord-bot -f Containerfile .
podman run --env-file .env -v ./data:/app/data kanidm-discord-bot
```

## Releasing

1. Bump `version` in `pyproject.toml` (CalVer: `YYYY.MM.patch`, e.g. `2026.03.2`)
2. Commit: `git commit -am "release 2026.03.2"`
3. Tag and push: `git tag v2026.03.2 && git push origin main --tags`

GitHub Actions (`.github/workflows/release.yaml`) then:
- Validates the tag matches `pyproject.toml` version
- Builds the container and pushes to GHCR
- Creates a GitHub Release with auto-generated notes

## Future considerations

### Cloudflare Workers deployment

The bot could be rewritten as a Cloudflare Worker for serverless/zero-ops hosting:

- Requires a TypeScript rewrite (Workers don't run Python)
- Switch from Discord gateway (WebSocket) to the HTTP interactions model
- Usermap storage moves from local JSON file to Cloudflare KV
- Ed25519 signature verification required for incoming interactions
- Free tier covers 100k requests/day with KV included
