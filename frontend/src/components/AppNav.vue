<template>
  <header class="nav-wrap">
    <div class="nav glass-card">
      <div class="brand-block">
        <div class="eyebrow">Visual Imitation Pipeline</div>
        <router-link class="brand" to="/tasks">H1 GMR Project</router-link>
      </div>

      <nav class="links">
        <router-link to="/tasks">任务列表</router-link>
        <router-link to="/tasks/create">新建任务</router-link>
        <template v-if="isLoggedIn">
          <span class="user-badge">{{ displayName }}</span>
          <button class="logout-btn" @click="logout">退出</button>
        </template>
        <router-link v-else to="/login">登录</router-link>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from "vue";

const token = ref(localStorage.getItem("token") || "");
const storedUser = ref(localStorage.getItem("user") || "");

const user = computed(() => {
  if (!storedUser.value) {
    return null;
  }

  try {
    return JSON.parse(storedUser.value);
  } catch {
    return null;
  }
});

const isLoggedIn = computed(() => Boolean(token.value));
const displayName = computed(() => user.value?.username || "已登录");

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/login";
}
</script>

<style scoped>
.nav-wrap {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 18px 20px 0;
}

.nav {
  max-width: var(--content-width);
  margin: 0 auto;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border-radius: 24px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.eyebrow {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.brand {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.links a {
  padding: 10px 14px;
  border-radius: 999px;
  color: var(--text-muted);
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.links a:hover {
  background: rgba(255, 255, 255, 0.7);
  color: var(--text);
  transform: translateY(-1px);
}

.links a.router-link-active {
  background: var(--primary-soft);
  color: var(--primary-strong);
  font-weight: 700;
}

.user-badge {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  max-width: 180px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--primary-strong);
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(194, 65, 12, 0.18);
  background: rgba(194, 65, 12, 0.08);
  color: var(--accent);
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.logout-btn:hover {
  background: rgba(194, 65, 12, 0.12);
  transform: translateY(-1px);
}

@media (max-width: 900px) {
  .nav {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .nav-wrap {
    padding: 14px 14px 0;
  }

  .brand {
    font-size: 20px;
  }
}
</style>
