<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="brand">📚 学习日志</router-link>
      <div class="nav-links">
        <router-link to="/" exact-active-class="active" class="nav-link">首页</router-link>
        <router-link to="/stats" active-class="active" class="nav-link">统计</router-link>
        <router-link to="/search" active-class="active" class="nav-link">搜索</router-link>
        <router-link to="/editor" active-class="active" class="nav-link nav-btn">✏️ 写日志</router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
</script>

<style scoped>
.navbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
}

.brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: color 0.15s, background 0.15s;
}

.nav-link:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.nav-link.active {
  color: var(--color-primary);
  background: var(--color-primary-light);
  font-weight: 600;
}

.nav-btn {
  background: var(--color-primary);
  color: #fff !important;
  font-weight: 600;
}

.nav-btn:hover {
  background: var(--color-primary-hover) !important;
  color: #fff !important;
}

.nav-btn.active {
  background: var(--color-primary-hover) !important;
  color: #fff !important;
}
</style>
