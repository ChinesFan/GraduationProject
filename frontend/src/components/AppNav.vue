<template>
  <div class="nav">
    <div class="nav-inner">
      <div class="brand">H1 GMR Project</div>

      <div class="links">
        <router-link to="/tasks">任务列表</router-link>
        <router-link to="/tasks/create">新建任务</router-link>
        <router-link to="/login">登录</router-link>
        <button class="logout-btn" @click="logout">退出</button>
      </div>
    </div>
  </div>
</template>

<script setup>
function logout() {
  localStorage.removeItem("token");
  window.location.href = "/login";
}
</script>

<style scoped>
.nav {
  background: #111827;
  color: white;
  padding: 14px 0;
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  font-weight: bold;
  font-size: 20px;
}
.links {
  display: flex;
  gap: 14px;
  align-items: center;
}
.links a {
  color: white;
}
.logout-btn {
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
}
</style>
