from flask import Blueprint
from flasgger import Swagger


def init_api(app):
    # 主蓝图
    main_bp = Blueprint('api', __name__)

    # 注册子蓝图
    from .auth import auth_bp
    from .user import user_bp
    from .session import session_bp
    from .message import message_bp
    from .docs import docs_bp
    from .system import system_bp
    from .favorite import favorite_bp

    main_bp.register_blueprint(auth_bp, url_prefix='/api/auth')
    main_bp.register_blueprint(user_bp, url_prefix='/api/user')
    main_bp.register_blueprint(session_bp, url_prefix='/api/session')
    main_bp.register_blueprint(message_bp, url_prefix='/api/message')
    main_bp.register_blueprint(system_bp, url_prefix='/api/system')
    main_bp.register_blueprint(favorite_bp, url_prefix='/api/favorite')
    main_bp.register_blueprint(docs_bp)

    # 注册主蓝图
    app.register_blueprint(main_bp)

    # 初始化Swagger
    Swagger(app, template_file='static/swagger.json')
