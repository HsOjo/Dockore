# dockore-backend

Dockore 的 FastAPI 后端：通过 docker-py SDK 管理容器/镜像/网络/存储卷，提供 REST API 与 WebSocket（事件广播、流式日志、终端）。

## 开发

```bash
uv sync --extra dev
uv run python -m app.main        # 或 DOCKORE_RELOAD=1 热重载
uv run --extra dev pytest
uv run python scripts/export_openapi.py
```

## 配置（环境变量）

- `DOCKORE_TOKEN`：访问令牌（默认 `dev-token-change-me`），客户端发送 `Authorization: Bearer <sha256hex(token)>`
- `DOCKORE_HOST` / `DOCKORE_PORT`：监听地址（默认 `127.0.0.1:8000`）
- `DOCKORE_DATA_DIR` / `DOCKORE_DB_URL`：SQLite 存储位置
- `DOCKORE_DOCKER_HOST`：Docker daemon 地址（优先级高于 `/api/settings` 中的 `docker_host`）
- `DOCKORE_TERMINAL_EXPIRES`：终端票据有效期秒数（默认 3600）

## 打包

```bash
uv run --extra dev python scripts/build.py   # PyInstaller onedir，供 Tauri sidecar 使用
```
