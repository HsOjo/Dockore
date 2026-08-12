<template>
  <TaskDrawer
    :open="open"
    :task-id="taskId"
    :title="title"
    event-name="stack.action"
    resize-message-type="stack.resize"
    :initial-status="fetchInitialStatus"
    @update:open="$emit('update:open', $event)"
    @finished="$emit('finished', $event.status)"
  >
    <template #actions="{ status, close }">
      <a-popconfirm
        v-if="status === 'running'"
        :title="t('stack.task.confirmCancel')"
        :ok-text="t('ok')"
        :cancel-text="t('cancel')"
        @confirm="cancelTask(close)"
      >
        <a-button danger>{{ t("stack.task.cancel") }}</a-button>
      </a-popconfirm>
      <a-button v-else type="primary" @click="close">{{ t("ok") }}</a-button>
    </template>
  </TaskDrawer>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";
import TaskDrawer from "@/components/common/TaskDrawer.vue";

const props = defineProps<{ open: boolean; taskId: string; stack: string; kind: string }>();
const emit = defineEmits<{ "update:open": [boolean]; finished: [string] }>();

const { t, te } = useI18n();
const store = useStackStore();

function tOr(key: string, fallback: string): string {
  return te(key) ? t(key) : fallback;
}

const title = computed(() => {
  const kind = tOr(`stack.kind.${props.kind}`, props.kind);
  return props.stack ? `${kind}: ${props.stack}` : kind;
});

async function fetchInitialStatus() {
  const tasks = await store.listTasks().catch(() => [] as any[]);
  const task = tasks.find((t: any) => t.id === props.taskId);
  return task && task.status !== "running" ? task : null;
}

async function cancelTask(close: () => void) {
  if (!props.taskId) return;
  try {
    await store.cancelTask(props.taskId);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}
</script>
