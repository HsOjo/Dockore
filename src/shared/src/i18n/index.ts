export type Locale = "zh-CN" | "en";

export const DEFAULT_LOCALE: Locale = "zh-CN";

export const SUPPORTED_LOCALES: Locale[] = ["zh-CN", "en"];

export function resolveLocale(locale?: string | null): Locale {
  if (!locale) return DEFAULT_LOCALE;
  if (SUPPORTED_LOCALES.includes(locale as Locale)) return locale as Locale;
  if (locale.startsWith("zh")) return "zh-CN";
  if (locale.startsWith("en")) return "en";
  return DEFAULT_LOCALE;
}

const messages: Record<Locale, Record<string, string>> = {
  "zh-CN": {
    "notification.image.pull.completed": "镜像 {{image}} 拉取完成",
    "notification.image.pull.error": "镜像 {{image}} 拉取失败",
  },
  "en": {
    "notification.image.pull.completed": "Image {{image}} pulled",
    "notification.image.pull.error": "Failed to pull image {{image}}",
  },
};

export function renderNotification(
  type: string,
  params: Record<string, any> | null | undefined,
  locale: string = DEFAULT_LOCALE
): string {
  const key = `notification.${type}`;
  const tmpl = messages[locale as Locale]?.[key] || messages["en"]?.[key] || key;
  if (!params) return tmpl;
  return tmpl.replace(/\{\{(\w+)\}\}/g, (_, k) => String(params[k] ?? ""));
}
