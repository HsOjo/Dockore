<template>
  <a-modal
    :open="open"
    :title="t('terminal.hostTitle')"
    :footer="null"
    width="800px"
    @cancel="emit('update:open', false)"
  >
    <div v-if="open" class="shell-terminal">
      <TerminalView host />
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import TerminalView from "@/components/container/TerminalView.vue";

defineProps<{ open: boolean }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
</script>

<style scoped>
.shell-terminal {
  display: flex;
  height: 420px;
}
</style>
