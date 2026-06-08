# 垃圾分类智能识别系统

基于深度学习的垃圾分类识别系统，使用 MobileNetV2 进行迁移学习，支持四类垃圾识别和相似图片检索。

## 功能特性

- 🤖 **智能识别**: 自动识别四类垃圾（可回收、厨余、有害、其他）
- 🔍 **相似检索**: 基于特征向量的相似图片检索
- 📱 **友好界面**: 响应式 Web 界面，支持拖拽上传
- 📊 **置信度显示**: 显示各类别的识别置信度

## 项目结构

```
garbage-classification/
├── app/
│   ├── __init__.py          # Flask 应用初始化
│   ├── routes.py            # 路由定义
│   ├── classifier.py        # 图像分类模块
│   └── feature_extractor.py # 特征提取和图像检索
├── models/                  # 模型和索引文件目录
├── data/
│   ├── train/               # 训练数据
│   │   ├── 可回收/
│   │   ├── 厨余/
│   │   ├── 有害/
│   └── 其他/
│   └── valid/               # 验证数据
├── static/
│   ├── css/style.css        # 样式文件
│   ├── js/app.js            # 前端逻辑
│   ├── uploads/             # 上传图片目录
│   └── similar/             # 相似图片目录
├── templates/
│   └── index.html           # 主页模板
├── train_model.py           # 模型训练脚本
├── generate_sample_data.py  # 生成示例数据
├── build_index.py           # 构建图像索引
├── run.py                   # 启动应用
└── requirements.txt         # 依赖清单
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成示例数据（可选）

```bash
python generate_sample_data.py
```

### 3. 训练模型

```bash
python train_model.py
```

### 4. 构建图像索引

```bash
python build_index.py
```

### 5. 启动应用

```bash
python run.py
```

然后访问 http://localhost:5000

## API 接口

### POST /api/classify
图像分类接口

**请求**:
- `image`: 图片文件

**响应**:
```json
{
  "success": true,
  "image_url": "/static/uploads/xxx.jpg",
  "predictions": [
    {
      "class": "可回收",
      "confidence": 0.92,
      "description": "...",
      "color": "#2196F3"
    }
  ]
}
```

### POST /api/search
相似图片检索接口

**请求**:
- `image`: 图片文件
- `top_k`: 返回数量（默认5）

**响应**:
```json
{
  "success": true,
  "query_image": "/static/uploads/xxx.jpg",
  "similar_images": [
    {
      "url": "/static/similar/xxx.jpg",
      "similarity": 0.85,
      "label": "可回收"
    }
  ]
}
```

### POST /api/classify_and_search
分类+检索合并接口

### GET /api/health
健康检查接口

## 垃圾类别说明

| 类别 | 颜色 | 说明 | 示例 |
|------|------|------|------|
| 可回收 | 🔵 蓝色 | 可循环利用的废弃物 | 废纸、塑料、玻璃、金属 |
| 厨余 | 🟢 绿色 | 易腐烂的生物质废弃物 | 剩菜、果皮、菜叶 |
| 有害 | 🔴 红色 | 对健康环境有害的废弃物 | 电池、药品、灯管 |
| 其他 | ⚫ 灰色 | 难以回收的其他废弃物 | 砖瓦、渣土、卫生纸 |

## 技术栈

- **后端框架**: Flask
- **深度学习**: TensorFlow + Keras
- **预训练模型**: MobileNetV2
- **特征匹配**: 余弦相似度
- **前端**: 原生 HTML/CSS/JavaScript

## 自定义数据集

将你的图片按类别放入 `data/train` 和 `data/valid` 对应的子目录中：

```
data/train/
├── 可回收/
│   ├── img1.jpg
│   └── img2.jpg
├── 厨余/
│   ├── img1.jpg
│   └── img2.jpg
...
```

## License

MIT
