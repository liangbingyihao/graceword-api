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
# @swag_from({
#     'tags': ['user'],
#     'description': 'Register a new user',
#     'parameters': [
#         {
#             'name': 'body',
#             'in': 'body',
#             'required': True,
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'username': {'type': 'string'},
#                     'email': {'type': 'string', 'format': 'email'},
#                     'password': {'type': 'string', 'format': 'password'}
#                 }
#             }
#         }
#     ],
#     'responses': {
#         201: {'description': 'User registered successfully'},
#         400: {'description': 'Invalid input'}
#     }
# })
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
    'tags': ['user'],
    'summary': '用户登录',
    'consumes': ['application/json'],
    "produces": [
        "application/json"
    ],
    'description': '用户登录接口，支持普通登录和游客登录，更新推送token。登录成功后返回用户信息和访问令牌。',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {
                        'type': 'string',
                        'description': '用户名',
                        'example': 'admin'
                    },
                    'password': {
                        'type': 'string',
                        'format': 'password',
                        'description': '密码',
                        'example': '123456'
                    },
                    'guest': {
                        'type': 'string',
                        'description': '如果是游客登录则设置本字段为设备的唯一标识，username和password参数不需要提供',
                        'example': "6c6cbd0d-503a-38e1-ba88-252340860c1a"
                    },
                    'fcmToken': {
                        'type': 'string',
                        'description': 'FCM推送令牌（Android设备）',
                        'example': 'fcm_token_here_12345'
                    },
                    'ios_push_token': {
                        'type': 'string',
                        'description': 'APNs推送令牌（iOS设备）',
                        'example': 'apns_token_here_12345'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': '登录成功',
            'content': {
                'application/json': {
                    'schema':{
                        '$ref': '#/components/schemas/User'
                    }
                }
            },
        }
    }
})
def login():
    # 登录实现
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    guest = data.get('guest')
    fcm_token = data.get('fcmToken')
    ios_token = data.get('ios_push_token')

    if guest:
        auth_data = AuthService.login_guest(guest, fcm_token, ios_token)
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
