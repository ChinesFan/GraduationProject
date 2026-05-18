<template>
  <div class="page app-shell">
    <section class="hero glass-card">
      <div>
        <div class="hero-tag">Task Detail</div>
        <h1>任务详情与产物预览</h1>
        <p>实时查看当前阶段、处理进度和最终生成的视频与 JSON 摘要结果。</p>
      </div>
      <button class="secondary-button" @click="loadAll">刷新</button>
    </section>

    <div v-if="loading" class="panel glass-card">加载中...</div>
    <div v-else-if="error" class="panel glass-card status-message error">{{ error }}</div>

    <template v-else>
      <section class="summary-grid">
        <div class="overview glass-card">
          <div class="overview-head">
            <div>
              <div class="card-tag">运行状态</div>
              <h2>任务 #{{ task.id }}</h2>
            </div>
            <span class="status-pill" :class="task.status">{{ task.status }}</span>
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
        </div>

        <div class="meta glass-card">
          <div class="meta-item">
            <span>项目 ID</span>
            <strong>{{ task.project_id }}</strong>
          </div>
          <div class="meta-item">
            <span>任务类型</span>
            <strong>{{ task.task_type }}</strong>
          </div>
          <div class="meta-item">
            <span>创建时间</span>
            <strong>{{ formatTime(task.created_at) }}</strong>
          </div>
          <div class="meta-item">
            <span>更新时间</span>
            <strong>{{ formatTime(task.updated_at) }}</strong>
          </div>
        </div>
      </section>

      <section class="card glass-card">
        <div class="section-head">
          <h2>基本信息</h2>
        </div>

        <div class="grid">
          <div class="info-tile full"><strong>输入路径</strong><span>{{ task.input_path }}</span></div>
          <div class="info-tile full"><strong>输出路径</strong><span>{{ task.output_path || "-" }}</span></div>
          <div class="info-tile full"><strong>消息</strong><span>{{ task.message || "-" }}</span></div>
        </div>
      </section>

      <section class="card glass-card" v-if="videoUrl" ref="videoSectionRef">
        <div class="section-head">
          <h2>视频预览</h2>
          <span>优先展示 Stage4 视频，没有则回退到 Stage1 视频</span>
        </div>
        <video :src="videoUrl" controls playsinline class="video-player"></video>
      </section>

      <section class="card glass-card">
        <div class="section-head">
          <h2>产物列表</h2>
          <span>{{ artifacts.length }} 个产物</span>
        </div>

        <div class="table-wrap">
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
                <td>#{{ item.id }}</td>
                <td><span class="artifact-type">{{ getArtifactTypeLabel(item.artifact_type) }}</span></td>
                <td>{{ item.filename }}</td>
                <td class="path-cell">{{ item.file_path }}</td>
                <td>
                  <div class="action-row">
                    <button
                      v-if="isVideoArtifact(item)"
                      class="table-btn table-btn-primary"
                      @click="playArtifactVideo(item.id)"
                    >
                      播放
                    </button>

                    <button
                      v-if="item.artifact_type === 'summary_json'"
                      class="table-btn table-btn-primary"
                      @click="loadJsonArtifact(item.id)"
                    >
                      查看JSON
                    </button>

                    <button class="table-btn" @click="downloadArtifact(item.id)">
                      下载
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card glass-card" v-if="summaryJson">
        <div class="section-head">
          <h2>动作摘要 JSON</h2>
          <span>用于检查 root 状态、关节范围和异常值统计</span>
        </div>
        <pre class="json-box">{{ formattedSummary }}</pre>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
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
const videoSectionRef = ref(null);

let pollTimer = null;

const formattedSummary = computed(() => {
  if (!summaryJson.value) return "";
  return JSON.stringify(summaryJson.value, null, 2);
});

function formatTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function isVideoArtifact(item) {
  return item.artifact_type === "stage1_video" || item.artifact_type === "stage4_video";
}

function getArtifactTypeLabel(type) {
  const labels = {
    human_motion: "人体动作数据",
    robot_motion: "H1机器人动作",
    summary_json: "动作检查摘要",
    stage1_video: "人体动作预览视频",
    stage4_video: "H1仿真视频",
  };

  return labels[type] || type;
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

async function playArtifactVideo(artifactId, shouldScroll = true) {
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

  if (shouldScroll) {
    await nextTick();
    videoSectionRef.value?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
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
    await playArtifactVideo(videoArtifact.id, false);
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
  }, 1000);
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
  display: grid;
  gap: 16px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 28px;
  border-radius: var(--radius-xl);
}

.hero-tag,
.card-tag {
  margin-bottom: 10px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero h1 {
  margin: 0 0 8px;
  font-size: clamp(30px, 4vw, 42px);
}

.hero p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.75;
}

.panel,
.card,
.overview,
.meta {
  padding: 22px;
  border-radius: var(--radius-xl);
}

.summary-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 18px;
}

.overview-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.overview-head h2 {
  margin: 0;
  font-size: 30px;
}

.meta {
  display: grid;
  gap: 14px;
  align-content: start;
}

.meta-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--line);
}

.meta-item span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.meta-item strong {
  display: block;
  word-break: break-word;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head h2 {
  margin: 0;
}

.section-head span {
  color: var(--text-muted);
  font-size: 14px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 14px;
}

.full {
  grid-column: 1 / -1;
}

.info-tile {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid var(--line);
}

.info-tile strong {
  display: block;
  margin-bottom: 8px;
}

.info-tile span {
  color: var(--text-muted);
  word-break: break-word;
  line-height: 1.7;
}

.progress-section {
  margin-top: 6px;
}

.progress-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.progress-bar {
  width: 100%;
  height: 14px;
  background: rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  background: linear-gradient(90deg, var(--accent) 0%, var(--primary) 100%);
  transition: width 0.4s ease;
}

.stage-message {
  margin-top: 10px;
  color: var(--text-muted);
  line-height: 1.7;
}

.video-player {
  width: 100%;
  border-radius: 20px;
  background: #000;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
}

.json-box {
  margin: 0;
  background: #ffffff;
  color: #111827;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.table-wrap {
  overflow-x: auto;
}

.artifact-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.artifact-table th,
.artifact-table td {
  border-bottom: 1px solid rgba(92, 67, 43, 0.1);
  padding: 14px 10px;
  text-align: left;
  vertical-align: middle;
}

.artifact-table th {
  color: var(--text-muted);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.path-cell {
  max-width: 420px;
  word-break: break-all;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 84px;
  padding: 8px 14px;
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

.artifact-type {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--primary-strong);
  font-size: 13px;
  font-weight: 700;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.table-btn {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: var(--text);
  cursor: pointer;
}

.table-btn-primary {
  background: var(--primary-soft);
  border-color: rgba(15, 118, 110, 0.18);
  color: var(--primary-strong);
  font-weight: 700;
}

@media (max-width: 960px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero,
  .panel,
  .card,
  .overview,
  .meta {
    padding: 20px 18px;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-top,
  .section-head,
  .overview-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
