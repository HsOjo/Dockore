<template>
  <a-drawer
    :open="open"
    :title="t('stack.create')"
    width="860"
    @close="handleClose"
  >
    <a-form layout="vertical">
      <a-form-item v-if="containerMode" :label="t('stack.field.directory')">
        <a-alert type="info" show-icon :message="t('stack.containerModeHint', { dir: stacksDir })" />
      </a-form-item>
      <a-form-item v-else :label="t('stack.field.directory')" required>
        <a-input-group compact class="directory-row">
          <a-input
            v-model:value="form.directory"
            :readonly="canPickDirectory"
            :placeholder="canPickDirectory ? t('stack.directoryPickPlaceholder') : '/opt/stacks'"
            class="directory-input"
            @blur="persistDirectory"
          />
          <a-button v-if="canPickDirectory" @click="browseDirectory">
            {{ t("stack.browse") }}
          </a-button>
        </a-input-group>
        <div v-if="form.directory && validName" class="hint">
          {{ directoryHint }}
        </div>
      </a-form-item>
      <a-form-item
        :label="t('stack.field.name')"
        required
        :validate-status="nameStatus"
        :help="nameHelp"
      >
        <a-input v-model:value="form.name" :placeholder="t('stack.namePlaceholder')" />
      </a-form-item>
      <a-tabs v-model:activeKey="method">
        <a-tab-pane key="manual" :tab="t('stack.methodManual')" />
        <a-tab-pane key="git" :tab="t('stack.methodGit')" :disabled="!gitAvailable" />
      </a-tabs>
      <a-form-item v-if="method === 'manual'" :label="t('stack.field.content')" required>
        <a-tabs v-model:activeKey="tab">
          <a-tab-pane key="compose" :tab="t('stack.tabCompose')" />
          <a-tab-pane key="env" :tab="t('stack.tabEnv')" />
        </a-tabs>
        <a-textarea
          v-if="tab === 'compose'"
          v-model:value="form.content"
          class="compose-editor"
          :rows="16"
          :placeholder="composePlaceholder"
        />
        <a-textarea
          v-else
          v-model:value="form.env"
          class="compose-editor"
          :rows="16"
          :placeholder="envPlaceholder"
        />
      </a-form-item>
      <template v-else>
        <a-alert
          v-if="!gitAvailable"
          type="warning"
          show-icon
          :message="t('stack.gitUnavailable')"
        />
        <template v-if="gitStep === 'clone'">
          <a-form-item :label="t('stack.repoUrl')" required>
            <a-input
              v-model:value="gitForm.repoUrl"
              :placeholder="t('stack.repoUrlPlaceholder')"
            />
          </a-form-item>
          <a-form-item :label="t('stack.branch')">
            <a-input
              v-model:value="gitForm.branch"
              :placeholder="t('stack.branchPlaceholder')"
            />
          </a-form-item>
        </template>
        <template v-else-if="gitStep === 'select'">
          <a-form-item>
            <a-alert
              type="success"
              show-icon
              :message="t('stack.gitRepoCloned', { url: gitForm.repoUrl })"
            />
          </a-form-item>
          <a-form-item :label="t('stack.composeFile')" required>
            <a-select
              v-model:value="gitForm.composePath"
              :options="composeOptions"
              show-search
            />
          </a-form-item>
          <a-form-item :label="t('stack.envTemplate')">
            <a-select
              v-model:value="gitForm.envTemplatePath"
              :options="envTemplateOptions"
            />
          </a-form-item>
        </template>
        <a-form-item v-else :label="t('stack.field.content')" required>
          <a-tabs v-model:activeKey="tab">
            <a-tab-pane key="compose" :tab="t('stack.tabCompose')" />
            <a-tab-pane key="env" :tab="t('stack.tabEnv')" />
          </a-tabs>
          <a-textarea
            v-if="tab === 'compose'"
            v-model:value="editForm.content"
            class="compose-editor"
            :rows="16"
          />
          <a-textarea
            v-else
            v-model:value="editForm.env"
            class="compose-editor"
            :rows="16"
            :placeholder="envPlaceholder"
          />
        </a-form-item>
      </template>
    </a-form>
    <template #footer>
      <div class="footer">
        <a-button @click="handleClose">{{ t("cancel") }}</a-button>
        <template v-if="method === 'git'">
          <a-button
            v-if="gitStep === 'clone'"
            type="primary"
            :loading="cloning"
            :disabled="!canClone"
            @click="handleClone"
          >
            {{ t("stack.clone") }}
          </a-button>
          <template v-else-if="gitStep === 'select'">
            <a-button @click="handleBack">{{ t("back") }}</a-button>
            <a-button
              type="primary"
              :loading="loadingFiles"
              :disabled="!gitForm.composePath"
              @click="handleNext"
            >
              {{ t("next") }}
            </a-button>
          </template>
          <template v-else>
            <a-button :disabled="creating" @click="handleBack">{{ t("back") }}</a-button>
            <a-button
              type="primary"
              :loading="creating"
              :disabled="!canGitCreate"
              @click="handleGitCreate"
            >
              {{ t("ok") }}
            </a-button>
          </template>
        </template>
        <a-button
          v-else
          type="primary"
          :loading="creating"
          :disabled="!canSubmit"
          @click="handleCreate"
        >
          {{ t("ok") }}
        </a-button>
      </div>
    </template>
  </a-drawer>
  <ProgressDrawer
    v-model:open="cloneProgressOpen"
    :task-id="cloneTaskId"
    :stack="form.name"
    kind="clone"
    @finished="onCloneFinished"
  />
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";
import type { GitCloneResult } from "@/stores";
import { getLastStackDir, isTauri, pickDirectory, saveLastStackDir } from "@/platform";
import ProgressDrawer from "@/components/stack/ProgressDrawer.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  created: [{ taskId: string; stack: string }];
}>();

const { t } = useI18n();
const store = useStackStore();

const creating = ref(false);
const cloning = ref(false);
const loadingFiles = ref(false);
const tab = ref<"compose" | "env">("compose");
const method = ref<"manual" | "git">("manual");
const gitStep = ref<"clone" | "select" | "edit">("clone");
const cloned = ref(false);
const cloneResult = ref<GitCloneResult | null>(null);
const cloneProgressOpen = ref(false);
const cloneTaskId = ref("");

const form = reactive({
  name: "",
  directory: "",
  content: "",
  env: "",
});

const gitForm = reactive({
  repoUrl: "",
  branch: "",
  composePath: "",
  envTemplatePath: "",
});

const editForm = reactive({
  content: "",
  env: "",
});

const NAME_RE = /^[a-z0-9][a-z0-9_-]*$/;

const validName = computed(() => NAME_RE.test(form.name));
const containerMode = computed(() => store.meta?.container_mode ?? false);
const stacksDir = computed(() => store.meta?.stacks_dir || "");
const canPickDirectory = computed(() => !containerMode.value && isTauri());
const gitAvailable = computed(() => store.meta?.git_available ?? false);

const directoryHint = computed(() => {
  const path = `${form.directory}/${form.name}/`;
  return method.value === "git"
    ? t("stack.gitDirectoryHint", { path })
    : t("stack.directoryHint", { path: `${path}compose.yml` });
});

async function browseDirectory() {
  const dir = await pickDirectory(t("stack.field.directory"));
  if (dir) {
    form.directory = dir;
    saveLastStackDir(dir);
  }
}

function persistDirectory() {
  const dir = form.directory.trim();
  if (dir) saveLastStackDir(dir);
}

const nameStatus = computed(() => {
  if (!form.name) return "";
  return validName.value ? "" : "error";
});

const nameHelp = computed(() => {
  if (!form.name || validName.value) return "";
  return t("stack.nameInvalid");
});

const canSubmit = computed(() => {
  if (!validName.value || !form.content.trim()) return false;
  if (!containerMode.value && !form.directory.trim()) return false;
  return true;
});

const gitDirectory = computed(() =>
  containerMode.value ? null : form.directory.trim() || null
);

const canClone = computed(() => {
  if (!validName.value || !gitForm.repoUrl.trim()) return false;
  if (!containerMode.value && !form.directory.trim()) return false;
  return true;
});

const canGitCreate = computed(() => validName.value && !!editForm.content.trim());

const composeOptions = computed(() =>
  (cloneResult.value?.compose_files ?? []).map((f) => ({ value: f, label: f }))
);

const envTemplateOptions = computed(() => [
  { value: "", label: t("stack.envTemplateNone") },
  ...(cloneResult.value?.env_templates ?? []).map((f) => ({ value: f, label: f })),
]);

const composePlaceholder = `services:
  app:
    image: nginx:latest
    ports:
      - "8080:80"`;

const envPlaceholder = "KEY=value\n# one per line";

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    Object.assign(form, { name: "", directory: getLastStackDir(), content: "", env: "" });
    Object.assign(gitForm, { repoUrl: "", branch: "", composePath: "", envTemplatePath: "" });
    Object.assign(editForm, { content: "", env: "" });
    tab.value = "compose";
    method.value = "manual";
    gitStep.value = "clone";
    cloned.value = false;
    cloneResult.value = null;
    cloneProgressOpen.value = false;
    cloneTaskId.value = "";
    if (!store.meta) {
      store.fetchMeta().catch((e) => message.error(errorMessage(e)));
    }
  }
);

watch(method, (m) => {
  if (m !== "git") cancelClone();
});

function cancelClone() {
  if (!cloned.value) return;
  cloned.value = false;
  store
    .gitCancel({ name: form.name, directory: gitDirectory.value })
    .catch(() => {});
  gitStep.value = "clone";
}

function handleClose() {
  cancelClone();
  emit("update:open", false);
}

async function handleClone() {
  cloning.value = true;
  try {
    const task = await store.gitClone({
      name: form.name,
      repo_url: gitForm.repoUrl.trim(),
      branch: gitForm.branch.trim() || null,
      directory: gitDirectory.value,
    });
    cloneTaskId.value = task.task_id;
    cloneProgressOpen.value = true;
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    cloning.value = false;
  }
}

async function onCloneFinished(status: string) {
  if (status !== "done") return;
  try {
    const result = await store.gitCandidates(form.name, gitDirectory.value);
    cloneResult.value = result;
    gitForm.composePath = result.compose_files[0] ?? "";
    gitForm.envTemplatePath = "";
    gitStep.value = "select";
    cloned.value = true;
    if (!containerMode.value) saveLastStackDir(form.directory.trim());
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

async function handleNext() {
  loadingFiles.value = true;
  try {
    const file = await store.gitReadFile(form.name, gitForm.composePath, gitDirectory.value);
    editForm.content = file.content;
    const dir = gitForm.composePath.split("/").slice(0, -1).join("/");
    const envPath = gitForm.envTemplatePath || (dir ? `${dir}/.env` : ".env");
    editForm.env = await store
      .gitReadFile(form.name, envPath, gitDirectory.value)
      .then((f) => f.content)
      .catch(() => "");
    tab.value = "compose";
    gitStep.value = "edit";
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loadingFiles.value = false;
  }
}

function handleBack() {
  if (gitStep.value === "edit") {
    gitStep.value = "select";
    return;
  }
  cancelClone();
}

async function handleGitCreate() {
  creating.value = true;
  try {
    const created = await store.gitCreate({
      name: form.name,
      compose_path: gitForm.composePath,
      env_template_path: gitForm.envTemplatePath || null,
      content: editForm.content,
      env: editForm.env,
      directory: gitDirectory.value,
    });
    cloned.value = false;
    emit("update:open", false);
    emit("created", { taskId: created.task_id, stack: form.name });
    store.fetchAll().catch(() => {});
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
}

async function handleCreate() {
  creating.value = true;
  try {
    const created = await store.create({
      name: form.name,
      content: form.content,
      directory: containerMode.value ? null : form.directory.trim(),
      env: form.env.trim() ? form.env : null,
    });
    if (!containerMode.value) saveLastStackDir(form.directory.trim());
    emit("update:open", false);
    emit("created", { taskId: created.task_id, stack: form.name });
    store.fetchAll().catch(() => {});
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
}
</script>

<style scoped>
.compose-editor {
  font-family: monospace;
  font-size: 12px;
}

.hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  font-family: monospace;
}

.directory-row {
  display: flex;
}

.directory-row .directory-input {
  flex: 1;
}

body.dockore-theme-dark .hint {
  color: rgba(255, 255, 255, 0.45);
}

.footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
