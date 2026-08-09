<template>
  <div class="detail-header">
    <a-button type="text" size="small" class="back" @click="emit('back')">
      <ArrowLeftOutlined />
    </a-button>
    <span class="title">{{ title }}</span>
    <div class="extra">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeftOutlined } from "@ant-design/icons-vue";

defineProps<{ title: string }>();
const emit = defineEmits<{ back: [] }>();
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  margin-bottom: 12px;
}

.back {
  padding: 0 4px;
}

.title {
  font-size: 15px;
  font-weight: 600;
}

.extra {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
