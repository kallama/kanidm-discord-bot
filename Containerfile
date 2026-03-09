FROM ghcr.io/astral-sh/uv:latest AS uv
FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/kallama/kanidm-discord-bot"
LABEL org.opencontainers.image.description="Discord bot for Kanidm user registration"

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY bot/ bot/

RUN groupadd --gid 1000 bot && \
    useradd --uid 1000 --gid bot --no-create-home --shell /usr/sbin/nologin bot && \
    mkdir -p data && chown 1000:1000 data

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD [".venv/bin/python", "-c", "import os,time; assert time.time() - os.path.getmtime('/tmp/healthy') < 120"]

USER 1000:1000

CMD [".venv/bin/python", "-m", "bot"]
