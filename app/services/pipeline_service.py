from __future__ import annotations

import math
import os
import pickle
import re
import subprocess
from pathlib import Path
from typing import Callable

import numpy as np

ProgressCallback = Callable[[int, str], None]
HIP_PITCH_FORWARD_BIAS = -0.35
HIP_PITCH_LIMIT = 0.75


def _pick_video_file(demo_dir: Path) -> str | None:
    if not demo_dir.exists():
        return None

    mp4_files = sorted(demo_dir.glob("*.mp4"))
    if not mp4_files:
        return None

    for p in mp4_files:
        if p.name.lower() == "1_incam.mp4":
            return str(p)

    for p in mp4_files:
        if "incam" in p.name.lower():
            return str(p)

    for p in mp4_files:
        if "global" in p.name.lower():
            return str(p)

    for p in mp4_files:
        if p.name.lower() == "0_input_video.mp4":
            return str(p)

    return str(mp4_files[0])


def prepare_paths(project_root: str, stem: str) -> dict:
    project_root = Path(project_root).resolve()

    human_motion_dir = project_root / "data" / "human_motion"
    robot_motion_dir = project_root / "data" / "robot_motion"

    human_motion_dir.mkdir(parents=True, exist_ok=True)
    robot_motion_dir.mkdir(parents=True, exist_ok=True)

    return {
        "project_root": project_root,
        "python_exec": project_root / "basketball" / "bin" / "python",
        "stage1_output": human_motion_dir / f"{stem}_hmr4d_results.pt",
        "stage2_output": robot_motion_dir / f"{stem}_h1.pkl",
        "stage3_output": robot_motion_dir / f"{stem}_summary.json",
        "stage4_output": robot_motion_dir / f"{stem}_stage4.mp4",
    }


def _yaw_only_quat_xyzw(quat: np.ndarray) -> list[float]:
    x, y, z, w = [float(v) for v in quat]
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    half_yaw = yaw * 0.5
    return [0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)]


def stabilize_robot_pelvis_and_upper_body(motion_path: Path) -> None:
    with motion_path.open("rb") as f:
        motion = pickle.load(f)

    dof_pos = motion.get("dof_pos")
    if dof_pos is not None:
        dof_pos = np.asarray(dof_pos).copy()
        # H1 joint order: index 2/7 are left/right hip pitch. Limit pelvis-leg
        # folding and bias the feet forward after root pitch is removed.
        dof_pos[:, [2, 7]] = np.clip(
            dof_pos[:, [2, 7]] + HIP_PITCH_FORWARD_BIAS,
            -HIP_PITCH_LIMIT,
            HIP_PITCH_LIMIT,
        )
        motion["dof_pos"] = dof_pos

    root_rot = motion.get("root_rot")
    if root_rot is not None:
        root_rot = np.asarray(root_rot)
        motion["root_rot"] = np.asarray([_yaw_only_quat_xyzw(q) for q in root_rot])

    with motion_path.open("wb") as f:
        pickle.dump(motion, f)


def _emit_progress(progress_callback: ProgressCallback | None, progress: int, message: str) -> None:
    if progress_callback:
        progress_callback(progress, message)


def _unbuffered_env(env: dict) -> dict:
    env = env.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _map_percent(percent: int, start: int, end: int) -> int:
    percent = max(0, min(100, int(percent)))
    return start + round((end - start) * percent / 100)


def _run_with_stage1_progress(
    cmd: list[str],
    *,
    cwd: str,
    env: dict,
    progress_callback: ProgressCallback | None,
) -> None:
    progress_patterns = [
        (re.compile(r"YoloV8 Tracking:\s*(\d+)%"), 10, 15, "Stage1 YOLO 人体检测与跟踪"),
        (re.compile(r"ViTPose:\s*(\d+)%"), 15, 20, "Stage1 ViTPose 2D关键点提取"),
        (re.compile(r"HMR2 Feature:\s*(\d+)%"), 20, 25, "Stage1 ViT图像特征提取"),
        (re.compile(r"(?:SimpleVO|DPVO).*?(\d+)%"), 25, 30, "Stage1 相机运动估计"),
    ]

    marker_progress = [
        ("[Preprocess] Start", 10, "Stage1 开始预处理"),
        ("[HMR4D] Predicting", 30, "Stage1 HMR4D 三维人体动作恢复"),
        ("[HMR4D] Elapsed", 35, "Stage1 人体动作恢复完成"),
    ]
    active_range: tuple[int, int, str] | None = None

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=_unbuffered_env(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    buffer = ""
    for chunk in iter(lambda: process.stdout.read(1), ""):
        print(chunk, end="", flush=True)
        if chunk not in ("\r", "\n"):
            buffer += chunk
            continue

        line = buffer.strip()
        buffer = ""
        if not line:
            continue

        if "[SimpleVO]" in line:
            active_range = (25, 30, "Stage1 SimpleVO 相机运动估计")
            _emit_progress(progress_callback, 25, "Stage1 SimpleVO 相机运动估计")

        for marker, progress, message in marker_progress:
            if marker in line:
                if marker == "[HMR4D] Predicting":
                    active_range = None
                _emit_progress(progress_callback, progress, message)

        matched_named_progress = False
        for pattern, start, end, message in progress_patterns:
            match = pattern.search(line)
            if match:
                matched_named_progress = True
                progress = _map_percent(int(match.group(1)), start, end)
                _emit_progress(progress_callback, progress, f"{message}：{match.group(1)}%")

        if active_range and not matched_named_progress:
            match = re.search(r"(\d+)%", line)
            if match:
                start, end, message = active_range
                progress = _map_percent(int(match.group(1)), start, end)
                _emit_progress(progress_callback, progress, f"{message}：{match.group(1)}%")

    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)


def _run_with_progress_patterns(
    cmd: list[str],
    *,
    cwd: str,
    env: dict,
    progress_callback: ProgressCallback | None,
    percent_patterns: list[tuple[re.Pattern, int, int, str]] | None = None,
    frame_patterns: list[tuple[re.Pattern, int, int, str]] | None = None,
    marker_progress: list[tuple[str, int, str]] | None = None,
) -> None:
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=_unbuffered_env(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    percent_patterns = percent_patterns or []
    frame_patterns = frame_patterns or []
    marker_progress = marker_progress or []

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        line = line.strip()
        if not line:
            continue

        for marker, progress, message in marker_progress:
            if marker in line:
                _emit_progress(progress_callback, progress, message)

        for pattern, start, end, message in percent_patterns:
            match = pattern.search(line)
            if match:
                percent = int(match.group(1))
                progress = _map_percent(percent, start, end)
                _emit_progress(progress_callback, progress, f"{message}：{percent}%")

        for pattern, start, end, message in frame_patterns:
            match = pattern.search(line)
            if match:
                frame = int(match.group(1))
                total = max(1, int(match.group(2)))
                percent = min(100, round(frame / total * 100))
                progress = _map_percent(percent, start, end)
                _emit_progress(progress_callback, progress, f"{message}：{percent}%")

    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)


def run_stage1(
    project_root: str,
    input_video: str,
    stem: str,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    paths = prepare_paths(project_root, stem)
    env = os.environ.copy()

    cmd1 = [
        str(paths["python_exec"]),
        "-m",
        "src.stage1_human.run_gvhmr",
        "--video",
        str(input_video),
        "--output",
        str(paths["stage1_output"]),
    ]
    _run_with_stage1_progress(
        cmd1,
        cwd=str(paths["project_root"]),
        env=env,
        progress_callback=progress_callback,
    )

    demo_root = paths["project_root"] / "third_party" / "GVHMR" / "outputs" / "demo"
    demo_dir = demo_root / stem
    stage1_video = _pick_video_file(demo_dir)

    return {
        "stage1_output": str(paths["stage1_output"]),
        "stage1_video": stage1_video,
    }


def run_stage2(
    project_root: str,
    stem: str,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    paths = prepare_paths(project_root, stem)
    env = os.environ.copy()

    cmd2 = [
        str(paths["python_exec"]),
        "-m",
        "src.stage2_retarget.run_gmr_h1",
        "--input",
        str(paths["stage1_output"]),
        "--robot",
        "unitree_h1",
        "--output",
        str(paths["stage2_output"]),
    ]
    _run_with_progress_patterns(
        cmd2,
        cwd=str(paths["project_root"]),
        env=env,
        progress_callback=progress_callback,
        percent_patterns=[
            (re.compile(r"GMR Retargeting:\s*(\d+)%"), 40, 60, "Stage2 GMR 重定向到 H1"),
        ],
        marker_progress=[
            ("Stage 2: GMR", 40, "Stage2 开始 GMR 重定向"),
            ("Saved to", 60, "Stage2 H1 机器人动作已保存"),
        ],
    )
    stabilize_robot_pelvis_and_upper_body(paths["stage2_output"])

    return {
        "stage2_output": str(paths["stage2_output"]),
    }


def run_stage3(project_root: str, stem: str) -> dict:
    paths = prepare_paths(project_root, stem)
    env = os.environ.copy()

    cmd3 = [
        str(paths["python_exec"]),
        "-m",
        "src.stage3_inspect.inspect_robot_motion",
        "--input",
        str(paths["stage2_output"]),
        "--save_json",
        str(paths["stage3_output"]),
    ]
    subprocess.run(cmd3, cwd=str(paths["project_root"]), check=True, env=env)

    return {
        "stage3_output": str(paths["stage3_output"]),
    }


def run_stage4(
    project_root: str,
    stem: str,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    paths = prepare_paths(project_root, stem)
    env = os.environ.copy()

    cmd4 = [
        str(paths["python_exec"]),
        "-m",
        "src.stage4_sim.export_h1_video",
        "--input",
        str(paths["stage2_output"]),
        "--output",
        str(paths["stage4_output"]),
        "--fixed_base",
    ]
    _run_with_progress_patterns(
        cmd4,
        cwd=str(paths["project_root"]),
        env=env,
        progress_callback=progress_callback,
        frame_patterns=[
            (re.compile(r"frame\s+(\d+)/(\d+)"), 80, 95, "Stage4 仿真视频逐帧导出"),
        ],
        marker_progress=[
            ("Stage 4: Export H1 Video", 80, "Stage4 开始导出 H1 仿真视频"),
            ("Stage 4 video saved", 95, "Stage4 仿真视频已保存"),
        ],
    )

    stage4_video = str(paths["stage4_output"]) if paths["stage4_output"].is_file() else None
    return {
        "stage4_video": stage4_video,
    }
