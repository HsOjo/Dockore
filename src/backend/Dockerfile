FROM python:3.12-slim

WORKDIR /app

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

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
