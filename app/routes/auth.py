from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.utils.security import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not username or not email or not password:
        return {"code": 1, "message": "username/email/password required"}, 400

    if User.query.filter_by(username=username).first():
        return {"code": 1, "message": "username already exists"}, 400

    if User.query.filter_by(email=email).first():
        return {"code": 1, "message": "email already exists"}, 400

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    return {"code": 0, "message": "register success"}


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return {"code": 1, "message": "invalid username or password"}, 401

    access_token = create_access_token(identity=str(user.id))
    return {
        "code": 0,
        "message": "login success",
        "data": {
            "token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        },
    }