@echo off
echo ========================================
echo      抽奖系统 - 启动脚本
echo ========================================
echo.

echo [1/5] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/5] 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建成功
) else (
    echo 虚拟环境已存在
)

echo.
echo [3/5] 激活虚拟环境并安装依赖...
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo [4/5] 执行数据库迁移...
python manage.py migrate

echo.
echo [5/5] 同步奖品库存到 Redis...
python manage.py sync_stock_to_redis

echo.
echo ========================================
echo      启动完成！
echo ========================================
echo.
echo 请确保 PostgreSQL 和 Redis 服务已启动
echo.
echo 常用命令:
echo   启动 Django: python manage.py runserver
echo   启动 Celery: celery -A lottery worker -l info --pool=solo
echo   创建管理员: python manage.py init_admin
echo.
echo 访问地址:
echo   前台页面: http://localhost:8000/
echo   管理后台: http://localhost:8000/admin/
echo.
pause
