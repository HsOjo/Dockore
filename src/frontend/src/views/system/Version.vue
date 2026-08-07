<template>
  <div>
    <a-page-header :title="t('system.title')">
      <template #extra>
        <a-button @click="load">
          <ReloadOutlined />
        </a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-tabs v-model:activeKey="tab" v-if="store.version">
        <a-tab-pane key="project" :tab="t('system.project')">
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item
              v-for="(value, key) in store.version.project"
              :key="key"
              :label="fieldLabel(String(key))"
            >
              {{ value }}
            </a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>
        <a-tab-pane
          v-for="(fields, component) in store.version.docker"
          :key="String(component)"
          :tab="String(component)"
        >
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item
              v-for="(value, key) in fields"
              :key="key"
              :label="fieldLabel(String(key))"
            >
              <a-switch
                v-if="typeof value === 'boolean'"
                :checked="value"
                disabled
                size="small"
              />
              <template v-else>{{ formatValue(value) }}</template>
            </a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>
      </a-tabs>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { useSystemStore, errorMessage } from "@/stores";

const { t, te } = useI18n();
const store = useSystemStore();

const tab = ref("project");
const loading = ref(false);

const fieldKeyMap: Record<string, string> = {
  version: "version",
  hostname: "hostname",
  python: "python",
  os: "os",
  arch: "arch",
  kernel: "kernel",
  kernelversion: "kernel",
  apiversion: "apiVersion",
  minapiversion: "minAPIVersion",
  goversion: "goVersion",
  gitcommit: "gitCommit",
  buildtime: "buildTime",
  experimental: "experimental",
};

function fieldLabel(key: string): string {
  const normalized = key.replace(/_/g, "").toLowerCase();
  const i18nKey = fieldKeyMap[normalized];
  if (i18nKey && te(`system.field.${i18nKey}`)) {
    return t(`system.field.${i18nKey}`);
  }
  return key;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

async function load() {
  loading.value = true;
  try {
    await store.fetchVersion();
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
