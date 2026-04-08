from __future__ import annotations

import os
import subprocess
from pathlib import Path


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


def run_stage1(project_root: str, input_video: str, stem: str) -> dict:
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
        "--static-camera",
    ]
    subprocess.run(cmd1, cwd=str(paths["project_root"]), check=True, env=env)

    demo_root = paths["project_root"] / "third_party" / "GVHMR" / "outputs" / "demo"
    demo_dir = demo_root / stem
    stage1_video = _pick_video_file(demo_dir)

    return {
        "stage1_output": str(paths["stage1_output"]),
        "stage1_video": stage1_video,
    }


def run_stage2(project_root: str, stem: str) -> dict:
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
    subprocess.run(cmd2, cwd=str(paths["project_root"]), check=True, env=env)

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


def run_stage4(project_root: str, stem: str) -> dict:
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
    subprocess.run(cmd4, cwd=str(paths["project_root"]), check=True, env=env)

    stage4_video = str(paths["stage4_output"]) if paths["stage4_output"].exists() else None
    return {
        "stage4_video": stage4_video,
    }