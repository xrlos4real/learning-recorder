<template>
  <div id="app">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from "./components/NavBar.vue";
</script>

<style>
/* ── CSS Variables ── */
:root {
  --color-primary: #4f46e5;
  --color-primary-hover: #4338ca;
  --color-primary-light: #eef2ff;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-text: #1e293b;
  --color-text-secondary: #64748b;
  --color-border: #e2e8f0;
  --color-danger: #ef4444;
  --color-success: #22c55e;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  --max-width: 960px;
}

/* ── Global Reset ── */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a {
  color: inherit;
  text-decoration: none;
}

.main-content {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 24px 16px 64px;
}
</style>
