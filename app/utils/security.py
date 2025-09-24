import base64
import hashlib
import hmac
import os
from typing import Optional

import bcrypt
from flask import current_app

def generate_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_jwt_token(identity):
    from flask_jwt_extended import create_access_token
    return create_access_token(identity=identity)

def verify_jwt_token(token):
    from flask_jwt_extended import decode_token
    try:
        decoded_token = decode_token(token)
        return decoded_token['sub']
    except:
        return None


SECRET_KEY = os.getenv("SECRET_KEY")


def generate_public_id(db_id: int) -> str:
    """
    生成混淆后的公共用户ID
    :param db_id: 数据库自增ID
    :return: 混淆后的公共ID
    """
    hmac_obj = hmac.new(
        SECRET_KEY.encode(),
        str(db_id).encode(),
        hashlib.sha256
    )
    return base64.urlsafe_b64encode(hmac_obj.digest()).decode().rstrip('=')


def parse_internal_id(public_id: str) -> Optional[int]:
    """
    解析公共ID获取原始数据库ID（简化版，实际需要存储映射关系）
    """
    try:
        # 补全Base64填充
        padding = len(public_id) % 4
        if padding:
            public_id += '=' * (4 - padding)

        decoded = base64.urlsafe_b64decode(public_id.encode())
        # 实际应用中这里应该验证HMAC签名
        return int.from_bytes(decoded[:4], byteorder='big')
    except:
        return None