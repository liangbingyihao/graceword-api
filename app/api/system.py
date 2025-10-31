from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.user_schema import UserSchema

system_bp = Blueprint('system', __name__)


@system_bp.route('/conf', methods=['GET'])
@jwt_required()
def get_configure():
    return jsonify({
        'success': True,
        'data': {"record":"",
                 "talk":"",
                 "pray":""}
    })

