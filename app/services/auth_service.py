import logging
from datetime import datetime, timedelta
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
        user = User(username=username, email=email, password=password, fcm_token="")
        db.session.add(user)
        db.session.commit()

        from services.session_service import SessionService
        SessionService.init_session(user.id)

        return user

    @staticmethod
    def login_user(username, password, fcm_token):
        user = User.query.filter_by(username=username).first()

        if not user or not user.verify_password(password):
            raise AuthError('Invalid username or password', 401)

        # 生成JWT令牌
        access_token = generate_jwt_token(user.id)

        return {
            'access_token': access_token,
            'user_id': user.public_id,
            'username': user.username,
            'email': user.email,
            'membership_expired_at': AuthService.cal_membership_left(user)
        }

    @staticmethod
    def login_guest(guest, fcm_token, ios_push_token):
        user = User.query.filter_by(username=guest).first()

        if not user:

            user = User(username=guest, email=guest, password="", fcm_token=fcm_token)
            user.ios_push_token = ios_push_token
            # 创建新用户
            now = datetime.now()
            current_year = now.year
            current_month = now.month

            free_days = 0
            if current_year == 2025 and current_month == 12:
                free_days = 90
            elif current_year == 2026 and current_month == 1:
                free_days = 60
            elif current_year == 2026 and current_month == 2:
                free_days = 30

            if free_days>0:
                user.membership_expired_at = now + timedelta(days=free_days)

            db.session.add(user)
            db.session.commit()
            from services.session_service import SessionService
            SessionService.init_session(user.id)
        elif fcm_token:
            user.fcm_token = fcm_token
            user.updated_at = datetime.now()
            db.session.commit()
        elif ios_push_token:
            user.ios_push_token = ios_push_token
            user.updated_at = datetime.now()
            db.session.commit()

        # 生成JWT令牌
        access_token = generate_jwt_token(user.id)

        return {
            'access_token': access_token,
            'user_id': user.public_id,
            'username': user.username,
            'email': user.email,
            'membership_expired_at': AuthService.cal_membership_left(user)
        }

    @staticmethod
    def cal_membership_left(user):
        if user.membership_expired_at is None:
            return 0
        now = datetime.now()
        # 计算剩余时间
        remaining = user.membership_expired_at - now
        return max(0, remaining.total_seconds())
