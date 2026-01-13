import logging
import os

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.session_schema import SessionSchema
from schemas.session_msg_schema import SessionMsgSchema
from services.session_service import SessionService
from services.message_service import MessageService
from utils.exceptions import AuthError
from utils.security import get_user_id

session_bp = Blueprint('session', __name__)

BASE_YML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'session')

@session_bp.route('', methods=['POST'])
# @swag_from({
#     'tags': ['恩语录'],
#     'description': '增加主题',
#     # 类似上面的Swagger定义
# })
@jwt_required()
def add():
    data = request.get_json()
    session_name = data.get('session_name')
    owner_id = get_user_id(request.headers) or get_jwt_identity()
    robot_id = data.get('robot_id')

    try:
        session = SessionService.new_session(session_name, owner_id, robot_id)
        return jsonify({
            'success': True,
            'data': SessionSchema().dump(session)
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@session_bp.route('', methods=['GET'])
@swag_from(os.path.join(BASE_YML_DIR, 'list.yml'))
@jwt_required()
def my_sessions():
    # logging.warning("=== HTTP Headers ===")
    # for header, value in request.headers.items():
    #     logging.warning(f"{header}: {value}")
    owner_id = get_user_id(request.headers) or get_jwt_identity()
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)

    data = SessionService.get_session_by_owner(owner_id, page=page,
                                               limit=limit)
    return jsonify({
        'success': True,
        # 'data': SessionSchema(many=True).dump(data),
        'data': {
            'items': SessionSchema(many=True).dump(data.items),
            'total': data.total
        }
    })


@session_bp.route('message', methods=['GET'])
@jwt_required()
def my_message():
    owner_id = get_user_id(request.headers) or get_jwt_identity()
    # 获取特定参数（带默认值）
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    session_id = request.args.get("session_id", default=0, type=int)
    status = request.args.get('status', default=-1, type=int)
    older_than = request.args.get('older_than', default='', type=int)

    data = MessageService.filter_message(owner_id=owner_id,older_than=older_than,
                                         session_id=session_id, status=status, page=page,
                                         limit=limit, with_ai=False)
    return jsonify({
        'success': True,
        'data': {
            'items': SessionMsgSchema(many=True).dump(data)
        }
    })

@session_bp.route('del', methods=['POST'])
@swag_from({
    'tags': ['session'],
    'description': '删除主题',
    # 类似上面的Swagger定义
})
@jwt_required()
def del_session():
    data = request.get_json()
    session_id = data.get('session_id')
    owner_id = get_user_id(request.headers) or get_jwt_identity()

    session = SessionService.del_session(owner_id, session_id)
    return jsonify({
        'success': True
    }), 201


# 带msg_id参数的路由
@session_bp.route('/<int:session_id>', methods=['POST'])
@jwt_required()
def set_topic(session_id):
    data = request.get_json()
    session_name = data.get('session_name')
    owner_id = get_user_id(request.headers) or get_jwt_identity()
    if session_name and len(session_name) > 20:
        return jsonify({"error": "session_name max length is 8"}), 400
    ret = SessionService.set_session_name(owner_id, session_id, session_name)
    return jsonify({
        'success': ret
    })
