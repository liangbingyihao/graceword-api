import os

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.session_schema import SessionSchema
from services.session_service import SessionService
from utils.exceptions import AuthError

session_bp = Blueprint('session', __name__)

BASE_YML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'session')

@session_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['恩语录'],
    'description': '增加主题',
    # 类似上面的Swagger定义
})
@jwt_required()
def add():
    data = request.get_json()
    session_name = data.get('session_name')
    owner_id = get_jwt_identity()
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
# @swag_from({
#     'tags': ['session'],
#     'description': 'my sessions',
#     'parameters': [
#         {
#             'name': 'page',
#             'in': 'query',
#             'schema': {'type': 'integer', 'default': 1},
#             'description': '页码'
#         },
#         {
#             'name': 'limit',
#             'in': 'query',
#             'schema': {'type': 'integer', 'default': 10},
#             'description': '每页数量'
#         }
#     ],
#     # 类似上面的Swagger定义
# })
@jwt_required()
def my_sessions():
    owner_id = get_jwt_identity()
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


@session_bp.route('del', methods=['POST'])
@swag_from({
    'tags': ['恩语录'],
    'description': '删除主题',
    # 类似上面的Swagger定义
})
@jwt_required()
def del_session():
    data = request.get_json()
    session_id = data.get('session_id')
    owner_id = get_jwt_identity()

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
    owner_id = get_jwt_identity()
    if session_name and len(session_name) > 20:
        return jsonify({"error": "session_name max length is 8"}), 400
    ret = SessionService.set_session_name(owner_id, session_id, session_name)
    return jsonify({
        'success': ret
    })
