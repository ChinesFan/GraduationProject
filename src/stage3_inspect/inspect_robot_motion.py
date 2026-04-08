import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def summarize_array(name: str, arr: np.ndarray) -> None:
    print(f"{name}:")
    print(f"  shape = {arr.shape}")
    print(f"  dtype = {arr.dtype}")
    print(f"  min   = {np.min(arr):.6f}")
    print(f"  max   = {np.max(arr):.6f}")
    print(f"  mean  = {np.mean(arr):.6f}")
    print(f"  std   = {np.std(arr):.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect retargeted H1 motion pkl.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to robot motion pickle file, e.g. data/robot_motion/basketball_h1.pkl",
    )
    parser.add_argument(
        "--save_json",
        type=str,
        default=None,
        help="Optional path to save summary JSON.",
    )
    args = parser.parse_args()

    motion_path = Path(args.input)
    if not motion_path.exists():
        raise FileNotFoundError(f"Motion file not found: {motion_path}")

    with open(motion_path, "rb") as f:
        motion_data = pickle.load(f)

    print("=" * 60)
    print("Stage 3: Inspect Robot Motion")
    print("=" * 60)
    print(f"Input file: {motion_path}")

    required_keys = ["fps", "root_pos", "root_rot", "dof_pos"]
    for key in required_keys:
        if key not in motion_data:
            raise KeyError(f"Missing required key in motion file: {key}")

    fps = motion_data["fps"]
    root_pos = np.asarray(motion_data["root_pos"])
    root_rot = np.asarray(motion_data["root_rot"])
    dof_pos = np.asarray(motion_data["dof_pos"])

    print(f"fps = {fps}")
    print(f"num_frames = {len(root_pos)}")

    summarize_array("root_pos", root_pos)
    summarize_array("root_rot", root_rot)
    summarize_array("dof_pos", dof_pos)

    print("\nSanity checks:")
    print(f"  root_pos has NaN: {np.isnan(root_pos).any()}")
    print(f"  root_rot has NaN: {np.isnan(root_rot).any()}")
    print(f"  dof_pos has NaN:  {np.isnan(dof_pos).any()}")
    print(f"  root_pos has Inf: {np.isinf(root_pos).any()}")
    print(f"  root_rot has Inf: {np.isinf(root_rot).any()}")
    print(f"  dof_pos has Inf:  {np.isinf(dof_pos).any()}")

    # quaternion norm check
    quat_norm = np.linalg.norm(root_rot, axis=1)
    print("\nQuaternion norm:")
    print(f"  min = {quat_norm.min():.6f}")
    print(f"  max = {quat_norm.max():.6f}")
    print(f"  mean = {quat_norm.mean():.6f}")

    # DOF range per joint
    num_dofs = dof_pos.shape[1]
    dof_summary = []
    print("\nDOF ranges:")
    for i in range(num_dofs):
        joint_min = float(np.min(dof_pos[:, i]))
        joint_max = float(np.max(dof_pos[:, i]))
        joint_mean = float(np.mean(dof_pos[:, i]))
        joint_std = float(np.std(dof_pos[:, i]))
        dof_summary.append(
            {
                "index": i,
                "min": joint_min,
                "max": joint_max,
                "mean": joint_mean,
                "std": joint_std,
            }
        )
        print(
            f"  dof[{i:02d}] -> min={joint_min:.4f}, max={joint_max:.4f}, "
            f"mean={joint_mean:.4f}, std={joint_std:.4f}"
        )

    summary = {
        "input": str(motion_path),
        "fps": float(fps),
        "num_frames": int(len(root_pos)),
        "root_pos_shape": list(root_pos.shape),
        "root_rot_shape": list(root_rot.shape),
        "dof_pos_shape": list(dof_pos.shape),
        "quat_norm_min": float(quat_norm.min()),
        "quat_norm_max": float(quat_norm.max()),
        "quat_norm_mean": float(quat_norm.mean()),
        "dof_summary": dof_summary,
    }

    if args.save_json is not None:
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nSaved summary JSON to: {out_path}")

    print("\nInspection complete.")


if __name__ == "__main__":
    main()