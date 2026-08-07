import { describe, it, expect } from "vitest";
import { renderNotification, resolveLocale, DEFAULT_LOCALE, SUPPORTED_LOCALES } from "./index.js";

describe("i18n", () => {
  it("defaults to zh-CN", () => {
    expect(DEFAULT_LOCALE).toBe("zh-CN");
    expect(SUPPORTED_LOCALES).toContain("en");
  });

  it("renders image pull completed notification in Chinese", () => {
    const result = renderNotification("image.pull.completed", { image: "nginx:latest" }, "zh-CN");
    expect(result).toBe("镜像 nginx:latest 拉取完成");
  });

  it("renders image pull error in English", () => {
    const result = renderNotification("image.pull.error", { image: "redis:7" }, "en");
    expect(result).toBe("Failed to pull image redis:7");
  });

  it("falls back to English when locale missing", () => {
    const result = renderNotification("image.pull.completed", { image: "busybox" }, "fr-FR");
    expect(result).toBe("Image busybox pulled");
  });

  it("returns template key when type unknown", () => {
    const result = renderNotification("unknown.type", {}, "en");
    expect(result).toBe("notification.unknown.type");
  });

  it("handles missing params gracefully", () => {
    const result = renderNotification("image.pull.completed", null, "zh-CN");
    expect(result).toBe("镜像 {{image}} 拉取完成");
  });

  it("resolveLocale normalizes locale strings", () => {
    expect(resolveLocale("zh")).toBe("zh-CN");
    expect(resolveLocale("en-US")).toBe("en");
    expect(resolveLocale("fr-FR")).toBe("zh-CN");
    expect(resolveLocale(null)).toBe("zh-CN");
  });
});
