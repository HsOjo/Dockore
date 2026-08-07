<template>
  <a-drawer
    :open="open"
    :title="t('container.logs')"
    width="860"
    @close="handleClose"
  >
    <div class="toolbar">
      <a-range-picker
        v-model:value="dtRange"
        show-time
        :placeholder="[t('container.logsRange'), t('container.logsRange')]"
      />
      <a-checkbox v-model:checked="follow">{{ t("container.logsFollow") }}</a-checkbox>
      <a-button type="primary" @click="startStream">{{ t("container.logsQuery") }}</a-button>
    </div>
    <pre ref="logsEl" class="logs">{{ content }}</pre>
  </a-drawer>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import type { Dayjs } from "dayjs";
import { LogsSocket, toWSURL } from "@dockore/shared";
import { useConnectionStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean; containerId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const conn = useConnectionStore();

const dtRange = ref<[Dayjs, Dayjs] | null>(null);
const follow = ref(true);
const content = ref("");
const logsEl = ref<HTMLElement | null>(null);

let socket: LogsSocket | null = null;

watch(
  () => props.open,
  (open) => {
    if (open) {
      content.value = "";
      dtRange.value = null;
      follow.value = true;
      startStream();
    } else {
      stopStream();
    }
  }
);

function startStream() {
  stopStream();
  if (!props.containerId) return;
  content.value = "";
  socket = new LogsSocket();
  const params: { since?: string; until?: string; follow?: boolean } = { follow: follow.value };
  if (dtRange.value && dtRange.value[0] && dtRange.value[1]) {
    params.since = dtRange.value[0].format("YYYY-MM-DD HH:mm:ss");
    params.until = dtRange.value[1].format("YYYY-MM-DD HH:mm:ss");
  }
  socket.on("data", (data: string) => {
    content.value += data;
    nextTick(() => {
      if (logsEl.value) logsEl.value.scrollTop = logsEl.value.scrollHeight;
    });
  });
  socket.on("error", () => message.error(t("connectFailed")));
  try {
    socket.connect(toWSURL(conn.baseURL), props.containerId, conn.token, params);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function stopStream() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

function handleClose() {
  stopStream();
  emit("update:open", false);
}
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.logs {
  margin: 0;
  padding: 12px;
  height: calc(100vh - 220px);
  overflow-y: auto;
  background: #000;
  color: #d4d4d4;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  border-radius: 4px;
}
</style>
