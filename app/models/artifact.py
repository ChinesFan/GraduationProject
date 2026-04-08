from datetime import datetime
from app.extensions import db


class Artifact(db.Model):
    __tablename__ = "artifacts"

    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey("tasks.id"), nullable=False, index=True)
    artifact_type = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)