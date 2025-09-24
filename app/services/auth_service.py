import logging
from datetime import datetime

from models.user import User
from utils.security import generate_jwt_token
from utils.exceptions import AuthError
from extensions import db


class AuthService:
    @staticmethod
    def register_user(username, email, password):
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            raise AuthError('Username already exists', 400)

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            raise AuthError('Email already exists', 400)

        # 创建新用户
        user = User(username=username, email=email, password=password,fcm_token="")
        db.session.add(user)
        db.session.commit()

        from services.session_service import SessionService
        SessionService.init_session(user.id)

        return user

    @staticmethod
    def login_user(username, password,fcm_token):
        user = User.query.filter_by(username=username).first()

        if not user or not user.verify_password(password):
            raise AuthError('Invalid username or password', 401)

        # 生成JWT令牌
        access_token = generate_jwt_token(user.id)

        return {
            'access_token': access_token,
            'user_id': user.public_id,
            'username': user.username,
            'email': user.email
        }

    @staticmethod
    def login_guest(guest,fcm_token):
        user = User.query.filter_by(username=guest).first()

        if not user:
            # 创建新用户
            user = User(username=guest, email=guest, password="",fcm_token=fcm_token)
            db.session.add(user)
            db.session.commit()
            from services.session_service import SessionService
            SessionService.init_session(user.id)
        elif fcm_token:
            logging.warning(f"update fcmtoken:{user.id,fcm_token}")
            user.fcm_token = fcm_token
            user.updated_at = datetime.now()
            db.session.commit()

        # 生成JWT令牌
        access_token = generate_jwt_token(user.id)

        return {
            'access_token': access_token,
            'user_id': user.public_id,
            'username': user.username,
            'email': user.email
        }