<template>
  <div class="settings-grid">
    <div class="column">
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

      <a-card :title="t('settings.proxy')" class="section">
        <a-form layout="vertical" style="max-width: 480px">
          <a-form-item :label="t('settings.httpProxy')">
            <a-input v-model:value="httpProxy" placeholder="http://127.0.0.1:7890" />
          </a-form-item>
          <a-form-item :label="t('settings.httpsProxy')">
            <a-input v-model:value="httpsProxy" placeholder="http://127.0.0.1:7890" />
          </a-form-item>
          <a-form-item :label="t('settings.noProxy')">
            <a-input v-model:value="noProxy" placeholder="localhost,127.0.0.1" />
          </a-form-item>
          <a-form-item :label="t('settings.proxyScope')">
            <a-space direction="vertical">
              <a-checkbox v-model:checked="proxyCli">
                {{ t("settings.proxyCli") }}
              </a-checkbox>
              <a-checkbox v-model:checked="proxyOutbound">
                {{ t("settings.proxyOutbound") }}
              </a-checkbox>
            </a-space>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="savingProxy" @click="saveProxy">
              {{ t("save") }}
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <div class="column">
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

      <a-card :title="t('settings.backend')" class="section">
        <a-form layout="vertical" style="max-width: 480px">
          <a-form-item :label="t('settings.dockerHost')">
            <a-input v-model:value="dockerHost" placeholder="unix:///var/run/docker.sock" />
          </a-form-item>
          <a-form-item :label="t('settings.metricsInterval')">
            <a-input-number v-model:value="metricsInterval" :min="1" :max="60" style="width: 120px" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="saving" @click="saveBackend">
              {{ t("save") }}
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
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

const theme = ref(ui.value.theme);
const localeValue = ref(locale.value);
const dockerHost = ref("");
const metricsInterval = ref(2);
const httpProxy = ref("");
const httpsProxy = ref("");
const noProxy = ref("");
const proxyCli = ref(true);
const proxyOutbound = ref(true);
const saving = ref(false);
const savingProxy = ref(false);

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
    const s = settingsStore.settings;
    dockerHost.value = s?.docker_host || "";
    metricsInterval.value = s?.metrics_interval ?? 2;
    httpProxy.value = s?.http_proxy || "";
    httpsProxy.value = s?.https_proxy || "";
    noProxy.value = s?.no_proxy || "";
    proxyCli.value = s?.proxy_cli !== false;
    proxyOutbound.value = s?.proxy_outbound !== false;
  } catch (e: any) {
    message.error(errorMessage(e));
  }
});

async function saveBackend() {
  saving.value = true;
  try {
    await settingsStore.update({
      docker_host: dockerHost.value || null,
      metrics_interval: metricsInterval.value,
    });
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
}

async function saveProxy() {
  savingProxy.value = true;
  try {
    await settingsStore.update({
      http_proxy: httpProxy.value,
      https_proxy: httpsProxy.value,
      no_proxy: noProxy.value,
      proxy_cli: proxyCli.value,
      proxy_outbound: proxyOutbound.value,
    });
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    savingProxy.value = false;
  }
}

async function handleDisconnect() {
  await conn.disconnect();
  router.push("/onboarding");
}
</script>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
  align-items: start;
}

.section {
  margin-bottom: 16px;
}
</style>
