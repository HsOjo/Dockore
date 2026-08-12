<template>
  <a-modal
    :open="open"
    :title="t('image.pull')"
    width="860px"
    :footer="null"
    @cancel="handleClose"
  >
    <div class="toolbar">
      <h3 style="margin: 0">{{ t("image.searchResults") }}</h3>
      <a-input-search
        v-model:value="keyword"
        :placeholder="t('image.searchHub')"
        style="width: 320px"
        :loading="searching"
        @search="doSearch"
      />
    </div>
    <a-table
      :data-source="results"
      :columns="columns"
      :pagination="{ pageSize: 5, showSizeChanger: false }"
      size="small"
      row-key="name"
      :custom-row="customRow"
      :row-class-name="rowClassName"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_official'">
          {{ record.is_official ? t("image.pullForm.yes") : t("image.pullForm.no") }}
        </template>
        <template v-else-if="column.key === 'is_automated'">
          {{ record.is_automated ? t("image.pullForm.yes") : t("image.pullForm.no") }}
        </template>
      </template>
    </a-table>
    <div class="footer">
      <a-input
        v-model:value="tag"
        :placeholder="t('image.pullForm.tag')"
        style="width: 180px"
      />
      <a-button @click="handleClose">{{ t("cancel") }}</a-button>
      <a-button type="primary" :disabled="!selected" :loading="starting" @click="startPull">
        {{ t("ok") }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useImageStore, errorMessage, type ImageSearchItem } from "@/stores";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  started: [{ taskId: string; name: string }];
}>();

const { t } = useI18n();
const store = useImageStore();

const keyword = ref("");
const searching = ref(false);
const results = ref<ImageSearchItem[]>([]);
const selected = ref<ImageSearchItem | null>(null);
const tag = ref("");
const starting = ref(false);

const columns = computed(() => [
  { title: t("image.pullForm.name"), key: "name", dataIndex: "name", width: 200 },
  { title: t("image.pullForm.description"), key: "description", dataIndex: "description" },
  { title: t("image.pullForm.starCount"), key: "star_count", dataIndex: "star_count", width: 100 },
  { title: t("image.pullForm.isOfficial"), key: "is_official", width: 90 },
  { title: t("image.pullForm.isAutomated"), key: "is_automated", width: 90 },
]);

function customRow(record: ImageSearchItem) {
  return { onClick: () => (selected.value = record) };
}

function rowClassName(record: ImageSearchItem) {
  return record.name === selected.value?.name ? "row-selected" : "";
}

async function doSearch() {
  if (!keyword.value) return;
  searching.value = true;
  try {
    results.value = await store.search(keyword.value);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    searching.value = false;
  }
}

async function startPull() {
  if (!selected.value?.name) return;
  starting.value = true;
  try {
    const created = await store.pull(selected.value.name, tag.value || null);
    const name = tag.value
      ? `${selected.value.name}:${tag.value}`
      : selected.value.name;
    emit("started", { taskId: created.pull_id, name });
    emit("update:open", false);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    starting.value = false;
  }
}

function handleClose() {
  emit("update:open", false);
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      keyword.value = "";
      results.value = [];
      selected.value = null;
      tag.value = "";
    }
  }
);
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

:deep(.row-selected) > td {
  background-color: rgba(22, 119, 255, 0.12) !important;
}

:deep(.ant-table-row) {
  cursor: pointer;
}
</style>
