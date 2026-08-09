<template>
  <a-modal
    :open="open"
    :title="t('network.create')"
    width="720px"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    :ok-button-props="{ disabled: !form.name }"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-tabs v-model:activeKey="tab">
      <a-tab-pane key="info" :tab="t('network.steps.info')">
        <a-form layout="vertical" style="max-width: 480px">
          <a-form-item :label="t('network.field.name')" required>
            <a-input v-model:value="form.name" />
          </a-form-item>
          <a-form-item :label="t('network.field.driver')">
            <a-select v-model:value="form.driver" :options="driverOptions" />
          </a-form-item>
          <a-form-item :label="t('network.field.subnet')">
            <a-input v-model:value="form.subnet" placeholder="x.x.x.x/yy" />
          </a-form-item>
          <a-form-item :label="t('network.field.gateway')">
            <a-input v-model:value="form.gateway" placeholder="x.x.x.x" />
          </a-form-item>
          <a-form-item :label="t('network.field.ipRange')">
            <a-input v-model:value="form.ip_range" placeholder="x.x.x.x/yy" />
          </a-form-item>
          <a-form-item>
            <a-checkbox v-model:checked="form.attachable">
              {{ t("network.field.attachable") }}
            </a-checkbox>
          </a-form-item>
        </a-form>
      </a-tab-pane>
      <a-tab-pane key="options" :tab="t('network.steps.options')">
        <a-table :data-source="form.options" :columns="optionColumns" :pagination="false" size="small">
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'key'">
              <a-auto-complete
                v-model:value="record.key"
                :options="optionSuggestions"
                :placeholder="t('network.optionKeyPlaceholder')"
                style="width: 100%"
                :filter-option="filterOption"
              />
            </template>
            <template v-else-if="column.key === 'value'">
              <a-input v-model:value="record.value" />
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="text" danger size="small" @click="form.options.splice(index, 1)">
                <DeleteOutlined />
              </a-button>
            </template>
          </template>
        </a-table>
        <a-button style="margin-top: 8px" @click="form.options.push({ key: '', value: '' })">
          <PlusOutlined /> {{ t("create") }}
        </a-button>
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons-vue";
import { useNetworkStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t, te } = useI18n();
const store = useNetworkStore();

const tab = ref("info");
const loading = ref(false);

interface OptionRow {
  key: string;
  value: string;
}

const form = reactive({
  name: "",
  driver: "bridge",
  subnet: "",
  gateway: "",
  ip_range: "",
  attachable: true,
  options: [] as OptionRow[],
});

const optionSuggestions = [
  "com.docker.network.bridge.name",
  "com.docker.network.bridge.host_binding_ipv4",
  "com.docker.network.bridge.mtu",
  "com.docker.network.bridge.default_bridge",
  "com.docker.network.bridge.enable_icc",
  "com.docker.network.bridge.enable_ip_masquerade",
].map((v) => ({ value: v }));

const driverOptions = computed(() =>
  ["bridge", "host", "overlay", "macvlan", "ipvlan", "none"].map((d) => ({
    label: te(`network.drivers.${d}`) ? t(`network.drivers.${d}`) : d,
    value: d,
  }))
);

const optionColumns = computed(() => [
  { title: t("network.optionKey"), key: "key", width: 320 },
  { title: t("network.optionValue"), key: "value" },
  { title: t("actions"), key: "actions", width: 60 },
]);

function filterOption(input: string, option: any) {
  return String(option.value).toLowerCase().includes(input.toLowerCase());
}

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    tab.value = "info";
    Object.assign(form, {
      name: "",
      driver: "bridge",
      subnet: "",
      gateway: "",
      ip_range: "",
      attachable: true,
      options: [],
    });
  }
);

async function handleOk() {
  loading.value = true;
  try {
    await store.create({
      name: form.name,
      driver: form.driver,
      attachable: form.attachable,
      options: form.options.filter((o) => o.key && o.value),
      subnet: form.subnet || null,
      gateway: form.gateway || null,
      ip_range: form.ip_range || null,
    });
    emit("update:open", false);
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>
