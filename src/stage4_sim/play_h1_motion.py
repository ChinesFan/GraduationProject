import argparse
import pickle
import time
from pathlib import Path
import tempfile

import numpy as np
import pybullet as p
import pybullet_data


DEFAULT_H1_JOINT_NAMES = [
    # left leg (5)
    "left_hip_yaw_joint",
    "left_hip_roll_joint",
    "left_hip_pitch_joint",
    "left_knee_joint",
    "left_ankle_joint",

    # right leg (5)
    "right_hip_yaw_joint",
    "right_hip_roll_joint",
    "right_hip_pitch_joint",
    "right_knee_joint",
    "right_ankle_joint",

    # waist (1)
    "torso_joint",

    # left arm (4)
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",

    # right arm (4)
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
]


def load_motion(motion_path: Path):
    with open(motion_path, "rb") as f:
        motion = pickle.load(f)
    return motion


def find_h1_urdf(project_root: Path) -> Path:
    candidates = [
        project_root / "h1_description" / "urdf" / "h1.urdf",
        project_root / "h1_description" / "h1.urdf",
        project_root / "third_party" / "unitree_h1" / "h1.urdf",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Cannot find h1.urdf. Checked:\n" + "\n".join(str(x) for x in candidates)
    )


def prepare_pybullet_urdf(original_urdf: Path, project_root: Path) -> Path:
    """
    Convert ROS-style package://h1_description/... mesh paths into absolute file paths
    for PyBullet, and save a temporary URDF.
    """
    text = original_urdf.read_text(encoding="utf-8")

    h1_root = (project_root / "h1_description").resolve().as_posix()
    text = text.replace("package://h1_description/", f"{h1_root}/")

    temp_dir = Path(tempfile.gettempdir()) / "h1_gmr_project_pybullet"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_urdf = temp_dir / "h1_pybullet.urdf"
    temp_urdf.write_text(text, encoding="utf-8")

    return temp_urdf


def build_joint_map(robot_id: int) -> dict:
    joint_map = {}
    for i in range(p.getNumJoints(robot_id)):
        joint_name = p.getJointInfo(robot_id, i)[1].decode("utf-8")
        joint_map[joint_name] = i
    return joint_map


def disable_default_motors(robot_id: int):
    for j in range(p.getNumJoints(robot_id)):
        p.setJointMotorControl2(
            robot_id,
            j,
            controlMode=p.VELOCITY_CONTROL,
            force=0,
        )


def apply_pose(robot_id: int, joint_indices: list, joint_targets: np.ndarray, kp=0.5, kd=0.1, max_force=80.0):
    for idx, target in zip(joint_indices, joint_targets):
        p.setJointMotorControl2(
            bodyUniqueId=robot_id,
            jointIndex=idx,
            controlMode=p.POSITION_CONTROL,
            targetPosition=float(target),
            positionGain=kp,
            velocityGain=kd,
            force=max_force,
        )


def main():
    parser = argparse.ArgumentParser(description="Stage 4: Play H1 motion in PyBullet.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Robot motion pkl, e.g. data/robot_motion/basketball_h1.pkl",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop playback.",
    )
    parser.add_argument(
        "--fixed_base",
        action="store_true",
        help="Use fixed base for robot.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Sleep according to motion fps.",
    )
    parser.add_argument(
        "--base_x",
        type=float,
        default=0.0,
        help="Robot base x position.",
    )
    parser.add_argument(
        "--base_y",
        type=float,
        default=0.0,
        help="Robot base y position.",
    )
    parser.add_argument(
        "--base_z",
        type=float,
        default=1.0,
        help="Robot base z position.",
    )
    args = parser.parse_args()

    motion_path = Path(args.input).resolve()
    project_root = Path(__file__).resolve().parents[2]
    original_urdf_path = find_h1_urdf(project_root)
    urdf_path = prepare_pybullet_urdf(original_urdf_path, project_root)

    motion = load_motion(motion_path)
    fps = float(motion["fps"])
    root_pos = np.asarray(motion["root_pos"])
    root_rot = np.asarray(motion["root_rot"])
    dof_pos = np.asarray(motion["dof_pos"])

    num_frames = len(dof_pos)

    print("=" * 60)
    print("Stage 4: Play H1 Motion")
    print("=" * 60)
    print(f"Motion file: {motion_path}")
    print(f"Original URDF: {original_urdf_path}")
    print(f"PyBullet URDF: {urdf_path}")
    print(f"fps:         {fps}")
    print(f"num_frames:  {num_frames}")
    print(f"dof shape:   {dof_pos.shape}")

    if dof_pos.shape[1] != len(DEFAULT_H1_JOINT_NAMES):
        raise ValueError(
            f"dof count mismatch: motion has {dof_pos.shape[1]} dofs, "
            f"but DEFAULT_H1_JOINT_NAMES has {len(DEFAULT_H1_JOINT_NAMES)} names"
        )

    physics_client = p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setAdditionalSearchPath(str(project_root))
    p.setGravity(0, 0, -9.81)

    try:
        p.loadURDF("plane.urdf")
    except Exception:
        plane_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[10, 10, 0.1])
        plane_visual = p.createVisualShape(
            p.GEOM_BOX, halfExtents=[10, 10, 0.1], rgbaColor=[0.7, 0.7, 0.7, 1.0]
        )
        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=plane_shape,
            baseVisualShapeIndex=plane_visual,
            basePosition=[0, 0, -0.1],
        )

    robot_id = p.loadURDF(
        str(urdf_path),
        basePosition=[args.base_x, args.base_y, args.base_z],
        baseOrientation=p.getQuaternionFromEuler([0, 0, 0]),
        useFixedBase=args.fixed_base,
    )
    
    print("\nAll joints in URDF:")
    for i in range(p.getNumJoints(robot_id)):
        info = p.getJointInfo(robot_id, i)
        print(f"  {i}: {info[1].decode('utf-8')}")

    joint_map = build_joint_map(robot_id)
    disable_default_motors(robot_id)

    print("\nJoint mapping:")
    joint_indices = []
    for name in DEFAULT_H1_JOINT_NAMES:
        if name not in joint_map:
            raise KeyError(f"Joint not found in URDF: {name}")
        joint_indices.append(joint_map[name])
        print(f"  {name}: {joint_map[name]}")

    print("\nStart playback...")
    frame = 0

    while True:
        q = dof_pos[frame]
        apply_pose(robot_id, joint_indices, q, kp=0.5, kd=0.1, max_force=100.0)

        if not args.fixed_base:
            # Optional root playback: only position, keep orientation simple if needed
            base_position = root_pos[frame].tolist()
            base_orientation_xyzw = root_rot[frame].tolist()
            try:
                p.resetBasePositionAndOrientation(
                    robot_id,
                    base_position,
                    base_orientation_xyzw,
                )
            except Exception:
                pass

        p.stepSimulation()

        if frame % 30 == 0:
            print(f"frame {frame}/{num_frames}")

        if args.realtime and fps > 1e-6:
            time.sleep(1.0 / fps)

        frame += 1
        if frame >= num_frames:
            if args.loop:
                frame = 0
            else:
                break

    print("Playback complete.")
    p.disconnect(physics_client)


if __name__ == "__main__":
    main()