FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
      > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

COPY src/backend/pyproject.toml src/backend/uv.lock ./
RUN touch README.md && \
    pip install uv && \
    uv sync --no-dev

COPY src/backend/app ./app
COPY src/backend/alembic ./alembic
COPY src/backend/alembic.ini ./
COPY src/backend/scripts/docker-entrypoint.sh ./docker-entrypoint.sh
COPY VERSION ./

RUN chmod +x ./docker-entrypoint.sh

ENV DOCKORE_HOST=0.0.0.0
ENV DOCKORE_PORT=8000
# Container deployment pins the stacks root; bind-mount the SAME host path
# onto /app/stacks so compose-relative bind paths resolve identically.
ENV DOCKORE_STACKS_DIR=/app/stacks

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
