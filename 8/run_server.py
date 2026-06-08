import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("  员工离职因素分析系统")
    print("=" * 60)
    print("\n正在启动服务器...")
    print("请在浏览器中访问: http://127.0.0.1:5000")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
