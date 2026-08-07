<template>
  <a-modal
    :open="open"
    :title="t('container.commit')"
    :ok-text="t('ok')"
    :cancel-text="t('cancel')"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="emit('update:open', false)"
  >
    <a-form layout="vertical">
      <a-form-item :label="t('container.commitForm.name')" required>
        <a-input v-model:value="form.name" />
      </a-form-item>
      <a-form-item :label="t('container.commitForm.tag')">
        <a-input v-model:value="form.tag" placeholder="latest" />
      </a-form-item>
      <a-form-item :label="t('container.commitForm.author')">
        <a-input v-model:value="form.author" />
      </a-form-item>
      <a-form-item :label="t('container.commitForm.message')">
        <a-textarea v-model:value="form.message" :rows="4" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { useContainerStore, errorMessage } from "@/stores";

const props = defineProps<{ open: boolean; containerId: string }>();
const emit = defineEmits<{ "update:open": [boolean] }>();

const { t } = useI18n();
const containerStore = useContainerStore();

const loading = ref(false);
const form = reactive({ name: "", tag: "", author: "", message: "" });

watch(
  () => props.open,
  (open) => {
    if (open) Object.assign(form, { name: "", tag: "", author: "", message: "" });
  }
);

async function handleOk() {
  if (!form.name) return;
  loading.value = true;
  try {
    await containerStore.commit(props.containerId, {
      name: form.name,
      tag: form.tag || null,
      author: form.author || null,
      message: form.message || null,
    });
    emit("update:open", false);
    message.success(t("saved"));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}
</script>
