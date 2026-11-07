FROM python:3.12-slim

# Optional mirror overrides for network-restricted environments (e.g. China).
# Leave empty to use upstream defaults.
#   APT_MIRROR_HOST=mirrors.aliyun.com
#   PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
#   UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
ARG APT_MIRROR_HOST=""
ARG PIP_INDEX_URL=""
ARG UV_DEFAULT_INDEX=""


WORKDIR /app

RUN if [ -n "$APT_MIRROR_HOST" ]; then \
      sed -i "s|deb\.debian\.org|$APT_MIRROR_HOST|g" /etc/apt/sources.list.d/debian.sources; \
    fi

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
      > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin openssh-client git && \
    rm -rf /var/lib/apt/lists/*

COPY src/backend/pyproject.toml src/backend/uv.lock ./
RUN touch README.md && \
    pip install ${PIP_INDEX_URL:+--index-url=$PIP_INDEX_URL} uv && \
    if [ -n "$UV_DEFAULT_INDEX" ]; then \
      export UV_DEFAULT_INDEX && \
      uv lock; \
    fi && \
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
