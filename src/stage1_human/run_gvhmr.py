from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from src.common.paths import GVHMR_DIR, PROJECT_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 1: run GVHMR on a video")
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to input video",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to final saved hmr4d_results.pt",
    )
    parser.add_argument(
        "--static-camera",
        action="store_true",
        help="Use static camera mode (-s)",
    )
    return parser.parse_args()


def build_expected_output(video_path: Path) -> Path:
    video_stem = video_path.stem
    return GVHMR_DIR / "outputs" / "demo" / video_stem / "hmr4d_results.pt"


def main() -> None:
    args = parse_args()

    video_path = (PROJECT_ROOT / args.video).resolve() if not Path(args.video).is_absolute() else Path(args.video).resolve()
    target_output = (PROJECT_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()

    demo_script = GVHMR_DIR / "tools" / "demo" / "demo.py"
    python_exec = PROJECT_ROOT / "basketball" / "bin" / "python"
    expected_output = build_expected_output(video_path)

    cmd = [
        str(python_exec),
        str(demo_script),
        f"--video={video_path}",
    ]
    if args.static_camera:
        cmd.append("-s")

    print("=" * 60)
    print("Stage 1: GVHMR 人体动作提取")
    print("=" * 60)
    print(f"GVHMR 目录: {GVHMR_DIR}")
    print(f"输入视频: {video_path}")
    print(f"执行脚本: {demo_script}")
    print(f"预期输出: {expected_output}")
    print(f"目标落盘: {target_output}")
    print(f"执行命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(GVHMR_DIR), check=False)

    # 关键逻辑：
    # GVHMR 的 demo.py 经常在最后 merge_videos / ffmpeg 阶段报错退出，
    # 但 hmr4d_results.pt 已经成功生成。
    # 这里只要核心输出存在，就视为 Stage1 成功。
    if not expected_output.exists():
        raise subprocess.CalledProcessError(result.returncode, cmd)

    if result.returncode != 0:
        print("[Stage1] demo.py 返回非零，但检测到核心结果文件已生成，忽略可视化/合并视频尾部错误。")

    target_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(expected_output, target_output)

    print(f"[Stage1] 核心输出已保存: {target_output}")
    print("Stage 1 完成。")


if __name__ == "__main__":
    main()