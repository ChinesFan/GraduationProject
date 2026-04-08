from app.extensions import db
from datetime import datetime


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)

    task_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending")

    progress = db.Column(db.Integer, nullable=False, default=0)
    current_stage = db.Column(db.String(64), nullable=False, default="pending")
    stage_message = db.Column(db.String(255), nullable=True)

    input_path = db.Column(db.String(512), nullable=True)
    output_path = db.Column(db.String(512), nullable=True)
    message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )