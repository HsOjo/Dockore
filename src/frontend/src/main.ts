import { createApp } from "vue";
import { createPinia } from "pinia";
import { createI18n } from "vue-i18n";
import Antd from "ant-design-vue";
import "ant-design-vue/dist/reset.css";

import App from "./App.vue";
import router from "./router";
import zhCN from "./locales/zh-CN.json";
import en from "./locales/en.json";
import { getUISettings } from "@/platform";

const ui = getUISettings();

const i18n = createI18n({
  legacy: false,
  locale: ui.value.locale,
  fallbackLocale: "en",
  messages: {
    "zh-CN": zhCN,
    en,
  },
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(i18n);
app.use(Antd);
app.mount("#app");
