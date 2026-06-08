import os
import sys
from app import app
from werkzeug.serving import run_simple

if __name__ == '__main__':
    print("=" * 50)
    print("垃圾分类智能识别系统")
    print("=" * 50)
    print("\n启动服务中...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")
    
    run_simple('0.0.0.0', 5000, app, use_debugger=False, use_reloader=False)
