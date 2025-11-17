import logging

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.auth_service import AuthService
from schemas.user_schema import AuthSchema, UserSchema
from services.user_service import UserService
from utils.exceptions import AuthError

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'description': 'Register a new user',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string', 'format': 'password'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'User registered successfully'},
        400: {'description': 'Invalid input'}
    }
})
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    try:
        user = AuthService.register_user(username, email, password)
        return jsonify({
            'success': True,
            'data': AuthSchema().dump(user)
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'description': 'Login with username and password',
    # 类似上面的Swagger定义
})
def login():
    # 登录实现
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    guest = data.get('guest')
    fcm_token = data.get('fcmToken')

    if guest:
        auth_data = AuthService.login_guest(guest, fcm_token)
    else:
        auth_data = AuthService.login_user(username, password, fcm_token)
    logging.warning(f"auth_data:{auth_data}")
    return jsonify({
        'success': True,
        'data': AuthSchema().dump(auth_data)
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = UserService.get_user_by_id(user_id)

    if not user:
        raise AuthError('User not found', 404)

    return jsonify({
        'success': True,
        'data': UserSchema().dump(user)
    })
