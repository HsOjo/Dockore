<template>
  <a-drawer
    :open="open"
    :title="typeof title === 'function' ? title(status) : title"
    width="860"
    @close="handleClose"
    @afterOpenChange="onDrawerOpenChange"
  >
    <div class="drawer-body">
      <TerminalView
        ref="termView"
        fill
        @resize="onTerminalResize"
      />
    </div>
    <template #footer>
      <TaskStatusFooter :status="status" prefix="stack.task">
        <template #actions>
          <slot name="actions" :status="status" :close="handleClose" />
        </template>
      </TaskStatusFooter>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { wsClient } from "@dockore/shared";
import TerminalView from "@/components/common/TerminalView.vue";
import TaskStatusFooter from "@/components/common/TaskStatusFooter.vue";

const props = defineProps<{
  open: boolean;
  taskId: string;
  title: string | ((status: string) => string);
  eventName: string;
  resizeMessageType?: string;
  initialStatus?: () => Promise<{ status: string; error?: unknown; returncode?: number | null } | null>;
}>();

const emit = defineEmits<{
  "update:open": [boolean];
  finished: [{ status: string; error?: unknown; returncode?: number | null }];
}>();

const status = ref("running");
const termView = ref<InstanceType<typeof TerminalView> | null>(null);
const termSize = ref<{ cols: number; rows: number } | null>(null);

function onTerminalResize(size: { cols: number; rows: number }) {
  termSize.value = size;
  if (status.value === "running" && props.resizeMessageType) {
    wsClient.send({
      type: props.resizeMessageType,
      task_id: props.taskId,
      rows: size.rows,
      cols: size.cols,
    });
  }
}

function writeTaskFailure(task: { status: string; error?: unknown; returncode?: number | null }) {
  if (task.error) termView.value?.write(String(task.error));
  if (task.returncode != null && task.status === "error") {
    termView.value?.write(`returncode: ${task.returncode}\n`);
  }
}

function onTaskEvent(data: any) {
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
    emit("finished", { status: data.status, error: data.error, returncode: data.returncode });
  }
}

function cleanup() {
  wsClient.off(props.eventName, onTaskEvent);
}

function handleClose() {
  cleanup();
  emit("update:open", false);
}

async function onDrawerOpenChange(open: boolean) {
  if (open && props.taskId) {
    termView.value?.clear();
    termView.value?.fit();

    if (props.initialStatus) {
      const task = await props.initialStatus();
      if (task && task.status !== "running") {
        status.value = task.status;
        writeTaskFailure(task);
        cleanup();
        emit("finished", { status: task.status, error: task.error, returncode: task.returncode });
        return;
      }
    }

    wsClient.on(props.eventName, onTaskEvent);
    if (termSize.value) onTerminalResize(termSize.value);
  }
}

watch(
  () => [props.open, props.taskId],
  ([open]) => {
    cleanup();
    if (open && props.taskId) {
      status.value = "running";
      wsClient.on(props.eventName, onTaskEvent);
    }
  }
);

onBeforeUnmount(cleanup);
</script>

<style scoped>
.drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
