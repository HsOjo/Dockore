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
        <a-switch :checked="store.showAll" @change="handleShowAll" />
        <span>{{ t("container.showAll") }}</span>
      </div>
      <div class="toolbar-right">
        <template v-if="selectedRowKeys.length">
          <a-button @click="batchAction('start')">{{ t("container.start") }}</a-button>
          <a-button @click="batchAction('stop')">{{ t("container.stop") }}</a-button>
          <a-button @click="batchAction('restart')">{{ t("container.restart") }}</a-button>
          <a-popconfirm
            :title="t('container.confirmBatchDelete', { n: selectedRowKeys.length })"
            :ok-text="t('ok')"
            :cancel-text="t('cancel')"
            @confirm="batchDelete"
          >
            <a-button danger>{{ t("delete") }}</a-button>
          </a-popconfirm>
        </template>
        <a-button @click="store.fetchAll()">
          <ReloadOutlined />
        </a-button>
        <a-button type="primary" @click="createOpen = true">{{ t("container.create") }}</a-button>
      </div>
    </div>

    <DataTable
      :data-source="tableData"
      :columns="columns"
      :loading="store.loading"
      :row-selection="{ selectedRowKeys, onChange: (keys: (string | number)[]) => (selectedRowKeys = keys.map(String)) }"
      :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }"
      row-key="id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'id'">
          <span class="mono">{{ shortId(record.id) }}</span>
        </template>
        <template v-else-if="column.key === 'image'">
          <router-link :to="`/images/${encodeURIComponent(record.image.id)}`">
            <EllipsisText :text="imageDisplayName(record.image)" />
          </router-link>
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
        <template v-else-if="column.key === 'actions'">
          <a-space :size="4" wrap>
            <router-link :to="`/containers/${record.id}`">{{ t("detail") }}</router-link>
            <a-button type="link" size="small" @click="openLogs(record)">
              {{ t("container.logs") }}
            </a-button>
            <a-button
              type="link"
              size="small"
              :disabled="record.status !== 'running'"
              @click="goTerminal(record.id)"
            >
              {{ t("container.terminal") }}
            </a-button>
            <a-dropdown>
              <a-button type="link" size="small">
                {{ t("more") }}
                <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu @click="(info: any) => handleAction(record, String(info.key))">
                  <a-menu-item key="rename">{{ t("container.rename") }}</a-menu-item>
                  <a-menu-item key="diff">{{ t("container.diff") }}</a-menu-item>
                  <a-menu-item key="commit">{{ t("container.commit") }}</a-menu-item>
                  <a-menu-item key="exec" :disabled="record.status !== 'running'">
                    {{ t("container.exec") }}
                  </a-menu-item>
                  <a-menu-item key="start" :disabled="record.status === 'running'">
                    {{ t("container.start") }}
                  </a-menu-item>
                  <a-menu-item key="stop" :disabled="record.status !== 'running'">
                    {{ t("container.stop") }}
                  </a-menu-item>
                  <a-menu-item key="restart">{{ t("container.restart") }}</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
            <a-popconfirm
              :title="t('container.confirmDelete', { name: record.name })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="handleDelete([record.id])"
            >
              <a-button type="link" size="small" danger>{{ t("delete") }}</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </DataTable>

    <CreateDrawer v-model:open="createOpen" />
    <LogsDrawer v-model:open="logsOpen" :container-id="activeId" />
    <DiffModal v-model:open="diffOpen" :container-id="activeId" />
    <CommitModal v-model:open="commitOpen" :container-id="activeId" />
    <RenameModal
      v-model:open="renameOpen"
      :container-id="activeId"
      :container-name="activeName"
    />
    <ExecModal v-model:open="execOpen" :container-id="activeId" :container-name="activeName" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { DownOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { relativeTime } from "@dockore/shared";
import { useContainerStore, errorMessage, type ContainerItem } from "@/stores";
import { containerStatusBadge, shortId, imageDisplayName } from "@/utils/text";
import CreateDrawer from "@/components/container/CreateDrawer.vue";
import LogsDrawer from "@/components/container/LogsDrawer.vue";
import DiffModal from "@/components/container/DiffModal.vue";
import CommitModal from "@/components/container/CommitModal.vue";
import RenameModal from "@/components/container/RenameModal.vue";
import ExecModal from "@/components/container/ExecModal.vue";
import DataTable from "@/components/common/DataTable.vue";
import EllipsisText from "@/components/common/EllipsisText.vue";

const { t, te, locale } = useI18n();
const router = useRouter();
const store = useContainerStore();

const keyword = ref("");
const selectedRowKeys = ref<string[]>([]);

const createOpen = ref(false);
const logsOpen = ref(false);
const diffOpen = ref(false);
const commitOpen = ref(false);
const renameOpen = ref(false);
const execOpen = ref(false);
const activeId = ref("");
const activeName = ref("");

const columns = computed(() => [
  { title: "ID", key: "id", dataIndex: "id", width: 120 },
  { title: t("name"), key: "name", dataIndex: "name", width: 200, ellipsis: true },
  {
    title: t("container.field.image"),
    key: "image",
    dataIndex: "image",
    width: 280,
    ellipsis: { showTitle: false },
  },
  { title: t("createTime"), key: "create_time", dataIndex: "create_time", width: 160 },
  { title: t("status"), key: "status", dataIndex: "status", width: 120 },
  { title: t("actions"), key: "actions", width: 380, fixed: "right" as const },
]);

const tableData = computed(() => {
  let items = store.containers;
  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    items = items.filter(
      (item) =>
        item.name.toLowerCase().includes(kw) ||
        item.id.toLowerCase().includes(kw) ||
        imageDisplayName(item.image).toLowerCase().includes(kw)
    );
  }
  return items;
});

function statusText(status: string): string {
  const key = `container.status.${status}`;
  return te(key) ? t(key) : status;
}

function handleShowAll(checked: string | number | boolean) {
  store.showAll = Boolean(checked);
  store.fetchAll().catch((e) => message.error(errorMessage(e)));
}

function activate(record: ContainerItem) {
  activeId.value = record.id;
  activeName.value = record.name;
}

function openLogs(record: ContainerItem) {
  activate(record);
  logsOpen.value = true;
}

function goTerminal(id: string) {
  router.push(`/containers/${id}/terminal`);
}

async function runWithError(fn: () => Promise<unknown>) {
  try {
    await fn();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function batchAction(action: "start" | "stop" | "restart") {
  for (const id of selectedRowKeys.value) {
    await runWithError(async () => {
      if (action === "start") await store.start(id);
      else if (action === "stop") await store.stop(id, 5);
      else await store.restart(id, 5);
    });
  }
  selectedRowKeys.value = [];
  await runWithError(() => store.fetchAll());
}

async function batchDelete() {
  const ids = [...selectedRowKeys.value];
  selectedRowKeys.value = [];
  await runWithError(() => store.remove(ids));
}

async function handleDelete(ids: string[]) {
  await runWithError(() => store.remove(ids));
}

async function handleAction(record: ContainerItem, cmd: string) {
  activate(record);
  switch (cmd) {
    case "rename":
      renameOpen.value = true;
      break;
    case "diff":
      diffOpen.value = true;
      break;
    case "commit":
      commitOpen.value = true;
      break;
    case "exec":
      execOpen.value = true;
      break;
    case "start":
      await runWithError(() => store.start(record.id));
      break;
    case "stop":
      await runWithError(() => store.stop(record.id, 5));
      break;
    case "restart":
      await runWithError(() => store.restart(record.id, 5));
      break;
  }
}

onMounted(() => {
  store.fetchAll().catch((e) => message.error(errorMessage(e)));
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
