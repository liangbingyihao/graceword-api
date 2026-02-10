import logging
import os

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.favorite_schema import FavoriteSchema
from schemas.session_schema import SessionSchema
from services.favorite_service import FavoriteService
from services.session_service import SessionService
from utils.exceptions import AuthError
from utils.security import get_user_id

favorite_bp = Blueprint('favorite', __name__)
BASE_YML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'favorite')


@favorite_bp.route('', methods=['POST'])
@jwt_required()
def add():
    data = request.get_json()
    message_id = data.get('message_id')
    content_type = data.get('content_type')
    owner_id = get_user_id(request.headers) or get_jwt_identity()

    try:
        res = FavoriteService.new_favorite(owner_id, message_id, content_type)
        return jsonify({
            'success': res
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@favorite_bp.route('/toggle', methods=['POST'])
@swag_from({
    'tags': ['收藏'],
    'description': '调转收藏状态（已收藏变未收藏，未收藏变已收藏）',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'message_id': {
                        'type': 'integer',
                        'example': 12345,
                        'description': '消息的唯一标识ID'
                    },
                    'content_type': {
                        'type': 'integer',
                        'enum': [1, 2],  # 明确枚举值
                        'example': 1,
                        'description': '内容类型: 1-用户信息, 2-AI信息'
                    }
                },
                'required': ['message_id', 'content_type']
            }
        }
    ],
    'responses': {
        200: {'success': "true/false", 'data': "0,不再收藏，1，已收藏，其他：失败"}
    }
})
@jwt_required()
def toggle():
    data = request.get_json()
    message_id = data.get('message_id')
    content_type = data.get('content_type')
    owner_id = get_user_id(request.headers) or get_jwt_identity()

    try:
        res = FavoriteService.toggle_favorite(owner_id, message_id, content_type)
        return jsonify({
            'success': True,
            'data': res
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400


@favorite_bp.route('', methods=['GET'])
@swag_from(os.path.join(BASE_YML_DIR, 'list.yml'))
@jwt_required()
def my_favorites():
    owner_id = get_user_id(request.headers) or get_jwt_identity()
    search = request.args.get('search', default="", type=str)
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    logging.warning(f"my_favorites:{owner_id}")

    try:
        items = FavoriteService.get_favorite_by_owner(owner_id, page=page,
                                                      limit=limit, search=search)
        return jsonify({
            'success': True,
            # 'data': SessionSchema(many=True).dump(data),
            'data': {
                'items': FavoriteSchema(many=True).dump(items),
            }
        })
    except AuthError as e:
        raise e
    except Exception as e:
        raise AuthError(str(e), 500)
