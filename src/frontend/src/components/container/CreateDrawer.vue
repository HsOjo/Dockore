<template>
  <a-drawer
    :open="open"
    :title="t('container.create')"
    width="860"
    @close="emit('update:open', false)"
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
        :data-source="filteredImages"
        :columns="imageColumns"
        :loading="imageStore.loading"
        :pagination="{ pageSize: 5, showSizeChanger: false }"
        size="small"
        row-key="id"
        :custom-row="customRow"
        :row-class-name="rowClassName"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'tags'">
            <a-tag v-for="tag in record.tags" :key="tag">{{ tag }}</a-tag>
          </template>
          <template v-else-if="column.key === 'create_time'">
            {{ relativeTime(record.create_time, locale) }}
          </template>
          <template v-else-if="column.key === 'size'">
            {{ formatBytes(record.size) }}
          </template>
        </template>
      </a-table>
    </div>

    <div v-show="step === 1">
      <a-form layout="vertical" style="max-width: 480px">
        <a-form-item :label="t('container.field.name')">
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item :label="t('container.imageName')">
          <a-input v-model:value="form.image" readonly />
        </a-form-item>
        <a-form-item :label="t('container.imageTag')">
          <a-select v-model:value="form.tag" :options="tagOptions" />
        </a-form-item>
        <a-form-item :label="t('container.field.command')">
          <a-input v-model:value="form.command" />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="form.tty">{{ t("container.field.tty") }}</a-checkbox>
          <a-checkbox v-model:checked="form.interactive">
            {{ t("container.field.interactive") }}
          </a-checkbox>
          <a-checkbox v-model:checked="form.privileged">
            {{ t("container.field.privileged") }}
          </a-checkbox>
        </a-form-item>
      </a-form>
    </div>

    <div v-show="step === 2">
      <a-table :data-source="form.ports" :columns="portColumns" :pagination="false" size="small">
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'port'">
            <a-input-number v-model:value="record.port" :min="1" :max="65535" style="width: 100%" />
          </template>
          <template v-else-if="column.key === 'protocol'">
            <a-select
              v-model:value="record.protocol"
              :options="[
                { label: 'TCP', value: 'tcp' },
                { label: 'UDP', value: 'udp' },
              ]"
              style="width: 100%"
            />
          </template>
          <template v-else-if="column.key === 'listen_ip'">
            <a-select
              v-model:value="record.listen_ip"
              :options="[
                { label: '0.0.0.0', value: '0.0.0.0' },
                { label: '127.0.0.1', value: '127.0.0.1' },
              ]"
              style="width: 100%"
            />
          </template>
          <template v-else-if="column.key === 'listen_port'">
            <a-input-number
              v-model:value="record.listen_port"
              :min="1"
              :max="65535"
              style="width: 100%"
            />
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="text" danger size="small" @click="form.ports.splice(index, 1)">
              <DeleteOutlined />
            </a-button>
          </template>
        </template>
      </a-table>
      <a-button style="margin-top: 8px" @click="appendPort">
        <PlusOutlined /> {{ t("container.addMapping") }}
      </a-button>
    </div>

    <div v-show="step === 3">
      <a-table :data-source="form.volumes" :columns="volumeColumns" :pagination="false" size="small">
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'path'">
            <a-auto-complete
              v-model:value="record.path"
              :options="volumeOptions"
              style="width: 100%"
              :filter-option="filterVolume"
            />
          </template>
          <template v-else-if="column.key === 'mode'">
            <a-select
              v-model:value="record.mode"
              :options="[
                { label: t('volume.mountMode.rw'), value: 'rw' },
                { label: t('volume.mountMode.ro'), value: 'ro' },
              ]"
              style="width: 100%"
            />
          </template>
          <template v-else-if="column.key === 'bind'">
            <a-input v-model:value="record.bind" placeholder="/data" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="text" danger size="small" @click="form.volumes.splice(index, 1)">
              <DeleteOutlined />
            </a-button>
          </template>
        </template>
      </a-table>
      <a-button style="margin-top: 8px" @click="appendVolume">
        <PlusOutlined /> {{ t("container.addMapping") }}
      </a-button>
    </div>

    <template #footer>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <a-switch
          v-model:checked="run"
          :checked-children="t('container.runContainer')"
          :un-checked-children="t('container.createOnly')"
        />
        <div>
          <a-button v-if="step > 0" style="margin-right: 8px" @click="step--">
            {{ t("back") }}
          </a-button>
          <a-button v-if="step < 3" type="primary" :disabled="step === 0 && !selectedImage" @click="step++">
            {{ t("next") }}
          </a-button>
          <a-button
            v-else
            type="primary"
            :loading="creating"
            :disabled="!form.image"
            @click="handleCreate"
          >
            {{ t("ok") }}
          </a-button>
        </div>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons-vue";
import { formatBytes, relativeTime } from "@dockore/shared";
import {
  useContainerStore,
  useImageStore,
  useVolumeStore,
  errorMessage,
  type ImageItem,
} from "@/stores";
import { shortId } from "@/utils/text";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ "update:open": [boolean]; created: [] }>();

const { t, locale } = useI18n();
const containerStore = useContainerStore();
const imageStore = useImageStore();
const volumeStore = useVolumeStore();

const step = ref(0);
const keyword = ref("");
const run = ref(true);
const creating = ref(false);
const selectedImage = ref<ImageItem | null>(null);

interface PortRow {
  port: number | null;
  protocol: string;
  listen_ip: string;
  listen_port: number | null;
}

interface VolumeRow {
  path: string;
  mode: string;
  bind: string;
}

const form = reactive({
  name: "",
  image: "",
  tag: "",
  command: "",
  tty: false,
  interactive: false,
  privileged: false,
  ports: [] as PortRow[],
  volumes: [] as VolumeRow[],
});

const stepItems = computed(() => [
  { title: t("container.createSteps.image") },
  { title: t("container.createSteps.info") },
  { title: t("container.createSteps.ports") },
  { title: t("container.createSteps.volumes") },
]);

const imageColumns = computed(() => [
  { title: t("image.field.id"), key: "id", dataIndex: "id", width: 140 },
  { title: t("image.field.tags"), key: "tags", dataIndex: "tags" },
  { title: t("image.field.author"), key: "author", dataIndex: "author", width: 140 },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 140 },
  { title: t("image.field.size"), key: "size", dataIndex: "size", width: 100 },
]);

const portColumns = computed(() => [
  { title: t("container.network.port"), key: "port", width: 140 },
  { title: t("container.network.protocol"), key: "protocol", width: 120 },
  { title: t("container.network.listenIp"), key: "listen_ip", width: 180 },
  { title: t("container.network.listenPort"), key: "listen_port", width: 140 },
  { title: t("actions"), key: "actions", width: 60 },
]);

const volumeColumns = computed(() => [
  { title: t("container.mountPath"), key: "path", width: 240 },
  { title: t("container.storage.mode"), key: "mode", width: 120 },
  { title: t("container.mountBind"), key: "bind", width: 240 },
  { title: t("actions"), key: "actions", width: 60 },
]);

const filteredImages = computed(() => {
  let items = imageStore.images;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) =>
        item.tags.join(",").toLowerCase().includes(kw) || item.id.toLowerCase().includes(kw)
    );
  }
  return items;
});

const tagOptions = computed(() => {
  if (!selectedImage.value) return [];
  return selectedImage.value.tags.map((tag) => ({
    label: tag.split(":")[1] || "latest",
    value: tag.split(":")[1] || "latest",
  }));
});

const volumeOptions = computed(() =>
  volumeStore.volumes.map((v) => ({ value: v.name, label: v.name }))
);

function filterVolume(input: string, option: any) {
  return String(option.value).toLowerCase().includes(input.toLowerCase());
}

function customRow(record: ImageItem) {
  return {
    onClick: () => selectImage(record),
  };
}

function rowClassName(record: ImageItem) {
  return record.id === selectedImage.value?.id ? "row-selected" : "";
}

async function selectImage(record: ImageItem) {
  selectedImage.value = record;
  try {
    const detail = await imageStore.fetch(record.id);
    selectedImage.value = detail;
    const firstTag = detail.tags[0] || "";
    form.image = firstTag.split(":")[0] || shortId(detail.id);
    form.tag = firstTag.split(":")[1] || "latest";
    form.command = detail.command || "";
    form.tty = detail.tty ?? false;
    form.interactive = detail.interactive ?? false;
    form.ports = (detail.ports || []).map(({ port, protocol }) => ({
      port,
      protocol,
      listen_ip: "0.0.0.0",
      listen_port: port,
    }));
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function appendPort() {
  form.ports.push({ port: null, protocol: "tcp", listen_ip: "0.0.0.0", listen_port: null });
}

function appendVolume() {
  form.volumes.push({ path: "", mode: "rw", bind: "" });
}

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    step.value = 0;
    keyword.value = "";
    run.value = true;
    selectedImage.value = null;
    Object.assign(form, {
      name: "",
      image: "",
      tag: "",
      command: "",
      tty: false,
      interactive: false,
      privileged: false,
      ports: [],
      volumes: [],
    });
    imageStore.fetchAll().catch((e) => message.error(errorMessage(e)));
    volumeStore.fetchAll().catch(() => {});
  }
);

async function handleCreate() {
  creating.value = true;
  try {
    const ports = form.ports
      .filter((p) => p.port && p.listen_port)
      .map((p) => ({
        port: p.port as number,
        protocol: p.protocol,
        listen_ip: p.listen_ip,
        listen_port: p.listen_port as number,
      }));
    const volumes = form.volumes.filter((v) => v.path && v.bind);
    await containerStore.create(
      {
        image: form.tag ? `${form.image}:${form.tag}` : form.image,
        command: form.command,
        name: form.name || null,
        tty: form.tty,
        interactive: form.interactive,
        privileged: form.privileged,
        ports,
        volumes,
      },
      run.value
    );
    emit("update:open", false);
    emit("created");
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
}
</script>

<style scoped>
:deep(.row-selected) > td {
  background-color: rgba(22, 119, 255, 0.12) !important;
}

:deep(.ant-table-row) {
  cursor: pointer;
}
</style>
