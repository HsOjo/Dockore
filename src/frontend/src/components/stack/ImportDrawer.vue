<template>
  <a-drawer
    :open="open"
    :title="t('stack.importTitle')"
    width="720"
    @close="emit('update:open', false)"
  >
    <DataTable
      :data-source="items"
      :columns="columns"
      :loading="store.loading"
      :pagination="false"
      :row-selection="{
        selectedRowKeys,
        onChange: (keys: (string | number)[]) => (selectedRowKeys = keys.map(String)),
      }"
      row-key="name"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusText(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'containers'">
          {{ record.running }}/{{ record.total }}
        </template>
        <template v-else-if="column.key === 'working_dir'">
          <EllipsisText :text="record.working_dir || t('none')" mono />
        </template>
      </template>
    </DataTable>
    <template #footer>
      <div class="footer">
        <a-popconfirm
          v-if="selectedRowKeys.length"
          :title="t('stack.importBatchConfirm', { count: selectedRowKeys.length })"
          :ok-text="t('ok')"
          :cancel-text="t('cancel')"
          @confirm="batchImport"
        >
          <a-button type="primary" :loading="importing">
            {{ t("stack.import") }} ({{ selectedRowKeys.length }})
          </a-button>
        </a-popconfirm>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";
import DataTable from "@/components/common/DataTable.vue";
import EllipsisText from "@/components/common/EllipsisText.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  imported: [];
}>();

const { t, te } = useI18n();
const store = useStackStore();

const importing = ref(false);
const selectedRowKeys = ref<string[]>([]);

const items = computed(() => store.stacks.filter((s) => !s.registered));

const columns = computed(() => [
  { title: t("name"), key: "name", dataIndex: "name", width: 160, ellipsis: true },
  { title: t("status"), key: "status", dataIndex: "status", width: 100 },
  { title: t("stack.field.containers"), key: "containers", width: 80 },
  {
    title: t("stack.field.workingDir"),
    key: "working_dir",
    dataIndex: "working_dir",
    ellipsis: { showTitle: false },
  },
]);

function statusColor(status: string): string {
  switch (status) {
    case "running":
      return "green";
    case "partial":
      return "orange";
    case "missing":
      return "red";
    default:
      return "default";
  }
}

function statusText(status: string): string {
  const key = `stack.status.${status}`;
  return te(key) ? t(key) : status;
}

watch(
  () => props.open,
  (open) => {
    if (open) store.fetchAll().catch((e) => message.error(errorMessage(e)));
  }
);

watch(
  items,
  (list) => {
    if (props.open) selectedRowKeys.value = list.map((s) => s.name);
  },
  { immediate: true }
);

async function batchImport() {
  const names = [...selectedRowKeys.value];
  importing.value = true;
  let ok = 0;
  try {
    for (const name of names) {
      try {
        await store.importStack(name);
        ok++;
      } catch (e: any) {
        message.error(`${name}: ${errorMessage(e)}`);
      }
    }
    if (ok) {
      message.success(t("stack.importBatchSuccess", { count: ok }));
      emit("imported");
    }
  } finally {
    importing.value = false;
  }
}
</script>

<style scoped>
.footer {
  display: flex;
  justify-content: flex-end;
}
</style>
