<template>
  <div>
    <a-page-header :title="t('settings.title')" />

    <a-card :title="t('settings.ui')" class="section">
      <a-form layout="vertical" style="max-width: 320px">
        <a-form-item :label="t('theme')">
          <a-select v-model:value="theme" :options="themeOptions" @change="handleThemeChange" />
        </a-form-item>
        <a-form-item :label="t('language')">
          <a-select v-model:value="localeValue" :options="localeOptions" @change="handleLocaleChange" />
        </a-form-item>
      </a-form>
    </a-card>

    <a-card :title="t('settings.backend')" class="section">
      <a-form layout="vertical" style="max-width: 480px">
        <a-form-item :label="t('settings.dockerHost')">
          <a-input v-model:value="dockerHost" placeholder="unix:///var/run/docker.sock" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" :loading="saving" @click="saveBackend">
            {{ t("save") }}
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card :title="t('settings.server')" class="section">
      <a-descriptions :column="1" style="max-width: 640px">
        <a-descriptions-item :label="t('settings.currentServer')">
          {{ conn.baseURL || "-" }}
          <a-tag v-if="conn.isBuiltIn" color="blue" style="margin-left: 8px">
            {{ t("connection.builtInTag") }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="t('status')">
          <a-badge
            :status="conn.isReady ? 'success' : 'error'"
            :text="conn.isReady ? t('connection.connected') : t('connection.disconnected')"
          />
        </a-descriptions-item>
        <a-descriptions-item :label="t('settings.frontendVersion')">
          {{ version }}
        </a-descriptions-item>
      </a-descriptions>
      <div style="margin-top: 16px">
        <a-popconfirm
          :title="t('settings.disconnectConfirm')"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="handleDisconnect"
        >
          <a-button danger>{{ t("settings.disconnect") }}</a-button>
        </a-popconfirm>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useConnectionStore, useSettingsStore, errorMessage } from "@/stores";
import { getUISettings, saveUISettings } from "@/platform";

const { t, locale } = useI18n();
const router = useRouter();
const conn = useConnectionStore();
const settingsStore = useSettingsStore();
const ui = getUISettings();

const version = __DOCKORE_VERSION__;

const theme = ref(ui.value.theme);
const localeValue = ref(locale.value);
const dockerHost = ref("");
const saving = ref(false);

const themeOptions = computed(() => [
  { label: t("themeLight"), value: "light" },
  { label: t("themeDark"), value: "dark" },
  { label: t("themeAuto"), value: "auto" },
]);

const localeOptions = [
  { label: "简体中文", value: "zh-CN" },
  { label: "English", value: "en" },
];

function handleThemeChange(val: string | number) {
  saveUISettings({ theme: String(val) });
}

function handleLocaleChange(val: string | number) {
  locale.value = String(val);
  saveUISettings({ locale: String(val) });
}

onMounted(async () => {
  try {
    await settingsStore.fetch();
    dockerHost.value = settingsStore.settings?.docker_host || "";
  } catch (e: any) {
    message.error(errorMessage(e));
  }
});

async function saveBackend() {
  saving.value = true;
  try {
    await settingsStore.update({ docker_host: dockerHost.value || null });
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
}

async function handleDisconnect() {
  await conn.disconnect();
  router.push("/onboarding");
}
</script>

<style scoped>
.section {
  margin-bottom: 16px;
}
</style>
