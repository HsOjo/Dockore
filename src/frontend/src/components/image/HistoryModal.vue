<template>
  <a-modal
    :open="open"
    :title="t('image.history')"
    width="960px"
    :footer="null"
    @cancel="emit('update:open', false)"
  >
    <a-table
      :data-source="histories"
      :columns="columns"
      :loading="loading"
      :pagination="{ pageSize: 10, hideOnSinglePage: true }"
      size="small"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'id'">
          <span v-if="record.id === '<missing>'" class="mono">{{ record.id }}</span>
          <router-link v-else :to="`/images/${encodeURIComponent(record.id)}`" class="mono">
            {{ shortId(record.id) }}
          </router-link>
        </template>
        <template v-else-if="column.key === 'tags'">
          <a-tag v-for="tag in record.tags || []" :key="tag">{{ tag }}</a-tag>
        </template>
        <template v-else-if="column.key === 'created_time'">
          {{ relativeTime(record.created_time, locale) }}
        </template>
        <template v-else-if="column.key === 'size'">
          {{ formatBytes(record.size) }}
        </template>
        <template v-else-if="column.key === 'created_by'">
          <a-popover :title="t('image.historyForm.createdBy')" placement="left">
            <template #content>
              <pre class="created-by">{{ record.created_by }}</pre>
            </template>
            <a-button size="small">{{ t("image.historyForm.view") }}</a-button>
          </a-popover>
        </template>
      </template>
    </a-table>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { formatBytes, relativeTime } from "@dockore/shared";
import { useImageStore, errorMessage, type HistoryItem } from "@/stores";
import { shortId } from "@/utils/text";

const props = defineProps<{ open: boolean; imageId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t, locale } = useI18n();
const store = useImageStore();

const loading = ref(false);
const histories = ref<HistoryItem[]>([]);

const columns = computed(() => [
  { title: t("image.historyForm.id"), key: "id", dataIndex: "id", width: 130 },
  { title: t("image.historyForm.tags"), key: "tags", dataIndex: "tags" },
  { title: t("image.historyForm.comment"), key: "comment", dataIndex: "comment" },
  { title: t("createTime"), key: "created_time", dataIndex: "created_time", width: 150 },
  { title: t("image.field.size"), key: "size", dataIndex: "size", width: 100 },
  { title: t("image.historyForm.createdBy"), key: "created_by", width: 100 },
]);

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    histories.value = [];
    loading.value = true;
    try {
      histories.value = await store.history(props.imageId);
    } catch (e: any) {
      message.error(errorMessage(e));
    } finally {
      loading.value = false;
    }
  }
);
</script>

<style scoped>
.mono {
  font-family: monospace;
}

.created-by {
  max-width: 480px;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
</style>
