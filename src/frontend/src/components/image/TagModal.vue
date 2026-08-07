<template>
  <a-modal
    :open="open"
    :title="t('image.tag')"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-form layout="vertical">
      <a-form-item :label="t('image.tagName')" required>
        <a-input v-model:value="name" :placeholder="t('image.tagPrompt')" />
      </a-form-item>
      <a-form-item :label="t('image.tagValue')">
        <a-input v-model:value="tag" placeholder="latest" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useImageStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean; imageId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const store = useImageStore();

const loading = ref(false);
const name = ref("");
const tag = ref("");

watch(
  () => props.open,
  (open) => {
    if (open) {
      name.value = "";
      tag.value = "";
    }
  }
);

async function handleOk() {
  if (!name.value) return;
  loading.value = true;
  try {
    await store.tag(props.imageId, name.value, tag.value || null);
    emit("update:open", false);
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>
