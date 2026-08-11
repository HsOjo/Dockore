<template>
  <div>
    <div class="toolbar">
      <div class="toolbar-left">
        <a-input
          v-model:value="keyword"
          :placeholder="t('searchPlaceholder')"
          style="width: 256px"
          allow-clear
        />
      </div>
      <div class="toolbar-right">
        <a-popconfirm
          v-if="selectedRowKeys.length"
          :title="t('network.confirmBatchDelete', { n: selectedRowKeys.length })"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="batchDelete"
        >
          <a-button danger>{{ t("delete") }}</a-button>
        </a-popconfirm>
        <a-button @click="store.fetchAll()">
          <ReloadOutlined />
        </a-button>
        <a-button type="primary" @click="createOpen = true">{{ t("network.create") }}</a-button>
      </div>
    </div>

    <DataTable
      :data-source="tableData"
      :columns="columns"
      :loading="store.loading"
      :row-selection="{ selectedRowKeys, onChange: (keys: (string | number)[]) => (selectedRowKeys = keys.map(String)) }"
      :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'id'">
          <span class="mono">{{ shortId(record.id) }}</span>
        </template>
        <template v-else-if="column.key === 'driver'">
          {{ driverText(record.driver) }}
        </template>
        <template v-else-if="column.key === 'create_time'">
          {{ relativeTime(record.create_time, locale) }}
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4" wrap>
            <router-link :to="`/networks/${record.id}`">{{ t("detail") }}</router-link>
            <a-button
              type="link"
              size="small"
              :disabled="record.driver === 'host'"
              @click="openConnect(record)"
            >
              {{ t("network.connect") }}
            </a-button>
            <a-popconfirm
              :title="t('network.confirmDelete', { name: record.name })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="handleDelete([record.id])"
            >
              <a-button type="link" size="small" danger>{{ t("delete") }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </DataTable>

    <CreateModal v-model:open="createOpen" />
    <ConnectModal v-model:open="connectOpen" :network-id="activeId" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { relativeTime } from "@dockore/shared";
import { useNetworkStore, errorMessage, type NetworkItem } from "@/stores";
import { shortId } from "@/utils/text";
import CreateModal from "@/components/network/CreateModal.vue";
import ConnectModal from "@/components/network/ConnectModal.vue";
import DataTable from "@/components/common/DataTable.vue";

const { t, te, locale } = useI18n();
const store = useNetworkStore();

const keyword = ref("");
const selectedRowKeys = ref<string[]>([]);

const createOpen = ref(false);
const connectOpen = ref(false);
const activeId = ref("");

const columns = computed(() => [
  { title: "ID", key: "id", dataIndex: "id", width: 120 },
  { title: t("name"), key: "name", dataIndex: "name", width: 220, ellipsis: true },
  { title: t("network.field.driver"), key: "driver", dataIndex: "driver", width: 120 },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 160 },
  { title: t("network.field.containerNum"), key: "container_num", dataIndex: "container_num", width: 120 },
  { title: t("actions"), key: "actions", width: 260, fixed: "right" as const },
]);

const tableData = computed(() => {
  let items = store.networks;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) => item.name.toLowerCase().includes(kw) || item.id.toLowerCase().includes(kw)
    );
  }
  return items;
});

function driverText(driver: string): string {
  const key = `network.drivers.${driver}`;
  return te(key) ? t(key) : driver;
}

function openConnect(record: NetworkItem) {
  activeId.value = record.id;
  connectOpen.value = true;
}

async function runWithError(fn: () => Promise<unknown>) {
  try {
    await fn();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function handleDelete(ids: string[]) {
  await runWithError(() => store.remove(ids));
}

async function batchDelete() {
  const ids = [...selectedRowKeys.value];
  selectedRowKeys.value = [];
  await runWithError(() => store.remove(ids));
}

onMounted(() => {
  store.fetchAll().catch((e) => message.error(errorMessage(e)));
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mono {
  font-family: monospace;
}
</style>
