<template>
  <div>
    <a-page-header
      :title="`${t('menu.volumes')}：${item?.name || ''}`"
      @back="router.push('/volumes')"
    >
      <template #extra>
        <a-button @click="load">
          <ReloadOutlined />
        </a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <template v-if="item">
        <a-descriptions :column="1" bordered style="max-width: 720px">
          <a-descriptions-item :label="t('volume.field.name')">
            {{ item.name }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('volume.field.driver')">
            {{ item.driver }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('volume.field.mountPoint')">
            <span class="mono">{{ item.mount_point }}</span>
          </a-descriptions-item>
          <a-descriptions-item :label="t('volume.field.scope')">
            {{ item.scope }}
          </a-descriptions-item>
          <a-descriptions-item :label="t('createTime')">
            {{ formatTime(item.create_time, locale) }}
          </a-descriptions-item>
        </a-descriptions>

        <a-card :title="t('volume.field.driverOpts')" style="max-width: 720px; margin-top: 16px">
          <a-table
            :data-source="optionRows"
            :columns="optionColumns"
            :pagination="false"
            size="small"
            row-key="key"
          />
        </a-card>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { message } from "ant-design-vue";
import { ReloadOutlined } from "@ant-design/icons-vue";
import { formatTime } from "@dockore/shared";
import { useVolumeStore, errorMessage, type VolumeItem } from "@/stores";

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const store = useVolumeStore();

const item = ref<VolumeItem | null>(null);
const loading = ref(false);

const optionColumns = computed(() => [
  { title: t("network.optionKey"), key: "key", dataIndex: "key" },
  { title: t("network.optionValue"), key: "value", dataIndex: "value" },
]);

const optionRows = computed(() => {
  const opts = item.value?.driver_opts || {};
  return Object.entries(opts).map(([key, value]) => ({ key, value }));
});

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

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.mono {
  font-family: monospace;
}
</style>
