<template>
  <LogDrawer
    :open="open"
    :title="t('container.logs')"
    :connect-path="connectLogs"
    @update:open="$emit('update:open', $event)"
  />
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { toWSURL } from "@dockore/shared";
import { useConnectionStore } from "@/stores";
import LogDrawer from "@/components/common/LogDrawer.vue";

const props = defineProps<{ open: boolean; containerId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const conn = useConnectionStore();

function connectLogs(socket: any, params: { since?: string; until?: string; follow: boolean }) {
  socket.connect(toWSURL(conn.baseURL), props.containerId, conn.token, params);
}
</script>
