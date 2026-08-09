<template>
  <div>
    <DetailHeader
      :title="`${t('menu.networks')}：${item?.name || ''}`"
      @back="router.push('/networks')"
    >
      <a-button :disabled="item?.driver === 'host'" @click="connectOpen = true">
        {{ t("network.connect") }}
      </a-button>
      <a-button @click="load">
        <ReloadOutlined />
      </a-button>
    </DetailHeader>

    <a-spin :spinning="loading">
      <a-tabs v-model:activeKey="tab" v-if="item">
        <a-tab-pane key="basic" :tab="t('network.tabs.basic')">
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item :label="t('network.field.id')">
              <span class="mono">{{ item.id }}</span>
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.name')">
              {{ item.name }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.driver')">
              {{ driverText(item.driver) }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.scope')">
              {{ item.scope }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('createTime')">
              {{ formatTime(item.create_time, locale) }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.attachable')">
              <a-checkbox :checked="item.attachable ?? false" disabled />
              <span style="margin-left: 16px">{{ t("network.field.internal") }}</span>
              <a-checkbox :checked="item.internal ?? false" disabled style="margin-left: 8px" />
            </a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>

        <a-tab-pane key="ipam" :tab="t('network.tabs.ipam')">
          <a-descriptions :column="1" bordered style="max-width: 720px">
            <a-descriptions-item :label="t('network.field.subnet')">
              {{ item.subnet || "-" }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.gateway')">
              {{ item.gateway || "-" }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.ipRange')">
              {{ item.ip_range || "-" }}
            </a-descriptions-item>
            <a-descriptions-item :label="t('network.field.ipamDriver')">
              {{ item.ipam_driver || "-" }}
            </a-descriptions-item>
          </a-descriptions>
          <a-card :title="t('network.steps.options')" style="max-width: 720px; margin-top: 16px">
            <a-table
              :data-source="optionRows"
              :columns="optionColumns"
              :pagination="false"
              size="small"
              row-key="key"
            />
          </a-card>
        </a-tab-pane>

        <a-tab-pane key="containers" :tab="t('network.tabs.containers')">
          <div class="containers-toolbar">
            <a-checkbox v-model:checked="force">{{ t("network.forceDisconnect") }}</a-checkbox>
            <a-button
              v-if="selectedRowKeys.length"
              danger
              @click="disconnectSelected"
            >
              {{ t("network.disconnectSelected") }}
            </a-button>
          </div>
          <a-table
            :data-source="item.containers || []"
            :columns="containerColumns"
            :row-selection="{ selectedRowKeys, onChange: (keys: (string | number)[]) => (selectedRowKeys = keys.map(String)) }"
            :pagination="{ pageSize: 10, hideOnSinglePage: true }"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'id'">
                <span class="mono">{{ shortId(record.id) }}</span>
              </template>
              <template v-else-if="column.key === 'ip'">
                {{ record.network?.ip || "" }}
              </template>
              <template v-else-if="column.key === 'prefix'">
                {{ record.network?.prefix ?? "" }}
              </template>
              <template v-else-if="column.key === 'gateway'">
                {{ record.network?.gateway || "" }}
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space :size="4">
                  <router-link :to="`/containers/${record.id}`">{{ t("detail") }}</router-link>
                  <a-popconfirm
                    :title="t('network.disconnect')"
                    :ok-text="t('ok')"
                    :cancel-text="t('cancel')"
                    @confirm="doDisconnect(record.id)"
                  >
                    <a-button type="link" size="small" danger>
                      {{ t("network.disconnect") }}
                    </a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-spin>

    <ConnectModal v-model:open="connectOpen" :network-id="networkId" @connected="load" />
  </div>
</template>

<script setup lang="ts">
import DetailHeader from "@/components/common/DetailHeader.vue";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { formatTime } from "@dockore/shared";
import { useNetworkStore, errorMessage, type NetworkItem } from "@/stores";
import { shortId } from "@/utils/text";
import ConnectModal from "@/components/network/ConnectModal.vue";

const { t, te, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const store = useNetworkStore();

const tab = ref("basic");
const item = ref<NetworkItem | null>(null);
const loading = ref(false);
const force = ref(false);
const selectedRowKeys = ref<string[]>([]);
const connectOpen = ref(false);

const networkId = computed(() => String(route.params.id));

const optionColumns = computed(() => [
  { title: t("network.optionKey"), key: "key", dataIndex: "key" },
  { title: t("network.optionValue"), key: "value", dataIndex: "value" },
]);

const containerColumns = computed(() => [
  { title: "ID", key: "id", dataIndex: "id", width: 120 },
  { title: t("name"), key: "name", dataIndex: "name" },
  { title: t("container.network.ip"), key: "ip", width: 150 },
  { title: t("container.network.prefix"), key: "prefix", width: 90 },
  { title: t("container.network.gateway"), key: "gateway", width: 150 },
  { title: t("actions"), key: "actions", width: 200 },
]);

const optionRows = computed(() => {
  const options = item.value?.options || {};
  return Object.entries(options).map(([key, value]) => ({ key, value }));
});

function driverText(driver?: string | null): string {
  if (!driver) return "-";
  const key = `network.drivers.${driver}`;
  return te(key) ? t(key) : driver;
}

async function load() {
  loading.value = true;
  try {
    item.value = await store.fetch(networkId.value);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}

async function doDisconnect(containerId: string) {
  try {
    await store.disconnect(networkId.value, containerId, force.value);
    await load();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function disconnectSelected() {
  const ids = [...selectedRowKeys.value];
  selectedRowKeys.value = [];
  for (const id of ids) {
    try {
      await store.disconnect(networkId.value, id, force.value);
    } catch (e: any) {
      message.error(errorMessage(e));
    }
  }
  await load();
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.mono {
  font-family: monospace;
}

.containers-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
</style>
