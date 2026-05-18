<template>
  <div>
    <AppNav v-if="showNav" />
    <router-view />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppNav from "./components/AppNav.vue";

const route = useRoute();
const showNav = computed(() => !["login", "register"].includes(route.name));
</script>

<style>
:root {
  color-scheme: light;
  --bg: #f4efe7;
  --bg-soft: #fbf8f3;
  --surface: rgba(255, 252, 247, 0.78);
  --surface-strong: #fffdf8;
  --surface-dark: #1f2937;
  --line: rgba(92, 67, 43, 0.14);
  --line-strong: rgba(92, 67, 43, 0.24);
  --text: #1f2937;
  --text-muted: #6b7280;
  --primary: #0f766e;
  --primary-strong: #115e59;
  --primary-soft: rgba(15, 118, 110, 0.12);
  --accent: #c2410c;
  --danger: #b91c1c;
  --success: #15803d;
  --shadow-lg: 0 24px 60px rgba(76, 58, 40, 0.14);
  --shadow-md: 0 14px 34px rgba(76, 58, 40, 0.1);
  --radius-xl: 28px;
  --radius-lg: 20px;
  --radius-md: 14px;
  --content-width: 1200px;
}

html {
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(194, 65, 12, 0.12), transparent 28%),
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.14), transparent 26%),
    linear-gradient(180deg, #f8f3eb 0%, #f2ede5 48%, #efe7dd 100%);
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: transparent;
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

* {
  box-sizing: border-box;
}

button,
input,
textarea,
select {
  font: inherit;
}

a {
  text-decoration: none;
  color: inherit;
}

#app {
  min-height: 100vh;
}

::selection {
  background: rgba(15, 118, 110, 0.18);
}

.app-shell {
  max-width: var(--content-width);
  margin: 0 auto;
  padding: 32px 20px 48px;
}

.glass-card {
  background: var(--surface);
  border: 1px solid var(--line);
  backdrop-filter: blur(14px);
  box-shadow: var(--shadow-md);
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 46px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-strong) 100%);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  box-shadow: 0 10px 24px rgba(15, 118, 110, 0.24);
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(15, 118, 110, 0.28);
}

.primary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--line-strong);
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.secondary-button:hover {
  background: rgba(255, 255, 255, 0.92);
  transform: translateY(-1px);
}

.status-message {
  padding: 12px 14px;
  border-radius: 14px;
  font-size: 14px;
}

.status-message.error {
  background: rgba(185, 28, 28, 0.08);
  border: 1px solid rgba(185, 28, 28, 0.18);
  color: var(--danger);
}

.status-message.success {
  background: rgba(21, 128, 61, 0.08);
  border: 1px solid rgba(21, 128, 61, 0.18);
  color: var(--success);
}

@media (max-width: 768px) {
  .app-shell {
    padding: 22px 14px 36px;
  }
}
</style>
