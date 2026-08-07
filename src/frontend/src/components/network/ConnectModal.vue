<template>
  <a-modal
    :open="open"
    :title="t('network.connect')"
    width="860px"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    :ok-button-props="{ disabled: !selected }"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-steps :current="step" :items="stepItems" size="small" style="margin-bottom: 24px" />

    <div v-show="step === 0">
      <a-input
        v-model:value="keyword"
        :placeholder="t('searchPlaceholder')"
        style="width: 256px; margin-bottom: 12px"
        allow-clear
      />
      <a-table
        :data-source="filteredContainers"
        :columns="containerColumns"
        :loading="containerStore.loading"
        :pagination="{ pageSize: 5, showSizeChanger: false }"
        size="small"
        row-key="id"
        :custom-row="customRow"
        :row-class-name="rowClassName"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'id'">
            <span class="mono">{{ shortId(record.id) }}</span>
          </template>
          <template v-else-if="column.key === 'create_time'">
            {{ relativeTime(record.create_time, locale) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge
              :status="containerStatusBadge(record.status)"
              :text="statusText(record.status)"
            />
          </template>
        </template>
      </a-table>
    </div>

    <div v-show="step === 1">
      <a-form layout="vertical" style="max-width: 480px">
        <a-form-item :label="t('network.field.name')">
          <a-input :value="network?.name" readonly />
        </a-form-item>
        <a-form-item :label="t('network.containerName')">
          <a-input :value="selected?.name" readonly />
        </a-form-item>
        <a-form-item :label="t('network.assignIPv4')">
          <a-input
            v-model:value="ipv4Address"
            :placeholder="
              t('network.subnetHint', {
                subnet: network?.subnet || '-',
                ipRange: network?.ip_range || '-',
              })
            "
          />
        </a-form-item>
      </a-form>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { relativeTime } from "@dockore/shared";
import {
  useContainerStore,
  useNetworkStore,
  errorMessage,
  type ContainerItem,
  type NetworkItem,
} from "@/stores";
import { containerStatusBadge, shortId } from "@/utils/text";

const props = defineProps<{ open: boolean; networkId: string }>();
const emit = defineEmits<{ "update:open": [boolean]; connected: [] }>();

const { t, te, locale } = useI18n();
const containerStore = useContainerStore();
const networkStore = useNetworkStore();

const step = ref(0);
const keyword = ref("");
const loading = ref(false);
const network = ref<NetworkItem | null>(null);
const selected = ref<ContainerItem | null>(null);
const ipv4Address = ref("");

const stepItems = computed(() => [
  { title: t("network.selectContainer") },
  { title: t("network.connectInfo") },
]);

const containerColumns = computed(() => [
  { title: "ID", key: "id", dataIndex: "id", width: 120 },
  { title: t("name"), key: "name", dataIndex: "name" },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 160 },
  { title: t("status"), key: "status", dataIndex: "status", width: 120 },
]);

const filteredContainers = computed(() => {
  const existed = new Set((network.value?.containers || []).map((c) => c.id));
  let items = containerStore.containers.filter((c) => !existed.has(c.id));
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (c) => c.name.toLowerCase().includes(kw) || c.id.toLowerCase().includes(kw)
    );
  }
  return items;
});

function statusText(status: string): string {
  const key = `container.status.${status}`;
  return te(key) ? t(key) : status;
}

function customRow(record: ContainerItem) {
  return {
    onClick: () => {
      selected.value = record;
      step.value = 1;
    },
  };
}

function rowClassName(record: ContainerItem) {
  return record.id === selected.value?.id ? "row-selected" : "";
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    step.value = 0;
    keyword.value = "";
    selected.value = null;
    ipv4Address.value = "";
    network.value = null;
    try {
      network.value = await networkStore.fetch(props.networkId);
      containerStore.showAll = true;
      await containerStore.fetchAll();
    } catch (e: any) {
      message.error(errorMessage(e));
    }
  }
);

async function handleOk() {
  if (!selected.value) return;
  loading.value = true;
  try {
    await networkStore.connect(props.networkId, selected.value.id, ipv4Address.value || null);
    emit("update:open", false);
    emit("connected");
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.mono {
  font-family: monospace;
}

:deep(.row-selected) > td {
  background-color: rgba(22, 119, 255, 0.12) !important;
}

:deep(.ant-table-row) {
  cursor: pointer;
}
</style>
