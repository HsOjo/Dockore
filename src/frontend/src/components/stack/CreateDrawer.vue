<template>
  <a-drawer
    :open="open"
    :title="t('stack.create')"
    width="860"
    @close="emit('update:open', false)"
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
          {{ t("stack.directoryHint", { path: `${form.directory}/${form.name}/compose.yml` }) }}
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
      <a-form-item :label="t('stack.field.content')" required>
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
    </a-form>
    <template #footer>
      <div class="footer">
        <a-button @click="emit('update:open', false)">{{ t("cancel") }}</a-button>
        <a-button
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
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";
import { getLastStackDir, isTauri, pickDirectory, saveLastStackDir } from "@/platform";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  created: [{ taskId: string; stack: string }];
}>();

const { t } = useI18n();
const store = useStackStore();

const creating = ref(false);
const tab = ref<"compose" | "env">("compose");

const form = reactive({
  name: "",
  directory: "",
  content: "",
  env: "",
});

const NAME_RE = /^[a-z0-9][a-z0-9_-]*$/;

const validName = computed(() => NAME_RE.test(form.name));
const containerMode = computed(() => store.meta?.container_mode ?? false);
const stacksDir = computed(() => store.meta?.stacks_dir || "");
const canPickDirectory = computed(() => !containerMode.value && isTauri());

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
    tab.value = "compose";
    if (!store.meta) {
      store.fetchMeta().catch((e) => message.error(errorMessage(e)));
    }
  }
);

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
