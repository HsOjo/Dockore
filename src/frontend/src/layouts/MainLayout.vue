<template>
  <a-layout class="main-layout">
    <a-layout-sider :width="200" theme="light" class="sider">
      <div class="logo" :class="{ 'mac-inset': macInset }" data-tauri-drag-region>{{ t("appName") }}</div>
      <a-menu v-model:selectedKeys="selectedKeys" mode="inline" class="menu">
        <a-menu-item key="/containers">
          <router-link to="/containers">{{ t("menu.containers") }}</router-link>
        </a-menu-item>
        <a-menu-item key="/images">
          <router-link to="/images">{{ t("menu.images") }}</router-link>
        </a-menu-item>
        <a-menu-item key="/networks">
          <router-link to="/networks">{{ t("menu.networks") }}</router-link>
        </a-menu-item>
        <a-menu-item key="/volumes">
          <router-link to="/volumes">{{ t("menu.volumes") }}</router-link>
        </a-menu-item>
        <a-menu-item key="/system">
          <router-link to="/system">{{ t("menu.system") }}</router-link>
        </a-menu-item>
      </a-menu>
      <div class="sider-footer">
        <a-menu :selectedKeys="settingsKey" mode="inline">
          <a-menu-item key="/settings">
            <router-link to="/settings">{{ t("menu.settings") }}</router-link>
          </a-menu-item>
        </a-menu>
      </div>
    </a-layout-sider>
    <a-layout>
      <a-layout-header
        class="header"
        data-tauri-drag-region
        @mousedown="startDraggingWindow"
      >
        <div class="header-left" data-tauri-drag-region="no-drag">
          <a-badge :status="conn.isReady ? 'success' : 'error'" />
          <span class="server-url">{{ conn.baseURL }}</span>
          <a-tag v-if="conn.isBuiltIn" color="blue">{{ t("connection.builtInTag") }}</a-tag>
        </div>
        <div class="header-right" data-tauri-drag-region="no-drag">
          <a-tooltip :title="t('theme')">
            <a-button type="text" @click="toggleTheme">
              <BulbFilled v-if="ui.theme === 'dark'" />
              <BulbOutlined v-else />
            </a-button>
          </a-tooltip>
          <a-dropdown>
            <a-button type="text">
              <GlobalOutlined /> {{ localeLabel }}
            </a-button>
            <template #overlay>
              <a-menu @click="handleLocaleChange">
                <a-menu-item key="zh-CN">简体中文</a-menu-item>
                <a-menu-item key="en">English</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import { BulbFilled, BulbOutlined, GlobalOutlined } from "@ant-design/icons-vue";
import { useConnectionStore } from "@/stores";
import { getUISettings, saveUISettings, startDraggingWindow, needsMacTitleInset } from "@/platform";

const { t, locale } = useI18n();
const route = useRoute();
const conn = useConnectionStore();
const ui = getUISettings();
const macInset = needsMacTitleInset();

const selectedKeys = ref<string[]>([]);
const settingsKey = computed(() => (route.path.startsWith("/settings") ? ["/settings"] : []));

watch(
  () => route.path,
  (path) => {
    const seg = "/" + (path.split("/")[1] || "containers");
    selectedKeys.value = [seg];
  },
  { immediate: true }
);

const localeLabel = computed(() => (locale.value === "zh-CN" ? "中文" : "EN"));

function toggleTheme() {
  const next = ui.value.theme === "dark" ? "light" : "dark";
  saveUISettings({ theme: next });
}

function handleLocaleChange({ key }: { key: string | number }) {
  locale.value = String(key);
  saveUISettings({ locale: String(key) });
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sider {
  border-right: 1px solid rgba(5, 5, 5, 0.06);
  display: flex;
  flex-direction: column;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.menu {
  flex: 1;
  overflow-y: auto;
}

.sider-footer {
  border-top: 1px solid rgba(5, 5, 5, 0.06);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
  line-height: 56px;
  background: transparent;
  border-bottom: 1px solid rgba(5, 5, 5, 0.06);
}

.logo.mac-inset {
  padding-left: 72px;
  justify-content: flex-start;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.server-url {
  font-family: monospace;
  font-size: 13px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.content {
  padding: 16px;
  overflow-y: auto;
}

body.dockore-theme-dark .sider,
body.dockore-theme-dark .sider :deep(.ant-menu),
body.dockore-theme-dark .sider-footer,
body.dockore-theme-dark .header {
  background: #141414;
  border-color: rgba(253, 253, 253, 0.12);
  color: rgba(255, 255, 255, 0.85);
}

body.dockore-theme-dark .sider :deep(.ant-menu) {
  color: rgba(255, 255, 255, 0.85);
}
</style>
