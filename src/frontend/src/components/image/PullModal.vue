<template>
  <a-modal
    :open="open"
    :title="t('image.pull')"
    width="860px"
    :footer="null"
    @cancel="handleClose"
  >
    <template v-if="!pulling">
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
    </template>

    <template v-else>
      <div class="pull-status">
        <p>{{ t("image.pulling", { name: pullName }) }}</p>
        <a-progress :percent="100" status="active" :show-info="false" />
        <p class="mono">{{ lastStatus }}</p>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { wsClient } from "@dockore/shared";
import { useImageStore, errorMessage, type ImageSearchItem } from "@/stores";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ "update:open": [boolean]; pulled: [] }>();

const { t } = useI18n();
const store = useImageStore();

const keyword = ref("");
const searching = ref(false);
const results = ref<ImageSearchItem[]>([]);
const selected = ref<ImageSearchItem | null>(null);
const tag = ref("");
const starting = ref(false);

const pulling = ref(false);
const pullName = ref("");
const lastStatus = ref("");

let pullId = "";

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

function onPullEvent(data: any) {
  if (!pullId || data?.pull_id !== pullId) return;
  if (data.status === "done") {
    cleanup();
    pulling.value = false;
    message.success(t("image.pullDone"));
    emit("update:open", false);
    emit("pulled");
    store.fetchAll().catch(() => {});
  } else if (data.status === "error") {
    lastStatus.value = data.error || "";
    cleanup();
    pulling.value = false;
    message.error(`${t("image.pullError")}: ${data.error || ""}`);
  } else {
    lastStatus.value = [data.id, data.status, data.progress].filter(Boolean).join(" ");
  }
}

function cleanup() {
  wsClient.off("image.pull", onPullEvent);
  pullId = "";
}

async function startPull() {
  if (!selected.value?.name) return;
  starting.value = true;
  try {
    const created = await store.pull(selected.value.name, tag.value || null);
    pullId = created.pull_id;
    pullName.value = tag.value
      ? `${selected.value.name}:${tag.value}`
      : selected.value.name;
    lastStatus.value = "";
    pulling.value = true;
    wsClient.on("image.pull", onPullEvent);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    starting.value = false;
  }
}

function handleClose() {
  cleanup();
  pulling.value = false;
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
      pulling.value = false;
    } else {
      cleanup();
    }
  }
);

onBeforeUnmount(cleanup);
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

.pull-status {
  padding: 32px 16px;
}

.mono {
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
}

:deep(.row-selected) > td {
  background-color: rgba(22, 119, 255, 0.12) !important;
}

:deep(.ant-table-row) {
  cursor: pointer;
}
</style>
