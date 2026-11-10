FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.14.10-alpine3.24

LABEL org.opencontainers.image.source="https://github.com/kallama/kanidm-discord-bot"
LABEL org.opencontainers.image.description="Discord bot for Kanidm user registration"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=bind,from=uv,source=/uv,target=/usr/local/bin/uv \
    uv sync --frozen --no-dev --compile-bytecode

COPY bot/ bot/
RUN .venv/bin/python -m compileall -q bot

RUN addgroup -g 1000 bot && \
    adduser -u 1000 -G bot -D -H -s /sbin/nologin bot && \
    mkdir -p data && chown 1000:1000 data

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD [".venv/bin/python", "-c", "import os,time; assert time.time() - os.path.getmtime('/tmp/healthy') < 120"]

USER 1000:1000

CMD [".venv/bin/python", "-m", "bot"]
