<template>
  <a-tooltip :title="truncated || displayText !== text ? text : ''">
    <span ref="el" class="ellipsis-text" :class="{ mono }" @mouseenter="checkTruncated">
      {{ displayText }}
    </span>
  </a-tooltip>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = defineProps<{
  text: string;
  displayText?: string;
  mono?: boolean;
}>();

const displayText = computed(() => props.displayText ?? props.text);

const el = ref<HTMLElement>();
const truncated = ref(false);

function checkTruncated() {
  truncated.value = !!el.value && el.value.scrollWidth > el.value.clientWidth;
}
</script>

<style scoped>
.ellipsis-text {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}

.mono {
  font-family: monospace;
}
</style>
