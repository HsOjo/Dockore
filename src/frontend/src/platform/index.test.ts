import { describe, it, expect, vi, beforeEach } from "vitest";
import { detectTauri, isTauri, getPlatformConfig, savePlatformConfig, hasUISettings } from "./index.js";

vi.mock("@tauri-apps/api/core", () => {
  throw new Error("not available");
});

describe("platform", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("detectTauri returns false when tauri api unavailable", async () => {
    const result = await detectTauri();
    expect(result).toBe(false);
  });

  it("isTauri reflects detectTauri result", async () => {
    await detectTauri();
    expect(isTauri()).toBe(false);
  });

  it("getPlatformConfig returns empty when localStorage empty", async () => {
    const cfg = await getPlatformConfig();
    expect(cfg).toEqual({ baseURL: "", token: "", isBuiltIn: false });
  });

  it("savePlatformConfig and getPlatformConfig round-trip", async () => {
    savePlatformConfig({ baseURL: "http://localhost:8000", token: "my-token", isBuiltIn: false });
    const cfg = await getPlatformConfig();
    expect(cfg).toEqual({ baseURL: "http://localhost:8000", token: "my-token", isBuiltIn: false });
  });

  it("built-in config is preserved", async () => {
    savePlatformConfig({ baseURL: "http://127.0.0.1:8000", token: "dev-token-change-me", isBuiltIn: true });
    const cfg = await getPlatformConfig();
    expect(cfg).toEqual({ baseURL: "http://127.0.0.1:8000", token: "dev-token-change-me", isBuiltIn: true });
  });

  it("getPlatformConfig returns empty for invalid JSON without clearing storage", async () => {
    localStorage.setItem("dockore_server", "not-json");
    const cfg = await getPlatformConfig();
    expect(cfg).toEqual({ baseURL: "", token: "", isBuiltIn: false });
    expect(localStorage.getItem("dockore_server")).toBe("not-json");
  });

  it("hasUISettings returns false when dockore_ui is missing", () => {
    expect(hasUISettings()).toBe(false);
  });

  it("hasUISettings returns true when dockore_ui is present", () => {
    localStorage.setItem("dockore_ui", JSON.stringify({ theme: "auto", locale: "zh-CN" }));
    expect(hasUISettings()).toBe(true);
  });
});
