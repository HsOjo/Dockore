<template>
  <a-modal
    :open="open"
    :title="t('volume.create')"
    width="720px"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    :ok-button-props="{ disabled: !form.name }"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-tabs v-model:activeKey="tab">
      <a-tab-pane key="info" :tab="t('volume.steps.info')">
        <a-form layout="vertical" style="max-width: 480px">
          <a-form-item :label="t('volume.field.name')" required>
            <a-input v-model:value="form.name" />
          </a-form-item>
          <a-form-item :label="t('volume.field.driver')">
            <a-select v-model:value="form.driver" :options="[{ label: 'local', value: 'local' }]" />
          </a-form-item>
        </a-form>
      </a-tab-pane>
      <a-tab-pane key="driverOpts" :tab="t('volume.steps.driverOpts')">
        <a-table :data-source="form.driver_opts" :columns="columns" :pagination="false" size="small">
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'key'">
              <a-auto-complete
                v-model:value="record.key"
                :options="suggestions"
                style="width: 100%"
                :filter-option="filterOption"
              />
            </template>
            <template v-else-if="column.key === 'value'">
              <a-input v-model:value="record.value" />
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button type="text" danger size="small" @click="form.driver_opts.splice(index, 1)">
                <DeleteOutlined />
              </a-button>
            </template>
          </template>
        </a-table>
        <a-button style="margin-top: 8px" @click="form.driver_opts.push({ key: '', value: '' })">
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
import { useVolumeStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const store = useVolumeStore();

const tab = ref("info");
const loading = ref(false);

interface OptionRow {
  key: string;
  value: string;
}

const form = reactive({
  name: "",
  driver: "local",
  driver_opts: [] as OptionRow[],
});

const suggestions = ["type", "device", "o"].map((v) => ({ value: v }));

const columns = computed(() => [
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
    Object.assign(form, { name: "", driver: "local", driver_opts: [] });
  }
);

async function handleOk() {
  loading.value = true;
  try {
    await store.create({
      name: form.name,
      driver: form.driver || null,
      driver_opts: form.driver_opts.filter((o) => o.key && o.value),
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
