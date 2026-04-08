<template>
  <div class="page">
    <div class="header">
      <h1>任务详情</h1>
      <button class="btn" @click="loadAll">刷新</button>
    </div>

    <div v-if="loading" class="card">加载中...</div>
    <div v-else-if="error" class="card error">{{ error }}</div>

    <template v-else>
      <section class="card">
        <h2>基本信息</h2>
        <div class="grid">
          <div><strong>任务ID：</strong>{{ task.id }}</div>
          <div><strong>项目ID：</strong>{{ task.project_id }}</div>
          <div><strong>任务类型：</strong>{{ task.task_type }}</div>
          <div><strong>状态：</strong>{{ task.status }}</div>
          <div class="full"><strong>输入路径：</strong>{{ task.input_path }}</div>
          <div class="full"><strong>输出路径：</strong>{{ task.output_path || "-" }}</div>
          <div class="full"><strong>消息：</strong>{{ task.message || "-" }}</div>
          <div><strong>创建时间：</strong>{{ task.created_at }}</div>
          <div><strong>更新时间：</strong>{{ task.updated_at }}</div>
        </div>

        <div class="progress-section">
          <div class="progress-top">
            <span><strong>当前阶段：</strong>{{ task.current_stage || "-" }}</span>
            <span><strong>进度：</strong>{{ task.progress ?? 0 }}%</span>
          </div>

          <div class="progress-bar">
            <div class="progress-inner" :style="{ width: `${task.progress || 0}%` }"></div>
          </div>

          <div class="stage-message">
            {{ task.stage_message || "等待任务开始" }}
          </div>
        </div>
      </section>

      <section class="card" v-if="videoUrl">
        <h2>视频预览</h2>
        <video :src="videoUrl" controls playsinline class="video-player"></video>
      </section>

      <section class="card" v-if="summaryJson">
        <h2>动作摘要 JSON</h2>
        <pre class="json-box">{{ formattedSummary }}</pre>
      </section>

      <section class="card">
        <h2>产物列表</h2>
        <table class="artifact-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>类型</th>
              <th>文件名</th>
              <th>路径</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in artifacts" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.artifact_type }}</td>
              <td>{{ item.filename }}</td>
              <td class="path-cell">{{ item.file_path }}</td>
              <td>
                <button
                  v-if="isVideoArtifact(item)"
                  class="btn small"
                  @click="playArtifactVideo(item.id)"
                >
                  播放
                </button>

                <button
                  v-if="item.artifact_type === 'summary_json'"
                  class="btn small"
                  @click="loadJsonArtifact(item.id)"
                >
                  查看JSON
                </button>

                <button class="btn small secondary" @click="downloadArtifact(item.id)">
                  下载
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { API_BASE, authHeaders } from "@/utils/api";

const route = useRoute();
const taskId = route.params.id;

const loading = ref(true);
const error = ref("");
const task = ref({});
const artifacts = ref([]);
const summaryJson = ref(null);
const videoUrl = ref("");

let pollTimer = null;

const formattedSummary = computed(() => {
  if (!summaryJson.value) return "";
  return JSON.stringify(summaryJson.value, null, 2);
});

function isVideoArtifact(item) {
  return item.artifact_type === "stage1_video" || item.artifact_type === "stage4_video";
}

function cleanupVideoUrl() {
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value);
    videoUrl.value = "";
  }
}

async function fetchTask() {
  const resp = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
    headers: authHeaders(),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`获取任务详情失败: ${resp.status} ${text}`);
  }

  const data = await resp.json();
  task.value = data.data;
}

async function fetchArtifacts() {
  const resp = await fetch(`${API_BASE}/api/tasks/${taskId}/artifacts`, {
    headers: authHeaders(),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`获取产物列表失败: ${resp.status} ${text}`);
  }

  const data = await resp.json();
  artifacts.value = data.data || [];
}

async function playArtifactVideo(artifactId) {
  cleanupVideoUrl();

  const resp = await fetch(`${API_BASE}/api/tasks/artifacts/${artifactId}/preview`, {
    headers: authHeaders(),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`加载视频失败: ${resp.status} ${text}`);
  }

  const blob = await resp.blob();
  videoUrl.value = URL.createObjectURL(blob);
}

async function loadJsonArtifact(artifactId) {
  const resp = await fetch(`${API_BASE}/api/tasks/artifacts/${artifactId}/content`, {
    headers: authHeaders(),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`加载JSON失败: ${resp.status} ${text}`);
  }

  const data = await resp.json();
  summaryJson.value = data.data;
}

async function downloadArtifact(artifactId) {
  const resp = await fetch(`${API_BASE}/api/tasks/artifacts/${artifactId}/download`, {
    headers: authHeaders(),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`下载失败: ${resp.status} ${text}`);
  }

  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
}

async function autoLoadPreviewArtifacts() {
  const videoArtifact =
    artifacts.value.find((x) => x.artifact_type === "stage4_video") ||
    artifacts.value.find((x) => x.artifact_type === "stage1_video");

  if (videoArtifact) {
    await playArtifactVideo(videoArtifact.id);
  }

  const jsonArtifact = artifacts.value.find((x) => x.artifact_type === "summary_json");
  if (jsonArtifact) {
    await loadJsonArtifact(jsonArtifact.id);
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function startPolling() {
  stopPolling();

  pollTimer = setInterval(async () => {
    try {
      await fetchTask();
      await fetchArtifacts();

      if (task.value.status === "success" || task.value.status === "failed") {
        stopPolling();
        await autoLoadPreviewArtifacts();
      }
    } catch (e) {
      console.error("poll failed", e);
    }
  }, 2000);
}

async function loadAll() {
  try {
    loading.value = true;
    error.value = "";

    await fetchTask();
    await fetchArtifacts();

    if (task.value.status === "success" || task.value.status === "failed") {
      await autoLoadPreviewArtifacts();
    } else {
      startPolling();
    }
  } catch (e) {
    error.value = e?.message || "加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadAll);

onBeforeUnmount(() => {
  stopPolling();
  cleanupVideoUrl();
});
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
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}
.error {
  color: #c62828;
}
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 12px 16px;
}
.full {
  grid-column: 1 / -1;
}
.progress-section {
  margin-top: 16px;
}
.progress-top {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.progress-bar {
  width: 100%;
  height: 14px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}
.progress-inner {
  height: 100%;
  background: #2563eb;
  transition: width 0.4s ease;
}
.stage-message {
  margin-top: 8px;
  color: #475569;
}
.video-player {
  width: 100%;
  max-width: 960px;
  border-radius: 10px;
  background: #000;
}
.json-box {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 10px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.artifact-table {
  width: 100%;
  border-collapse: collapse;
}
.artifact-table th,
.artifact-table td {
  border-bottom: 1px solid #eee;
  padding: 10px 8px;
  text-align: left;
  vertical-align: top;
}
.path-cell {
  max-width: 420px;
  word-break: break-all;
}
.btn {
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  background: #2563eb;
  color: white;
}
.btn.small {
  padding: 6px 10px;
  margin-right: 8px;
  margin-bottom: 4px;
}
.btn.secondary {
  background: #475569;
}
.btn:hover {
  opacity: 0.92;
}
</style>