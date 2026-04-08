import argparse
import subprocess
import sys
from pathlib import Path

from src.common.paths import (
    GMR_DIR,
    HUMAN_MOTION_DIR,
    ROBOT_MOTION_DIR,
    ensure_dirs,
    require_dir,
    require_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 2: 用 GMR 将 GVHMR 的人体动作 retarget 到 Unitree H1"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入人体动作文件，例如 data/human_motion/basketball_hmr4d_results.pt",
    )
    parser.add_argument(
        "--robot",
        type=str,
        default="unitree_h1",
        help="目标机器人，默认 unitree_h1",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="输出机器人动作文件，例如 data/robot_motion/basketball_h1.pkl",
    )
    parser.add_argument(
        "--record-video",
        action="store_true",
        help="是否让 GMR 录制可视化视频",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="是否循环播放动作",
    )
    parser.add_argument(
        "--rate-limit",
        action="store_true",
        help="是否按人体原始 FPS 限速播放",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dirs()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    require_file(input_path, "输入人体动作文件")
    require_dir(GMR_DIR, "GMR 目录")

    gmr_script = (GMR_DIR / "scripts" / "gvhmr_to_robot.py").resolve()
    require_file(gmr_script, "GMR retargeting 脚本")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(gmr_script),
        "--gvhmr_pred_file",
        str(input_path),
        "--robot",
        args.robot,
        "--save_path",
        str(output_path),
    ]

    if args.record_video:
        cmd.append("--record_video")
    if args.loop:
        cmd.append("--loop")
    if args.rate_limit:
        cmd.append("--rate_limit")

    print("=" * 60)
    print("Stage 2: GMR -> Unitree H1 Retargeting")
    print("=" * 60)
    print(f"GMR 目录: {GMR_DIR}")
    print(f"输入人体动作: {input_path}")
    print(f"目标机器人: {args.robot}")
    print(f"输出机器人动作: {output_path}")
    print("执行命令:", " ".join(cmd))

    subprocess.run(cmd, cwd=str(GMR_DIR), check=True)

    require_file(output_path, "GMR 输出机器人动作文件")
    print(f"\n已保存 H1 动作文件到: {output_path}")


if __name__ == "__main__":
    main()