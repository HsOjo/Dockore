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
          :title="t('volume.confirmBatchDelete', { n: selectedRowKeys.length })"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="batchDelete"
        >
          <a-button danger>{{ t("delete") }}</a-button>
        </a-popconfirm>
        <a-button @click="store.fetchAll()">
          <ReloadOutlined />
        </a-button>
        <a-button type="primary" @click="createOpen = true">{{ t("volume.create") }}</a-button>
      </div>
    </div>

    <a-table
      :data-source="tableData"
      :columns="columns"
      :loading="store.loading"
      :row-selection="{ selectedRowKeys, onChange: (keys: (string | number)[]) => (selectedRowKeys = keys.map(String)) }"
      :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'create_time'">
          {{ relativeTime(record.create_time, locale) }}
        </template>
        <template v-else-if="column.key === 'mount_point'">
          <span class="mono">{{ record.mount_point }}</span>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4">
            <router-link :to="`/volumes/${encodeURIComponent(record.id)}`">
              {{ t("detail") }}
            </router-link>
            <a-popconfirm
              :title="t('volume.confirmDelete', { name: record.name })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="handleDelete([record.id])"
            >
              <a-button type="link" size="small" danger>{{ t("delete") }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <CreateModal v-model:open="createOpen" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { relativeTime } from "@dockore/shared";
import { useVolumeStore, errorMessage } from "@/stores";
import CreateModal from "@/components/volume/CreateModal.vue";

const { t, locale } = useI18n();
const store = useVolumeStore();

const keyword = ref("");
const selectedRowKeys = ref<string[]>([]);
const createOpen = ref(false);

const columns = computed(() => [
  { title: t("volume.field.name"), key: "name", dataIndex: "name", width: 200 },
  { title: t("volume.field.driver"), key: "driver", dataIndex: "driver", width: 140 },
  { title: t("volume.field.mountPoint"), key: "mount_point", dataIndex: "mount_point" },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 180 },
  { title: t("actions"), key: "actions", width: 160, fixed: "right" as const },
]);

const tableData = computed(() => {
  let items = store.volumes;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) => item.name.toLowerCase().includes(kw) || item.id.toLowerCase().includes(kw)
    );
  }
  return items;
});

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
