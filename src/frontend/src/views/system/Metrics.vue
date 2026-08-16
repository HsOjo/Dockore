<template>
  <div>
    <a-alert
      v-if="metrics?.error"
      type="warning"
      show-icon
      :message="t('metrics.hostProcMissing')"
      style="max-width: 960px"
    />
    <div v-else-if="metrics" class="panel">
      <div class="panel-header">
        <span class="hostname">{{ hostname }}</span>
        <span class="uptime">({{ t("metrics.uptime") }}: {{ uptimeText }})</span>
      </div>
      <div class="cards-grid">
                  <a-card :title="t('metrics.groupCpu')" size="small" class="group-card">
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><DashboardOutlined /> {{ t("metrics.cpu") }}</span>
                <span class="metric-value">{{ metrics.cpu_percent.toFixed(2) }}% of {{ metrics.cpu_count }} CPU(s)</span>
              </div>
              <a-progress
                :percent="metrics.cpu_percent"
                :show-info="false"
                :stroke-color="strokeColor(metrics.cpu_percent)"
                size="small"
              />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><FieldTimeOutlined /> {{ t("metrics.ioDelay") }}</span>
                <span class="metric-value">{{ metrics.io_delay === null || metrics.io_delay === undefined ? "-" : metrics.io_delay.toFixed(2) + "%" }}</span>
              </div>
              <a-progress
                :percent="metrics.io_delay ?? 0"
                :show-info="false"
                :stroke-color="strokeColor(metrics.io_delay ?? 0)"
                size="small"
              />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><ThunderboltOutlined /> {{ t("metrics.cpuFreq") }}</span>
                <span class="metric-value">{{ freqText }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><BarChartOutlined /> {{ t("metrics.loadAvg") }}</span>
                <span class="metric-value">{{ metrics.load_avg ? metrics.load_avg.join(", ") : "-" }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
          </a-card>
                  <a-card :title="t('metrics.groupMemory')" size="small" class="group-card">
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><DatabaseOutlined /> {{ t("metrics.memory") }}</span>
                <span class="metric-value">{{ usageText(metrics.memory) }}</span>
              </div>
              <a-progress
                :percent="metrics.memory?.percent ?? 0"
                :show-info="false"
                :stroke-color="strokeColor(metrics.memory?.percent ?? 0)"
                size="small"
              />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><SwapOutlined /> {{ t("metrics.swap") }}</span>
                <span class="metric-value">{{ metrics.swap && metrics.swap.total > 0 ? usageText(metrics.swap) : t("none") }}</span>
              </div>
              <a-progress
                v-if="metrics.swap && metrics.swap.total > 0"
                :percent="metrics.swap.percent"
                :show-info="false"
                :stroke-color="strokeColor(metrics.swap.percent)"
                size="small"
              />
              <div v-else class="bar-spacer" />
            </div>
          </a-card>
                  <a-card :title="t('metrics.groupDisk')" size="small" class="group-card">
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><HddOutlined /> {{ t("metrics.hdSpace") }}</span>
                <span class="metric-value">{{ usageText(metrics.disk) }}</span>
              </div>
              <div class="disk-path">{{ metrics.disk?.path || "/" }}</div>
              <a-progress
                :percent="metrics.disk?.percent ?? 0"
                :show-info="false"
                :stroke-color="strokeColor(metrics.disk?.percent ?? 0)"
                size="small"
              />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><DownloadOutlined /> {{ t("metrics.diskRead") }}</span>
                <span class="metric-value">{{ formatRate(metrics.disk_io?.read_rate) }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><UploadOutlined /> {{ t("metrics.diskWrite") }}</span>
                <span class="metric-value">{{ formatRate(metrics.disk_io?.write_rate) }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
          </a-card>
                  <a-card :title="t('metrics.groupNet')" size="small" class="group-card">
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><ArrowDownOutlined /> {{ t("metrics.netIn") }}</span>
                <span class="metric-value">{{ formatRate(metrics.net?.in_rate) }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><ArrowUpOutlined /> {{ t("metrics.netOut") }}</span>
                <span class="metric-value">{{ formatRate(metrics.net?.out_rate) }}</span>
              </div>
              <div class="bar-spacer" />
            </div>
          </a-card>
          <a-card :title="t('metrics.groupHost')" size="small" class="group-card">
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><DashboardOutlined /> CPU(s)</span>
              </div>
              <div class="metric-block-value">{{ store.version?.project.cpu || "-" }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-line">
                <span class="metric-label"><CodeOutlined /> {{ t("metrics.kernel") }}</span>
              </div>
              <div class="metric-block-value">{{ store.version?.project.kernel || "-" }}</div>
            </div>
          </a-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  BarChartOutlined,
  CodeOutlined,
  DashboardOutlined,
  DatabaseOutlined,
  DownloadOutlined,
  FieldTimeOutlined,
  HddOutlined,
  SwapOutlined,
  ThunderboltOutlined,
  UploadOutlined,
} from "@ant-design/icons-vue";
import { formatBytes, wsClient } from "@dockore/shared";
import { useSystemStore } from "@/stores";

interface UsageGauge {
  total: number;
  used: number;
  percent: number;
}

interface Metrics {
  error: string | null;
  timestamp: number;
  cpu_percent: number;
  cpu_count: number;
  io_delay?: number | null;
  cpu_freq?: { current: number; max: number } | null;
  memory?: UsageGauge | null;
  swap?: UsageGauge | null;
  disk?: (UsageGauge & { path: string }) | null;
  load_avg?: number[] | null;
  net?: { in_rate: number | null; out_rate: number | null } | null;
  disk_io?: { read_rate: number | null; write_rate: number | null } | null;
  uptime: number;
}

const { t } = useI18n();
const store = useSystemStore();

const metrics = ref<Metrics | null>(null);

const hostname = computed(() => store.version?.project.hostname || "");

const uptimeText = computed(() => formatUptime(metrics.value?.uptime ?? 0));

const freqText = computed(() => {
  const f = metrics.value?.cpu_freq;
  if (!f) return "-";
  return f.max > 0
    ? `${f.current.toFixed(0)} / ${f.max.toFixed(0)} MHz`
    : `${f.current.toFixed(0)} MHz`;
});

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function formatUptime(sec: number): string {
  const days = Math.floor(sec / 86400);
  const time = [sec / 3600 % 24, sec / 60 % 60, sec % 60]
    .map((v) => pad(Math.floor(v)))
    .join(":");
  return t("metrics.uptimeValue", { days, time });
}

function usageText(g?: UsageGauge | null): string {
  if (!g) return "-";
  return `${formatBytes(g.used)} / ${formatBytes(g.total)}`;
}

function strokeColor(percent: number): string {
  if (percent >= 90) return "#f5222d";
  if (percent >= 70) return "#faad14";
  return "#1677ff";
}

function formatRate(v?: number | null): string {
  return v === null || v === undefined ? "-" : `${formatBytes(v)}/s`;
}

function onMetrics(data: any) {
  metrics.value = data?.data ?? null;
}

function subscribeMetrics() {
  wsClient.send({ type: "metrics.subscribe" });
}

onMounted(() => {
  if (!store.version) store.fetchVersion().catch(() => {});
  wsClient.on("system.metrics", onMetrics);
  wsClient.on("open", subscribeMetrics);
  subscribeMetrics();
});

onUnmounted(() => {
  wsClient.send({ type: "metrics.unsubscribe" });
  wsClient.off("system.metrics", onMetrics);
  wsClient.off("open", subscribeMetrics);
});
</script>

<style scoped>
.panel {
  max-width: 1200px;
  border: 1px solid rgba(5, 5, 5, 0.1);
  border-radius: 8px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.6);
}

.panel-header {
  font-size: 15px;
  margin-bottom: 16px;
}

.panel-header .hostname {
  color: #1677ff;
  font-weight: 500;
}

.panel-header .uptime {
  color: rgba(0, 0, 0, 0.65);
  margin-left: 4px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
}

.group-card {
  height: 100%;
}

.group-card :deep(.ant-card-head) {
  min-height: 36px;
}

.group-card :deep(.ant-card-body) {
  padding: 12px 16px;
}

.metric-item {
  margin-bottom: 12px;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-line {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 2px;
}

.metric-label {
  flex: 1 1 auto;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-value {
  white-space: nowrap;
  flex-shrink: 0;
}

.metric-block-value {
  word-break: break-all;
  font-family: monospace;
  font-size: 13px;
  margin: 2px 0 6px 22px;
}

.bar-spacer {
  height: 8px;
}

.disk-path {
  font-size: 12px;
  font-family: monospace;
  color: rgba(0, 0, 0, 0.45);
  word-break: break-all;
  margin-bottom: 2px;
}

.metric-line :deep(.anticon) {
  margin-right: 6px;
  color: rgba(0, 0, 0, 0.65);
}

body.dockore-theme-dark .panel {
  border-color: rgba(253, 253, 253, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

body.dockore-theme-dark .panel-header .uptime,
body.dockore-theme-dark .metric-line :deep(.anticon) {
  color: rgba(255, 255, 255, 0.65);
}

body.dockore-theme-dark .disk-path {
  color: rgba(255, 255, 255, 0.45);
}
</style>
