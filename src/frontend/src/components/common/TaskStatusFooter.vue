<template>
  <div class="footer">
    <a-tag :color="statusColor">
      <LoadingOutlined v-if="status === 'running'" />
      {{ statusText }}
    </a-tag>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { LoadingOutlined } from "@ant-design/icons-vue";

const props = defineProps<{ status: string; prefix?: string }>();

const { t, te } = useI18n();

const statusText = computed(() => {
  const key = props.prefix ? `${props.prefix}.${props.status}` : props.status;
  return te(key) ? t(key) : props.status;
});

const statusColor = computed(() => {
  switch (props.status) {
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
</script>

<style scoped>
.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
