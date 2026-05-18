from __future__ import annotations

import argparse
import pickle
import re
import tempfile
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pybullet as p
import pybullet_data

from src.common.paths import PROJECT_ROOT


DEFAULT_H1_JOINT_NAMES = [
    "left_hip_yaw_joint",
    "left_hip_roll_joint",
    "left_hip_pitch_joint",
    "left_knee_joint",
    "left_ankle_joint",
    "right_hip_yaw_joint",
    "right_hip_roll_joint",
    "right_hip_pitch_joint",
    "right_knee_joint",
    "right_ankle_joint",
    "torso_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
]

FRONT_CAMERA_YAW_DEG = 205.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 4: export H1 motion to mp4")
    parser.add_argument("--input", type=str, required=True, help="Input robot motion pkl")
    parser.add_argument("--output", type=str, required=True, help="Output mp4 path")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fixed_base", action="store_true", help="Load robot with fixed base")
    parser.add_argument("--fps_override", type=float, default=None, help="Override output fps")
    return parser.parse_args()


def load_motion(path: Path) -> dict:
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def find_h1_urdf(project_root: Path) -> Path:
    candidates = [
        project_root / "h1_description" / "urdf" / "h1.urdf",
        project_root / "h1_description" / "h1.urdf",
        project_root / "third_party" / "unitree_h1" / "h1.urdf",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Cannot find h1.urdf. Checked:\n" + "\n".join(str(x) for x in candidates)
    )


def make_pybullet_urdf(original_urdf: Path) -> Path:
    """
    把 package://h1_description/... 替换成 h1_description 的绝对路径，
    生成一个 PyBullet 可加载的临时 urdf。
    """
    project_root = PROJECT_ROOT
    h1_description_dir = project_root / "h1_description"

    text = original_urdf.read_text(encoding="utf-8")
    text = text.replace(
        "package://h1_description/",
        str(h1_description_dir).replace("\\", "/") + "/",
    )

    tmp_dir = Path(tempfile.gettempdir()) / "h1_gmr_project_pybullet"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_urdf = tmp_dir / "h1_pybullet.urdf"
    tmp_urdf.write_text(text, encoding="utf-8")
    return tmp_urdf


def build_joint_map(robot_id: int) -> dict[str, int]:
    joint_name_to_id: dict[str, int] = {}
    num_joints = p.getNumJoints(robot_id)
    for i in range(num_joints):
        joint_info = p.getJointInfo(robot_id, i)
        joint_name = joint_info[1].decode("utf-8")
        joint_name_to_id[joint_name] = i
    return joint_name_to_id


def reset_robot_pose(robot_id: int, root_pos, root_rot, dof_values, joint_map: dict[str, int]):
    # base pose
    p.resetBasePositionAndOrientation(robot_id, root_pos, root_rot)

    # joint pose
    for joint_name, joint_value in zip(DEFAULT_H1_JOINT_NAMES, dof_values):
        if joint_name not in joint_map:
            continue
        joint_id = joint_map[joint_name]
        p.resetJointState(robot_id, joint_id, float(joint_value))


def render_frame(robot_id: int, width: int, height: int):
    base_pos, _ = p.getBasePositionAndOrientation(robot_id)

    target = [base_pos[0], base_pos[1], base_pos[2] + 0.7]
    distance = 2.8
    yaw = FRONT_CAMERA_YAW_DEG
    pitch = -20
    roll = 0
    up_axis_index = 2

    view_matrix = p.computeViewMatrixFromYawPitchRoll(
        cameraTargetPosition=target,
        distance=distance,
        yaw=yaw,
        pitch=pitch,
        roll=roll,
        upAxisIndex=up_axis_index,
    )

    projection_matrix = p.computeProjectionMatrixFOV(
        fov=60.0,
        aspect=float(width) / float(height),
        nearVal=0.1,
        farVal=100.0,
    )

    _, _, rgba, _, _ = p.getCameraImage(
        width=width,
        height=height,
        viewMatrix=view_matrix,
        projectionMatrix=projection_matrix,
        renderer=p.ER_BULLET_HARDWARE_OPENGL,
    )

    frame = np.reshape(rgba, (height, width, 4))[:, :, :3]
    return frame.astype(np.uint8)


def main():
    args = parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    motion = load_motion(input_path)

    fps = float(motion.get("fps", 30))
    if args.fps_override is not None:
        fps = float(args.fps_override)

    root_pos = np.asarray(motion["root_pos"])
    root_rot = np.asarray(motion["root_rot"])
    dof_pos = np.asarray(motion["dof_pos"])

    if dof_pos.shape[1] != len(DEFAULT_H1_JOINT_NAMES):
        raise ValueError(
            f"dof count mismatch: motion has {dof_pos.shape[1]} dofs, "
            f"but DEFAULT_H1_JOINT_NAMES has {len(DEFAULT_H1_JOINT_NAMES)} names"
        )

    project_root = PROJECT_ROOT
    original_urdf = find_h1_urdf(project_root)
    pybullet_urdf = make_pybullet_urdf(original_urdf)

    print("=" * 60)
    print("Stage 4: Export H1 Video")
    print("=" * 60)
    print(f"Motion file: {input_path}")
    print(f"Original URDF: {original_urdf}")
    print(f"PyBullet URDF: {pybullet_urdf}")
    print(f"Output video: {output_path}")
    print(f"fps: {fps}")
    print(f"num_frames: {len(root_pos)}")
    print(f"dof shape: {dof_pos.shape}")

    client = p.connect(p.DIRECT)
    try:
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)

        plane_id = p.loadURDF("plane.urdf")
        robot_id = p.loadURDF(
            str(pybullet_urdf),
            basePosition=root_pos[0].tolist(),
            baseOrientation=root_rot[0].tolist(),
            useFixedBase=args.fixed_base,
            flags=p.URDF_USE_INERTIA_FROM_FILE,
        )

        joint_map = build_joint_map(robot_id)

        print("Joint mapping:")
        for name in DEFAULT_H1_JOINT_NAMES:
            print(f"  {name}: {joint_map.get(name, 'NOT_FOUND')}")

        writer = imageio.get_writer(
            str(output_path),
            fps=fps,
            codec="libx264",
            quality=8,
            macro_block_size=None,
        )

        try:
            last_progress = -1
            for i in range(len(root_pos)):
                reset_robot_pose(
                    robot_id=robot_id,
                    root_pos=root_pos[i],
                    root_rot=root_rot[i],
                    dof_values=dof_pos[i],
                    joint_map=joint_map,
                )
                frame = render_frame(robot_id, args.width, args.height)
                writer.append_data(frame)

                progress = min(100, int((i + 1) / len(root_pos) * 100))
                if progress != last_progress:
                    print(f"frame {i}/{len(root_pos)}", flush=True)
                    last_progress = progress
        finally:
            writer.close()

        print(f"frame {len(root_pos)}/{len(root_pos)}", flush=True)
        print(f"Stage 4 video saved to: {output_path}", flush=True)

    finally:
        p.disconnect(client)


if __name__ == "__main__":
    main()
