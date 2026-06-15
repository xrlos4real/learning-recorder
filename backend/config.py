"""应用配置"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "learning-log-dev-key-2026"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"sqlite:///{os.path.join(BASE_DIR, 'data', 'log.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False  # 让 Flask 直接输出中文，不转义为 \uxxxx
