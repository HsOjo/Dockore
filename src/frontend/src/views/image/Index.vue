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
        <a-switch :checked="store.showAll" @change="handleShowAll" />
        <span>{{ t("image.showAll") }}</span>
      </div>
      <div class="toolbar-right">
        <a-popconfirm
          v-if="selectedRowKeys.length"
          :title="t('image.confirmBatchDelete', { n: selectedRowKeys.length })"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="batchDelete"
        >
          <a-button danger>{{ t("delete") }}</a-button>
        </a-popconfirm>
        <a-button @click="store.fetchAll()">
          <ReloadOutlined />
        </a-button>
        <a-button type="primary" @click="pullOpen = true">{{ t("image.pull") }}</a-button>
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
        <template v-else-if="column.key === 'tags'">
          <a-tag v-for="tag in record.tags" :key="tag" closable @close.prevent>
            {{ tag }}
            <template #closeIcon>
              <a-popconfirm
                :title="t('image.confirmDeleteTag', { tag })"
                :ok-text="t('ok')"
                :cancel-text="t('cancel')"
                @confirm="deleteTag(tag)"
              >
                <CloseOutlined />
              </a-popconfirm>
            </template>
          </a-tag>
        </template>
        <template v-else-if="column.key === 'create_time'">
          {{ relativeTime(record.create_time, locale) }}
        </template>
        <template v-else-if="column.key === 'size'">
          {{ formatBytes(record.size) }}
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4" wrap>
            <router-link :to="`/images/${encodeURIComponent(record.id)}`">
              {{ t("detail") }}
            </router-link>
            <a-button type="link" size="small" @click="openTag(record)">
              {{ t("image.tag") }}
            </a-button>
            <a-button type="link" size="small" @click="openHistory(record)">
              {{ t("image.history") }}
            </a-button>
            <a-popconfirm
              :title="t('image.confirmDelete', { name: imageDisplayName(record) })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="deleteImage(record)"
            >
              <a-button type="link" size="small" danger>{{ t("delete") }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </DataTable>

    <PullModal v-model:open="pullOpen" />
    <TagModal v-model:open="tagOpen" :image-id="activeId" />
    <HistoryModal v-model:open="historyOpen" :image-id="activeId" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { CloseOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { formatBytes, relativeTime } from "@dockore/shared";
import { useImageStore, errorMessage, type ImageItem } from "@/stores";
import { shortId, imageDisplayName } from "@/utils/text";
import PullModal from "@/components/image/PullModal.vue";
import TagModal from "@/components/image/TagModal.vue";
import HistoryModal from "@/components/image/HistoryModal.vue";
import DataTable from "@/components/common/DataTable.vue";

const { t, locale } = useI18n();
const store = useImageStore();

const keyword = ref("");
const selectedRowKeys = ref<string[]>([]);

const pullOpen = ref(false);
const tagOpen = ref(false);
const historyOpen = ref(false);
const activeId = ref("");

const columns = computed(() => [
  { title: "ID", key: "id", dataIndex: "id", width: 120 },
  { title: t("image.field.tags"), key: "tags", dataIndex: "tags", width: 320 },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 160 },
  { title: t("image.field.size"), key: "size", dataIndex: "size", width: 110 },
  { title: t("actions"), key: "actions", width: 300, fixed: "right" as const },
]);

const tableData = computed(() => {
  let items = store.images;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) =>
        item.tags.join(",").toLowerCase().includes(kw) || item.id.toLowerCase().includes(kw)
    );
  }
  return items;
});

function handleShowAll(checked: string | number | boolean) {
  store.showAll = Boolean(checked);
  store.fetchAll().catch((e) => message.error(errorMessage(e)));
}

async function runWithError(fn: () => Promise<unknown>) {
  try {
    await fn();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function openTag(record: ImageItem) {
  activeId.value = record.id;
  tagOpen.value = true;
}

function openHistory(record: ImageItem) {
  activeId.value = record.id;
  historyOpen.value = true;
}

async function deleteTag(tag: string) {
  await runWithError(() => store.remove([tag], true));
}

async function deleteImage(record: ImageItem) {
  const ids = record.tags.length > 1 ? record.tags : [record.id];
  await runWithError(() => store.remove(ids));
}

async function batchDelete() {
  const ids: string[] = [];
  for (const key of selectedRowKeys.value) {
    const item = store.images.find((i) => i.id === key);
    if (!item) continue;
    if (item.tags.length > 1) ids.push(...item.tags);
    else ids.push(item.id);
  }
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
