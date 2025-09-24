from flask import jsonify
from werkzeug.exceptions import HTTPException

class AuthError(HTTPException):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super().__init__(description=message)

def handle_auth_error(ex):
    response = jsonify({
        'success': False,
        'error': ex.status_code,
        'message': ex.message
    })
    response.status_code = ex.status_code
    return response