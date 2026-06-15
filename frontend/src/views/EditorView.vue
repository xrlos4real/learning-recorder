<template>
  <div class="editor-page">
    <!-- 编辑模式加载中 -->
    <div v-if="editLoading" class="loading-wrap">
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
      <div class="skeleton-editor"></div>
    </div>

    <div v-else class="editor-form">
      <!-- ── 顶部表单 ── -->
      <div class="form-top">
        <input
          v-model="title"
          type="text"
          class="input title-input"
          placeholder="今天学了什么？"
          maxlength="200"
        />
        <div class="form-row">
          <input
            v-model="dateStr"
            type="date"
            class="input date-input"
          />
          <input
            v-model.number="duration"
            type="number"
            class="input duration-input"
            placeholder="学习时长（分钟）"
            min="0"
          />
        </div>
      </div>

      <!-- ── 标签区域 ── -->
      <div class="tags-area">
        <span class="tags-label">标签：</span>
        <span
          v-for="tag in allTags"
          :key="tag.id"
          :class="['tag-chip', { selected: isTagSelected(tag.name) }]"
          @click="toggleTag(tag.name)"
        >{{ tag.name }}</span>
        <input
          ref="newTagInputRef"
          v-model="newTagName"
          class="tag-input"
          placeholder="+ 新标签"
          @keydown.enter.prevent="addNewTag"
        />
      </div>

      <!-- ── EasyMDE 编辑区 ── -->
      <div class="editor-wrapper">
        <textarea ref="editorRef"></textarea>
      </div>

      <!-- ── 底部操作栏 ── -->
      <div class="actions">
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="handleSave"
        >{{ saving ? '保存中…' : '保存' }}</button>
        <button
          class="btn btn-cancel"
          :disabled="saving"
          @click="handleCancel"
        >取消</button>
        <button
          v-if="isEdit"
          class="btn btn-danger"
          :disabled="saving"
          @click="handleDelete"
        >删除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import EasyMDE from "easymde";
import "easymde/dist/easymde.min.css";
import { getTags, createLog, updateLog, getLog, deleteLog } from "../api";

const route = useRoute();
const router = useRouter();

// ── 模式判断 ──

const logId = computed(() => {
  const id = route.params.id;
  return id ? Number(id) : null;
});
const isEdit = computed(() => !!logId.value);

// ── 表单字段 ──

const title = ref("");
const dateStr = ref(todayStr());
const duration = ref(30);
const allTags = ref([]);
const selectedTagNames = ref([]);
const newTagName = ref("");

const editorRef = ref(null);
const newTagInputRef = ref(null);

let easyMDE = null;

const editLoading = ref(false);
const saving = ref(false);

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ── 标签操作 ──

function isTagSelected(name) {
  return selectedTagNames.value.includes(name);
}

function toggleTag(name) {
  const idx = selectedTagNames.value.indexOf(name);
  if (idx >= 0) {
    selectedTagNames.value.splice(idx, 1);
  } else {
    selectedTagNames.value.push(name);
  }
}

function addNewTag() {
  const name = newTagName.value.trim();
  if (!name) return;
  if (!selectedTagNames.value.includes(name)) {
    selectedTagNames.value.push(name);
  }
  newTagName.value = "";
}

// ── 保存 ──

async function handleSave() {
  // 校验
  if (!title.value.trim()) {
    alert("请输入标题");
    return;
  }
  if (!Number.isInteger(duration.value) || duration.value < 0) {
    alert("学习时长必须为非负整数");
    return;
  }

  saving.value = true;
  try {
    const payload = {
      title: title.value.trim(),
      content: easyMDE ? easyMDE.value() : "",
      duration: duration.value,
      date: dateStr.value,
      tags: selectedTagNames.value,
    };

    let resultLog;
    if (isEdit.value) {
      resultLog = await updateLog(logId.value, payload);
    } else {
      resultLog = await createLog(payload);
    }

    // 清除草稿
    clearAutosave();

    router.push(`/log/${resultLog.id}`);
  } catch (e) {
    alert("保存失败：" + (e.message || "未知错误"));
  } finally {
    saving.value = false;
  }
}

function handleCancel() {
  router.back();
}

// ── 删除 ──

async function handleDelete() {
  if (!confirm("确定要删除这篇日志吗？此操作不可撤销。")) return;

  saving.value = true;
  try {
    await deleteLog(logId.value);
    clearAutosave();
    router.push("/");
  } catch (e) {
    alert("删除失败：" + (e.message || "未知错误"));
  } finally {
    saving.value = false;
  }
}

// ── 草稿 ──

function getAutosaveKey() {
  return `learning-log-draft-${logId.value || "new"}`;
}

function clearAutosave() {
  try {
    localStorage.removeItem("smde_" + getAutosaveKey());
  } catch (_) {}
}

// ── EasyMDE 初始化 ──

function initEasyMDE() {
  if (!editorRef.value) return;

  easyMDE = new EasyMDE({
    element: editorRef.value,
    spellChecker: false,
    placeholder: "用 Markdown 记录今天的学习内容…",
    minHeight: "300px",
    toolbar: [
      "bold",
      "italic",
      "heading",
      "|",
      "quote",
      "code",
      "|",
      "unordered-list",
      "ordered-list",
      "|",
      "link",
      "|",
      "preview",
      "fullscreen",
    ],
    autosave: {
      enabled: true,
      uniqueId: getAutosaveKey(),
      delay: 1000,
    },
    status: false,
  });
}

function destroyEasyMDE() {
  if (easyMDE) {
    easyMDE.toTextArea();
    easyMDE = null;
  }
}

// ── 编辑模式：加载已有日志 ──

async function loadExistingLog() {
  editLoading.value = true;
  try {
    const log = await getLog(logId.value);
    title.value = log.title;
    dateStr.value = log.date;
    duration.value = log.duration;
    selectedTagNames.value = (log.tags || []).map((t) => t.name);
    // EasyMDE 加载内容
    await nextTick();
    if (easyMDE) {
      easyMDE.value(log.content || "");
    }
  } catch (e) {
    alert("加载日志失败：" + (e.message || "未知错误"));
    router.replace("/editor");
  } finally {
    editLoading.value = false;
  }
}

// ── 生命周期 ──

onMounted(async () => {
  // 并发加载标签 + 初始化编辑器
  try {
    const tags = await getTags();
    allTags.value = tags;
  } catch (_) {
    // 标签加载失败不阻塞
  }

  await nextTick();
  initEasyMDE();

  if (isEdit.value) {
    await loadExistingLog();
  }
});

onUnmounted(() => {
  destroyEasyMDE();
});
</script>

<style scoped>
.editor-page {
  max-width: 860px;
}

/* ── 加载态 ── */
.loading-wrap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-card {
  height: 48px;
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-editor {
  height: 340px;
  background: var(--color-surface);
  border-radius: var(--radius);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* ── 表单 ── */
.editor-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-top {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input {
  width: 100%;
  padding: 10px 14px;
  font-size: 15px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
}

.input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.input::placeholder {
  color: #c0c7cf;
}

.title-input {
  font-size: 20px;
  font-weight: 600;
  padding: 12px 16px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.date-input {
  flex: 1;
  max-width: 200px;
}

.duration-input {
  flex: 1;
  max-width: 220px;
}

/* ── 标签 ── */
.tags-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  min-height: 44px;
}

.tags-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.tag-chip {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 14px;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-bg);
  transition: all 0.12s;
}

.tag-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.tag-chip.selected {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.tag-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--color-text);
  min-width: 80px;
  font-family: inherit;
  padding: 3px 4px;
}

.tag-input::placeholder {
  color: #c0c7cf;
}

/* ── 编辑器 ── */
.editor-wrapper {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
}

/* ── 操作按钮 ── */
.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn {
  padding: 10px 24px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, opacity 0.15s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-cancel {
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-cancel:hover:not(:disabled) {
  background: var(--color-border);
}

.btn-danger {
  background: transparent;
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
  margin-left: auto;
}

.btn-danger:hover:not(:disabled) {
  background: var(--color-danger);
  color: #fff;
}
</style>
