from flask import Blueprint, jsonify, request
from flasgger import swag_from
from flask_jwt_extended import jwt_required, get_jwt_identity

from schemas.user_schema import UserSchema
from services.user_service import UserService
from utils.exceptions import AuthError

user_bp = Blueprint('user', __name__)


@user_bp.route('/users', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {'description': 'List of users'},
        401: {'description': 'Unauthorized'}
    }
})
def get_users():
    users = UserService.get_all_users()
    return jsonify({
        'success': True,
        'data': UserSchema(many=True).dump(users)
    })

