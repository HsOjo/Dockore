<template>
  <a-table :scroll="{ x: 'max-content' }" v-bind="$attrs" :columns="resolvedColumns">
    <template v-for="(_, name) in $slots" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps ?? {}" />
    </template>
  </a-table>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useAttrs } from "vue";

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

// <768px 移除列的 fixed(如操作列),避免固定列遮住横向滚动的表格;>=768px 保持原行为
const MOBILE_QUERY = "(max-width: 767px)";
const mql = typeof window !== "undefined" ? window.matchMedia(MOBILE_QUERY) : null;
const isMobile = ref(mql?.matches ?? false);

function syncMobile() {
  isMobile.value = mql?.matches ?? false;
}

onMounted(() => {
  mql?.addEventListener("change", syncMobile);
});

onBeforeUnmount(() => {
  mql?.removeEventListener("change", syncMobile);
});

const resolvedColumns = computed(() => {
  const raw = attrs.columns;
  if (!isMobile.value || !Array.isArray(raw)) return raw;
  return raw.map((col: unknown) => {
    if (!col || typeof col !== "object" || !("fixed" in col)) return col;
    const resolved = { ...(col as Record<string, unknown>) };
    delete resolved.fixed;
    return resolved;
  });
});
</script>

<style scoped>
:deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
}
</style>
