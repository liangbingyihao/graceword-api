import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '324354364565757567')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'abdfdfjdfljdgjrldfdfg')
    COZE_API_TOKEN = os.getenv('COZE_API_TOKEN', '111111111111')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    SQLALCHEMY_ECHO = False
    SWAGGER = {
        'openapi': '3.0.2',  # 只保留这一个版本声明
        'title': 'GW API Docs',
        'specs_route': '/api/docs/',
        'init_oauth': None
    }