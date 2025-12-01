from flask import Blueprint, jsonify
import os

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/swagger.json')
def swagger():
    # 可以动态生成或返回静态文件
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "用户&消息api",
            "version": "1.0",
            "description": "API for user authentication and message"
        },
        "servers": [
            {"url": "http://localhost:5000/api", "description": "用户&消息api"}
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    })