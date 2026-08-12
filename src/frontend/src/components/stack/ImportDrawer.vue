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
        <template v-else-if="column.key === 'actions'">
          <a-button
            type="link"
            size="small"
            :loading="importingName === record.name"
            @click="confirmImport(record)"
          >
            {{ t("stack.import") }}
          </a-button>
        </template>
      </template>
    </DataTable>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message, Modal } from "ant-design-vue";
import { useStackStore, errorMessage, type StackItem } from "@/stores";
import DataTable from "@/components/common/DataTable.vue";
import EllipsisText from "@/components/common/EllipsisText.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  imported: [];
}>();

const { t, te } = useI18n();
const store = useStackStore();

const importingName = ref("");

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
  { title: t("actions"), key: "actions", width: 90 },
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

function confirmImport(record: StackItem) {
  Modal.confirm({
    title: t("stack.importConfirm", { name: record.name }),
    okText: t("ok"),
    cancelText: t("cancel"),
    onOk: async () => {
      importingName.value = record.name;
      try {
        await store.importStack(record.name);
        message.success(t("stack.importSuccess", { name: record.name }));
        emit("imported");
      } catch (e: any) {
        message.error(errorMessage(e));
      } finally {
        importingName.value = "";
      }
    },
  });
}
</script>
