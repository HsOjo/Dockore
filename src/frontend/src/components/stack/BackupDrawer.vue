<template>
  <a-drawer
    :open="open"
    :title="t('stack.backupsTitle', { name: stackName })"
    width="860"
    @close="emit('update:open', false)"
  >
    <div class="drawer-toolbar">
      <a-popconfirm
        :title="t('stack.backupConfirm', { name: stackName })"
        :ok-text="t('ok')"
        :cancel-text="t('cancel')"
        @confirm="createBackup"
      >
        <a-button type="primary" :disabled="backupDisabled" :loading="starting">
          {{ t("stack.backup") }}
        </a-button>
      </a-popconfirm>
      <a-button @click="load">
        <ReloadOutlined />
      </a-button>
    </div>
    <a-table
      :data-source="backups"
      :columns="columns"
      :loading="loading"
      :pagination="false"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'size'">
          {{ formatBytes(record.size) }}
        </template>
        <template v-else-if="column.key === 'contents'">
          <div v-if="record.volumes.length + record.binds.length" class="contents">
            <div v-for="v in record.volumes" :key="`v-${v.name}`" class="content-item">
              <a-tag color="blue">{{ t("stack.backupsVolume") }}</a-tag>
              <EllipsisText :text="v.name" mono />
            </div>
            <div v-for="b in record.binds" :key="`b-${b.source}`" class="content-item">
              <a-tag>{{ t("stack.backupsBind") }}</a-tag>
              <EllipsisText :text="b.source" mono />
            </div>
          </div>
          <span v-else>{{ t("none") }}</span>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4">
            <a-button type="link" size="small" @click="download(record)">
              {{ t("stack.backupsDownload") }}
            </a-button>
            <a-popconfirm
              :title="t('stack.backupsDeleteConfirm', { id: record.id })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="remove(record)"
            >
              <a-button type="link" size="small" danger>
                {{ t("delete") }}
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { formatBytes, formatTime } from "@dockore/shared";
import { useStackStore, errorMessage, type BackupItem } from "@/stores";
import EllipsisText from "@/components/common/EllipsisText.vue";

const props = defineProps<{
  open: boolean;
  stackName: string;
  backupDisabled?: boolean;
}>();
const emit = defineEmits<{ "update:open": [boolean]; started: [string] }>();

const { t } = useI18n();
const store = useStackStore();

const backups = ref<BackupItem[]>([]);
const loading = ref(false);
const starting = ref(false);

const columns = computed(() => [
  { title: t("stack.backupsTime"), key: "created_at", dataIndex: "created_at", width: 180 },
  { title: t("stack.backupsSize"), key: "size", dataIndex: "size", width: 100 },
  { title: t("stack.backupsContentsTitle"), key: "contents" },
  { title: t("actions"), key: "actions", width: 160 },
]);

async function load() {
  if (!props.stackName) return;
  loading.value = true;
  try {
    backups.value = await store.listBackups(props.stackName);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}

async function createBackup() {
  starting.value = true;
  try {
    const created = await store.backup(props.stackName);
    emit("started", created.task_id);
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    starting.value = false;
  }
}

async function download(record: BackupItem) {
  try {
    await store.downloadBackup(props.stackName, record.id);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function remove(record: BackupItem) {
  try {
    await store.deleteBackup(props.stackName, record.id);
    await load();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

watch(
  () => [props.open, props.stackName],
  ([open]) => {
    if (open) load();
  }
);

defineExpose({ load });
</script>

<style scoped>
.drawer-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.contents {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.content-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
</style>
