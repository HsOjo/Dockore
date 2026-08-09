FROM node:20-slim AS builder

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable

WORKDIR /app

# Copy workspace root configuration
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./

# Copy package manifests only for the packages involved in this build.
# This layer is cached unless package.json or the lockfile changes.
COPY src/shared/package.json ./src/shared/package.json
COPY src/frontend/package.json ./src/frontend/package.json

# Install only frontend and its dependencies.
# Because source files are not yet copied, dependency install is cached across
# source-only changes.
RUN pnpm --filter @dockore/frontend... install --frozen-lockfile

# Copy source files after dependencies are installed to maximize cache hits.
COPY src/shared ./src/shared
COPY src/frontend ./src/frontend
COPY VERSION ./

# Build shared package first
RUN pnpm --filter @dockore/shared build

# Build the frontend web app (remote mode, without Tauri)
RUN pnpm --filter @dockore/frontend build:vite

# Production stage: serve the static build with nginx
FROM nginx:alpine

COPY --from=builder /app/src/frontend/dist /usr/share/nginx/html
COPY src/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
