function isTauriEnv(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as any;
  return !!(w.__TAURI__ || w.__TAURI_INTERNALS__ || w.__TAURI_METADATA__);
}

let _isTauriCache: boolean | null = isTauriEnv() ? true : null;

export async function detectTauri(): Promise<boolean> {
  if (_isTauriCache !== null) return _isTauriCache;
  _isTauriCache = isTauriEnv();
  return _isTauriCache;
}

export function isTauri(): boolean {
  return _isTauriCache ?? false;
}

export interface ServerConfig {
  baseURL: string;
  token: string;
  isBuiltIn?: boolean;
}

const SERVER_STORAGE_KEY = "dockore_server";

export async function getPlatformConfig(): Promise<ServerConfig> {
  const empty = { baseURL: "", token: "", isBuiltIn: false };

  const raw = localStorage.getItem(SERVER_STORAGE_KEY);
  if (!raw) return empty;

  try {
    const parsed = JSON.parse(raw);
    return {
      baseURL: parsed.baseURL || "",
      token: parsed.token || "",
      isBuiltIn: parsed.isBuiltIn ?? false,
    };
  } catch {
    return empty;
  }
}

export function savePlatformConfig(cfg: ServerConfig) {
  localStorage.setItem(SERVER_STORAGE_KEY, JSON.stringify(cfg));
}

import { ref, type Ref } from "vue";

export const UI_STORAGE_KEY = "dockore_ui";

type UISettings = {
  theme: string;
  locale: string;
};

const defaults: UISettings = { theme: "auto", locale: "zh-CN" };

function loadUISettings(): UISettings {
  if (typeof window === "undefined") return { ...defaults };
  const raw = localStorage.getItem(UI_STORAGE_KEY);
  if (!raw) return { ...defaults };
  try {
    const parsed = JSON.parse(raw);
    return {
      theme: parsed.theme || defaults.theme,
      locale: parsed.locale || defaults.locale,
    };
  } catch {
    return { ...defaults };
  }
}

const uiState = ref<UISettings>(loadUISettings());

export const uiSettings = uiState;

export function getUISettings(): Ref<UISettings> {
  return uiState;
}

export function getEffectiveTheme(theme: string): "light" | "dark" {
  if (theme === "dark") return "dark";
  if (theme === "light") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function saveUISettings(settings: Partial<UISettings>) {
  uiState.value = { ...uiState.value, ...settings };
  localStorage.setItem(UI_STORAGE_KEY, JSON.stringify(uiState.value));
}

export function hasUISettings(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(UI_STORAGE_KEY) !== null;
}

export function isMac(): boolean {
  if (typeof navigator === "undefined") return false;
  const uaData = (navigator as any).userAgentData;
  if (uaData?.platform) {
    return /macOS|Mac/i.test(uaData.platform);
  }
  return (
    /Mac/i.test(navigator.platform || "") ||
    /Mac OS X|macOS/i.test(navigator.userAgent || "")
  );
}

export function needsMacTitleInset(): boolean {
  return isTauri() && isMac();
}

export async function openExternal(url: string) {
  if (await detectTauri()) {
    const { open } = await import("@tauri-apps/plugin-shell");
    await open(url);
  } else {
    window.open(url, "_blank");
  }
}

export async function pickDirectory(title?: string): Promise<string | null> {
  if (!(await detectTauri())) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const selected = await open({ directory: true, title });
  return typeof selected === "string" ? selected : null;
}

const LAST_STACK_DIR_KEY = "dockore_last_stack_dir";

export function getLastStackDir(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(LAST_STACK_DIR_KEY) || "";
}

export function saveLastStackDir(dir: string) {
  localStorage.setItem(LAST_STACK_DIR_KEY, dir);
}

let _windowApi: any = null;

async function getWindowApi() {
  if (_windowApi) return _windowApi;
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  _windowApi = getCurrentWindow();
  return _windowApi;
}

export async function startDraggingWindow() {
  if (await detectTauri()) {
    const win = await getWindowApi();
    await win.startDragging();
  }
}

export async function sendNotification(title: string, body: string) {
  if (await detectTauri()) {
    try {
      const { sendNotification: notify } = await import("@tauri-apps/plugin-notification");
      notify({ title, body });
    } catch {
      // ignore
    }
  }
}

let _menuSetupDone = false;

export async function setupAppMenu(
  reloadText: string,
  preferencesText: string,
  devToolsText: string,
  checkUpdateText: string
) {
  if (_menuSetupDone || !(await detectTauri())) return;
  _menuSetupDone = true;

  const { Menu, Submenu, MenuItem } = await import("@tauri-apps/api/menu");
  const { emit } = await import("@tauri-apps/api/event");
  const menu = await Menu.default();

  if (await menu.get("reload")) {
    return;
  }

  const appMenu = await findAppSubmenu(menu);
  const prefsAccelerator = isMac() ? "Cmd+," : "Ctrl+,";
  const prefsItem = await MenuItem.new({
    id: "preferences",
    text: preferencesText,
    accelerator: prefsAccelerator,
    action: () => {
      emit("menu:open-settings");
    },
  });
  if (appMenu) {
    await appMenu.insert(prefsItem, 2);
  } else {
    const editMenu = await findOrCreateEditSubmenu(menu, Submenu);
    await editMenu.append(prefsItem);
  }

  const checkUpdateItem = await MenuItem.new({
    id: "check-update",
    text: checkUpdateText,
    action: () => {
      emit("menu:check-update");
    },
  });
  if (appMenu) {
    await appMenu.insert(checkUpdateItem, 3);
  } else {
    const editMenu = await findOrCreateEditSubmenu(menu, Submenu);
    await editMenu.append(checkUpdateItem);
  }

  const viewMenu = await findOrCreateViewSubmenu(menu, Submenu);

  const devToolsAccelerator = isMac() ? "Cmd+Option+I" : "Ctrl+Shift+I";
  const devToolsItem = await MenuItem.new({
    id: "developer-tools",
    text: devToolsText,
    accelerator: devToolsAccelerator,
    action: async () => {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("toggle_devtools").catch(console.error);
    },
  });
  await viewMenu.append(devToolsItem);

  const accelerator = isMac() ? "Cmd+R" : "Ctrl+R";
  const reloadItem = await MenuItem.new({
    id: "reload",
    text: reloadText,
    accelerator,
    action: () => {
      window.location.reload();
    },
  });

  await viewMenu.append(reloadItem);
  await menu.setAsAppMenu();
}

type TauriMenu = import("@tauri-apps/api/menu").Menu;
type TauriSubmenu = import("@tauri-apps/api/menu").Submenu;

async function findAppSubmenu(menu: TauriMenu): Promise<TauriSubmenu | null> {
  const items = await menu.items();
  const first = items[0];
  if (first && first.kind === "Submenu") {
    return first as TauriSubmenu;
  }
  return null;
}

async function findOrCreateEditSubmenu(
  menu: TauriMenu,
  Submenu: typeof import("@tauri-apps/api/menu").Submenu
): Promise<TauriSubmenu> {
  const items = await menu.items();
  for (const item of items) {
    if (item.kind === "Submenu") {
      const text = await (item as TauriSubmenu).text();
      if (text === "Edit" || text === "编辑") {
        return item as TauriSubmenu;
      }
    }
  }
  return await Submenu.new({ text: "Edit" });
}

async function findOrCreateViewSubmenu(
  menu: TauriMenu,
  Submenu: typeof import("@tauri-apps/api/menu").Submenu
): Promise<TauriSubmenu> {
  const items = await menu.items();
  for (const item of items) {
    if (item.kind === "Submenu") {
      const text = await (item as TauriSubmenu).text();
      if (text === "View" || text === "视图") {
        return item as TauriSubmenu;
      }
    }
  }
  return await Submenu.new({ text: "View" });
}
