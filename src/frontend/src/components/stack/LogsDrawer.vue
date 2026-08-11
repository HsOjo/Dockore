<template>
  <a-drawer
    :open="open"
    :title="`${t('stack.logs')}: ${stackName}`"
    width="860"
    @close="handleClose"
    @afterOpenChange="onDrawerOpenChange"
  >
    <div class="toolbar">
      <a-checkbox v-model:checked="follow">{{ t("container.logsFollow") }}</a-checkbox>
      <a-button type="primary" @click="startStream">{{ t("container.logsQuery") }}</a-button>
    </div>
    <TerminalView ref="termView" />
  </a-drawer>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { LogsSocket, toWSURL } from "@dockore/shared";
import { useConnectionStore } from "@/stores";
import TerminalView from "@/components/common/TerminalView.vue";

const props = defineProps<{ open: boolean; stackName: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const conn = useConnectionStore();

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
  if (!props.stackName) return;
  termView.value?.clear();
  socket = new LogsSocket();
  socket.on("data", (data: string | ArrayBuffer) => {
    const text = data instanceof ArrayBuffer ? new TextDecoder().decode(data) : data;
    termView.value?.write(text);
  });
  socket.on("error", () => message.error(t("connectFailed")));
  socket.connectPath(
    toWSURL(conn.baseURL),
    `/ws/stacks/${encodeURIComponent(props.stackName)}/logs`,
    conn.token,
    { follow: follow.value }
  );
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
</style>
