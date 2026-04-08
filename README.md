# GraduationProject

基于视觉模仿学习的人形机器人动作生成与仿真控制系统设计与实现。

## 项目简介

本项目实现了从单目视频输入到人形机器人动作生成与仿真展示的完整流程。系统首先利用人体三维动作恢复方法从视频中提取人体运动信息，再通过动作重定向技术将人体动作映射到 Unitree H1 人形机器人关节空间，随后对生成的机器人动作进行检查与分析，最后在 PyBullet 仿真环境中完成动作播放与视频导出。

在工程实现上，项目采用 Flask + MySQL 构建后端服务，Vue + Vite 实现前端展示，支持用户上传视频、创建任务、查看任务进度，并在网页中直接查看机器人仿真结果和动作摘要信息。

## 核心功能

- 单目视频驱动动作生成
- 人体三维动作恢复
- 人体动作到 H1 机器人的动作重定向
- 机器人动作检查与摘要生成
- PyBullet 仿真播放与 MP4 导出
- 前后端一体化任务管理与结果展示

## 技术栈

### 算法与仿真
- Python
- GVHMR
- GMR
- PyBullet
- NumPy
- PyTorch

### 后端
- Flask
- MySQL
- SQLAlchemy
- Flask-Migrate
- JWT

### 前端
- Vue
- Vite

## 项目结构

```text
GraduationProject/
├── app/                        # Flask 后端
│   ├── config.py
│   ├── extensions.py
│   ├── routes/
│   ├── services/
│   └── utils/
├── src/                        # 四阶段核心算法与仿真脚本
│   ├── stage1_human/
│   ├── stage2_retarget/
│   ├── stage3_inspect/
│   └── stage4_sim/
├── frontend/                   # Vue 前端
├── migrations/                 # 数据库迁移文件
├── h1_description/             # H1 机器人描述文件与 mesh
├── run.py                      # 后端启动入口
└── requirements_backend.txt    # 后端依赖
````

## 核心流程

系统整体流程分为四个阶段：

### Stage 1：人体动作提取

基于 GVHMR 从单目视频中恢复人体三维动作。

* 输入：原始视频
* 输出：`hmr4d_results.pt`

### Stage 2：动作重定向到 H1

基于 GMR 将人体动作映射到 Unitree H1 机器人关节空间。

* 输入：Stage 1 输出的人体动作结果
* 输出：`*_h1.pkl`

### Stage 3：机器人动作检查与摘要生成

对重定向后的机器人动作进行合理性检查，并生成摘要 JSON。

检查内容包括：

* fps
* 帧数
* root_pos
* root_rot
* dof_pos
* NaN / Inf 检查
* 四元数归一化情况
* DOF 范围统计

### Stage 4：仿真播放与视频导出

在 PyBullet 中加载 H1 机器人动作，进行播放并导出 MP4 视频。

* 输出：`*_stage4.mp4`

## 系统功能说明

### 后端功能

* 用户登录认证
* 视频任务创建
* 任务状态查询
* 流水线后台执行
* 产物列表、下载、预览、内容读取

### 前端功能

* 登录页面
* 任务列表页面
* 创建任务页面
* 任务详情页面
* 进度条实时刷新
* 视频结果展示
* JSON 摘要展示

## 启动方式

### 1. 启动后端

进入项目目录并激活虚拟环境：

```bash
cd ~/h1_gmr_project
source basketball/bin/activate
python run.py
```

### 2. 启动前端

新开一个终端：

```bash
cd ~/h1_gmr_project/frontend
npm install
npm run dev
```

## 四阶段脚本运行示例

### Stage 1

```bash
python src/stage1_human/run_gvhmr.py
```

### Stage 2

```bash
python src/stage2_retarget/run_gmr_h1.py
```

### Stage 3

```bash
python src/stage3_inspect/inspect_robot_motion.py
```

### Stage 4

```bash
python src/stage4_sim/export_h1_video.py
```

或播放动作：

```bash
python src/stage4_sim/play_h1_motion.py
```

## 任务执行机制

系统当前采用“后台线程 + 数据库更新 + 前端轮询”的方式运行：

1. 用户上传视频
2. 后端立即创建 task 并返回 `task_id`
3. 后端后台线程执行 Stage1 ~ Stage4
4. 每完成一个阶段更新：

   * `progress`
   * `current_stage`
   * `stage_message`
5. 前端任务详情页每 2 秒轮询一次任务状态
6. 完成后显示视频和摘要结果

## 进度设计

推荐进度节点如下：

* 上传成功：10%
* Stage1 开始：15%
* Stage1 完成：35%
* Stage2 开始：40%
* Stage2 完成：60%
* Stage3 开始：65%
* Stage3 完成：75%
* Stage4 开始：80%
* Stage4 完成：95%
* 全部完成：100%

`current_stage` 建议值：

* `uploaded`
* `stage1`
* `stage2`
* `stage3`
* `stage4`
* `completed`
* `failed`

## 已实现接口

### 认证

* `POST /api/auth/login`

### 任务

* `GET /api/tasks`
* `GET /api/tasks/<id>`
* `POST /api/tasks/run_pipeline`

### 产物

* `GET /api/tasks/<id>/artifacts`
* `GET /api/tasks/artifacts/<artifact_id>/download`
* `GET /api/tasks/artifacts/<artifact_id>/preview`
* `GET /api/tasks/artifacts/<artifact_id>/content`

## 注意事项

1. 本仓库未包含模型权重、checkpoint、输出视频、上传数据和虚拟环境。
2. `third_party` 相关依赖仓库及模型文件需自行准备。
3. 若需完整运行 Stage1 / Stage2，请确保 GVHMR、GMR 及相关依赖已正确安装。
4. MySQL 数据库需提前配置完成。
5. 开发阶段建议适当延长 JWT 有效期，避免频繁重新登录。

## Git 管理说明

为避免仓库过大，以下内容默认不上传：

* 模型权重
* checkpoint
* `.pt / .pth / .ckpt / .pkl`
* 视频输出文件
* 上传文件
* 虚拟环境
* `frontend/node_modules`
* `third_party` 大型依赖与输出文件

## 项目总结

本项目已经完成了从单目视频输入，到人体动作恢复、机器人动作重定向、动作检查、仿真视频导出，再到 Web 前后端展示的完整闭环。用户可以登录系统、上传视频、查看任务进度，并直接在网页中查看机器人模仿结果。
