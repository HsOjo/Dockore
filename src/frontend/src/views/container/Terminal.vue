<template>
  <div class="terminal-page">
    <DetailHeader
      :title="`${t('terminal.title')}：${item?.name || ''}`"
      @back="router.push('/containers')"
    >
      <template v-if="item">
        <a-button type="primary" :disabled="item.status === 'running'" @click="doStart">
          {{ t("container.start") }}
        </a-button>
        <a-button :disabled="item.status !== 'running'" @click="doStop">
          {{ t("container.stop") }}
        </a-button>
        <a-button @click="doRestart">{{ t("container.restart") }}</a-button>
      </template>
      <a-button @click="termView?.reconnect()">
        <ReloadOutlined />
      </a-button>
    </DetailHeader>
    <TerminalView ref="termView" :container-id="containerId()" />
  </div>
</template>

<script setup lang="ts">
import DetailHeader from "@/components/common/DetailHeader.vue";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import TerminalView from "@/components/container/TerminalView.vue";
import { useContainerStore, errorMessage, type ContainerItem } from "@/stores";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const store = useContainerStore();

const termView = ref<InstanceType<typeof TerminalView> | null>(null);
const item = ref<ContainerItem | null>(null);

const containerId = () => String(route.params.id);

async function loadItem() {
  try {
    item.value = await store.fetch(containerId());
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function doStart() {
  try {
    await store.start(containerId());
    await loadItem();
    await termView.value?.reconnect();
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
    await termView.value?.reconnect();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

onMounted(loadItem);
</script>

<style scoped>
.terminal-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 88px);
}
</style>
