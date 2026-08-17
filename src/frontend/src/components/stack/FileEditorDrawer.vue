<template>
  <a-drawer
    :open="open"
    :title="`${t('stack.editFile')}: ${stackName}`"
    width="860"
    root-class-name="file-editor-drawer"
    :body-style="{ display: 'flex', flexDirection: 'column' }"
    @close="handleClose"
  >
    <a-tabs v-model:activeKey="tab" @change="handleTabChange">
      <a-tab-pane key="compose" :tab="t('stack.tabCompose')" />
      <a-tab-pane key="env" :tab="t('stack.tabEnv')" />
    </a-tabs>
    <a-spin :spinning="loading" wrapper-class-name="editor-spin">
      <div class="editor-panel">
        <div class="path mono">{{ current.path }}</div>
        <a-textarea
          v-model:value="current.content"
          class="compose-editor"
          :placeholder="tab === 'env' ? envPlaceholder : ''"
        />
        <a-alert
          v-if="current.error"
          type="error"
          show-icon
          style="margin-top: 12px"
          :message="t('stack.fileInvalid')"
          :description="current.error"
        />
      </div>
    </a-spin>
    <template #footer>
      <div class="footer">
        <span class="hint">{{ t("stack.editHint") }}</span>
        <a-button type="primary" :loading="saving" :disabled="loading" @click="handleSave">
          {{ t("save") }}
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";

type FileKind = "compose" | "env";

interface FileState {
  path: string;
  content: string;
  error: string;
  loaded: boolean;
}

const props = defineProps<{ open: boolean; stackName: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const store = useStackStore();

const loading = ref(false);
const saving = ref(false);
const tab = ref<FileKind>("compose");

const files = reactive<Record<FileKind, FileState>>({
  compose: { path: "", content: "", error: "", loaded: false },
  env: { path: "", content: "", error: "", loaded: false },
});

const current = computed(() => files[tab.value]);

const envPlaceholder = "KEY=value\n# one per line";

async function load(kind: FileKind) {
  loading.value = true;
  try {
    const file = kind === "compose"
      ? await store.readFile(props.stackName)
      : await store.readEnv(props.stackName);
    Object.assign(files[kind], {
      path: file.path,
      content: file.content,
      error: "",
      loaded: true,
    });
  } catch (e: any) {
    message.error(errorMessage(e));
    emit("update:open", false);
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.open,
  (open) => {
    if (!open || !props.stackName) return;
    tab.value = "compose";
    files.compose = { path: "", content: "", error: "", loaded: false };
    files.env = { path: "", content: "", error: "", loaded: false };
    load("compose");
  }
);

function handleTabChange(key: string | number) {
  const kind = key as FileKind;
  if (!files[kind].loaded) load(kind);
}

async function handleSave() {
  saving.value = true;
  current.value.error = "";
  try {
    const result = tab.value === "compose"
      ? await store.writeFile(props.stackName, current.value.content)
      : await store.writeEnv(props.stackName, current.value.content);
    if (result.valid) {
      message.success(t("stack.fileSaved"));
    } else {
      current.value.error = result.error || "";
    }
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
}

function handleClose() {
  files.compose.error = "";
  files.env.error = "";
  emit("update:open", false);
}
</script>

<style scoped>
.compose-editor {
  font-family: monospace;
  font-size: 12px;
}

.mono {
  font-family: monospace;
}

.path {
  margin-bottom: 8px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

body.dockore-theme-dark .path {
  color: rgba(255, 255, 255, 0.45);
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

body.dockore-theme-dark .hint {
  color: rgba(255, 255, 255, 0.45);
}
</style>

<style>
.file-editor-drawer .editor-spin {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.file-editor-drawer .editor-spin > .ant-spin-container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.file-editor-drawer .editor-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.file-editor-drawer .compose-editor {
  flex: 1;
  min-height: 0;
  resize: none;
}
</style>
