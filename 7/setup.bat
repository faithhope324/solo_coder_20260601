@echo off
echo ========================================
echo 垃圾分类智能识别系统 - 环境配置
echo ========================================
echo.

echo [1/5] 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查 Python 环境
    pause
    exit /b 1
)
echo.

echo [2/5] 生成示例数据...
python generate_sample_data.py
echo.

echo [3/5] 训练模型（首次运行可能需要较长时间）...
python train_model.py
echo.

echo [4/5] 构建图像检索索引...
python build_index.py
echo.

echo [5/5] 配置完成！
echo.
echo ========================================
echo 运行 python run.py 启动服务
echo 访问 http://localhost:5000
echo ========================================
pause
