<template>
  <div>
    <DetailHeader
      :title="`${t('menu.images')}：${item ? imageDisplayName(item) : ''}`"
      @back="router.push('/images')"
    >
      <a-button @click="load">
        <ReloadOutlined />
      </a-button>
    </DetailHeader>

    <a-spin :spinning="loading">
      <template v-if="item">
        <a-descriptions :column="1" bordered style="max-width: 720px">
          <a-descriptions-item :label="t('image.field.id')">
            <span class="mono">{{ item.id }}</span>
          </a-descriptions-item>
          <a-descriptions-item :label="t('image.field.tags')">
            <a-popconfirm
              v-for="tag in item.tags"
              :key="tag"
              :title="t('image.confirmDeleteTag', { tag })"
              :ok-text="t('ok')"
              :cancel-text="t('cancel')"
              @confirm="deleteTag(tag)"
            >
              <a-tag closable @close.prevent>{{ tag }}</a-tag>
            </a-popconfirm>
            <template v-if="!item.tags.length">{{ t("none") }}</template>
          </a-descriptions-item>
          <a-descriptions-item :label="t('image.field.os')">
            {{ item.os || "" }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('image.field.arch')">
            {{ item.architecture || "" }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('image.field.command')">
            <span class="mono">{{ item.command }}</span>
          </a-descriptions-item>
          <a-descriptions-item :label="t('createTime')">
            {{ formatTime(item.create_time, locale) }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('image.field.size')">
            {{ formatBytes(item.size) }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('container.field.tty')">
            <a-checkbox :checked="item.tty ?? false" disabled />
            <span style="margin-left: 16px">{{ t("container.field.interactive") }}</span>
            <a-checkbox :checked="item.interactive ?? false" disabled style="margin-left: 8px" />
          </a-descriptions-item>
        </a-descriptions>

        <a-card :title="t('image.field.ports')" style="max-width: 720px; margin-top: 16px">
          <a-table
            :data-source="item.ports || []"
            :columns="portColumns"
            :pagination="false"
            size="small"
            row-key="port"
          />
        </a-card>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import DetailHeader from "@/components/common/DetailHeader.vue";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { formatBytes, formatTime } from "@dockore/shared";
import { useImageStore, errorMessage, type ImageItem } from "@/stores";
import { imageDisplayName } from "@/utils/text";

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const store = useImageStore();

const item = ref<ImageItem | null>(null);
const loading = ref(false);

const portColumns = computed(() => [
  { title: t("container.network.port"), key: "port", dataIndex: "port" },
  { title: t("container.network.protocol"), key: "protocol", dataIndex: "protocol" },
]);

async function load() {
  loading.value = true;
  try {
    item.value = await store.fetch(String(route.params.id));
  } catch (e: any) {
    message.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
}

async function deleteTag(tag: string) {
  try {
    await store.remove([tag], true);
    await load();
  } catch (e: any) {
    message.error(errorMessage(e));
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.mono {
  font-family: monospace;
}
</style>
