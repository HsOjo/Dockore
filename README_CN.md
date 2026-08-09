# Dockore

<img src="images/icon.png" alt="Dockore" width="128" />

[English](README.md) | **中文**

一个简单、便捷、开箱即用的 Docker GUI 管理工具。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy(async) + SQLite + docker-py |
| 前端 | Vue 3 + TypeScript + Ant Design Vue + Pinia + Vue I18n |
| 桌面端 | Tauri 2（后端经 PyInstaller 打包为内嵌 sidecar） |
| 共享包 | openapi-typescript + openapi-fetch（前后端类型同步） |

## 项目结构

```
├── VERSION                 # 版本唯一来源
├── docker-compose.yml      # Web 形态部署
└── src/
    ├── backend/            # FastAPI 后端（uv 管理）
    ├── frontend/           # Vue3 前端 + src-tauri 桌面端
    ├── shared/             # @dockore/shared（API 类型/客户端、WS 封装）
    └── proxy/              # Web 形态聚合代理（nginx）
```

## 功能

- 容器：列表/详情/创建/运行/启动/停止/重启/更名/删除/日志（流式）/差异/提交镜像/执行命令/Web 终端
- 镜像：列表/详情/拉取（实时进度）/搜索/打标签/历史/删除
- 网络：列表/详情/创建/删除/连接/断开容器
- 卷：列表/详情/创建/删除
- 系统：版本信息；设置（Docker Host 等运行时配置）
- 明暗双主题、中英文双语、桌面（Tauri）+ Web 双形态

## 开发

```bash
pnpm install
pnpm gen:api        # 从后端 openapi.json 生成 TS 类型
pnpm dev            # 同时启动后端(8000)与前端(1420)
```

桌面端开发：`pnpm --filter @dockore/frontend dev`（需先 `pnpm build:backend` 生成 sidecar）

## 测试

```bash
pnpm test           # shared + backend + frontend 全部单测
pnpm --filter @dockore/frontend test:e2e   # Playwright e2e
```

## 构建

```bash
pnpm build                  # gen:api + shared + backend(PyInstaller) + frontend
pnpm build:frontend         # Tauri 桌面应用打包
```

## Docker Compose 部署（Web 形态）

```bash
docker compose up -d --build
```

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| DOCKORE_TOKEN | change-me | 后端访问令牌（前端连接时填写） |
| DOCKORE_PORT | 8000 | 后端 API 端口 |
| DOCKORE_FRONTEND_PORT | 8001 | 前端 SPA 端口 |
| DOCKORE_PROXY_PORT | 8002 | 聚合代理端口（API + WS + 前端同一入口） |
| DOCKORE_CORS_ORIGINS | 8001/8002 各源 | 允许跨域来源，逗号分隔 |

- 数据持久化在 `./data`（SQLite 设置）；backend 容器只读挂载宿主机 `/var/run/docker.sock`
- 通过 proxy（8002）访问时 API/WS 与页面同源；直连 frontend（8001）时在引导页填写后端地址 + Token

## 发布

桌面端安装包由 GitHub Actions 构建（`.github/workflows/release.yml`，手动触发）：macOS arm64/x64 + Windows x64/arm64 产物上传至 draft Release。

## 版本管理

`VERSION` 文件为唯一版本来源：

```bash
python3 scripts/sync_version.py <version>   # 同步到 Cargo.toml / pyproject.toml / uv.lock
python3 scripts/sync_version.py --check     # 校验一致性
```

## License

见 [LICENSE](LICENSE)。
