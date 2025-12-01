import uuid
from datetime import datetime, timezone
from sqlalchemy import text, TIMESTAMP
from extensions import db
from utils.security import generate_password_hash,verify_password


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(100), unique=True, nullable=False)
    fcm_token = db.Column(db.String(255))
    ios_push_token = db.Column(db.String(255))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    updated_at = db.Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    membership_expired_at = db.Column(
        TIMESTAMP,
        server_default=text('NULL'),  # 明确设置默认值为 NULL
        nullable=True
    )

    def __init__(self, username, email, password,fcm_token):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.fcm_token = fcm_token

    def verify_password(self, password):
        return verify_password(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'