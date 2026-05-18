<template>
  <div class="page app-shell">
    <section class="hero glass-card">
      <div>
        <div class="hero-tag">Task Dashboard</div>
        <h1>任务列表与流水线运行概览</h1>
        <p>统一查看上传任务、阶段进度与仿真结果入口，适合答辩演示和开发排查时快速浏览。</p>
      </div>
      <router-link class="primary-button" to="/tasks/create">新建任务</router-link>
    </section>

    <section class="stats" v-if="!loading && !error">
      <div class="stat-card glass-card">
        <span>任务总数</span>
        <strong>{{ tasks.length }}</strong>
      </div>
      <div class="stat-card glass-card">
        <span>运行中</span>
        <strong>{{ runningCount }}</strong>
      </div>
      <div class="stat-card glass-card">
        <span>已完成</span>
        <strong>{{ successCount }}</strong>
      </div>
      <div class="stat-card glass-card">
        <span>失败</span>
        <strong>{{ failedCount }}</strong>
      </div>
    </section>

    <div v-if="loading" class="panel glass-card">加载中...</div>
    <div v-else-if="error" class="panel glass-card status-message error">{{ error }}</div>

    <section v-else class="panel glass-card">
      <div class="panel-head">
        <h2>最近任务</h2>
        <span>{{ tasks.length }} 条记录</span>
      </div>

      <div v-if="tasks.length === 0" class="empty-state">
        <h3>还没有任务</h3>
        <p>可以先创建一个视频模仿任务，系统会自动开始完整流水线处理。</p>
      </div>

      <div v-else class="table-wrap">
        <table class="task-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>项目</th>
              <th>类型</th>
              <th>状态</th>
              <th>阶段</th>
              <th>进度</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in tasks" :key="item.id">
              <td>#{{ item.id }}</td>
              <td>{{ item.project_id }}</td>
              <td>{{ item.task_type }}</td>
              <td>
                <span class="status-pill" :class="item.status">{{ item.status }}</span>
              </td>
              <td>
                <div class="stage-cell">
                  <strong>{{ item.current_stage || "-" }}</strong>
                  <span>{{ item.stage_message || "-" }}</span>
                </div>
              </td>
              <td>
                <div class="mini-progress">
                  <div class="mini-progress-bar">
                    <div class="mini-progress-inner" :style="{ width: `${item.progress || 0}%` }"></div>
                  </div>
                  <span>{{ item.progress ?? 0 }}%</span>
                </div>
              </td>
              <td>{{ formatTime(item.updated_at) }}</td>
              <td>
                <router-link class="detail-link" :to="`/tasks/${item.id}`">查看详情</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { API_BASE, authHeaders } from "@/utils/api";

const loading = ref(true);
const error = ref("");
const tasks = ref([]);

const runningCount = computed(() => tasks.value.filter((item) => item.status === "running").length);
const successCount = computed(() => tasks.value.filter((item) => item.status === "success").length);
const failedCount = computed(() => tasks.value.filter((item) => item.status === "failed").length);

function formatTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

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
  display: grid;
  gap: 22px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 28px;
  border-radius: var(--radius-xl);
}

.hero-tag {
  margin-bottom: 10px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero h1 {
  margin: 0 0 8px;
  font-size: clamp(30px, 4vw, 44px);
}

.hero p {
  margin: 0;
  max-width: 760px;
  color: var(--text-muted);
  line-height: 1.75;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card,
.panel {
  padding: 22px;
  border-radius: var(--radius-xl);
}

.stat-card span {
  display: block;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.stat-card strong {
  font-size: 34px;
  color: var(--primary-strong);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-head h2 {
  margin: 0;
}

.panel-head span {
  color: var(--text-muted);
}

.empty-state {
  padding: 24px 4px;
  text-align: center;
}

.empty-state h3 {
  margin-bottom: 8px;
}

.empty-state p {
  margin: 0;
  color: var(--text-muted);
}

.table-wrap {
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.task-table th,
.task-table td {
  border-bottom: 1px solid rgba(92, 67, 43, 0.1);
  padding: 14px 10px;
  text-align: left;
  vertical-align: middle;
}

.task-table th {
  color: var(--text-muted);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.stage-cell strong {
  display: block;
  margin-bottom: 4px;
}

.stage-cell span {
  display: block;
  max-width: 280px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.mini-progress {
  min-width: 140px;
}

.mini-progress span {
  display: inline-block;
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.mini-progress-bar {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.08);
}

.mini-progress-inner {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent) 0%, var(--primary) 100%);
  transition: width 0.8s ease;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 74px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.14);
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
  text-transform: capitalize;
}

.status-pill.running {
  background: rgba(194, 65, 12, 0.1);
  color: var(--accent);
}

.status-pill.success {
  background: rgba(21, 128, 61, 0.1);
  color: var(--success);
}

.status-pill.failed {
  background: rgba(185, 28, 28, 0.1);
  color: var(--danger);
}

.status-pill.pending {
  background: rgba(15, 118, 110, 0.1);
  color: var(--primary-strong);
}

.detail-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--primary-strong);
  font-weight: 700;
}

@media (max-width: 960px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero,
  .stat-card,
  .panel {
    padding: 20px 18px;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats {
    grid-template-columns: 1fr;
  }
}
</style>
