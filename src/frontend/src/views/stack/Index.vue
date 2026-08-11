<template>
  <div>
    <div class="toolbar">
      <div class="toolbar-left">
        <a-input
          v-model:value="keyword"
          :placeholder="t('searchPlaceholder')"
          style="width: 256px"
          allow-clear
        />
        <a-alert
          v-if="store.meta && !store.meta.cli_available"
          type="warning"
          show-icon
          :message="t('stack.cliUnavailable')"
          style="padding: 2px 12px"
        />
      </div>
      <div class="toolbar-right">
        <a-button @click="refresh">
          <ReloadOutlined />
        </a-button>
        <a-tooltip :title="cliAvailable ? '' : t('stack.cliUnavailable')">
          <a-button type="primary" :disabled="!cliAvailable" @click="createOpen = true">
            {{ t("stack.create") }}
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <a-table
      :data-source="tableData"
      :columns="columns"
      :loading="store.loading"
      :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }"
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
        <template v-else-if="column.key === 'source'">
          {{ sourceText(record) }}
        </template>
        <template v-else-if="column.key === 'working_dir'">
          <span class="mono">{{ record.working_dir || t("none") }}</span>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4" wrap>
            <a-button type="link" size="small" @click="openLogs(record)">
              {{ t("stack.logs") }}
            </a-button>
            <a-tooltip :title="fileActionDisabled(record) ? disabledReason(record) : ''">
              <span>
                <a-button
                  type="link"
                  size="small"
                  :disabled="fileActionDisabled(record)"
                  @click="openEditor(record)"
                >
                  {{ t("stack.editFile") }}
                </a-button>
              </span>
            </a-tooltip>
            <a-tooltip :title="fileActionDisabled(record) ? disabledReason(record) : ''">
              <span>
                <a-button
                  type="link"
                  size="small"
                  :disabled="fileActionDisabled(record)"
                  @click="triggerTask(record, 'up')"
                >
                  {{ t("stack.up") }}
                </a-button>
              </span>
            </a-tooltip>
            <a-dropdown>
              <a-button type="link" size="small">
                {{ t("more") }}
                <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu @click="(info: any) => handleAction(record, String(info.key))">
                  <a-menu-item key="start" :disabled="!cliAvailable">
                    {{ t("stack.start") }}
                  </a-menu-item>
                  <a-menu-item key="stop" :disabled="!cliAvailable">
                    {{ t("stack.stop") }}
                  </a-menu-item>
                  <a-menu-item key="restart" :disabled="!cliAvailable">
                    {{ t("stack.restart") }}
                  </a-menu-item>
                  <a-menu-item key="pull" :disabled="fileActionDisabled(record)">
                    {{ t("stack.pull") }}
                  </a-menu-item>
                  <a-menu-item v-if="!record.registered" key="import">
                    {{ t("stack.import") }}
                  </a-menu-item>
                  <a-menu-item v-else key="unregister">
                    {{ t("stack.unregister") }}
                  </a-menu-item>
                  <a-menu-item key="down" :disabled="!cliAvailable" danger>
                    {{ t("stack.down") }}
                  </a-menu-item>
                  <a-menu-item key="destroy" :disabled="!record.registered || !cliAvailable" danger>
                    {{ t("stack.destroy") }}
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </template>
    </a-table>

      <a-modal
      :open="destroyOpen"
      :title="t('stack.destroy')"
      :ok-text="t('ok')"
      :cancel-text="t('cancel')"
      :ok-button-props="{ danger: true, loading: destroyStarting }"
      @ok="confirmDestroy"
      @cancel="destroyOpen = false"
    >
      <p>{{ t("stack.destroyConfirm", { name: activeName }) }}</p>
      <a-checkbox v-model:checked="destroyRemoveVolumes">{{ t("stack.removeVolumes") }}</a-checkbox>
      <br />
      <a-checkbox v-if="destroyCanDeleteFiles" v-model:checked="destroyDeleteFiles">
        {{ t("stack.deleteFiles") }}
      </a-checkbox>
    </a-modal>

    <a-modal
      :open="downOpen"
      :title="t('stack.down')"
      :ok-text="t('ok')"
      :cancel-text="t('cancel')"
      :ok-button-props="{ danger: true, loading: downStarting }"
      @ok="confirmDown"
      @cancel="downOpen = false"
    >
      <p>{{ t("stack.downConfirm", { name: activeName }) }}</p>
      <a-checkbox v-model:checked="downRemoveVolumes">{{ t("stack.removeVolumes") }}</a-checkbox>
    </a-modal>

    <CreateDrawer v-model:open="createOpen" @created="onCreated" />
    <ProgressDrawer
      v-model:open="progressOpen"
      :task-id="progressTaskId"
      :stack="progressStack"
      :kind="progressKind"
    />
    <FileEditorDrawer v-model:open="editorOpen" :stack-name="activeName" />
    <LogsDrawer v-model:open="logsOpen" :stack-name="activeName" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { message, Modal } from "ant-design-vue";
import { DownOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { useStackStore, errorMessage, type StackItem } from "@/stores";
import CreateDrawer from "@/components/stack/CreateDrawer.vue";
import ProgressDrawer from "@/components/stack/ProgressDrawer.vue";
import FileEditorDrawer from "@/components/stack/FileEditorDrawer.vue";
import LogsDrawer from "@/components/stack/LogsDrawer.vue";

const { t, te } = useI18n();
const store = useStackStore();

const keyword = ref("");

const createOpen = ref(false);
const progressOpen = ref(false);
const editorOpen = ref(false);
const logsOpen = ref(false);
const downOpen = ref(false);
const downRemoveVolumes = ref(false);
const downStarting = ref(false);
const destroyOpen = ref(false);
const destroyRemoveVolumes = ref(false);
const destroyDeleteFiles = ref(true);
const destroyCanDeleteFiles = ref(false);
const destroyStarting = ref(false);
const activeName = ref("");

const progressTaskId = ref("");
const progressStack = ref("");
const progressKind = ref("");

const cliAvailable = computed(() => store.meta?.cli_available ?? false);

const columns = computed(() => [
  { title: t("name"), key: "name", dataIndex: "name", width: 180 },
  { title: t("status"), key: "status", dataIndex: "status", width: 110 },
  { title: t("stack.field.containers"), key: "containers", width: 90 },
  { title: t("stack.field.source"), key: "source", dataIndex: "source", width: 110 },
  { title: t("stack.field.workingDir"), key: "working_dir", dataIndex: "working_dir" },
  { title: t("actions"), key: "actions", width: 320, fixed: "right" as const },
]);

const tableData = computed(() => {
  let items = store.stacks;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) =>
        item.name.toLowerCase().includes(kw) || item.working_dir.toLowerCase().includes(kw)
    );
  }
  return items;
});

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

function sourceText(record: StackItem): string {
  const key = `stack.source.${record.source}`;
  if (te(key)) return t(key);
  return record.registered ? t("stack.source.registered") : t("stack.source.discovered");
}

function fileActionDisabled(record: StackItem): boolean {
  return !cliAvailable.value || !record.file_accessible;
}

function disabledReason(record: StackItem): string {
  if (!cliAvailable.value) return t("stack.cliUnavailable");
  if (!record.file_accessible) return t("stack.fileInaccessible");
  return "";
}

async function runWithError(fn: () => Promise<unknown>) {
  try {
    await fn();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function refresh() {
  runWithError(async () => {
    await store.fetchAll();
    await store.fetchMeta();
  });
}

function openProgress(taskId: string, stack: string, kind: string) {
  progressTaskId.value = taskId;
  progressStack.value = stack;
  progressKind.value = kind;
  progressOpen.value = true;
}

async function triggerTask(record: StackItem, kind: "up" | "pull") {
  try {
    const created =
      kind === "up" ? await store.up(record.name) : await store.pull(record.name);
    openProgress(created.task_id, record.name, kind);
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

function onCreated(payload: { taskId: string; stack: string }) {
  openProgress(payload.taskId, payload.stack, "create");
}

function openLogs(record: StackItem) {
  activeName.value = record.name;
  logsOpen.value = true;
}

function openEditor(record: StackItem) {
  activeName.value = record.name;
  editorOpen.value = true;
}

function confirmDown() {
  downStarting.value = true;
  store
    .down(activeName.value, downRemoveVolumes.value)
    .then((created) => {
      downOpen.value = false;
      openProgress(created.task_id, activeName.value, "down");
    })
    .catch((e) => message.error(errorMessage(e)))
    .finally(() => {
      downStarting.value = false;
    });
}

function confirmDestroy() {
  destroyStarting.value = true;
  store
    .destroy(activeName.value, destroyRemoveVolumes.value, destroyDeleteFiles.value)
    .then((created) => {
      destroyOpen.value = false;
      openProgress(created.task_id, activeName.value, "destroy");
    })
    .catch((e) => message.error(errorMessage(e)))
    .finally(() => {
      destroyStarting.value = false;
    });
}

function confirmUnregister(record: StackItem) {
  Modal.confirm({
    title: t("stack.unregisterConfirm", { name: record.name }),
    okText: t("ok"),
    cancelText: t("cancel"),
    onOk: () => runWithError(() => store.unregister(record.name)),
  });
}

function confirmImport(record: StackItem) {
  Modal.confirm({
    title: t("stack.importConfirm", { name: record.name }),
    okText: t("ok"),
    cancelText: t("cancel"),
    onOk: () => runWithError(() => store.importStack(record.name)),
  });
}

async function handleAction(record: StackItem, cmd: string) {
  activeName.value = record.name;
  switch (cmd) {
    case "start":
      await runWithError(() => store.start(record.name));
      break;
    case "stop":
      await runWithError(() => store.stop(record.name));
      break;
    case "restart":
      await runWithError(() => store.restart(record.name));
      break;
    case "pull":
      await triggerTask(record, "pull");
      break;
    case "import":
      confirmImport(record);
      break;
    case "unregister":
      confirmUnregister(record);
      break;
    case "down":
      downRemoveVolumes.value = false;
      downOpen.value = true;
      break;
    case "destroy": {
      const canDelete = record.source === "created";
      destroyRemoveVolumes.value = false;
      destroyDeleteFiles.value = canDelete;
      destroyCanDeleteFiles.value = canDelete;
      destroyOpen.value = true;
      break;
    }
  }
}

onMounted(() => {
  store.fetchAll().catch((e) => message.error(errorMessage(e)));
  store.fetchMeta().catch(() => {});
});
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mono {
  font-family: monospace;
}
</style>
