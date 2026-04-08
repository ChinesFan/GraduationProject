import argparse
import pickle
from pathlib import Path

import numpy as np

from general_motion_retargeting import RobotMotionViewer


def xyzw_to_wxyz(q_xyzw: np.ndarray) -> np.ndarray:
    q_xyzw = np.asarray(q_xyzw)
    if q_xyzw.shape[-1] != 4:
        raise ValueError(f"Quaternion last dim must be 4, got {q_xyzw.shape}")
    return q_xyzw[..., [3, 0, 1, 2]]


def main():
    parser = argparse.ArgumentParser(description="Stage 4 (Plan B): play H1 motion with GMR viewer")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to robot motion pkl, e.g. data/robot_motion/basketball_h1.pkl",
    )
    parser.add_argument(
        "--robot",
        type=str,
        default="unitree_h1",
        help="Robot type for GMR viewer, default: unitree_h1",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop playback",
    )
    parser.add_argument(
        "--rate_limit",
        action="store_true",
        help="Playback at motion fps",
    )
    parser.add_argument(
        "--record_video",
        action="store_true",
        help="Record video using GMR viewer",
    )
    parser.add_argument(
        "--video_path",
        type=str,
        default=None,
        help="Optional video output path when --record_video is enabled",
    )
    parser.add_argument(
        "--transparent_robot",
        type=float,
        default=0.0,
        help="Robot transparency passed to viewer",
    )
    args = parser.parse_args()

    motion_path = Path(args.input).resolve()
    if not motion_path.exists():
        raise FileNotFoundError(f"Motion file not found: {motion_path}")

    with open(motion_path, "rb") as f:
        motion_data = pickle.load(f)

    required_keys = ["fps", "root_pos", "root_rot", "dof_pos"]
    for k in required_keys:
        if k not in motion_data:
            raise KeyError(f"Missing required key: {k}")

    fps = float(motion_data["fps"])
    root_pos = np.asarray(motion_data["root_pos"], dtype=np.float64)
    root_rot_xyzw = np.asarray(motion_data["root_rot"], dtype=np.float64)
    dof_pos = np.asarray(motion_data["dof_pos"], dtype=np.float64)

    num_frames = len(root_pos)
    if len(root_rot_xyzw) != num_frames or len(dof_pos) != num_frames:
        raise ValueError("root_pos, root_rot, dof_pos frame counts do not match")

    # 关键点：
    # Stage 2 存盘时把 root_rot 从 wxyz 改成了 xyzw
    # GMR 的 RobotMotionViewer.step() 使用的是原始 qpos 风格，需转回 wxyz
    root_rot_wxyz = xyzw_to_wxyz(root_rot_xyzw)

    if args.record_video:
        if args.video_path is None:
            video_path = f"videos/{args.robot}_{motion_path.stem}.mp4"
        else:
            video_path = args.video_path
    else:
        video_path = None

    print("=" * 60)
    print("Stage 4 (Plan B): GMR Viewer Playback")
    print("=" * 60)
    print(f"Motion file: {motion_path}")
    print(f"Robot:       {args.robot}")
    print(f"fps:         {fps}")
    print(f"num_frames:  {num_frames}")
    print(f"dof shape:   {dof_pos.shape}")
    if args.record_video:
        print(f"video_path:  {video_path}")

    viewer = RobotMotionViewer(
        robot_type=args.robot,
        motion_fps=fps,
        transparent_robot=args.transparent_robot,
        record_video=args.record_video,
        video_path=video_path,
    )

    try:
        i = 0
        while True:
            viewer.step(
                root_pos=root_pos[i],
                root_rot=root_rot_wxyz[i],
                dof_pos=dof_pos[i],
                human_motion_data=None,
                human_pos_offset=np.array([0.0, 0.0, 0.0]),
                show_human_body_name=False,
                rate_limit=args.rate_limit,
            )

            if i % 30 == 0:
                print(f"frame {i}/{num_frames}")

            i += 1
            if i >= num_frames:
                if args.loop:
                    i = 0
                else:
                    break

        print("Playback complete.")
    finally:
        viewer.close()


if __name__ == "__main__":
    main()