<template>
  <div class="terminal-view">
    <div ref="termEl" class="terminal-inner" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { SearchAddon } from "@xterm/addon-search";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import { TerminalSocket, toWSURL } from "@dockore/shared";
import { useConnectionStore, useContainerStore, errorMessage } from "@/stores";

const props = defineProps<{ containerId: string; command?: string | null }>();

const { t } = useI18n();
const conn = useConnectionStore();
const store = useContainerStore();

const termEl = ref<HTMLElement | null>(null);

const term = new Terminal({ cursorBlink: true, macOptionIsMeta: true });
const fit = new FitAddon();
const search = new SearchAddon();
const webLinks = new WebLinksAddon();

let socket: TerminalSocket | null = null;
let ro: ResizeObserver | null = null;
let resizeTimer: ReturnType<typeof setTimeout> | null = null;

async function connect() {
  try {
    socket?.disconnect();
    term.reset();
    const ticket = await store.createTerminalTicket(props.containerId, props.command);
    socket = new TerminalSocket();
    socket.on("data", (data: string | ArrayBuffer) => {
      if (typeof data === "string") {
        term.write(data);
      } else {
        term.write(new Uint8Array(data));
      }
    });
    socket.on("close", () => {
      term.write(t("terminal.networkDown"));
    });
    socket.connect(toWSURL(conn.baseURL), ticket.ticket);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function fitToScreen() {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    try {
      fit.fit();
      socket?.resize(term.rows, term.cols);
    } catch {
      // ignore
    }
  }, 200);
}

defineExpose({ reconnect: connect });

onMounted(async () => {
  term.loadAddon(fit);
  term.loadAddon(search);
  term.loadAddon(webLinks);
  if (termEl.value) {
    term.open(termEl.value);
    fit.fit();
  }
  term.onData((data) => socket?.sendInput(data));

  ro = new ResizeObserver(() => fitToScreen());
  if (termEl.value) ro.observe(termEl.value);

  await connect();
  fitToScreen();
});

onBeforeUnmount(() => {
  if (resizeTimer) clearTimeout(resizeTimer);
  ro?.disconnect();
  socket?.disconnect();
  term.dispose();
});
</script>

<style scoped>
.terminal-view {
  flex: 1;
  min-height: 0;
  background: #000;
  border-radius: 4px;
  padding: 8px;
  overflow: hidden;
}

.terminal-inner {
  height: 100%;
}
</style>
