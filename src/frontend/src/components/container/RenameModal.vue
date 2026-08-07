<template>
  <a-modal
    :open="open"
    :title="`${t('container.rename')}：${containerName}`"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-input v-model:value="name" :placeholder="t('container.newName')" @press-enter="handleOk" />
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useContainerStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean; containerId: string; containerName: string }>();
const emit = defineEmits<{ "update:open": [boolean]; renamed: [] }>();

const { t } = useI18n();
const containerStore = useContainerStore();

const loading = ref(false);
const name = ref("");

watch(
  () => props.open,
  (open) => {
    if (open) name.value = props.containerName;
  }
);

async function handleOk() {
  if (!name.value) return;
  loading.value = true;
  try {
    await containerStore.rename(props.containerId, name.value);
    emit("update:open", false);
    emit("renamed");
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>
