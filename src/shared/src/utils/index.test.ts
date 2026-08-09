import { describe, it, expect } from "vitest";
import {
  normalizeBaseURL,
  getDefaultServerURL,
  toWSURL,
  sha256Hex,
  encodeCredentials,
  decodeCredentials,
  maskToken,
  formatBytes,
  formatTime,
  relativeTime,
} from "./index.js";

describe("utils", () => {
  describe("normalizeBaseURL", () => {
    it("removes single trailing slash", () => {
      expect(normalizeBaseURL("http://localhost:8000/")).toBe("http://localhost:8000");
    });

    it("removes multiple trailing slashes", () => {
      expect(normalizeBaseURL("http://localhost:8000///")).toBe("http://localhost:8000");
    });

    it("leaves URL without slash unchanged", () => {
      expect(normalizeBaseURL("http://localhost:8000")).toBe("http://localhost:8000");
    });
  });

  describe("getDefaultServerURL", () => {
    const withWindow = (origin: string | undefined, fn: () => void) => {
      const originalWindow = globalThis.window;
      try {
        Object.defineProperty(globalThis, "window", {
          value: origin === undefined ? undefined : { location: { origin } },
          configurable: true,
          writable: true,
        });
        fn();
      } finally {
        Object.defineProperty(globalThis, "window", {
          value: originalWindow,
          configurable: true,
          writable: true,
        });
      }
    };

    it("returns window.location.origin for HTTP origins", () => {
      withWindow("http://localhost:5173", () => {
        expect(getDefaultServerURL()).toBe("http://localhost:5173");
      });
    });

    it("falls back to dev backend URL for non-HTTP origins in dev mode", () => {
      withWindow("tauri://localhost", () => {
        expect(getDefaultServerURL(true)).toBe("http://localhost:8000");
      });
    });

    it("returns empty string for non-HTTP origins in production mode", () => {
      withWindow("tauri://localhost", () => {
        expect(getDefaultServerURL(false)).toBe("");
      });
    });

    it("returns empty string when window is undefined", () => {
      withWindow(undefined, () => {
        expect(getDefaultServerURL()).toBe("");
      });
    });
  });

  describe("toWSURL", () => {
    it("converts http to ws", () => {
      expect(toWSURL("http://localhost:8000")).toBe("ws://localhost:8000");
    });

    it("converts https to wss", () => {
      expect(toWSURL("https://dockore.example.com")).toBe("wss://dockore.example.com");
    });

    it("strips trailing slash", () => {
      expect(toWSURL("http://localhost:8000/")).toBe("ws://localhost:8000");
    });
  });

  describe("sha256Hex", () => {
    it("returns a 64-char hex string", () => {
      expect(sha256Hex("token")).toMatch(/^[a-f0-9]{64}$/);
    });

    it("matches known sha256 value", () => {
      // echo -n "" | sha256sum
      expect(sha256Hex("")).toBe("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    });
  });

  describe("encodeCredentials / decodeCredentials", () => {
    it("round-trips correctly", () => {
      const encoded = encodeCredentials("http://localhost", "my-token");
      const decoded = decodeCredentials(encoded);
      expect(decoded).toEqual({ baseURL: "http://localhost", token: "my-token" });
    });

    it("returns null for invalid input", () => {
      expect(decodeCredentials("not-valid-base64!!!")).toBeNull();
      expect(decodeCredentials(btoa("not-json"))).toBeNull();
    });
  });

  describe("maskToken", () => {
    it("returns empty string for empty token", () => {
      expect(maskToken("")).toBe("");
    });

    it("returns token unchanged when length is 4 or less", () => {
      expect(maskToken("ab")).toBe("ab");
      expect(maskToken("abcd")).toBe("abcd");
    });

    it("masks middle part and keeps first and last 2 characters", () => {
      expect(maskToken("abcdef")).toBe("ab***ef");
      expect(maskToken("my-token")).toBe("my***en");
    });
  });

  describe("formatBytes", () => {
    it("formats zero", () => {
      expect(formatBytes(0)).toBe("0 B");
    });

    it("formats bytes without decimals", () => {
      expect(formatBytes(512)).toBe("512 B");
    });

    it("formats larger units", () => {
      expect(formatBytes(2048)).toBe("2.0 KB");
      expect(formatBytes(5 * 1024 * 1024)).toBe("5.0 MB");
      expect(formatBytes(3 * 1024 ** 3)).toBe("3.0 GB");
    });

    it("returns empty for null/undefined/NaN", () => {
      expect(formatBytes(null)).toBe("");
      expect(formatBytes(undefined)).toBe("");
      expect(formatBytes(NaN)).toBe("");
    });
  });

  describe("formatTime", () => {
    it("formats ISO string to locale string", () => {
      const result = formatTime("2024-01-15T08:30:00Z", "zh-CN");
      expect(result).toContain("2024");
      expect(result).toContain("01");
      expect(result).toContain("15");
    });

    it("returns empty for null/undefined", () => {
      expect(formatTime(null)).toBe("");
      expect(formatTime(undefined)).toBe("");
    });

    it("returns original for invalid date", () => {
      expect(formatTime("not-a-date")).toBe("not-a-date");
    });
  });

  describe("relativeTime", () => {
    it("returns '刚刚' for very recent time", () => {
      const now = new Date().toISOString();
      expect(relativeTime(now, "zh-CN")).toBe("刚刚");
    });

    it("falls back to formatTime for old dates", () => {
      const old = "2020-01-01T00:00:00Z";
      const result = relativeTime(old, "zh-CN");
      expect(result).toContain("2020");
    });

    it("supports English locale", () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      expect(relativeTime(fiveMinAgo, "en")).toBe("5m ago");
    });

    it("returns empty for null/undefined", () => {
      expect(relativeTime(null)).toBe("");
      expect(relativeTime(undefined)).toBe("");
    });
  });
});
