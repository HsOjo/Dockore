<template>
  <div>
    <a-page-header
      :title="`${t('menu.containers')}：${item?.name || ''}`"
      @back="router.push('/containers')"
    >
      <template #extra>
        <a-button @click="load">
          <ReloadOutlined />
        </a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-tabs v-model:activeKey="tab" v-if="item">
        <a-tab-pane key="basic" :tab="t('container.tabs.basic')">
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item :label="t('container.field.id')">
              <span class="mono">{{ item.id }}</span>
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.field.name')">
              {{ item.name }}
              <a-button type="link" size="small" @click="renameOpen = true">
                <EditOutlined />
              </a-button>
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.field.image')">
              <router-link :to="`/images/${encodeURIComponent(item.image.id)}`">
                {{ imageDisplayName(item.image) }}
              </router-link>
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.field.command')">
              <span class="mono">{{ item.command }}</span>
            </a-descriptions-item>
            <a-descriptions-item :label="t('createTime')">
              {{ formatTime(item.create_time, locale) }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('status')">
              <a-badge
                :status="containerStatusBadge(item.status)"
                :text="statusText(item.status)"
              />
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.field.tty')">
              <a-checkbox :checked="item.tty ?? false" disabled />
              <span style="margin-left: 16px">{{ t("container.field.interactive") }}</span>
              <a-checkbox :checked="item.interactive ?? false" disabled style="margin-left: 8px" />
            </a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>

        <a-tab-pane key="network" :tab="t('container.tabs.network')">
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item :label="t('container.network.ip')">
              {{ item.network?.ip || t("container.network.notRunning") }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.network.prefix')">
              {{ item.network?.prefix ?? "" }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.network.gateway')">
              {{ item.network?.gateway || "" }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('container.network.mac')">
              {{ item.network?.mac_address || "" }}
            </a-descriptions-item>
          </a-descriptions>
          <a-card :title="t('container.network.ports')" style="max-width: 720px; margin-top: 16px">
            <a-table
              :data-source="item.network?.ports || []"
              :columns="portColumns"
              :pagination="false"
              size="small"
              row-key="port"
            />
          </a-card>
        </a-tab-pane>

        <a-tab-pane key="storage" :tab="t('container.tabs.storage')">
          <a-card :title="t('container.storage.mounts')">
            <a-table
              :data-source="item.mounts || []"
              :columns="mountColumns"
              :pagination="false"
              size="small"
              :row-key="(r: any) => `${r.src}-${r.dest}`"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  {{ mountTypeText(record.type) }}
                </template>
                <template v-else-if="column.key === 'name'">
                  <router-link v-if="record.name" :to="`/volumes/${encodeURIComponent(record.name)}`">
                    {{ record.name }}
                  </router-link>
                  <template v-else>{{ t("none") }}</template>
                </template>
                <template v-else-if="column.key === 'driver'">
                  {{ record.driver || t("none") }}
                </template>
                <template v-else-if="column.key === 'mode'">
                  {{ mountModeText(record.mode) }}
                </template>
              </template>
            </a-table>
          </a-card>
        </a-tab-pane>
      </a-tabs>
    </a-spin>

    <RenameModal
      v-if="item"
      v-model:open="renameOpen"
      :container-id="item.id"
      :container-name="item.name"
      @renamed="load"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { EditOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { formatTime } from "@dockore/shared";
import { useContainerStore, errorMessage, type ContainerItem } from "@/stores";
import { containerStatusBadge, imageDisplayName } from "@/utils/text";
import RenameModal from "@/components/container/RenameModal.vue";

const { t, te, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const store = useContainerStore();

const tab = ref("basic");
const item = ref<ContainerItem | null>(null);
const loading = ref(false);
const renameOpen = ref(false);

const portColumns = computed(() => [
  { title: t("container.network.port"), key: "port", dataIndex: "port" },
  { title: t("container.network.protocol"), key: "protocol", dataIndex: "protocol" },
  { title: t("container.network.listenIp"), key: "listen_ip", dataIndex: "listen_ip" },
  { title: t("container.network.listenPort"), key: "listen_port", dataIndex: "listen_port" },
]);

const mountColumns = computed(() => [
  { title: t("container.storage.type"), key: "type", dataIndex: "type", width: 140 },
  { title: t("container.storage.volumeName"), key: "name", dataIndex: "name", width: 200 },
  { title: t("container.storage.driver"), key: "driver", dataIndex: "driver", width: 140 },
  { title: t("container.storage.mode"), key: "mode", dataIndex: "mode", width: 120 },
  { title: t("container.storage.src"), key: "src", dataIndex: "src" },
  { title: t("container.storage.dest"), key: "dest", dataIndex: "dest" },
]);

function statusText(status: string): string {
  const key = `container.status.${status}`;
  return te(key) ? t(key) : status;
}

function mountTypeText(type: string): string {
  const key = `volume.mountType.${type}`;
  return te(key) ? t(key) : type;
}

function mountModeText(mode: string): string {
  const key = `volume.mountMode.${mode}`;
  return te(key) ? t(key) : mode || "-";
}

async function load() {
  loading.value = true;
  try {
    item.value = await store.fetch(String(route.params.id));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.mono {
  font-family: monospace;
}
</style>
