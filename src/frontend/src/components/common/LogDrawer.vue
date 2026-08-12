<template>
  <a-drawer
    :open="open"
    :title="title"
    width="860"
    @close="handleClose"
    @afterOpenChange="onDrawerOpenChange"
  >
    <div class="drawer-body">
      <div class="toolbar">
        <a-range-picker
          v-model:value="dtRange"
          show-time
          :placeholder="[t('container.logsRange'), t('container.logsRange')]"
        />
        <a-checkbox v-model:checked="follow">{{ t("container.logsFollow") }}</a-checkbox>
        <a-button type="primary" @click="startStream">{{ t("container.logsQuery") }}</a-button>
      </div>
      <TerminalView ref="termView" fill />
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import type { Dayjs } from "dayjs";
import { LogsSocket } from "@dockore/shared";
import TerminalView from "@/components/common/TerminalView.vue";

const props = defineProps<{
  open: boolean;
  title: string;
  connectPath: (socket: LogsSocket, params: { since?: string; until?: string; follow: boolean }) => void;
}>();

const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();

const dtRange = ref<[Dayjs, Dayjs] | null>(null);
const follow = ref(true);
const termView = ref<InstanceType<typeof TerminalView> | null>(null);

let socket: LogsSocket | null = null;

function onDrawerOpenChange(open: boolean) {
  if (open) {
    follow.value = true;
    termView.value?.fit();
    startStream();
  }
}

watch(
  () => props.open,
  (open) => {
    if (!open) stopStream();
  }
);

onBeforeUnmount(stopStream);

function startStream() {
  stopStream();
  termView.value?.clear();
  socket = new LogsSocket();
  const params: { since?: string; until?: string; follow: boolean } = { follow: follow.value };
  if (dtRange.value && dtRange.value[0] && dtRange.value[1]) {
    params.since = dtRange.value[0].format("YYYY-MM-DD HH:mm:ss");
    params.until = dtRange.value[1].format("YYYY-MM-DD HH:mm:ss");
  }
  socket.on("data", (data: string | ArrayBuffer) => {
    const text = data instanceof ArrayBuffer ? new TextDecoder().decode(data) : data;
    termView.value?.write(text);
    nextTick(() => termView.value?.scrollToBottom());
  });
  socket.on("error", () => message.error(t("connectFailed")));
  props.connectPath(socket, params);
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
.drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
</style>
