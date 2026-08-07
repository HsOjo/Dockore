import { defineStore } from "pinia";
import { ref } from "vue";
import { invoke } from "@tauri-apps/api/core";
import {
  api,
  normalizeBaseURL,
  setBaseURL,
  setAuthToken,
  toWSURL,
  wsClient,
} from "@dockore/shared";
import type { components } from "@dockore/shared/api";
import { getPlatformConfig, savePlatformConfig, isTauri } from "@/platform";

export type ContainerItem = components["schemas"]["ContainerItem"];
export type ContainerCreate = components["schemas"]["ContainerCreate"];
export type ContainerDiff = components["schemas"]["ContainerDiff"];
export type ImageItem = components["schemas"]["ImageItem"];
export type ImageSearchItem = components["schemas"]["ImageSearchItem"];
export type HistoryItem = components["schemas"]["HistoryItem"];
export type NetworkItem = components["schemas"]["NetworkItem"];
export type NetworkCreate = components["schemas"]["NetworkCreate"];
export type VolumeItem = components["schemas"]["VolumeItem"];
export type VolumeCreate = components["schemas"]["VolumeCreate"];
export type SystemVersion = components["schemas"]["SystemVersion"];
export type SettingsData = components["schemas"]["SettingsData"];
export type ExecResult = components["schemas"]["ExecResult"];

function isValidJsonResponse(body: unknown): boolean {
  if (typeof body !== "string") return false;
  try {
    JSON.parse(body);
    return true;
  } catch {
    return false;
  }
}

export function errorMessage(e: any): string {
  if (!e) return "Unknown error";
  if (typeof e === "string") return e;
  if (Array.isArray(e.detail)) {
    return e.detail.map((d: any) => d.msg || String(d)).join("; ");
  }
  return e.detail || e.message || String(e);
}

async function must<T>(p: Promise<{ data?: T; error?: any }>): Promise<T> {
  const { data, error } = await p;
  if (error) throw new Error(errorMessage(error));
  return data as T;
}

function reportDeleteFailures(failed: Record<string, string> | undefined) {
  if (failed && Object.keys(failed).length > 0) {
    throw new Error(
      Object.entries(failed)
        .map(([id, msg]) => `${id}: ${msg}`)
        .join("; ")
    );
  }
}

let wsHandlersRegistered = false;

function registerWebSocketHandlers() {
  if (wsHandlersRegistered) return;
  wsHandlersRegistered = true;
  wsClient.on("image.pull", (data: any) => {
    if (data?.status === "done") {
      const imageStore = useImageStore();
      imageStore.fetchAll().catch(() => {});
    }
  });
}

interface BuiltinBackendConfig {
  port: number;
  token: string;
}

// Fallback token used in dev mode where the backend is not bundled.
export const BUILTIN_TOKEN = "dev-token-change-me";

export async function pollUntil<T>(
  fn: () => Promise<T>,
  predicate: (result: T) => boolean,
  options: { interval: number; timeout: number }
): Promise<T> {
  const start = Date.now();
  while (true) {
    const result = await fn();
    if (predicate(result)) return result;
    const elapsed = Date.now() - start;
    if (elapsed >= options.timeout) {
      throw new Error("Polling timed out");
    }
    await new Promise((resolve) =>
      setTimeout(resolve, Math.min(options.interval, options.timeout - elapsed))
    );
  }
}

export const useConnectionStore = defineStore("connection", () => {
  const baseURL = ref("");
  const token = ref("");
  const isReady = ref(false);
  const isBuiltIn = ref(false);
  const isInitializing = ref(false);
  const initError = ref("");

  async function init() {
    isInitializing.value = true;
    initError.value = "";
    try {
      const cfg = await getPlatformConfig();
      let url = cfg.baseURL;
      let t = cfg.token;
      let builtIn = cfg.isBuiltIn ?? false;

      if (builtIn && isTauri() && import.meta.env.PROD) {
        // Desktop release builds bundle the backend; start it on demand and
        // refresh the port/token so each launch uses a fresh built-in instance.
        const builtin = await invoke<BuiltinBackendConfig>("start_builtin_backend");
        url = `http://127.0.0.1:${builtin.port}`;
        t = builtin.token;

        // Wait for the bundled backend to be ready before the health check.
        try {
          await pollUntil(
            () => invoke<boolean>("is_backend_ready"),
            (ready) => ready,
            { interval: 500, timeout: 10000 }
          );
        } catch {
          throw new Error("等待内建后端启动超时");
        }
      }

      if (url && t) {
        await connect(url, t, builtIn);
      }
    } catch (e: any) {
      console.error("Failed to initialize connection:", e);
      initError.value = e.message || "初始化连接失败";
    } finally {
      isInitializing.value = false;
    }
  }

  async function connect(url: string, t: string, builtIn = false) {
    // Clear stale data from any previous connection.
    resetAllStores();

    const normalized = normalizeBaseURL(url);

    // Set up the client so the health check can reach the server.
    setBaseURL(normalized);
    setAuthToken(t);

    // All connections must be reachable before we switch to the main page.
    // Poll the health endpoint, but only retry for network-level failures.
    // Any HTTP response (including non-2xx) means the server has responded and
    // we should stop and report the actual status instead of retrying.
    let healthResult: { error?: unknown; response?: Response; body?: string } | undefined;
    try {
      healthResult = await pollUntil(
        async () => {
          try {
            // Use parseAs: "text" so a non-JSON response (e.g. HTML fallback from
            // the dev server) does not throw a SyntaxError and is treated as a
            // server-level response instead of a network error.
            const result = await api.GET("/api/health", { parseAs: "text" } as any);
            return { error: result.error, response: result.response, body: result.data as string };
          } catch (e) {
            return { error: e, response: undefined, body: undefined };
          }
        },
        (result) => result.response !== undefined,
        { interval: 1000, timeout: 10000 }
      );
    } catch {
      setBaseURL("");
      setAuthToken("");
      throw new Error(`无法连接到服务器: ${url}`);
    }

    if (
      healthResult?.response?.status !== 200 ||
      !isValidJsonResponse(healthResult.body)
    ) {
      setBaseURL("");
      setAuthToken("");
      throw new Error(`服务器返回错误: ${healthResult?.response?.status ?? "unknown"}`);
    }

    // Validate token; use text parsing for the same reason as health check.
    const validateResult = await api.GET("/api/auth/validate", { parseAs: "text" } as any);
    const validateStatus = (validateResult.response as Response | undefined)?.status;
    if (validateStatus !== 200) {
      setBaseURL("");
      setAuthToken("");
      if (validateStatus === 401) {
        throw new Error("访问令牌无效");
      }
      throw new Error(
        validateStatus ? `服务器返回错误: ${validateStatus}` : `无法连接到服务器: ${url}`
      );
    }
    if (!isValidJsonResponse(validateResult.data)) {
      setBaseURL("");
      setAuthToken("");
      throw new Error("服务器返回错误");
    }

    baseURL.value = normalized;
    token.value = t;
    isBuiltIn.value = builtIn;
    savePlatformConfig({ baseURL: normalized, token: t, isBuiltIn: builtIn });
    isReady.value = true;
    wsClient.connect(`${toWSURL(normalized)}/ws`, t);
    registerWebSocketHandlers();
  }

  async function disconnect() {
    wsClient.disconnect();
    setBaseURL("");
    setAuthToken("");
    resetAllStores();
    baseURL.value = "";
    token.value = "";
    isReady.value = false;
    isBuiltIn.value = false;
  }

  return { baseURL, token, isReady, isBuiltIn, isInitializing, initError, init, connect, disconnect };
});

export const useContainerStore = defineStore("container", () => {
  const containers = ref<ContainerItem[]>([]);
  const loading = ref(false);
  const showAll = ref(true);

  async function fetchAll() {
    loading.value = true;
    try {
      containers.value = await must(
        api.GET("/api/containers", { params: { query: { all: showAll.value } } })
      );
    } finally {
      loading.value = false;
    }
  }

  async function fetch(id: string) {
    return await must(api.GET("/api/containers/{id}", { params: { path: { id } } }));
  }

  async function create(body: ContainerCreate, run: boolean) {
    const data = await must(
      api.POST("/api/containers", { params: { query: { run } }, body })
    );
    await fetchAll().catch(() => {});
    return data;
  }

  async function remove(ids: string[]) {
    const result = await must(api.DELETE("/api/containers", { body: { ids } }));
    reportDeleteFailures(result.failed);
    await fetchAll().catch(() => {});
  }

  async function start(id: string) {
    await must(api.POST("/api/containers/{id}/start", { params: { path: { id } } }));
    await fetchAll().catch(() => {});
  }

  async function stop(id: string, timeout?: number) {
    await must(
      api.POST("/api/containers/{id}/stop", { params: { path: { id }, query: { timeout } } })
    );
    await fetchAll().catch(() => {});
  }

  async function restart(id: string, timeout?: number) {
    await must(
      api.POST("/api/containers/{id}/restart", { params: { path: { id }, query: { timeout } } })
    );
    await fetchAll().catch(() => {});
  }

  async function rename(id: string, name: string) {
    await must(
      api.POST("/api/containers/{id}/rename", { params: { path: { id } }, body: { name } })
    );
    await fetchAll().catch(() => {});
  }

  async function diff(id: string) {
    return await must(api.GET("/api/containers/{id}/diff", { params: { path: { id } } }));
  }

  async function commit(
    id: string,
    body: { name: string; tag?: string | null; message?: string | null; author?: string | null }
  ) {
    return await must(
      api.POST("/api/containers/{id}/commit", { params: { path: { id } }, body })
    );
  }

  async function exec(id: string, command: string) {
    return await must(
      api.POST("/api/containers/{id}/exec", {
        params: { path: { id } },
        body: { command, interactive: true, tty: true, privileged: false },
      })
    );
  }

  async function createTerminalTicket(id: string, command?: string | null) {
    return await must(
      api.POST("/api/containers/{id}/terminal", {
        params: { path: { id } },
        body: { command: command ?? null },
      })
    );
  }

  function reset() {
    containers.value = [];
    loading.value = false;
    showAll.value = true;
  }

  return {
    containers,
    loading,
    showAll,
    fetchAll,
    fetch,
    create,
    remove,
    start,
    stop,
    restart,
    rename,
    diff,
    commit,
    exec,
    createTerminalTicket,
    reset,
  };
});

export const useImageStore = defineStore("image", () => {
  const images = ref<ImageItem[]>([]);
  const loading = ref(false);
  const showAll = ref(false);

  async function fetchAll() {
    loading.value = true;
    try {
      images.value = await must(
        api.GET("/api/images", { params: { query: { all: showAll.value } } })
      );
    } finally {
      loading.value = false;
    }
  }

  async function fetch(id: string) {
    return await must(api.GET("/api/images/{id}", { params: { path: { id } } }));
  }

  async function remove(ids: string[], tagOnly = false) {
    const result = await must(
      api.DELETE("/api/images", { body: { ids, tag_only: tagOnly } })
    );
    reportDeleteFailures(result.failed);
    await fetchAll().catch(() => {});
  }

  async function pull(name: string, tag?: string | null) {
    return await must(api.POST("/api/images/pull", { body: { name, tag: tag ?? null } }));
  }

  async function tag(id: string, name: string, tagValue?: string | null) {
    await must(
      api.POST("/api/images/{id}/tag", {
        params: { path: { id } },
        body: { name, tag: tagValue ?? null },
      })
    );
    await fetchAll().catch(() => {});
  }

  async function history(id: string) {
    return await must(api.GET("/api/images/{id}/history", { params: { path: { id } } }));
  }

  async function search(keyword: string) {
    return await must(
      api.GET("/api/images/search/{keyword}", { params: { path: { keyword } } })
    );
  }

  function reset() {
    images.value = [];
    loading.value = false;
    showAll.value = false;
  }

  return { images, loading, showAll, fetchAll, fetch, remove, pull, tag, history, search, reset };
});

export const useNetworkStore = defineStore("network", () => {
  const networks = ref<NetworkItem[]>([]);
  const loading = ref(false);

  async function fetchAll() {
    loading.value = true;
    try {
      networks.value = await must(api.GET("/api/networks"));
    } finally {
      loading.value = false;
    }
  }

  async function fetch(id: string) {
    return await must(api.GET("/api/networks/{id}", { params: { path: { id } } }));
  }

  async function create(body: NetworkCreate) {
    const data = await must(api.POST("/api/networks", { body }));
    await fetchAll().catch(() => {});
    return data;
  }

  async function remove(ids: string[]) {
    const result = await must(api.DELETE("/api/networks", { body: { ids } }));
    reportDeleteFailures(result.failed);
    await fetchAll().catch(() => {});
  }

  async function connect(id: string, containerId: string, ipv4Address?: string | null) {
    await must(
      api.POST("/api/networks/{id}/connect", {
        params: { path: { id } },
        body: { container_id: containerId, ipv4_address: ipv4Address || null },
      })
    );
  }

  async function disconnect(id: string, containerId: string, force = false) {
    await must(
      api.POST("/api/networks/{id}/disconnect", {
        params: { path: { id }, query: { force } },
        body: { container_id: containerId },
      })
    );
  }

  function reset() {
    networks.value = [];
    loading.value = false;
  }

  return { networks, loading, fetchAll, fetch, create, remove, connect, disconnect, reset };
});

export const useVolumeStore = defineStore("volume", () => {
  const volumes = ref<VolumeItem[]>([]);
  const loading = ref(false);

  async function fetchAll() {
    loading.value = true;
    try {
      volumes.value = await must(api.GET("/api/volumes"));
    } finally {
      loading.value = false;
    }
  }

  async function fetch(id: string) {
    return await must(api.GET("/api/volumes/{id}", { params: { path: { id } } }));
  }

  async function create(body: VolumeCreate) {
    const data = await must(api.POST("/api/volumes", { body }));
    await fetchAll().catch(() => {});
    return data;
  }

  async function remove(ids: string[]) {
    const result = await must(api.DELETE("/api/volumes", { body: { ids } }));
    reportDeleteFailures(result.failed);
    await fetchAll().catch(() => {});
  }

  function reset() {
    volumes.value = [];
    loading.value = false;
  }

  return { volumes, loading, fetchAll, fetch, create, remove, reset };
});

export const useSystemStore = defineStore("system", () => {
  const version = ref<SystemVersion | null>(null);

  async function fetchVersion() {
    version.value = await must(api.GET("/api/system/version"));
  }

  function reset() {
    version.value = null;
  }

  return { version, fetchVersion, reset };
});

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<SettingsData | null>(null);

  async function fetch() {
    settings.value = await must(api.GET("/api/settings"));
  }

  async function update(vals: { docker_host?: string | null }) {
    settings.value = await must(api.PUT("/api/settings", { body: vals }));
  }

  function reset() {
    settings.value = null;
  }

  return { settings, fetch, update, reset };
});

export function resetAllStores() {
  useContainerStore().reset();
  useImageStore().reset();
  useNetworkStore().reset();
  useVolumeStore().reset();
  useSystemStore().reset();
  useSettingsStore().reset();
}
