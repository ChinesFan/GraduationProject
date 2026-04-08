from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.project import Project

project_bp = Blueprint("project", __name__)


@project_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return {"code": 1, "message": "project name required"}, 400

    project = Project(
        user_id=user_id,
        name=name,
        description=description or None,
    )
    db.session.add(project)
    db.session.commit()

    return {
        "code": 0,
        "message": "project created",
        "data": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        },
    }


@project_bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    user_id = int(get_jwt_identity())
    projects = (
        Project.query.filter_by(user_id=user_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return {
        "code": 0,
        "message": "ok",
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at.isoformat(),
            }
            for p in projects
        ],
    }