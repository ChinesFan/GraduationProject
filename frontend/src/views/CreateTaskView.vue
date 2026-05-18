<template>
  <div class="page app-shell">
    <section class="hero glass-card">
      <div>
        <div class="hero-tag">Create Pipeline Task</div>
        <h1>上传视频并启动 H1 动作生成流程</h1>
        <p>
          系统会自动串联 Stage1 到 Stage4，完成人体动作恢复、机器人重定向、动作检查和仿真视频导出。
        </p>
      </div>
      <div class="hero-side">
        <div class="metric">
          <strong>4</strong>
          <span>处理阶段</span>
        </div>
        <div class="metric">
          <strong>1</strong>
          <span>单目视频输入</span>
        </div>
      </div>
    </section>

    <section class="layout">
      <div class="card glass-card">
        <div class="section-head">
          <h2>任务参数</h2>
          <p>填写项目编号并上传视频文件，提交后会自动跳转到任务详情页。</p>
        </div>

        <div class="form-item">
          <label>项目 ID</label>
          <input v-model="projectId" type="number" placeholder="例如 1" />
        </div>

        <div class="form-item">
          <label>选择视频</label>
          <label class="upload-box">
            <input type="file" accept="video/*" @change="onFileChange" />
            <span class="upload-title">{{ file ? file.name : "点击选择视频文件" }}</span>
            <span class="upload-tip">支持常见 mp4 等视频格式，建议上传清晰的人体动作视频。</span>
          </label>
        </div>

        <button class="primary-button submit-btn" :disabled="loading" @click="submitTask">
          {{ loading ? "提交中..." : "上传并运行流水线" }}
        </button>

        <div v-if="error" class="status-message error">{{ error }}</div>
        <div v-if="message" class="status-message success">{{ message }}</div>
      </div>

      <aside class="tips glass-card">
        <h3>流程说明</h3>
        <div class="tip-item">
          <strong>Stage1</strong>
          <span>GVHMR 从单目视频恢复人体 3D 动作。</span>
        </div>
        <div class="tip-item">
          <strong>Stage2</strong>
          <span>GMR 将人体动作映射到 Unitree H1 关节空间。</span>
        </div>
        <div class="tip-item">
          <strong>Stage3</strong>
          <span>检查 fps、关节范围、root 状态与异常值。</span>
        </div>
        <div class="tip-item">
          <strong>Stage4</strong>
          <span>在 PyBullet 中播放并导出最终仿真 mp4。</span>
        </div>
      </aside>
    </section>
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
  display: grid;
  gap: 22px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
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
  margin: 0 0 10px;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.1;
}

.hero p {
  max-width: 740px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.75;
}

.hero-side {
  display: flex;
  gap: 14px;
}

.metric {
  min-width: 118px;
  padding: 18px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--line);
  text-align: center;
}

.metric strong {
  display: block;
  font-size: 28px;
  color: var(--primary-strong);
}

.metric span {
  color: var(--text-muted);
  font-size: 13px;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(280px, 0.9fr);
  gap: 22px;
}

.card,
.tips {
  padding: 26px;
  border-radius: var(--radius-xl);
}

.section-head {
  margin-bottom: 20px;
}

.section-head h2,
.tips h3 {
  margin: 0 0 8px;
  font-size: 28px;
}

.section-head p {
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

input[type="number"] {
  width: 100%;
  min-height: 52px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid var(--line-strong);
  background: rgba(255, 255, 255, 0.84);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

input[type="number"]:focus {
  outline: none;
  border-color: rgba(15, 118, 110, 0.44);
  box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
}

.upload-box {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 18px;
  border: 1.5px dashed rgba(15, 118, 110, 0.34);
  background: linear-gradient(180deg, rgba(15, 118, 110, 0.05), rgba(255, 255, 255, 0.74));
  cursor: pointer;
}

.upload-box input[type="file"] {
  display: none;
}

.upload-title {
  font-weight: 700;
  color: var(--text);
}

.upload-tip {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.6;
}

.submit-btn {
  width: 100%;
}

.status-message {
  margin-top: 14px;
}

.tips {
  align-self: start;
}

.tip-item + .tip-item {
  margin-top: 16px;
}

.tip-item strong {
  display: inline-flex;
  padding: 6px 10px;
  margin-bottom: 8px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary-strong);
  font-size: 13px;
}

.tip-item span {
  display: block;
  color: var(--text-muted);
  line-height: 1.7;
}

@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .hero,
  .card,
  .tips {
    padding: 20px 18px;
  }

  .hero-side {
    width: 100%;
  }

  .metric {
    flex: 1;
  }
}
</style>
