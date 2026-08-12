<template>
  <a-drawer
    :open="open"
    :title="t('stack.register')"
    width="640"
    @close="handleClose"
  >
    <a-form layout="vertical">
      <a-form-item v-if="containerMode" :label="t('stack.field.directory')">
        <a-alert
          type="info"
          show-icon
          :message="t('stack.registerContainerHint', { dir: stacksDir })"
        />
      </a-form-item>
      <a-form-item :label="t('stack.field.directory')" required>
        <a-input-group compact class="directory-row">
          <a-input
            v-model:value="path"
            :readonly="canPickDirectory"
            :placeholder="
              canPickDirectory
                ? t('stack.directoryPickPlaceholder')
                : t('stack.registerPathPlaceholder')
            "
            class="directory-input"
            @blur="prefillName"
          />
          <a-button v-if="canPickDirectory" @click="browseDirectory">
            {{ t("stack.browse") }}
          </a-button>
        </a-input-group>
        <div class="hint">{{ t("stack.registerPathHint") }}</div>
      </a-form-item>
      <a-form-item
        :label="t('stack.field.name')"
        required
        :validate-status="nameStatus"
        :help="nameHelp"
      >
        <a-input v-model:value="name" :placeholder="t('stack.namePlaceholder')" />
      </a-form-item>
    </a-form>
    <template #footer>
      <div class="footer">
        <a-button @click="handleClose">{{ t("cancel") }}</a-button>
        <a-button
          type="primary"
          :loading="registering"
          :disabled="!canSubmit"
          @click="handleRegister"
        >
          {{ t("ok") }}
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useStackStore, errorMessage } from "@/stores";
import { isTauri, pickDirectory, saveLastStackDir } from "@/platform";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  "update:open": [boolean];
  registered: [];
}>();

const { t } = useI18n();
const store = useStackStore();

const path = ref("");
const name = ref("");
const nameTouched = ref(false);
const registering = ref(false);

const NAME_RE = /^[a-z0-9][a-z0-9_-]*$/;

const containerMode = computed(() => store.meta?.container_mode ?? false);
const stacksDir = computed(() => store.meta?.stacks_dir || "");
const canPickDirectory = computed(() => !containerMode.value && isTauri());
const validName = computed(() => NAME_RE.test(name.value));

const nameStatus = computed(() => {
  if (!name.value) return "";
  return validName.value ? "" : "error";
});

const nameHelp = computed(() => {
  if (!name.value || validName.value) return "";
  return t("stack.nameInvalid");
});

const canSubmit = computed(
  () => !!path.value.trim() && validName.value && !registering.value
);

watch(name, () => {
  nameTouched.value = true;
});

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    path.value = "";
    name.value = "";
    nameTouched.value = false;
    if (!store.meta) {
      await store.fetchMeta().catch((e) => message.error(errorMessage(e)));
    }
  }
);

function prefillName() {
  const dir = path.value.trim().replace(/\/+$/, "");
  if (!dir || nameTouched.value) return;
  const base = dir.split("/").pop() || "";
  name.value = NAME_RE.test(base) ? base : "";
}

async function browseDirectory() {
  const dir = await pickDirectory(t("stack.field.directory"));
  if (dir) {
    path.value = dir;
    prefillName();
  }
}

function handleClose() {
  emit("update:open", false);
}

async function handleRegister() {
  registering.value = true;
  try {
    await store.register({ name: name.value, path: path.value.trim() });
    const dir = path.value.trim().replace(/\/+$/, "");
    const parent = dir.split("/").slice(0, -1).join("/");
    if (parent) saveLastStackDir(parent);
    message.success(t("stack.registerSuccess", { name: name.value }));
    emit("update:open", false);
    emit("registered");
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    registering.value = false;
  }
}
</script>

<style scoped>
.directory-row {
  display: flex;
}

.directory-row .directory-input {
  flex: 1;
}

.hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
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
