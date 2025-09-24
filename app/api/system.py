from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.user_schema import UserSchema
from services.coze_service import  msg_feedback,msg_explore,msg_pray

system_bp = Blueprint('system', __name__)


@system_bp.route('/conf', methods=['GET'])
@jwt_required()
def get_configure():
    return jsonify({
        'success': True,
        'data': {"record":msg_feedback,
                 "talk":msg_explore,
                 "pray":msg_pray}
    })

