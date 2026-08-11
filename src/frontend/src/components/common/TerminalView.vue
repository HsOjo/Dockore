<template>
  <div ref="termEl" class="xterm-wrapper"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { Terminal } from "xterm";
import { FitAddon } from "@xterm/addon-fit";
import "xterm/css/xterm.css";

const emit = defineEmits<{ resize: [{ cols: number; rows: number }] }>();

const termEl = ref<HTMLElement | null>(null);
let resizeObserver: ResizeObserver | null = null;

const term = new Terminal({
  scrollback: 10000,
  convertEol: false,
  cursorBlink: false,
  fontFamily: "monospace",
  fontSize: 12,
  theme: {
    background: "#000000",
    foreground: "#d4d4d4",
  },
});
const fitAddon = new FitAddon();

onMounted(() => {
  if (!termEl.value) return;
  term.loadAddon(fitAddon);
  term.open(termEl.value);
  term.onResize(({ cols, rows }) => emit("resize", { cols, rows }));
  fitAddon.fit();
  resizeObserver = new ResizeObserver(() => {
    try {
      fitAddon.fit();
    } catch {
      // ignore when container is hidden
    }
  });
  resizeObserver.observe(termEl.value);
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  term.dispose();
});

function fit() {
  try {
    fitAddon.fit();
  } catch {
    // ignore
  }
}

function clear() {
  term.clear();
}

function write(data: string | Uint8Array) {
  term.write(data);
}

defineExpose({ write, fit, clear, cols: () => term.cols, rows: () => term.rows });
</script>

<style scoped>
.xterm-wrapper {
  height: calc(100vh - 220px);
  min-height: 320px;
  overflow-x: hidden;
  overflow-y: hidden;
  padding: 8px;
  background: #000;
  border-radius: 4px;
}

.xterm-wrapper :deep(.xterm) {
  height: 100%;
}
</style>
