<template>
  <a-table :scroll="{ x: 'max-content' }" v-bind="$attrs">
    <template v-for="(_, name) in $slots" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps ?? {}" />
    </template>
  </a-table>
</template>

<script setup lang="ts">
defineOptions({ inheritAttrs: false });
</script>

<style scoped>
:deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
}
</style>
