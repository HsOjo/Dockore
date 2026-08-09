<template>
  <div class="onboarding">
    <div class="onboarding-container">
      <div class="onboarding-header">
        <h1 class="onboarding-title">{{ t("welcomeTitle") }}</h1>
        <p class="onboarding-desc">{{ t("welcomeDescription") }}</p>
      </div>

      <a-steps :current="currentStep - 1" :items="stepItems" class="onboarding-steps" />

      <div class="onboarding-content">
        <div v-if="currentStep === 1">
          <a-form layout="vertical">
            <a-form-item :label="t('language')">
              <a-select
                v-model:value="selectedLocale"
                :options="localeOptions"
                @change="handleLocaleChange"
              />
            </a-form-item>
            <a-form-item :label="t('theme')">
              <a-select
                v-model:value="selectedTheme"
                :options="themeOptions"
                @change="handleThemeChange"
              />
            </a-form-item>
          </a-form>
          <div class="onboarding-actions">
            <a-button type="primary" size="large" @click="goToStep2">
              {{ t("next") }}
            </a-button>
          </div>
        </div>

        <div v-else>
          <a-space direction="vertical" style="width: 100%">
            <a-radio-group v-model:value="mode" option-type="button" button-style="solid">
              <a-radio-button v-if="tauri" value="builtin">{{ t("builtIn") }}</a-radio-button>
              <a-radio-button value="remote">{{ t("remote") }}</a-radio-button>
            </a-radio-group>

            <template v-if="mode === 'remote'">
              <a-input v-model:value="url" :placeholder="t('baseURL')" />
              <a-input-password v-model:value="tokenInput" :placeholder="t('token')" />
            </template>

            <a-alert
              v-if="conn.initError"
              type="error"
              :message="conn.initError"
              show-icon
            />

            <div class="onboarding-actions">
              <a-button size="large" @click="currentStep = 1">
                {{ t("back") }}
              </a-button>
              <a-button type="primary" size="large" :loading="connecting" @click="handleConnect">
                {{ t("connect") }}
              </a-button>
            </div>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { invoke } from "@tauri-apps/api/core";
import { useConnectionStore, BUILTIN_TOKEN, pollUntil } from "@/stores";
import {
  detectTauri,
  getPlatformConfig,
  getUISettings,
  saveUISettings,
  hasUISettings,
} from "@/platform";
import { getDefaultServerURL } from "@dockore/shared";

const router = useRouter();
const conn = useConnectionStore();
const { locale, t } = useI18n();
const tauri = ref(false);

const ui = getUISettings();
const currentStep = ref(1);
const selectedLocale = ref(locale.value);
const selectedTheme = ref(ui.value.theme);

const stepItems = computed(() => [
  { title: t("stepPreferences") },
  { title: t("stepConnection") },
]);

const localeOptions = [
  { label: "简体中文", value: "zh-CN" },
  { label: "English", value: "en" },
];

const themeOptions = computed(() => [
  { label: t("themeLight"), value: "light" },
  { label: t("themeDark"), value: "dark" },
  { label: t("themeAuto"), value: "auto" },
]);

function handleLocaleChange(val: string | number) {
  locale.value = String(val);
  saveUISettings({ locale: String(val) });
}

function handleThemeChange(val: string | number) {
  saveUISettings({ theme: String(val) });
}

function goToStep2() {
  saveUISettings({ locale: selectedLocale.value, theme: selectedTheme.value });
  currentStep.value = 2;
}

onMounted(async () => {
  tauri.value = await detectTauri();
  if (hasUISettings()) {
    currentStep.value = 2;
  }
  const cfg = await getPlatformConfig();
  if (cfg.baseURL) {
    mode.value = cfg.isBuiltIn ? "builtin" : "remote";
    if (!cfg.isBuiltIn) {
      url.value = cfg.baseURL;
      tokenInput.value = cfg.token;
    }
  } else if (import.meta.env.PROD && tauri.value) {
    // No saved config likely means the previous session was built-in (not persisted).
    mode.value = "builtin";
  }
});

const mode = ref("remote");
const url = ref(getDefaultServerURL());
const tokenInput = ref("");
const connecting = ref(false);

async function handleConnect() {
  connecting.value = true;
  try {
    if (mode.value === "builtin") {
      let port = 8000;
      let token = BUILTIN_TOKEN;
      if (import.meta.env.PROD) {
        const cfg = await invoke<{ port: number; token: string }>("start_builtin_backend");
        port = cfg.port;
        token = cfg.token;
        // Wait for the bundled backend to become ready before the health check.
        try {
          await pollUntil(
            () => invoke<boolean>("is_backend_ready"),
            (ready) => ready,
            { interval: 500, timeout: 60000 }
          );
        } catch {
          throw new Error("等待内建后端启动超时");
        }
      }
      await conn.connect(`http://127.0.0.1:${port}`, token, true);
    } else {
      await conn.connect(url.value, tokenInput.value);
    }
    router.push("/");
  } catch (e: any) {
    console.error(e);
    message.error(e.message || t("connectFailed"));
  } finally {
    connecting.value = false;
  }
}
</script>

<style scoped>
.onboarding {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
  background-color: #ffffff;
  color: #1f2225;
  transition: background-color 0.2s ease, color 0.2s ease;
}

body.dockore-theme-dark .onboarding {
  background-color: #101014;
  color: #ffffff;
}

.onboarding-container {
  width: 100%;
  max-width: 480px;
}

.onboarding-header {
  text-align: center;
  margin-bottom: 32px;
}

.onboarding-title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 600;
}

.onboarding-desc {
  margin: 0;
  font-size: 14px;
  opacity: 0.7;
}

.onboarding-steps {
  margin-bottom: 32px;
}

.onboarding-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
