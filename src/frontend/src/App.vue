<template>
  <a-config-provider :theme="themeConfig" :locale="antdLocale">
    <div v-if="loading" class="backend-loading">
      <a-spin size="large" />
      <p>{{ t("loadingBackend") }}</p>
    </div>
    <router-view v-else />
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useI18n } from "vue-i18n";
import { theme as antdTheme } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import enUS from "ant-design-vue/es/locale/en_US";
import { useConnectionStore } from "@/stores";
import { getUISettings, saveUISettings, getEffectiveTheme } from "@/platform";

const { t } = useI18n();
const conn = useConnectionStore();
const loading = computed(() => conn.isInitializing);

const ui = getUISettings();

const themeConfig = computed(() => ({
  algorithm:
    getEffectiveTheme(ui.value.theme) === "dark"
      ? antdTheme.darkAlgorithm
      : antdTheme.defaultAlgorithm,
}));

const antdLocale = computed(() => (ui.value.locale.startsWith("zh") ? zhCN : enUS));

function applyThemeClass(theme: string) {
  document.body.classList.remove("dockore-theme-light", "dockore-theme-dark");
  const resolved = getEffectiveTheme(theme);
  document.body.classList.add(`dockore-theme-${resolved}`);
}

applyThemeClass(ui.value.theme);

watch(
  () => ui.value.theme,
  (theme, oldTheme) => {
    applyThemeClass(theme);
    if (oldTheme !== undefined) {
      saveUISettings({ theme });
    }
  }
);

const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
mediaQuery.addEventListener("change", () => {
  if (ui.value.theme === "auto") {
    applyThemeClass("auto");
  }
});
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
  overscroll-behavior: none;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

.backend-loading {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}
</style>
