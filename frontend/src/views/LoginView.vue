<template>
  <div class="page">
    <div class="card">
      <h1>登录</h1>

      <div class="form-item">
        <label>用户名</label>
        <input v-model="username" placeholder="请输入用户名" />
      </div>

      <div class="form-item">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" />
      </div>

      <button class="btn" :disabled="loading" @click="login">
        {{ loading ? "登录中..." : "登录" }}
      </button>

      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="message" class="success">{{ message }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { API_BASE } from "@/utils/api";

const username = ref("admin");
const password = ref("123456");
const loading = ref(false);
const error = ref("");
const message = ref("");

async function login() {
  try {
    loading.value = true;
    error.value = "";
    message.value = "";

    const resp = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    });

    const data = await resp.json();

    if (!resp.ok || data.code !== 0) {
      throw new Error(data.message || "登录失败");
    }

    localStorage.setItem("token", data.data.token);
    message.value = "登录成功，正在跳转...";
    setTimeout(() => {
      window.location.href = "/tasks";
    }, 500);
  } catch (e) {
    error.value = e?.message || "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
}
.card {
  width: 420px;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.form-item {
  margin-bottom: 16px;
}
label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}
input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
}
.btn {
  width: 100%;
  border: none;
  background: #2563eb;
  color: white;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
}
.error {
  color: #dc2626;
  margin-top: 12px;
}
.success {
  color: #16a34a;
  margin-top: 12px;
}
</style>
