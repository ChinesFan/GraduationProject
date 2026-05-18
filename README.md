# H1 GMR Project

基于单目视频的人形机器人动作生成与仿真展示系统。项目把 GVHMR 人体三维动作恢复、GMR 动作重定向、H1 动作检查和 PyBullet 仿真导出串成一条可在网页端提交、追踪和预览的完整流水线。

## 当前能力

- 用户注册、登录和 JWT 鉴权
- 项目与任务数据管理
- 上传视频并后台执行 Stage1 ~ Stage4
- 任务列表、任务详情、阶段进度和错误信息展示
- 产物归档、下载、视频预览和 JSON 摘要读取
- H1 URDF / mesh 本地加载，支持 PyBullet 导出仿真 MP4

## 技术栈

- 后端：Flask、Flask-SQLAlchemy、Flask-Migrate、Flask-JWT-Extended、MySQL
- 前端：Vue 3、Vue Router、Vite
- 算法与仿真：GVHMR、GMR、PyBullet、PyTorch、NumPy、OpenCV、imageio
- 机器人资源：Unitree H1 URDF、MJCF 和 mesh 资源

## 项目结构

```text
h1_gmr_project/
├── app/                         # Flask 后端应用
│   ├── models/                  # User / Project / Task / Artifact
│   ├── routes/                  # auth / project / task API
│   ├── services/                # 流水线编排与业务服务
│   ├── config.py                # MySQL、JWT、上传目录等配置
│   └── extensions.py
├── frontend/                    # Vue + Vite 前端
│   └── src/
│       ├── views/               # 登录、注册、任务列表、创建任务、任务详情
│       ├── router/
│       └── utils/api.js
├── src/
│   ├── common/paths.py          # 项目路径和 third_party 路径
│   ├── stage1_human/            # GVHMR 单目人体动作恢复
│   ├── stage2_retarget/         # GMR -> Unitree H1 重定向
│   ├── stage3_inspect/          # H1 动作检查与摘要 JSON
│   └── stage4_sim/              # PyBullet 播放与 MP4 导出
├── h1_description/              # H1 URDF、MJCF、mesh 和 ROS 包描述
├── migrations/                  # Alembic 数据库迁移
├── data/                        # 运行时生成目录，仓库不保存
├── third_party/                 # GVHMR / GMR / pytorch3d 等外部依赖，仓库不保存
├── run.py                       # 后端启动入口
└── requirements_backend.txt     # 当前 Python 环境依赖参考
```

## 运行前准备

1. 准备 Python 环境。当前后端流水线默认调用项目根目录下的 `basketball/bin/python`，见 `app/services/pipeline_service.py` 和 `src/stage1_human/run_gvhmr.py`。如果使用其他虚拟环境，需要同步修改这两个位置或保持相同路径。
2. 准备 MySQL，并创建数据库，例如 `graduation_project`。
3. 准备外部算法依赖：
   - `third_party/GVHMR`
   - `third_party/GMR`
   - GVHMR / GMR 需要的模型权重、SMPL 资源和 checkpoint
   - 可用的 PyTorch / CUDA / pytorch3d 环境
4. 安装前端依赖。前端要求 Node `^20.19.0 || >=22.12.0`。

后端环境变量可放在项目根目录 `.env`：

```env
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=graduation_project
```

## 模型与权重下载

以下链接按当前项目实际依赖整理。下载时需要遵守各项目自己的 license；其中 SMPL / SMPL-X 需要注册账号后才能下载。

| 资源 | 用途 | 下载 / 来源 |
| --- | --- | --- |
| GVHMR 代码 | Stage1 单目人体动作恢复 | https://github.com/zju3dv/GVHMR |
| GVHMR 官方安装说明 | checkpoint 目录结构参考 | https://github.com/zju3dv/GVHMR/blob/main/docs/INSTALL.md |
| GVHMR 预训练权重合集 | `gvhmr_siga24_release.ckpt`、HMR2、ViTPose、DPVO、YOLO 等 | https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link |
| SMPL | GVHMR 渲染与评估所需人体模型 | https://smpl.is.tue.mpg.de/ |
| SMPL-X | GVHMR 预测 SMPL-X 参数所需人体模型 | https://smpl-x.is.tue.mpg.de/ |
| GMR 代码 | Stage2 人体动作到机器人动作重定向 | https://github.com/YanjieZe/GMR |
| Unitree H1 description | H1 URDF、MJCF、mesh 来源参考 | https://github.com/unitreerobotics/unitree_ros/tree/master/robots/h1_description |
| Unitree robot models | Unitree 官方机器人模型数据集，GitHub 仓库提示后续更新迁移到这里 | https://huggingface.co/datasets/unitreerobotics/unitree_model |

GVHMR 权重建议放在 `third_party/GVHMR/inputs/checkpoints/` 下，目录结构按官方说明组织：

```text
third_party/GVHMR/inputs/checkpoints/
├── body_models/
│   ├── smpl/
│   │   └── SMPL_{GENDER}.pkl
│   └── smplx/
│       └── SMPLX_{GENDER}.npz
├── dpvo/
│   └── dpvo.pth
├── gvhmr/
│   └── gvhmr_siga24_release.ckpt
├── hmr2/
│   └── epoch=10-step=25000.ckpt
├── vitpose/
│   └── vitpose-h-multi-coco.pth
└── yolo/
    └── yolov8x.pt
```

GMR 当前主要需要代码仓库和机器人配置，不需要像 GVHMR 一样单独放置大型 checkpoint。本项目已经带有 `h1_description/`，如果后续替换或更新 H1 机器人模型，可以从 Unitree 官方 `unitree_ros` 的 `robots/h1_description` 同步。

## 启动后端

```bash
cd ~/h1_gmr_project
source basketball/bin/activate
pip install -r requirements_backend.txt
flask --app run.py db upgrade
python run.py
```

后端默认监听 `http://127.0.0.1:5000`，健康检查接口为：

```bash
curl http://127.0.0.1:5000/api/health
```

## 启动前端

```bash
cd ~/h1_gmr_project/frontend
npm install
npm run dev
```

前端 API 地址固定为 `http://127.0.0.1:5000`，配置位于 `frontend/src/utils/api.js`。

## 首次使用流程

1. 打开前端，进入注册页创建账号。
2. 登录后需要先创建一个项目。当前页面只填写项目 ID，还没有项目创建页面，可以先用接口创建：

```bash
curl -X POST http://127.0.0.1:5000/api/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"H1 Demo","description":"demo project"}'
```

3. 进入“新建任务”，填写项目 ID 并上传视频。
4. 系统创建 `full_pipeline` 任务，并在后台线程执行四阶段流程。
5. 在任务详情页查看进度、阶段信息、产物列表、Stage4 仿真视频和 Stage3 摘要 JSON。

登录页默认填入的 `admin / 123456` 只是演示填写项；如果数据库里没有该用户，需要先注册。

## 四阶段流水线

### Stage1：人体动作恢复

入口：`src/stage1_human/run_gvhmr.py`

输入上传视频，调用 `third_party/GVHMR/tools/demo/demo.py` 生成 `hmr4d_results.pt`。当前封装会把结果复制到：

```text
data/human_motion/<stem>_hmr4d_results.pt
```

如果 GVHMR 在最后视频合成阶段返回非零，但核心 `hmr4d_results.pt` 已生成，脚本会继续视为 Stage1 成功。

### Stage2：重定向到 H1

入口：`src/stage2_retarget/run_gmr_h1.py`

调用 `third_party/GMR/scripts/gvhmr_to_robot.py`，将 GVHMR 输出转换为 Unitree H1 机器人动作：

```text
data/robot_motion/<stem>_h1.pkl
```

后端流水线会额外对 pelvis 和上半身做稳定化处理：限制髋 pitch 并将 root 旋转压成 yaw-only，以便 Stage4 预览更稳定。

### Stage3：动作检查

入口：`src/stage3_inspect/inspect_robot_motion.py`

检查 `fps`、`root_pos`、`root_rot`、`dof_pos`、NaN / Inf、四元数范数和每个 DOF 的统计范围，并生成：

```text
data/robot_motion/<stem>_summary.json
```

### Stage4：仿真视频导出

入口：`src/stage4_sim/export_h1_video.py`

使用 `h1_description/urdf/h1.urdf` 和 PyBullet DIRECT 模式逐帧渲染 H1 动作，默认输出：

```text
data/robot_motion/<stem>_stage4.mp4
```

后端流水线当前以 `--fixed_base` 导出，适合网页预览和答辩演示。

## 单独运行脚本

```bash
python -m src.stage1_human.run_gvhmr \
  --video data/uploads/demo.mp4 \
  --output data/human_motion/demo_hmr4d_results.pt

python -m src.stage2_retarget.run_gmr_h1 \
  --input data/human_motion/demo_hmr4d_results.pt \
  --robot unitree_h1 \
  --output data/robot_motion/demo_h1.pkl

python -m src.stage3_inspect.inspect_robot_motion \
  --input data/robot_motion/demo_h1.pkl \
  --save_json data/robot_motion/demo_summary.json

python -m src.stage4_sim.export_h1_video \
  --input data/robot_motion/demo_h1.pkl \
  --output data/robot_motion/demo_stage4.mp4 \
  --fixed_base
```

也可以用 `src/stage4_sim/play_h1_motion.py` 或 `src/stage4_sim/play_h1_motion_gmr.py` 做本地播放调试。

## API 概览

### 基础

- `GET /`
- `GET /api/health`

### 认证

- `POST /api/auth/register`
- `POST /api/auth/login`

### 项目

- `POST /api/projects`
- `GET /api/projects`

### 任务

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/<task_id>`
- `POST /api/tasks/run_pipeline`
- `GET /api/tasks/<task_id>/artifacts`

### 产物

- `GET /api/tasks/artifacts/<artifact_id>/download`
- `GET /api/tasks/artifacts/<artifact_id>/preview`
- `GET /api/tasks/artifacts/<artifact_id>/content`

`/content` 当前只支持 JSON 产物。

## 运行时产物

```text
data/uploads/                 # 原始上传视频
data/human_motion/            # GVHMR 人体动作结果
data/robot_motion/            # H1 pkl、summary json、Stage4 mp4
third_party/GVHMR/outputs/    # GVHMR 自身 demo 输出和可视化视频
```

这些目录下的上传文件、模型输出和大文件不应提交到仓库。

## 注意事项

- `requirements_backend.txt` 是当前开发环境的依赖快照，包含 editable Git 依赖和本机路径依赖；在新机器上通常需要按 CUDA、PyTorch 和 pytorch3d 实际环境调整。
- Stage1 / Stage2 依赖外部仓库和模型权重，本仓库只保存业务封装代码，不包含完整权重。
- MySQL、GVHMR、GMR、CUDA、ffmpeg 或 OpenGL 相关依赖未配置好时，网页任务会进入 `failed`，错误会写入任务详情页的阶段信息。
- 后台任务使用 Flask 进程内线程实现，适合本地演示和毕业设计原型；如果要部署为多人长期服务，应替换为 Celery / RQ 等任务队列。
