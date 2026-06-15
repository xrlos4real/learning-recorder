<template>
  <div class="stats-page">
    <!-- ── 加载态 ── -->
    <div v-if="loading" class="loading-wrap">
      <div class="skeleton skeleton-cards" v-for="i in 3" :key="i"></div>
      <div class="skeleton skeleton-chart"></div>
      <div class="skeleton skeleton-chart"></div>
    </div>

    <!-- ── 内容 ── -->
    <template v-else>
      <!-- Summary 卡片 -->
      <section class="summary-cards">
        <div class="scard">
          <div class="scard-icon">📝</div>
          <div class="scard-body">
            <div class="scard-value">{{ summary.total_logs }}</div>
            <div class="scard-label">记录天数</div>
          </div>
        </div>
        <div class="scard">
          <div class="scard-icon">⏱️</div>
          <div class="scard-body">
            <div class="scard-value">{{ formatHours(summary.total_duration) }}</div>
            <div class="scard-label">总学习时长</div>
          </div>
        </div>
        <div class="scard">
          <div class="scard-icon">🔥</div>
          <div class="scard-body">
            <div class="scard-value">{{ summary.streak }} <span class="scard-unit">天</span></div>
            <div class="scard-label">连续打卡</div>
          </div>
        </div>
      </section>

      <!-- 30 天柱状图 -->
      <section class="chart-section">
        <h3 class="section-title">📈 最近 30 天学习时长</h3>
        <div class="chart-container">
          <canvas ref="barCanvasRef"></canvas>
        </div>
      </section>

      <!-- 标签分布甜甜圈 -->
      <section class="chart-section">
        <h3 class="section-title">🏷️ 标签分布</h3>
        <div v-if="activeTags.length === 0" class="no-tags">
          暂无标签数据
        </div>
        <div v-else class="chart-container chart-doughnut">
          <canvas ref="doughnutCanvasRef"></canvas>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import {
  Chart,
  BarController,
  DoughnutController,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { getSummary, getDaily, getTags } from "../api";

// 注册 Chart.js 组件
Chart.register(
  BarController,
  DoughnutController,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
);

const TAG_COLORS = [
  "#3b82f6", "#ef4444", "#f59e0b", "#10b981",
  "#8b5cf6", "#ec4899", "#06b6d4", "#f97316",
  "#84cc16", "#f43f5e",
];

// ── 状态 ──

const loading = ref(true);
const summary = ref(null);
const dailyData = ref([]);
const activeTags = ref([]);

const barCanvasRef = ref(null);
const doughnutCanvasRef = ref(null);

let barChart = null;
let doughnutChart = null;

// ── 工具 ──

function formatHours(min) {
  return (min / 60).toFixed(1) + "h";
}

// ── 柱状图 ──

function renderBarChart() {
  if (!barCanvasRef.value) return;

  const labels = dailyData.value.map((d) => d.date.slice(5)); // "MM-DD"
  const values = dailyData.value.map((d) => d.duration);

  // 每隔 5 天显示一个 label，其余为空字符串
  const sparseLabels = labels.map((l, i) => (i % 5 === 0 ? l : ""));

  barChart = new Chart(barCanvasRef.value, {
    type: "bar",
    data: {
      labels: sparseLabels,
      datasets: [
        {
          label: "学习时长（分钟）",
          data: values,
          backgroundColor: "#4f46e5",
          hoverBackgroundColor: "#4338ca",
          borderRadius: 4,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => labels[items[0].dataIndex],
            label: (item) => `${item.raw} 分钟`,
          },
        },
      },
      scales: {
        x: {
          ticks: { font: { size: 11 }, color: "#94a3b8" },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: {
            font: { size: 11 },
            color: "#94a3b8",
            callback: (v) => v + " min",
          },
          grid: { color: "#e2e8f0" },
        },
      },
      interaction: {
        intersect: false,
        mode: "index",
      },
    },
  });
}

// ── 甜甜圈图 ──

function renderDoughnut() {
  if (!doughnutCanvasRef.value || activeTags.value.length === 0) return;

  const labels = activeTags.value.map((t) => t.name);
  const values = activeTags.value.map((t) => t.log_count);
  const bg = activeTags.value.map(
    (_, i) => TAG_COLORS[i % TAG_COLORS.length]
  );

  doughnutChart = new Chart(doughnutCanvasRef.value, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: bg,
          borderWidth: 2,
          borderColor: "#fff",
          hoverBorderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            padding: 20,
            usePointStyle: true,
            font: { size: 12 },
            color: "#64748b",
          },
        },
        tooltip: {
          callbacks: {
            label: (item) => ` ${item.label}: ${item.raw} 条`,
          },
        },
      },
    },
  });
}

// ── 销毁 ──

function destroyCharts() {
  if (barChart) { barChart.destroy(); barChart = null; }
  if (doughnutChart) { doughnutChart.destroy(); doughnutChart = null; }
}

// ── 加载 ──

async function loadData() {
  loading.value = true;
  destroyCharts();
  try {
    const [s, daily, tags] = await Promise.all([
      getSummary(),
      getDaily(),
      getTags(),
    ]);
    summary.value = s;
    dailyData.value = daily;
    activeTags.value = (tags || []).filter((t) => t.log_count > 0);

    await nextTick();
    renderBarChart();
    renderDoughnut();
  } catch (e) {
    console.error("统计数据加载失败:", e);
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
onUnmounted(destroyCharts);
</script>

<style scoped>
.stats-page {
  max-width: 800px;
  margin: 0 auto;
}

/* ── 加载态 ── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.skeleton {
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}
.skeleton-cards { height: 72px; }
.skeleton-chart { height: 240px; }

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ── Summary 卡片 ── */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.scard {
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.scard-icon { font-size: 28px; line-height: 1; }
.scard-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}
.scard-unit {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
}
.scard-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* ── 分区标题 ── */
.section-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}

/* ── 图表容器 ── */
.chart-section {
  margin-bottom: 36px;
}
.chart-container {
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px 24px 16px;
  height: 300px;
  position: relative;
}
.chart-doughnut {
  height: 380px;
}

.no-tags {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 48px 24px;
  font-size: 15px;
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

@media (max-width: 640px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
  .chart-container { height: 250px; }
  .chart-doughnut { height: 340px; }
}
</style>
