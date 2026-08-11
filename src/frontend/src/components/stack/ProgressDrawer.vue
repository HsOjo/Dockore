<template>
  <a-drawer
    :open="open"
    :title="title"
    width="860"
    @close="handleClose"
    @afterOpenChange="onDrawerOpenChange"
  >
    <TerminalView
      ref="termView"
      @resize="onTerminalResize"
    />
    <template #footer>
      <div class="footer">
        <a-tag :color="statusColor">
          <LoadingOutlined v-if="status === 'running'" />
          {{ statusText }}
        </a-tag>
        <a-popconfirm
          v-if="status === 'running'"
          :title="t('stack.task.confirmCancel')"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="cancelTask"
        >
          <a-button danger>{{ t("stack.task.cancel") }}</a-button>
        </a-popconfirm>
        <a-button v-else type="primary" @click="handleClose">{{ t("ok") }}</a-button>
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
import { useStackStore, errorMessage } from "@/stores";
import TerminalView from "@/components/common/TerminalView.vue";

const props = defineProps<{ open: boolean; taskId: string; stack: string; kind: string }>();
const emit = defineEmits<{ "update:open": [boolean]; finished: [string] }>();

const { t, te } = useI18n();
const store = useStackStore();

const status = ref("running");
const termView = ref<InstanceType<typeof TerminalView> | null>(null);
const termSize = ref<{ cols: number; rows: number } | null>(null);

function tOr(key: string, fallback: string): string {
  return te(key) ? t(key) : fallback;
}

const title = computed(() => {
  const kind = tOr(`stack.kind.${props.kind}`, props.kind);
  return props.stack ? `${kind}: ${props.stack}` : kind;
});

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

function sendResize(size: { cols: number; rows: number }) {
  if (!props.taskId) return;
  wsClient.send({
    type: "stack.resize",
    task_id: props.taskId,
    rows: size.rows,
    cols: size.cols,
  });
}

function onTerminalResize(size: { cols: number; rows: number }) {
  termSize.value = size;
  if (status.value === "running") sendResize(size);
}

function writeTaskFailure(task: { status: string; error?: unknown; returncode?: number | null }) {
  if (task.error) termView.value?.write(String(task.error));
  if (task.returncode != null && task.status === "error") {
    termView.value?.write(`returncode: ${task.returncode}\n`);
  }
}

function onActionEvent(data: any) {
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
    emit("finished", data.status);
  }
}

function cleanup() {
  wsClient.off("stack.action", onActionEvent);
}

async function cancelTask() {
  if (!props.taskId) return;
  try {
    await store.cancelTask(props.taskId);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function handleClose() {
  cleanup();
  emit("update:open", false);
}

async function onDrawerOpenChange(open: boolean) {
  if (open && props.taskId) {
    termView.value?.clear();
    termView.value?.fit();
    // Check current task state in case it already finished while the drawer was closed.
    const tasks = await store.listTasks().catch(() => [] as any[]);
    const task = tasks.find((t: any) => t.id === props.taskId);
    if (task && task.status !== "running") {
      status.value = task.status;
      writeTaskFailure(task);
      emit("finished", task.status);
      return;
    }
    wsClient.on("stack.action", onActionEvent);
    if (termSize.value) sendResize(termSize.value);
  }
}

watch(
  () => [props.open, props.taskId],
  ([open]) => {
    cleanup();
    if (open && props.taskId) {
      status.value = "running";
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
