import { sha256 } from "js-sha256";

export function normalizeBaseURL(url: string): string {
  return url.replace(/\/+$/, "");
}

export function getDefaultServerURL(isDev = import.meta.env?.DEV): string {
  if (typeof window === "undefined") return "";
  const origin = window.location.origin;
  // Browser dev/prod can use the current origin when served together with the backend.
  // Tauri/Capacitor webviews use custom schemes (e.g. tauri://localhost) which cannot be
  // used as an API base URL, so fall back to the dev backend URL in development.
  if (origin.startsWith("http://") || origin.startsWith("https://")) {
    return origin;
  }
  if (isDev) return "http://localhost:8000";
  return "";
}

export function toWSURL(baseURL: string): string {
  const base = normalizeBaseURL(baseURL);
  return base.replace(/^http/, "ws");
}

export function sha256Hex(input: string): string {
  return sha256(input);
}

export function encodeCredentials(baseURL: string, token: string): string {
  const payload = JSON.stringify({ b: normalizeBaseURL(baseURL), t: token });
  return btoa(payload);
}

export function decodeCredentials(encoded: string): { baseURL: string; token: string } | null {
  try {
    const payload = atob(encoded);
    const parsed = JSON.parse(payload);
    return { baseURL: parsed.b, token: parsed.t };
  } catch {
    return null;
  }
}

export function maskToken(token: string): string {
  if (!token) return "";
  if (token.length <= 4) return token;
  return token.slice(0, 2) + "***" + token.slice(-2);
}

export function formatBytes(bytes: number | null | undefined, decimals = 1): string {
  if (bytes === null || bytes === undefined || isNaN(bytes)) return "";
  if (bytes === 0) return "0 B";
  if (bytes < 0) return "-" + formatBytes(-bytes, decimals);
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(i === 0 ? 0 : decimals)} ${units[i]}`;
}

export function formatTime(iso: string | null | undefined, locale = "zh-CN"): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(locale, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function relativeTime(iso: string | null | undefined, locale = "zh-CN"): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = Date.now();
  const diff = now - d.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (locale.startsWith("zh")) {
    if (minutes < 1) return "刚刚";
    if (minutes < 60) return `${minutes} 分钟前`;
    if (hours < 24) return `${hours} 小时前`;
    if (days < 30) return `${days} 天前`;
    return formatTime(iso, locale);
  }

  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 30) return `${days}d ago`;
  return formatTime(iso, locale);
}
