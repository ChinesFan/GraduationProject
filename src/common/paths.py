from pathlib import Path


# 项目根目录：假设当前文件在 src/common/paths.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
THIRD_PARTY_DIR = PROJECT_ROOT / "third_party"

RAW_VIDEOS_DIR = DATA_DIR / "raw_videos"
HUMAN_MOTION_DIR = DATA_DIR / "human_motion"
ROBOT_MOTION_DIR = DATA_DIR / "robot_motion"
RENDERED_DIR = DATA_DIR / "rendered"

GMR_DIR = THIRD_PARTY_DIR / "GMR"
GVHMR_DIR = THIRD_PARTY_DIR / "GVHMR"


def ensure_dirs() -> None:
    """确保项目基础目录存在。"""
    for d in [
        DATA_DIR,
        RAW_VIDEOS_DIR,
        HUMAN_MOTION_DIR,
        ROBOT_MOTION_DIR,
        RENDERED_DIR,
        THIRD_PARTY_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def require_dir(path: Path, name: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{name} 不存在: {path}")


def require_file(path: Path, name: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{name} 不存在: {path}")