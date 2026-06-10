@echo off
echo ========================================
echo      Celery Worker - 启动脚本
echo ========================================
echo.

call venv\Scripts\activate

echo 启动 Celery Worker...
celery -A lottery worker -l info --pool=solo

pause
