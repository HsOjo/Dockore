<template>
  <a-modal
    :open="open"
    :title="t('container.diff')"
    width="860px"
    :footer="null"
    @cancel="emit('update:open', false)"
  >
    <a-input
      v-model:value="keyword"
      :placeholder="t('searchPlaceholder')"
      style="width: 256px; margin-bottom: 12px"
      allow-clear
    />
    <a-spin :spinning="loading">
      <a-empty v-if="empty" :description="t('container.diffEmpty')" style="padding: 64px 0" />
      <a-collapse v-else :default-active-key="['add', 'change', 'delete']">
        <a-collapse-panel
          v-for="group in groups"
          :key="group.key"
          :header="`${group.label} (${group.files.length})`"
        >
          <a-list size="small" :data-source="group.files" :pagination="{ pageSize: 10, size: 'small', hideOnSinglePage: true }">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-tag :color="group.color">{{ group.label }}</a-tag>
                <span class="file-path">{{ item }}</span>
              </a-list-item>
            </template>
          </a-list>
        </a-collapse-panel>
      </a-collapse>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useContainerStore, errorMessage, type ContainerDiff } from "@/stores";

const props = defineProps<{ open: boolean; containerId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const containerStore = useContainerStore();

const keyword = ref("");
const loading = ref(false);
const diff = ref<ContainerDiff | null>(null);

const groups = computed(() => {
  const kw = keyword.value.toLowerCase();
  const filter = (files: string[] | undefined) =>
    (files || []).filter((f) => !kw || f.toLowerCase().includes(kw));
  return [
    {
      key: "add",
      label: t("container.diffGroups.add"),
      color: "green",
      files: filter(diff.value?.add),
    },
    {
      key: "change",
      label: t("container.diffGroups.change"),
      color: "orange",
      files: filter(diff.value?.change),
    },
    {
      key: "delete",
      label: t("container.diffGroups.delete"),
      color: "red",
      files: filter(diff.value?.delete),
    },
    {
      key: "other",
      label: t("container.diffGroups.other"),
      color: "default",
      files: filter(diff.value?.other),
    },
  ].filter((g) => g.files.length > 0);
});

const empty = computed(() => !loading.value && groups.value.length === 0);

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    keyword.value = "";
    diff.value = null;
    loading.value = true;
    try {
      diff.value = await containerStore.diff(props.containerId);
    } catch (e: any) {
      message.error(errorMessage(e));
    } finally {
      loading.value = false;
    }
  }
);
</script>

<style scoped>
.file-path {
  font-family: monospace;
  font-size: 12px;
  word-break: break-all;
}
</style>
