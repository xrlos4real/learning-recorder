<template>
  <div class="search-page">
    <!-- ── 搜索栏 ── -->
    <div class="search-bar">
      <div class="search-input-wrap">
        <span class="search-icon">🔍</span>
        <input
          v-model.trim="query"
          type="text"
          class="search-input"
          placeholder="搜索标题或内容…"
          @input="onQueryInput"
          @keydown.enter="doSearch"
        />
        <button
          v-show="query"
          class="search-clear"
          @click="clearQuery"
          title="清空"
        >✕</button>
      </div>
    </div>

    <!-- ── 标签筛选 ── -->
    <div class="tag-filter-bar" v-if="tags.length > 0">
      <button
        :class="['tag-btn', { active: selectedTag === '' }]"
        @click="selectTag('')"
      >全部</button>
      <button
        v-for="tag in tags"
        :key="tag.id"
        :class="['tag-btn', { active: selectedTag === tag.name }]"
        @click="selectTag(tag.name)"
      >{{ tag.name }}</button>
    </div>

    <!-- ── 加载态 ── -->
    <div v-if="loading" class="loading-wrap">
      <div class="skeleton-card" v-for="i in 5" :key="i"></div>
    </div>

    <!-- ── 空状态 ── -->
    <div v-else-if="total === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <template v-if="query || selectedTag">
        <h2>没有找到匹配的记录</h2>
        <p v-if="query">未找到包含「<strong>{{ query }}</strong>」的日志</p>
        <p v-if="selectedTag">标签「<strong>{{ selectedTag }}</strong>」下暂无日志</p>
      </template>
      <template v-else>
        <h2>还没有日志</h2>
        <p>去写第一篇吧</p>
        <router-link to="/editor" class="empty-cta">✏️ 写日志</router-link>
      </template>
    </div>

    <!-- ── 结果列表 ── -->
    <template v-else>
      <div class="log-list">
        <div
          v-for="log in logs"
          :key="log.id"
          class="log-item"
        >
          <div class="log-main">
            <router-link :to="'/log/' + log.id" class="log-title">
              <span v-html="highlightTitle(log.title)"></span>
            </router-link>
            <div class="log-meta">
              <span>📅 {{ log.date }}</span>
              <span>⏱️ {{ log.duration }} 分钟</span>
            </div>
            <div class="log-tags" v-if="log.tags && log.tags.length">
              <span
                v-for="tag in log.tags"
                :key="tag.id"
                class="tag-badge"
                :style="{ background: tagColor(tag.name) }"
                @click.stop="selectTag(tag.name)"
              >{{ tag.name }}</span>
            </div>
          </div>
          <router-link :to="'/editor/' + log.id" class="log-edit-btn" title="编辑">✏️</router-link>
        </div>
      </div>

      <!-- ── 分页 ── -->
      <div class="pagination" v-if="pages > 1">
        <button
          class="page-btn"
          :disabled="page <= 1"
          @click="goPage(page - 1)"
        >‹ 上一页</button>

        <template v-for="p in visiblePages" :key="p">
          <span v-if="p === '...'" class="page-ellipsis">…</span>
          <button
            v-else
            :class="['page-btn', 'page-num', { current: p === page }]"
            @click="goPage(p)"
          >{{ p }}</button>
        </template>

        <button
          class="page-btn"
          :disabled="page >= pages"
          @click="goPage(page + 1)"
        >下一页 ›</button>

        <span class="page-total">共 {{ total }} 条记录</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getLogs, getTags } from "../api";

const route = useRoute();
const router = useRouter();

// ── 搜索 / 筛选状态 ──
const query = ref("");
const selectedTag = ref("");
const page = ref(1);
const limit = 10;

const logs = ref([]);
const total = ref(0);
const pages = ref(0);
const tags = ref([]);
const loading = ref(false);

let debounceTimer = null;

// ── 从 URL 初始化 ──
function initFromRoute() {
  query.value = (route.query.q || "").trim();
  selectedTag.value = (route.query.tag || "").trim();
  page.value = Number(route.query.page) || 1;
}

// ── 同步到 URL ──
function syncToRoute() {
  const q = {};
  if (query.value) q.q = query.value;
  if (selectedTag.value) q.tag = selectedTag.value;
  if (page.value > 1) q.page = String(page.value);
  router.replace({ query: Object.keys(q).length ? q : undefined });
}

// ── 搜索 ──
async function doSearch() {
  loading.value = true;
  try {
    const params = { page: page.value, limit };
    if (query.value) params.q = query.value;
    if (selectedTag.value) params.tag = selectedTag.value;
    const result = await getLogs(params);
    logs.value = result.items || [];
    total.value = result.total || 0;
    pages.value = result.pages || 0;
  } catch (e) {
    console.error("搜索失败:", e);
  } finally {
    loading.value = false;
  }
}

function onQueryInput() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    page.value = 1;
    doSearch();
    syncToRoute();
  }, 300);
}

function clearQuery() {
  query.value = "";
  page.value = 1;
  doSearch();
  syncToRoute();
}

// ── 标签 ──
function selectTag(name) {
  selectedTag.value = name;
  page.value = 1;
  doSearch();
  syncToRoute();
}

// ── 分页 ──
function goPage(p) {
  page.value = p;
  doSearch();
  syncToRoute();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

const visiblePages = computed(() => {
  const p = page.value;
  const totalPages = pages.value;
  const result = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) result.push(i);
  } else {
    result.push(1);
    if (p > 3) result.push("...");
    const start = Math.max(2, p - 1);
    const end = Math.min(totalPages - 1, p + 1);
    for (let i = start; i <= end; i++) result.push(i);
    if (p < totalPages - 2) result.push("...");
    result.push(totalPages);
  }
  return result;
});

// ── 高亮 ──
function highlightTitle(title) {
  if (!query.value) return escapeHtml(title);
  const escaped = escapeHtml(title);
  const q = escapeHtml(query.value);
  const regex = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  return escaped.replace(regex, '<mark class="search-highlight">$1</mark>');
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── 标签颜色 ──
function tagColor(name) {
  const palette = [
    "#3b82f6", "#ef4444", "#f59e0b", "#10b981",
    "#8b5cf6", "#ec4899", "#06b6d4", "#f97316",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++)
    hash = ((hash << 5) - hash + name.charCodeAt(i)) | 0;
  return palette[Math.abs(hash) % palette.length];
}

// ── 初始化 ──

onMounted(async () => {
  initFromRoute();

  // 加载标签列表
  try {
    const tagList = await getTags();
    tags.value = tagList || [];
  } catch (_) {}

  await doSearch();
});

// 路由变化（浏览器前进后退）→ 从 URL 恢复
watch(
  () => route.query,
  () => {
    initFromRoute();
    doSearch();
  }
);
</script>

<style scoped>
.search-page {
  max-width: 800px;
  margin: 0 auto;
}

/* ── 搜索栏 ── */
.search-bar {
  margin-bottom: 16px;
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 14px;
  font-size: 16px;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 42px;
  font-size: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.search-input::placeholder { color: #c0c7cf; }

.search-clear {
  position: absolute;
  right: 8px;
  background: var(--color-border);
  border: none;
  color: #94a3b8;
  border-radius: 50%;
  width: 26px;
  height: 26px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.12s;
}

.search-clear:hover {
  background: #cbd5e1;
  color: #64748b;
}

/* ── 标签筛选 ── */
.tag-filter-bar {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 20px;
  -webkit-overflow-scrolling: touch;
}

.tag-filter-bar::-webkit-scrollbar { height: 4px; }
.tag-filter-bar::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.tag-btn {
  flex-shrink: 0;
  padding: 5px 16px;
  font-size: 13px;
  font-family: inherit;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.12s;
  white-space: nowrap;
}

.tag-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.tag-btn.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
  font-weight: 600;
}

/* ── 加载态 ── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skeleton-card {
  height: 80px;
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
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h2 {
  font-size: 20px;
  color: var(--color-text);
  margin-bottom: 6px;
}
.empty-state p { font-size: 14px; margin-bottom: 16px; }
.empty-state strong { color: var(--color-primary); }
.empty-cta {
  display: inline-block;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 15px;
}

/* ── 日志列表 ── */
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
  cursor: default;
}

.log-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }

.log-main { min-width: 0; flex: 1; }

.log-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  transition: color 0.12s;
}

.log-title:hover { color: var(--color-primary); }

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
  cursor: pointer;
  transition: opacity 0.12s;
  white-space: nowrap;
}

.tag-badge:hover { opacity: 0.8; }

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

/* ── 关键词高亮 ── */
:deep(.search-highlight) {
  color: var(--color-primary);
  font-weight: 700;
  background: transparent;
}

/* ── 分页 ── */
.pagination {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 28px;
  flex-wrap: wrap;
  justify-content: center;
}

.page-btn {
  padding: 6px 14px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.12s;
}

.page-btn:hover:not(:disabled):not(.current) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-num.current {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
  font-weight: 600;
}

.page-ellipsis {
  padding: 6px 4px;
  color: var(--color-text-secondary);
}

.page-total {
  margin-left: 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

@media (max-width: 640px) {
  .log-edit-btn { display: none; }
  .page-total { width: 100%; text-align: center; margin-left: 0; margin-top: 8px; }
}
</style>
