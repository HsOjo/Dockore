<template>
  <a-drawer
    :open="open"
    :title="title"
    width="860"
    @close="handleClose"
    @afterOpenChange="onDrawerOpenChange"
  >
    <TerminalView ref="termView" />
    <template #footer>
      <div class="footer">
        <a-tag :color="statusColor">
          <LoadingOutlined v-if="status === 'running'" />
          {{ statusText }}
        </a-tag>
        <a-button v-if="status !== 'running'" type="primary" @click="handleClose">
          {{ t("ok") }}
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { LoadingOutlined } from "@ant-design/icons-vue";
import { wsClient } from "@dockore/shared";
import { useImageStore } from "@/stores";
import TerminalView from "@/components/common/TerminalView.vue";

const props = defineProps<{ open: boolean; taskId: string; image: string }>();
const emit = defineEmits<{ "update:open": [boolean]; finished: [string] }>();

const { t, te } = useI18n();
const store = useImageStore();

const status = ref("running");
const termView = ref<InstanceType<typeof TerminalView> | null>(null);

function tOr(key: string, fallback: string): string {
  return te(key) ? t(key) : fallback;
}

const title = computed(() =>
  status.value === "running"
    ? t("image.pulling", { name: props.image })
    : `${t("image.pull")}: ${props.image}`
);

const statusText = computed(() => tOr(`stack.task.${status.value}`, status.value));

const statusColor = computed(() => {
  switch (status.value) {
    case "done":
      return "green";
    case "error":
      return "red";
    case "cancelled":
      return "orange";
    default:
      return "blue";
  }
});

function writeTaskFailure(task: { status: string; error?: unknown; returncode?: number | null }) {
  if (task.error) termView.value?.write(String(task.error));
  if (task.returncode != null && task.status === "error") {
    termView.value?.write(`returncode: ${task.returncode}\n`);
  }
}

function onPullEvent(data: any) {
  if (!props.taskId || data?.task_id !== props.taskId) return;
  if (data.status === "running" && data.data) {
    try {
      const bytes = Uint8Array.from(atob(data.data), (c) => c.charCodeAt(0));
      termView.value?.write(bytes);
    } catch {
      termView.value?.write(data.data);
    }
    return;
  }
  if (data.status === "done" || data.status === "error" || data.status === "cancelled") {
    status.value = data.status;
    writeTaskFailure(data);
    cleanup();
    if (data.status === "done") {
      message.success(t("image.pullDone"));
      store.fetchAll().catch(() => {});
    } else if (data.status === "error") {
      message.error(`${t("image.pullError")}: ${data.error || ""}`);
    }
    emit("finished", data.status);
  }
}

function cleanup() {
  wsClient.off("image.pull", onPullEvent);
}

function handleClose() {
  cleanup();
  emit("update:open", false);
}

async function onDrawerOpenChange(open: boolean) {
  if (open && props.taskId) {
    termView.value?.clear();
    termView.value?.fit();
  }
}

watch(
  () => [props.open, props.taskId],
  ([open]) => {
    cleanup();
    if (open && props.taskId) {
      status.value = "running";
      wsClient.on("image.pull", onPullEvent);
    }
  }
);

onBeforeUnmount(cleanup);
</script>

<style scoped>
.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
