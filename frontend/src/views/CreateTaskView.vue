<template>
  <div class="page">
    <div class="card">
      <h1>新建流水线任务</h1>

      <div class="form-item">
        <label>项目 ID</label>
        <input v-model="projectId" type="number" placeholder="例如 1" />
      </div>

      <div class="form-item">
        <label>选择视频</label>
        <input type="file" accept="video/*" @change="onFileChange" />
      </div>

      <button class="btn" :disabled="loading" @click="submitTask">
        {{ loading ? "提交中..." : "上传并运行流水线" }}
      </button>

      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="message" class="success">{{ message }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { API_BASE, authHeaders } from "@/utils/api";

const projectId = ref(1);
const file = ref(null);
const loading = ref(false);
const error = ref("");
const message = ref("");

function onFileChange(event) {
  const files = event.target.files;
  file.value = files && files.length ? files[0] : null;
}

async function submitTask() {
  try {
    loading.value = true;
    error.value = "";
    message.value = "";

    if (!projectId.value) {
      throw new Error("project_id 必填");
    }

    if (!file.value) {
      throw new Error("请选择视频文件");
    }

    const formData = new FormData();
    formData.append("project_id", String(projectId.value));
    formData.append("file", file.value);

    const resp = await fetch(`${API_BASE}/api/tasks/run_pipeline`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });

    const data = await resp.json();

    if (!resp.ok || data.code !== 0) {
      throw new Error(data.message || data.error || "创建任务失败");
    }

    message.value = "文件提交成功，流水线已开始执行，正在跳转...";
    const taskId = data.data.task_id;

    setTimeout(() => {
      window.location.href = `/tasks/${taskId}`;
    }, 500);
  } catch (e) {
    error.value = e?.message || "创建任务失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px;
}
.card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.form-item {
  margin-bottom: 16px;
}
label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}
input[type="number"],
input[type="file"] {
  width: 100%;
  padding: 10px 12px;
}
.btn {
  border: none;
  background: #2563eb;
  color: white;
  padding: 12px 18px;
  border-radius: 8px;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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