<template>
  <div class="detail-page">
    <!-- ── 加载态 ── -->
    <div v-if="loading" class="loading-wrap">
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-meta"></div>
      <div class="skeleton skeleton-divider"></div>
      <div class="skeleton skeleton-line" v-for="i in 8" :key="i" :style="{ width: (60 + Math.random() * 40).toFixed(0) + '%' }"></div>
    </div>

    <!-- ── 内容 ── -->
    <template v-else-if="log">
      <article>
        <!-- 标题 -->
        <h1 class="detail-title">{{ log.title }}</h1>

        <!-- 元信息行 -->
        <div class="detail-meta">
          <span class="meta-item">📅 {{ log.date }}</span>
          <span class="meta-item">⏱️ {{ log.duration }} 分钟</span>
        </div>

        <!-- 标签 -->
        <div class="detail-tags" v-if="log.tags && log.tags.length">
          <router-link
            v-for="tag in log.tags"
            :key="tag.id"
            :to="'/search?tag=' + encodeURIComponent(tag.name)"
            class="tag-badge"
            :style="{ background: tagColor(tag.name) }"
          >{{ tag.name }}</router-link>
        </div>

        <!-- 分割线 -->
        <hr class="detail-divider" />

        <!-- Markdown 正文 -->
        <div class="markdown-body" v-html="renderedContent"></div>

        <!-- 底部操作栏 -->
        <div class="detail-actions">
          <router-link :to="'/editor/' + log.id" class="btn btn-primary">✏️ 编辑</router-link>
          <button class="btn btn-back" @click="$router.back()">← 返回</button>
        </div>
      </article>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import { getLog } from "../api";

const route = useRoute();
const router = useRouter();

const log = ref(null);
const loading = ref(true);

const renderedContent = computed(() => {
  if (!log.value?.content) return "";
  return marked.parse(log.value.content) || "";
});

// ── 标签颜色 ──

function tagColor(name) {
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

// ── 加载 ──

async function load() {
  loading.value = true;
  try {
    const id = Number(route.params.id);
    if (!id) throw new Error("无效 ID");
    log.value = await getLog(id);
    document.title = `${log.value.title} · 学习日志`;
  } catch (e) {
    console.error("日志加载失败:", e);
    router.replace("/");
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.id, load);
onMounted(load);
</script>

<style scoped>
.detail-page {
  max-width: 800px;
  margin: 0 auto;
}

/* ── 加载态 ── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.skeleton {
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-title {
  height: 36px;
  width: 65%;
}

.skeleton-meta {
  height: 20px;
  width: 40%;
}

.skeleton-divider {
  height: 2px;
  width: 100%;
}

.skeleton-line {
  height: 14px;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ── 标题 ── */
.detail-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--color-text);
  margin-bottom: 16px;
}

/* ── 元信息 ── */
.detail-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.meta-item {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* ── 标签 ── */
.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.tag-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 14px;
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  transition: opacity 0.12s;
}

.tag-badge:hover {
  opacity: 0.85;
}

/* ── 分割线 ── */
.detail-divider {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 24px 0;
}

/* ── 底部操作栏 ── */
.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: 36px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
  text-decoration: none;
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-back {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-back:hover {
  background: var(--color-border);
}

/* ═══════════════════════════════════════════
   Markdown 正文样式 (.markdown-body)
   ═══════════════════════════════════════════ */

.markdown-body :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 28px 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.markdown-body :deep(h2) {
  font-size: 20px;
  font-weight: 700;
  margin: 24px 0 12px;
}

.markdown-body :deep(h3) {
  font-size: 17px;
  font-weight: 600;
  margin: 20px 0 10px;
}

.markdown-body :deep(p) {
  line-height: 1.8;
  margin-bottom: 14px;
}

.markdown-body :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(strong) {
  font-weight: 700;
}

.markdown-body :deep(em) {
  font-style: italic;
}

/* inline code */
.markdown-body :deep(code) {
  background: #f1f5f9;
  color: #e11d48;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  word-break: break-word;
}

/* block code */
.markdown-body :deep(pre) {
  background: #1e293b;
  border-radius: var(--radius);
  padding: 16px 20px;
  overflow-x: auto;
  margin-bottom: 16px;
  line-height: 1.6;
}

.markdown-body :deep(pre code) {
  background: none;
  color: #e2e8f0;
  padding: 0;
  font-size: 14px;
}

/* blockquote */
.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--color-primary);
  background: var(--color-primary-light);
  padding: 10px 16px;
  margin: 0 0 16px;
  border-radius: 0 var(--radius) var(--radius) 0;
  color: var(--color-text-secondary);
}

.markdown-body :deep(blockquote p) {
  margin-bottom: 4px;
}

/* lists */
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-body :deep(li) {
  margin-bottom: 6px;
  line-height: 1.7;
}

.markdown-body :deep(ul ul),
.markdown-body :deep(ol ol),
.markdown-body :deep(ul ol),
.markdown-body :deep(ol ul) {
  margin-bottom: 0;
  margin-top: 6px;
}

/* horizontal rule */
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 24px 0;
}

/* images */
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: var(--radius);
}

/* tables */
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--color-bg);
  font-weight: 600;
  font-size: 14px;
}

.markdown-body :deep(tr:nth-child(even)) {
  background: var(--color-bg);
}
</style>
