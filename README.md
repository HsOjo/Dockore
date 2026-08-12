# Dockore

<img src="images/icon.png" alt="Dockore" width="128" />

**English** | [中文](README_CN.md)

A simple, handy, out-of-the-box Docker GUI manager.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy (async) + SQLite + docker-py |
| Frontend | Vue 3 + TypeScript + Ant Design Vue + Pinia + Vue I18n |
| Desktop | Tauri 2 (backend bundled as an embedded sidecar via PyInstaller) |
| Shared | openapi-typescript + openapi-fetch (type-safe API client) |

## Project Structure

```
├── VERSION                 # Single source of truth for versioning
├── compose.yml             # Web deployment
└── src/
    ├── backend/            # FastAPI backend (managed by uv)
    ├── frontend/           # Vue 3 frontend + src-tauri desktop app
    ├── shared/             # @dockore/shared (API types/client, WS wrappers)
    └── proxy/              # Aggregating reverse proxy for Web (nginx)
```

## Features

- Containers: list/detail/create/run/start/stop/restart/rename/delete/logs (streaming)/diff/commit/exec/web terminal
- Images: list/detail/pull (live progress)/search/tag/history/delete
- Networks: list/detail/create/delete/connect/disconnect containers
- Volumes: list/detail/create/delete
- System: version info; Settings (Docker host and other runtime options)
- Light/dark themes, Chinese & English UI, desktop (Tauri) + Web forms

## Development

```bash
pnpm install
pnpm gen:api        # Generate TS types from backend openapi.json
pnpm dev            # Start backend (:8000) and frontend (:1420) together
```

Desktop development: `pnpm --filter @dockore/frontend dev` (requires `pnpm build:backend` first to produce the sidecar)

## Testing

```bash
pnpm test           # All unit tests: shared + backend + frontend
pnpm --filter @dockore/frontend test:e2e   # Playwright e2e
```

## Build

```bash
pnpm build                  # gen:api + shared + backend (PyInstaller) + frontend
pnpm build:frontend         # Package the Tauri desktop app
```

## Docker Compose Deployment (Web)

```bash
docker compose up -d --build
```

| Variable | Default | Description |
|---|---|---|
| DOCKORE_TOKEN | change-me | Backend access token (entered in the frontend) |
| DOCKORE_PORT | 8000 | Backend API port |
| DOCKORE_FRONTEND_PORT | 8001 | Frontend SPA port |
| DOCKORE_PROXY_PORT | 8002 | Aggregated proxy port (API + WS + SPA on one origin) |
| DOCKORE_CORS_ORIGINS | * | Allowed CORS origins, comma-separated |
| DOCKORE_DOCKER_SOCK | /var/run/docker.sock | Container daemon socket on the host (point to the podman socket for Podman) |
| DOCKORE_STACKS_DIR | /app/stacks | Stacks directory, bind-mounted at the same path on host and container |

- Data is persisted in `./data` (SQLite settings); the backend container mounts the host `/var/run/docker.sock` read-only
- Via the proxy (8002), API/WS share the page origin; when hitting the frontend directly (8001), enter the backend address + token on the onboarding page

### Stack (Compose project) management

The backend image ships the docker CLI with the compose plugin. `compose.yml` enables stack management by default: `DOCKORE_STACKS_DIR` (default `/app/stacks`) is bind-mounted at the **same path** on host and container, since relative bind paths inside compose files rely on path identity. Point it at your host stacks directory in `.env`:

```env
DOCKORE_STACKS_DIR=/your/host/stacks
```

- New stacks are always created at `<DOCKORE_STACKS_DIR>/<name>/compose.yml`; stacks outside the stacks dir are read-only plus start/stop/restart/down/logs
- The desktop (Tauri) build leaves `DOCKORE_STACKS_DIR` unset: pick any directory when creating a stack, and import stacks from arbitrary paths
- The desktop build requires the docker CLI on the host (compose v2 plugin preferred, v1 `docker-compose` as fallback); set `docker_cli_path` on the Settings page to point at a specific binary

## Release

Desktop releases are built by GitHub Actions (`.github/workflows/release.yml`, manual trigger): macOS arm64/x64 + Windows x64/arm64 installers are uploaded to a draft release.

## Versioning

The `VERSION` file is the single source of truth:

```bash
python3 scripts/sync_version.py <version>   # Sync to Cargo.toml / pyproject.toml / uv.lock
python3 scripts/sync_version.py --check     # Verify consistency
```

## License

See [LICENSE](LICENSE).
