import os
import threading
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.artifact import Artifact
from app.models.project import Project
from app.models.task import Task
from app.services.pipeline_service import run_stage1, run_stage2, run_stage3, run_stage4

task_bp = Blueprint("task", __name__)


def update_task_progress(
    task,
    *,
    status=None,
    progress=None,
    current_stage=None,
    stage_message=None,
    output_path=None,
    message=None,
):
    if status is not None:
        task.status = status
    if progress is not None:
        task.progress = progress
    if current_stage is not None:
        task.current_stage = current_stage
    if stage_message is not None:
        task.stage_message = stage_message
    if output_path is not None:
        task.output_path = output_path
    if message is not None:
        task.message = message
    db.session.commit()


def run_pipeline_in_background(app, task_id: int, saved_path: str, stem: str):
    with app.app_context():
        task = Task.query.get(task_id)
        if not task:
            return

        try:
            update_task_progress(
                task,
                status="running",
                progress=15,
                current_stage="stage1",
                stage_message="正在执行 Stage1：人体动作提取",
            )
            result1 = run_stage1(
                project_root=current_app.config["BASE_DIR"],
                input_video=saved_path,
                stem=stem,
            )

            update_task_progress(
                task,
                progress=35,
                current_stage="stage1",
                stage_message="Stage1 完成：人体动作结果已生成",
            )

            update_task_progress(
                task,
                progress=40,
                current_stage="stage2",
                stage_message="正在执行 Stage2：重定向到 H1",
            )
            result2 = run_stage2(
                project_root=current_app.config["BASE_DIR"],
                stem=stem,
            )

            update_task_progress(
                task,
                progress=60,
                current_stage="stage2",
                stage_message="Stage2 完成：机器人动作已生成",
                output_path=result2["stage2_output"],
            )

            update_task_progress(
                task,
                progress=65,
                current_stage="stage3",
                stage_message="正在执行 Stage3：动作检查与摘要生成",
            )
            result3 = run_stage3(
                project_root=current_app.config["BASE_DIR"],
                stem=stem,
            )

            update_task_progress(
                task,
                progress=75,
                current_stage="stage3",
                stage_message="Stage3 完成：摘要 JSON 已生成",
            )

            update_task_progress(
                task,
                progress=80,
                current_stage="stage4",
                stage_message="正在执行 Stage4：导出机器人仿真视频",
            )
            result4 = run_stage4(
                project_root=current_app.config["BASE_DIR"],
                stem=stem,
            )

            update_task_progress(
                task,
                progress=95,
                current_stage="stage4",
                stage_message="Stage4 完成：仿真视频已导出",
            )

            artifacts = [
                Artifact(
                    task_id=task.id,
                    artifact_type="human_motion",
                    file_path=result1["stage1_output"],
                ),
                Artifact(
                    task_id=task.id,
                    artifact_type="robot_motion",
                    file_path=result2["stage2_output"],
                ),
                Artifact(
                    task_id=task.id,
                    artifact_type="summary_json",
                    file_path=result3["stage3_output"],
                ),
            ]

            if result1.get("stage1_video"):
                artifacts.append(
                    Artifact(
                        task_id=task.id,
                        artifact_type="stage1_video",
                        file_path=result1["stage1_video"],
                    )
                )

            if result4.get("stage4_video"):
                artifacts.append(
                    Artifact(
                        task_id=task.id,
                        artifact_type="stage4_video",
                        file_path=result4["stage4_video"],
                    )
                )

            db.session.add_all(artifacts)
            db.session.commit()

            update_task_progress(
                task,
                status="success",
                progress=100,
                current_stage="completed",
                stage_message="流水线执行完成",
                output_path=result2["stage2_output"],
                message="pipeline completed",
            )

        except Exception as e:
            update_task_progress(
                task,
                status="failed",
                current_stage="failed",
                stage_message=f"执行失败：{str(e)}",
                message=str(e),
            )


@task_bp.route("", methods=["POST"])
@jwt_required()
def create_task():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    task_type = (data.get("task_type") or "").strip()
    project_id = data.get("project_id")
    input_path = data.get("input_path")
    output_path = data.get("output_path")
    message = data.get("message")

    if not task_type:
        return {"code": 1, "message": "task_type required"}, 400

    if not project_id:
        return {"code": 1, "message": "project_id required"}, 400

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return {"code": 1, "message": "project not found"}, 400

    task = Task(
        user_id=user_id,
        project_id=project_id,
        task_type=task_type,
        status="pending",
        progress=0,
        current_stage="pending",
        stage_message="任务已创建，等待执行",
        input_path=input_path,
        output_path=output_path,
        message=message,
    )
    db.session.add(task)
    db.session.commit()

    return {
        "code": 0,
        "message": "task created",
        "data": {
            "id": task.id,
            "status": task.status,
            "task_type": task.task_type,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "stage_message": task.stage_message,
        },
    }


@task_bp.route("", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = int(get_jwt_identity())
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()

    return {
        "code": 0,
        "message": "ok",
        "data": [
            {
                "id": t.id,
                "project_id": t.project_id,
                "task_type": t.task_type,
                "status": t.status,
                "progress": t.progress,
                "current_stage": t.current_stage,
                "stage_message": t.stage_message,
                "input_path": t.input_path,
                "output_path": t.output_path,
                "message": t.message,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            }
            for t in tasks
        ],
    }


@task_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id: int):
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()

    if not task:
        return {"code": 1, "message": "task not found"}, 404

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "id": task.id,
            "project_id": task.project_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "stage_message": task.stage_message,
            "input_path": task.input_path,
            "output_path": task.output_path,
            "message": task.message,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
        },
    }


@task_bp.route("/run_pipeline", methods=["POST"])
@jwt_required()
def run_pipeline():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return {"code": 1, "message": "file is required"}, 400

    file = request.files["file"]
    if not file or not file.filename:
        return {"code": 1, "message": "invalid file"}, 400

    project_id = request.form.get("project_id", type=int)
    if not project_id:
        return {"code": 1, "message": "project_id required"}, 400

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return {"code": 1, "message": "project not found"}, 400

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(file.filename)
    stem = f"{uuid4().hex}_{Path(safe_name).stem}"
    ext = Path(safe_name).suffix or ".mp4"
    saved_path = upload_dir / f"{stem}{ext}"
    file.save(saved_path)

    task = Task(
        user_id=user_id,
        project_id=project_id,
        task_type="full_pipeline",
        status="running",
        progress=10,
        current_stage="uploaded",
        stage_message="文件上传成功，流水线已开始执行",
        input_path=str(saved_path),
        message="pipeline started",
    )
    db.session.add(task)
    db.session.commit()

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_pipeline_in_background,
        args=(app, task.id, str(saved_path), stem),
        daemon=True,
    )
    thread.start()

    return {
        "code": 0,
        "message": "pipeline started",
        "data": {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "stage_message": task.stage_message,
        },
    }


@task_bp.route("/<int:task_id>/artifacts", methods=["GET"])
@jwt_required()
def list_task_artifacts(task_id: int):
    user_id = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return {"code": 1, "message": "task not found"}, 404

    artifacts = Artifact.query.filter_by(task_id=task.id).all()
    return {
        "code": 0,
        "message": "ok",
        "data": [
            {
                "id": a.id,
                "task_id": a.task_id,
                "artifact_type": a.artifact_type,
                "file_path": a.file_path,
                "filename": os.path.basename(a.file_path) if a.file_path else "",
                "created_at": a.created_at.isoformat(),
            }
            for a in artifacts
        ],
    }


@task_bp.route("/artifacts/<int:artifact_id>/download", methods=["GET"])
@jwt_required()
def download_artifact(artifact_id: int):
    user_id = int(get_jwt_identity())
    artifact = (
        db.session.query(Artifact)
        .join(Task, Artifact.task_id == Task.id)
        .filter(Artifact.id == artifact_id, Task.user_id == user_id)
        .first()
    )
    if not artifact:
        return {"code": 1, "message": "artifact not found"}, 404

    path = Path(artifact.file_path)
    if not path.exists():
        return {"code": 1, "message": "file not found"}, 404

    return send_file(path, as_attachment=True)


@task_bp.route("/artifacts/<int:artifact_id>/preview", methods=["GET"])
@jwt_required()
def preview_artifact(artifact_id: int):
    user_id = int(get_jwt_identity())
    artifact = (
        db.session.query(Artifact)
        .join(Task, Artifact.task_id == Task.id)
        .filter(Artifact.id == artifact_id, Task.user_id == user_id)
        .first()
    )
    if not artifact:
        return {"code": 1, "message": "artifact not found"}, 404

    path = Path(artifact.file_path)
    if not path.exists():
        return {"code": 1, "message": "file not found"}, 404

    return send_file(path, as_attachment=False)


@task_bp.route("/artifacts/<int:artifact_id>/content", methods=["GET"])
@jwt_required()
def artifact_content(artifact_id: int):
    user_id = int(get_jwt_identity())
    artifact = (
        db.session.query(Artifact)
        .join(Task, Artifact.task_id == Task.id)
        .filter(Artifact.id == artifact_id, Task.user_id == user_id)
        .first()
    )
    if not artifact:
        return {"code": 1, "message": "artifact not found"}, 404

    path = Path(artifact.file_path)
    if not path.exists():
        return {"code": 1, "message": "file not found"}, 404

    if path.suffix.lower() != ".json":
        return {"code": 1, "message": "only json content is supported"}, 400

    import json

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {"code": 0, "message": "ok", "data": data}