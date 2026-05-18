<template>
  <div class="page app-shell">
    <section class="register-layout">
      <div class="intro">
        <div class="intro-chip">H1 Visual Imitation System</div>
        <h1>创建账号后开始管理视频模仿任务</h1>
        <p>
          新账号可用于提交单目视频、追踪四阶段处理进度，并在网页中查看 H1 机器人仿真结果。
        </p>

        <div class="feature-list">
          <div class="feature-item">
            <span class="dot"></span>
            <span>账号注册后可直接登录系统</span>
          </div>
          <div class="feature-item">
            <span class="dot"></span>
            <span>任务进度、阶段日志与结果文件统一展示</span>
          </div>
          <div class="feature-item">
            <span class="dot"></span>
            <span>适配演示场景的仿真视频预览入口</span>
          </div>
        </div>
      </div>

      <div class="card glass-card">
        <div class="card-head">
          <div class="card-tag">新账号</div>
          <h2>注册系统</h2>
          <p>填写用户名、邮箱和密码，注册成功后会自动跳转到登录页。</p>
        </div>

        <div class="form-item">
          <label>用户名</label>
          <input v-model.trim="username" placeholder="请输入用户名" autocomplete="username" />
        </div>

        <div class="form-item">
          <label>邮箱</label>
          <input v-model.trim="email" type="email" placeholder="请输入邮箱" autocomplete="email" />
        </div>

        <div class="form-item">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" autocomplete="new-password" />
        </div>

        <div class="form-item">
          <label>确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            autocomplete="new-password"
          />
        </div>

        <button class="primary-button submit-btn" :disabled="loading" @click="register">
          {{ loading ? "注册中..." : "创建账号" }}
        </button>

        <div class="switch-entry">
          <span>已有账号？</span>
          <router-link to="/login">返回登录</router-link>
        </div>

        <div v-if="error" class="status-message error">{{ error }}</div>
        <div v-if="message" class="status-message success">{{ message }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { API_BASE } from "@/utils/api";

const router = useRouter();
const username = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");
const message = ref("");

function validateForm() {
  if (!username.value || !email.value || !password.value || !confirmPassword.value) {
    throw new Error("请完整填写注册信息");
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    throw new Error("请输入有效的邮箱地址");
  }

  if (password.value.length < 6) {
    throw new Error("密码长度至少为 6 位");
  }

  if (password.value !== confirmPassword.value) {
    throw new Error("两次输入的密码不一致");
  }
}

async function register() {
  try {
    loading.value = true;
    error.value = "";
    message.value = "";
    validateForm();

    const resp = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: username.value,
        email: email.value,
        password: password.value,
      }),
    });

    const data = await resp.json();

    if (!resp.ok || data.code !== 0) {
      throw new Error(data.message || "注册失败");
    }

    message.value = "注册成功，正在跳转到登录页...";
    setTimeout(() => {
      router.push("/login");
    }, 700);
  } catch (e) {
    error.value = e?.message || "注册失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  min-height: calc(100vh - 110px);
  display: grid;
  align-items: center;
}

.register-layout {
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(320px, 460px);
  gap: 28px;
  align-items: center;
}

.intro {
  padding: 24px 4px;
}

.intro-chip {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid var(--line);
  color: var(--primary-strong);
  font-weight: 700;
  font-size: 13px;
}

.intro h1 {
  margin: 18px 0 14px;
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.05;
}

.intro p {
  max-width: 620px;
  margin: 0 0 24px;
  color: var(--text-muted);
  font-size: 17px;
  line-height: 1.75;
}

.feature-list {
  display: grid;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  font-weight: 600;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);
  box-shadow: 0 0 0 6px rgba(15, 118, 110, 0.08);
}

.card {
  padding: 30px;
  border-radius: var(--radius-xl);
  animation: card-in 0.45s ease;
}

.card-head {
  margin-bottom: 22px;
}

.card-tag {
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 10px;
}

.card-head h2 {
  margin: 0 0 8px;
  font-size: 30px;
}

.card-head p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.form-item {
  margin-bottom: 18px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 700;
}

input {
  width: 100%;
  min-height: 50px;
  padding: 0 14px;
  border: 1px solid var(--line-strong);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.84);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

input:focus {
  outline: none;
  border-color: rgba(15, 118, 110, 0.44);
  box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
  background: #fff;
}

.submit-btn {
  width: 100%;
}

.switch-entry {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 14px;
}

.switch-entry a {
  color: var(--primary-strong);
  font-weight: 800;
}

.status-message {
  margin-top: 14px;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .register-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page {
    min-height: auto;
  }

  .card {
    padding: 22px 18px;
  }

  .intro h1 {
    font-size: 34px;
  }
}
</style>
