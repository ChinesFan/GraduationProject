<template>
  <div class="page">
    <div class="header">
      <h1>任务列表</h1>
      <router-link class="btn" to="/tasks/create">新建任务</router-link>
    </div>

    <div v-if="loading" class="card">加载中...</div>
    <div v-else-if="error" class="card error">{{ error }}</div>

    <div v-else class="card">
      <table class="task-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>项目ID</th>
            <th>类型</th>
            <th>状态</th>
            <th>输入</th>
            <th>输出</th>
            <th>更新时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in tasks" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.project_id }}</td>
            <td>{{ item.task_type }}</td>
            <td>{{ item.status }}</td>
            <td class="path-cell">{{ item.input_path }}</td>
            <td class="path-cell">{{ item.output_path }}</td>
            <td>{{ item.updated_at }}</td>
            <td>
              <router-link class="link-btn" :to="`/tasks/${item.id}`">查看详情</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { API_BASE, authHeaders } from "@/utils/api";

const loading = ref(true);
const error = ref("");
const tasks = ref([]);

async function fetchTasks() {
  try {
    loading.value = true;
    error.value = "";

    const resp = await fetch(`${API_BASE}/api/tasks`, {
      headers: authHeaders(),
    });

    const data = await resp.json();

    if (!resp.ok || data.code !== 0) {
      throw new Error(data.message || "获取任务列表失败");
    }

    tasks.value = data.data || [];
  } catch (e) {
    error.value = e?.message || "获取任务列表失败";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchTasks);
</script>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card {
  background: white;
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.error {
  color: #dc2626;
}
.btn, .link-btn {
  display: inline-block;
  background: #2563eb;
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
}
.task-table {
  width: 100%;
  border-collapse: collapse;
}
.task-table th,
.task-table td {
  border-bottom: 1px solid #eee;
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
}
.path-cell {
  max-width: 260px;
  word-break: break-all;
}
</style>
