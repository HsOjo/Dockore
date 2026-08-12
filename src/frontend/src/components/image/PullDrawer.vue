<template>
  <TaskDrawer
    :open="open"
    :task-id="taskId"
    :title="title"
    event-name="image.pull"
    @update:open="$emit('update:open', $event)"
    @finished="onFinished"
  >
    <template #actions="{ status, close }">
      <a-button v-if="status !== 'running'" type="primary" @click="close">{{ t("ok") }}</a-button>
    </template>
  </TaskDrawer>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useImageStore } from "@/stores";
import TaskDrawer from "@/components/common/TaskDrawer.vue";

const props = defineProps<{ open: boolean; taskId: string; image: string }>();
const emit = defineEmits<{ "update:open": [boolean]; finished: [string] }>();

const { t } = useI18n();
const store = useImageStore();

const title = (s: string) =>
  s === "running"
    ? t("image.pulling", { name: props.image })
    : `${t("image.pull")}: ${props.image}`;

function onFinished(task: { status: string; error?: unknown; returncode?: number | null }) {
  if (task.status === "done") {
    message.success(t("image.pullDone"));
    store.fetchAll().catch(() => {});
  } else if (task.status === "error") {
    message.error(`${t("image.pullError")}: ${task.error || ""}`);
  }
  emit("finished", task.status);
}
</script>
