from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.project import project_bp
    from app.routes.task import task_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(task_bp, url_prefix="/api/tasks")

    @app.route("/", methods=["GET"])
    def index():
        return {"code": 0, "message": "backend running"}

    @app.route("/api/health", methods=["GET"])
    def health():
        return {"code": 0, "message": "ok"}

    return app