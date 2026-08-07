<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <a-page-header
        :title="`${t('terminal.title')}：${item?.name || ''}`"
        @back="router.push('/containers')"
      />
      <div class="terminal-actions">
        <template v-if="item">
          <a-button type="primary" :disabled="item.status === 'running'" @click="doStart">
            {{ t("container.start") }}
          </a-button>
          <a-button :disabled="item.status !== 'running'" @click="doStop">
            {{ t("container.stop") }}
          </a-button>
          <a-button @click="doRestart">{{ t("container.restart") }}</a-button>
        </template>
        <a-button @click="reload">
          <ReloadOutlined />
        </a-button>
      </div>
    </div>
    <div ref="termEl" class="terminal" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { SearchAddon } from "@xterm/addon-search";
import { WebLinksAddon } from "@xterm/addon-web-links";
import "@xterm/xterm/css/xterm.css";
import { TerminalSocket, toWSURL } from "@dockore/shared";
import {
  useConnectionStore,
  useContainerStore,
  errorMessage,
  type ContainerItem,
} from "@/stores";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const conn = useConnectionStore();
const store = useContainerStore();

const termEl = ref<HTMLElement | null>(null);
const item = ref<ContainerItem | null>(null);

const term = new Terminal({ cursorBlink: true, macOptionIsMeta: true });
const fit = new FitAddon();
const search = new SearchAddon();
const webLinks = new WebLinksAddon();

let socket: TerminalSocket | null = null;
let ro: ResizeObserver | null = null;
let resizeTimer: ReturnType<typeof setTimeout> | null = null;

const containerId = () => String(route.params.id);

async function connect() {
  try {
    const ticket = await store.createTerminalTicket(containerId());
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

async function loadItem() {
  try {
    item.value = await store.fetch(containerId());
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

async function doStart() {
  try {
    await store.start(containerId());
    await loadItem();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function doStop() {
  try {
    await store.stop(containerId(), 5);
    await loadItem();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function doRestart() {
  try {
    await store.restart(containerId(), 5);
    await loadItem();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function reload() {
  router.go(0);
}

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

  await loadItem();
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
.terminal-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 88px);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.terminal-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
}

.terminal {
  flex: 1;
  background: #000;
  border-radius: 4px;
  padding: 8px;
  overflow: hidden;
}
</style>
