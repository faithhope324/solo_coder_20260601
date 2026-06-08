from flask import Flask
import os
from app.config import Config
from app.routes import api_bp
from app.websocket import socketio


def create_app():
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)

    app.register_blueprint(api_bp)

    socketio.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("在线抢答系统启动中...")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("请确保 Redis 服务已启动")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
