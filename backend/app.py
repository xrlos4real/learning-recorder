"""Flask 入口 — 注册蓝图、CORS、自动建表、错误处理"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS — 允许跨域
    CORS(app, origins=[
    "http://localhost:5173",
    "https://learning-recorder-mu.vercel.app"  # 换成你的真实域名
])

    # 禁用严格尾部斜杠，避免 /api/logs → /api/logs/ 重定向
    app.url_map.strict_slashes = False

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    from routes.logs import logs_bp
    from routes.tags import tags_bp
    from routes.stats import stats_bp

    app.register_blueprint(logs_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(stats_bp)

    # 自动建表
    with app.app_context():
        db.create_all()

    # 统一错误处理
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(code=400, data=None, msg=str(e.description) or "请求参数错误"), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(code=404, data=None, msg="资源不存在"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(code=500, data=None, msg="服务器内部错误"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
