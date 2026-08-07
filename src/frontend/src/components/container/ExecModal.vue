<template>
  <a-modal
    :open="open"
    :title="`${t('container.exec')}：${containerName}`"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    width="720px"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-input
      v-model:value="command"
      :placeholder="t('container.execPlaceholder')"
      @press-enter="handleOk"
    />
    <template v-if="result">
      <div class="result-header">
        <span>{{ t("container.execResult") }}</span>
        <a-tag :color="result.exit_code === 0 ? 'green' : 'red'">
          {{ t("container.exitCode") }}: {{ result.exit_code }}
        </a-tag>
      </div>
      <pre class="result-output">{{ result.output }}</pre>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useContainerStore, errorMessage, type ExecResult } from "@/stores";

const props = defineProps<{ open: boolean; containerId: string; containerName: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const containerStore = useContainerStore();

const loading = ref(false);
const command = ref("");
const result = ref<ExecResult | null>(null);

watch(
  () => props.open,
  (open) => {
    if (open) {
      command.value = "";
      result.value = null;
    }
  }
);

async function handleOk() {
  if (!command.value) return;
  loading.value = true;
  try {
    result.value = await containerStore.exec(props.containerId, command.value);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.result-output {
  margin: 0;
  padding: 12px;
  max-height: 320px;
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
