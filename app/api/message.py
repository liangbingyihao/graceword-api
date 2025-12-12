import logging
import os

from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.favorite_schema import FavoriteSchema
from schemas.message_schema import MessageSchema
from schemas.search_msg_schema import SearchMsgSchema
from schemas.session_msg_schema import SessionMsgSchema
from services.favorite_service import FavoriteService
from services.message_service import MessageService
from services.search_service import SearchService

message_bp = Blueprint('message', __name__)
BASE_YML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'message')

@message_bp.route('', methods=['POST'])
@swag_from(os.path.join(BASE_YML_DIR, 'add.yml'))
@jwt_required()
def add():
    data = request.get_json()
    content = data.get('text')  # 新增的信息内容
    action = data.get('action')  # 新增的信息内容
    context_id = data.get('context_id') or 0  # 探索对应的原msg id
    prompt = data.get("prompt")
    reply = data.get("reply")
    lang = request.args.get('lang', default="zh-hant", type=str)
    owner_id = get_jwt_identity()
    # session_id = data.get("session_id")

    if not content:
        return jsonify({"error": "Missing required parameter 'content'"}), 400

    message_id = MessageService.new_message(owner_id, content, context_id, action, prompt, reply,lang)
    return jsonify({
        'success': True,
        'data': {"id": message_id}
    }), 201


@message_bp.route('/renew', methods=['POST'])
@jwt_required()
def renew():
    owner_id = get_jwt_identity()
    data = request.get_json()
    prompt = data.get("prompt")
    msg_id = data.get("message_id")
    logging.warning(f"renew message:{msg_id}")
    # session_id = data.get("session_id")

    message_id = MessageService.renew(owner_id, msg_id, prompt)
    return jsonify({
        'success': message_id == msg_id,
        'data': {"id": message_id}
    }), 201


@message_bp.route('/del', methods=['POST'])
@swag_from(os.path.join(BASE_YML_DIR, 'del.yml'))
@jwt_required()
def del_msg():
    owner_id = get_jwt_identity()
    data = request.get_json()
    content_type = data.get("content_type")
    msg_id = data.get("message_id")
    logging.warning(f"del message:{content_type}")
    # session_id = data.get("session_id")

    message_id = MessageService.del_msg(owner_id, msg_id, content_type)
    return jsonify({
        'success': message_id == msg_id,
        'data': {"id": message_id}
    }), 200


@message_bp.route('', methods=['GET'])
# @swag_from({
#     'tags': ['message'],
#     'description': 'my message',
#     # 类似上面的Swagger定义
# })
@jwt_required()
def my_message():
    # FIXME 下个版本仅获取message，不搜索
    owner_id = get_jwt_identity()
    # 获取特定参数（带默认值）
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    session_id = request.args.get("session_id", default=0, type=int)
    session_type = request.args.get("session_type", default='', type=str)  # "topic", "question"
    search = request.args.get('search', default='', type=str)

    if session_type == "favorite":
        data = FavoriteService.get_favorite_by_owner(owner_id, page=page,
                                                     limit=limit, search=search)
    else:
        data = MessageService.filter_message(owner_id=owner_id, session_id=session_id, session_type=session_type,
                                             search=search, page=page,
                                             limit=limit)
    # import flask_sqlalchemy
    # if isinstance(data, flask_sqlalchemy.BaseQuery):
    #     return jsonify({
    #         'success': True,
    #         'data': {
    #             'items': SessionMsgSchema(many=True).dump(data)
    #         }
    #     })
    # else:
    return jsonify({
        'success': True,
        'data': {
            'items': SessionMsgSchema(many=True).dump(data)
        }
    })


# 带msg_id参数的路由
@message_bp.route('/<string:msg_id>', methods=['GET'])
@swag_from(os.path.join(BASE_YML_DIR, 'detail.yml'))
@jwt_required()
def msg_detail(msg_id):
    owner_id = get_jwt_identity()
    retry = request.args.get('retry', default=0, type=int)
    stop = request.args.get('stop', default=0, type=int)
    lang = request.args.get('lang', default='', type=str)
    logging.warning(f"get_message:{msg_id}")
    if msg_id == "welcome":
        return jsonify({
            'success': True,
            'data': MessageService.welcome_msg
        })
    else:
        data = MessageService.get_message(owner_id, msg_id, retry, stop, lang)
        return jsonify({
            'success': True,
            'data': MessageSchema().dump(data)
        })


# 带msg_id参数的路由
@message_bp.route('/<string:msg_id>', methods=['POST'])
@jwt_required()
def set_summary(msg_id):
    data = request.get_json()
    summary = data.get('summary')
    session_id = data.get('session_id')
    session_name = data.get('session_name')
    owner_id = get_jwt_identity()
    if summary and len(summary) > 120:
        return jsonify({"error": "summary max length is 120"}), 400
    session_id = MessageService.set_summary(owner_id, msg_id, summary, session_id, session_name)
    return jsonify({
        'success': True,
        'data': {
            "session_id": session_id
        }
    })

@message_bp.route('/<string:msg_id>/renew', methods=['POST'])
@swag_from({
    'tags': ['message'],
    'summary': '重新生成ai回复',
    'consumes': ['application/json'],
    'responses': {
        '201': {
            'description': '成功',
            'content': {
                'application/json': {
                    'schema':{
                        '$ref': '#/components/schemas/MessageId'
                    }
                }
            }
        }
    },
    'security': [{'Bearer': []}]
})
@jwt_required()
def renew_message(msg_id):
    owner_id = get_jwt_identity()
    logging.warning(f"renew message:{msg_id}")
    # session_id = data.get("session_id")

    message_id = MessageService.renew(owner_id, msg_id, "")
    return jsonify({
        'success': message_id == msg_id,
        'data': {"id": message_id}
    }), 201


@message_bp.route('filter', methods=['GET'])
# @swag_from({
#     'tags': ['消息'],
#     'description': 'filter message',
#     # 类似上面的Swagger定义
# })
@jwt_required()
def search_message():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    session_id = request.args.get("session_id", default=0, type=int)
    session_type = request.args.get("session_type", default='', type=str)  # "topic", "question"
    search = request.args.get('search', default='', type=str)
    owner_id = get_jwt_identity()

    # try:
    data = SearchService.filter_message(owner_id=owner_id, session_id=session_id, session_type=session_type,
                                        search=search, page=page,
                                        limit=limit)
    return jsonify({
        'success': True,
        'data': {
            'items': data
        }
    })
    # except Exception as e:
    #     return jsonify({
    #         'success': False,
    #         'message': str(e)
    #     }), 400
