<template>
  <div class="home">
    <!-- ── 加载态 ── -->
    <div v-if="loading" class="loading-wrap">
      <div class="skeleton-card" v-for="i in 3" :key="i"></div>
      <div class="skeleton-heatmap"></div>
      <div class="skeleton-card" v-for="i in 5" :key="'l'+i"></div>
    </div>

    <!-- ── 空状态 ── -->
    <div v-else-if="isEmpty" class="empty-state">
      <div class="empty-icon">📝</div>
      <h2>还没有记录</h2>
      <p>开始记录你每天的学习内容吧</p>
      <router-link to="/editor" class="empty-cta">去写第一篇 →</router-link>
    </div>

    <!-- ── 主内容 ── -->
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

      <!-- 热力图 -->
      <section class="heatmap-section">
        <h3 class="section-title">📊 打卡热力图（过去 52 周）</h3>
        <div class="heatmap-scroll">
          <div class="heatmap-container" @mousemove="handleCanvasMove" @mouseleave="handleCanvasLeave">
            <canvas ref="canvasRef"></canvas>
            <div
              v-show="tooltipVisible"
              class="heatmap-tooltip"
              :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
            >{{ tooltipText }}</div>
          </div>
        </div>
        <!-- 图例 -->
        <div class="heatmap-legend">
          <span class="legend-label">Less</span>
          <span class="legend-cell" v-for="c in [0,1,2,3,4]" :key="c" :style="{ background: heatColor(c) }"></span>
          <span class="legend-label">More</span>
        </div>
      </section>

      <!-- 最近日志 -->
      <section class="recent-logs">
        <h3 class="section-title">📋 最近日志</h3>
        <div v-if="recentLogs.length === 0" class="sub-empty">暂无日志</div>
        <div v-else class="log-list">
          <div
            v-for="log in recentLogs"
            :key="log.id"
            class="log-item"
          >
            <div class="log-main">
              <router-link :to="'/log/' + log.id" class="log-title">{{ log.title }}</router-link>
              <div class="log-meta">
                <span class="log-date">{{ log.date }}</span>
                <span class="log-duration">⏱ {{ log.duration }} 分钟</span>
              </div>
              <div class="log-tags" v-if="log.tags && log.tags.length">
                <span
                  v-for="tag in log.tags"
                  :key="tag.id"
                  class="tag-badge"
                  :style="{ background: getTagColor(tag.name) }"
                >{{ tag.name }}</span>
              </div>
            </div>
            <router-link :to="'/editor/' + log.id" class="log-edit-btn" title="编辑">✏️</router-link>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from "vue";
import { getSummary, getHeatmap, getLogs } from "../api";

// ── 常量 ──

const CELL_SIZE = 12;
const CELL_GAP = 3;
const CELL_STEP = CELL_SIZE + CELL_GAP;
const COLS = 52;
const ROWS = 7;
const PAD_LEFT = 36;
const PAD_TOP = 22;
const MONTH_NAMES = [
  "1月", "2月", "3月", "4月", "5月", "6月",
  "7月", "8月", "9月", "10月", "11月", "12月",
];
const DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", ""];

// ── 响应式状态 ──

const loading = ref(true);
const summary = ref(null);
const heatmapData = ref([]);
const recentLogs = ref([]);

const canvasRef = ref(null);
const tooltipVisible = ref(false);
const tooltipText = ref("");
const tooltipX = ref(0);
const tooltipY = ref(0);

const isEmpty = ref(false);

// ── 工具函数 ──

function heatColor(count) {
  if (count === 0) return "#ebedf0";
  if (count === 1) return "#9be9a8";
  if (count === 2) return "#40c463";
  if (count === 3) return "#30a14e";
  return "#216e39";
}

function getTagColor(name) {
  const palette = [
    "#3b82f6", "#ef4444", "#f59e0b", "#10b981",
    "#8b5cf6", "#ec4899", "#06b6d4", "#f97316",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
  }
  return palette[Math.abs(hash) % palette.length];
}

function formatHours(min) {
  return (min / 60).toFixed(1) + "h";
}

/** 返回某个日期所在周的周一（Mon=0 基准） */
function getMonday(d) {
  const r = new Date(d);
  const jsDay = r.getDay(); // 0=Sun
  const diff = jsDay === 0 ? -6 : 1 - jsDay;
  r.setDate(r.getDate() + diff);
  r.setHours(0, 0, 0, 0);
  return r;
}

// ── Canvas 绘制 ──

function drawHeatmap() {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const dpr = window.devicePixelRatio || 1;
  const w = PAD_LEFT + COLS * CELL_STEP + 4;
  const h = PAD_TOP + ROWS * CELL_STEP + 4;

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";

  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  // 构建 date → count 映射
  const dataMap = {};
  heatmapData.value.forEach((d) => (dataMap[d.date] = d.count));

  // 计算起始周一
  const today = new Date();
  const currentMonday = getMonday(today);
  const startMonday = new Date(currentMonday);
  startMonday.setDate(currentMonday.getDate() - 51 * 7);

  let lastMonth = -1;
  const months = [];

  ctx.clearRect(0, 0, w, h);

  // 绘制格子
  for (let col = 0; col < COLS; col++) {
    for (let row = 0; row < ROWS; row++) {
      const d = new Date(startMonday);
      d.setDate(startMonday.getDate() + col * 7 + row);
      const dateStr = d.toISOString().slice(0, 10);
      const count = dataMap[dateStr] || 0;

      const x = PAD_LEFT + col * CELL_STEP;
      const y = PAD_TOP + row * CELL_STEP;

      ctx.fillStyle = heatColor(count);
      // 圆角矩形
      const r = 2;
      const cx = x + r, cy = y + r;
      const cw = x + CELL_SIZE - r, ch = y + CELL_SIZE - r;
      ctx.beginPath();
      ctx.moveTo(cx, y);
      ctx.arcTo(x + CELL_SIZE, y, x + CELL_SIZE, ch, r);
      ctx.arcTo(x + CELL_SIZE, y + CELL_SIZE, cw, y + CELL_SIZE, r);
      ctx.arcTo(x, y + CELL_SIZE, x, ch, r);
      ctx.arcTo(x, y, cx, y, r);
      ctx.fill();

      // 月份追踪：每个 week column 的第一行检测月份变化
      if (row === 0) {
        const month = d.getMonth();
        if (month !== lastMonth) {
          months.push({ col, label: MONTH_NAMES[month] });
          lastMonth = month;
        }
      }
    }
  }

  // 周标签（左侧）
  ctx.fillStyle = "#94a3b8";
  ctx.font = "10px -apple-system, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (let row = 0; row < ROWS; row++) {
    if (DAY_LABELS[row]) {
      ctx.fillText(
        DAY_LABELS[row],
        PAD_LEFT - 6,
        PAD_TOP + row * CELL_STEP + CELL_SIZE / 2,
      );
    }
  }

  // 月份标签（顶部）
  ctx.fillStyle = "#94a3b8";
  ctx.font = "10px -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  months.forEach((m) => {
    ctx.fillText(m.label, PAD_LEFT + m.col * CELL_STEP, 4);
  });

  // 存储映射用于 tooltip
  canvas._startMonday = startMonday.getTime();
  canvas._dataMap = dataMap;
}

// ── Tooltip ──

function handleCanvasMove(e) {
  const canvas = canvasRef.value;
  if (!canvas || !canvas._dataMap) return;

  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  const col = Math.floor((mx - PAD_LEFT) / CELL_STEP);
  const row = Math.floor((my - PAD_TOP) / CELL_STEP);

  if (col >= 0 && col < COLS && row >= 0 && row < ROWS) {
    const startMonday = new Date(canvas._startMonday);
    const d = new Date(startMonday);
    d.setDate(startMonday.getDate() + col * 7 + row);
    const dateStr = d.toISOString().slice(0, 10);
    const count = canvas._dataMap[dateStr] || 0;

    tooltipText.value = `${dateStr}  ·  ${count} 条记录`;
    // 保持在 canvas 可视范围内
    const tooltipW = 150;
    const rightEdge = rect.width;
    const tx = mx + 14;
    tooltipX.value = tx + tooltipW > rightEdge ? mx - tooltipW - 8 : tx;
    tooltipY.value = my - 30;
    tooltipVisible.value = true;
  } else {
    tooltipVisible.value = false;
  }
}

function handleCanvasLeave() {
  tooltipVisible.value = false;
}

// ── 数据加载 ──

async function loadData() {
  loading.value = true;
  try {
    const [s, h, logsResult] = await Promise.all([
      getSummary(),
      getHeatmap(),
      getLogs({ limit: 10 }),
    ]);
    summary.value = s;
    heatmapData.value = h;
    recentLogs.value = logsResult.items;
    isEmpty.value = logsResult.total === 0;
  } catch (e) {
    console.error("首页数据加载失败:", e);
  } finally {
    loading.value = false;
    await nextTick();
    drawHeatmap();
  }
}

watch(heatmapData, async () => {
  await nextTick();
  drawHeatmap();
});

onMounted(loadData);
</script>

<style scoped>
/* ── 加载态 ── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  height: 72px;
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-heatmap {
  height: 140px;
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ── 空状态 ── */
.empty-state {
  text-align: center;
  padding: 64px 24px;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.empty-state h2 {
  font-size: 22px;
  color: var(--color-text);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 15px;
  margin-bottom: 24px;
}

.empty-cta {
  display: inline-block;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 15px;
  transition: background 0.15s;
}

.empty-cta:hover {
  background: var(--color-primary-hover);
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

.scard-icon {
  font-size: 28px;
  line-height: 1;
}

.scard-body {
  min-width: 0;
}

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

/* ── 热力图 ── */
.heatmap-section {
  margin-bottom: 32px;
}

.heatmap-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 8px;
}

.heatmap-container {
  position: relative;
  display: inline-block;
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 12px 10px 8px;
}

.heatmap-tooltip {
  position: absolute;
  background: #1e293b;
  color: #fff;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 20;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 8px;
}

.legend-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.legend-cell {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  display: inline-block;
}

/* ── 日志列表 ── */
.recent-logs {
  margin-bottom: 32px;
}

.sub-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 24px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-item {
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  transition: box-shadow 0.15s;
}

.log-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.log-main {
  min-width: 0;
  flex: 1;
}

.log-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  transition: color 0.12s;
}

.log-title:hover {
  color: var(--color-primary);
}

.log-meta {
  display: flex;
  gap: 16px;
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.log-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  color: #fff;
  font-weight: 500;
  white-space: nowrap;
}

.log-edit-btn {
  font-size: 16px;
  padding: 6px 8px;
  border-radius: var(--radius);
  color: var(--color-text-secondary);
  transition: color 0.12s, background 0.12s;
  flex-shrink: 0;
  margin-left: 12px;
}

.log-edit-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

/* ── 响应式 ── */
@media (max-width: 640px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }

  .log-edit-btn {
    display: none;
  }
}
</style>
