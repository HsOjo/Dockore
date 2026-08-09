<template>
  <a-modal
    :open="open"
    :title="`${t('container.exec')}：${containerName}`"
    :footer="null"
    width="800px"
    @cancel="emit('update:open', false)"
  >
    <div class="exec-input">
      <a-input
        v-model:value="command"
        :placeholder="t('container.execPlaceholder')"
        @press-enter="run"
      />
      <a-button type="primary" :disabled="!command" @click="run">
        {{ t("container.execRun") }}
      </a-button>
    </div>
    <div v-if="sessionKey" class="exec-terminal">
      <TerminalView :key="sessionKey" :container-id="containerId" :command="sessionCommand" />
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import TerminalView from "@/components/container/TerminalView.vue";

const props = defineProps<{ open: boolean; containerId: string; containerName: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();

const command = ref("");
const sessionCommand = ref("");
const sessionKey = ref(0);

watch(
  () => props.open,
  (open) => {
    if (open) {
      command.value = "";
      sessionKey.value = 0;
    }
  }
);

function run() {
  if (!command.value) return;
  sessionCommand.value = command.value;
  sessionKey.value += 1;
}
</script>

<style scoped>
.exec-input {
  display: flex;
  gap: 8px;
}

.exec-terminal {
  display: flex;
  height: 360px;
  margin-top: 12px;
}
</style>
