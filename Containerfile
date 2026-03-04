FROM ghcr.io/astral-sh/uv:latest AS uv
FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/kallama/kanidm-discord-bot"
LABEL org.opencontainers.image.description="Discord bot for Kanidm user registration"

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY bot/ bot/

VOLUME /app/data

CMD ["uv", "run", "python", "-m", "bot"]
