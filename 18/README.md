# 抽奖系统

基于 Django + PostgreSQL + Redis 构建的高性能抽奖系统，支持转盘动画、概率抽奖、库存管理、实时推送等功能。

## 功能特性

### 🎯 核心功能
- **转盘抽奖**: Canvas 绘制的精美转盘，流畅的转动动画
- **概率算法**: 按配置概率抽取奖品，支持库存检查和自动重抽
- **每日限制**: 用户每日 3 次免费抽奖机会
- **实时更新**: WebSocket 实时推送剩余抽奖次数和中奖结果

### 🏆 奖品配置
| 奖项 | 奖品 | 概率 | 库存 |
|------|------|------|------|
| 一等奖 | iPhone 15 Pro | 1% | 10 |
| 二等奖 | 蓝牙耳机 | 5% | 100 |
| 三等奖 | 优惠券 | 14% | 1000 |
| 四等奖 | 50积分 | 20% | 10000 |
| 五等奖 | 20积分 | 20% | 10000 |
| 六等奖 | 10积分 | 20% | 10000 |
| 七等奖 | 5积分 | 10% | 10000 |
| 八等奖 | 谢谢参与 | 10% | 999999 |

### 🔒 安全限制
- **Redis 限流**: 同一用户每秒只能抽一次
- **库存扣减**: 原子操作，避免超卖
- **自动重抽**: 库存不足时自动抽取其他奖品，提升用户体验

### 👨‍💼 管理后台
- 奖品管理：配置奖品信息、概率、库存
- 抽奖记录：查看所有用户的中奖记录，含今日统计
- 用户管理：管理用户信息和积分
- 批量操作：同步库存到 Redis、清除缓存等

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Django | 4.2+ | Web 框架 |
| PostgreSQL | 12+ | 关系型数据库 |
| Redis | 6.0+ | 缓存、消息队列、限流 |
| Celery | 5.3+ | 异步任务队列 |
| Channels | 4.0+ | WebSocket 实时通信 |
| Canvas | HTML5 | 转盘动画绘制 |

## 项目结构

```
lottery-system/
├── lottery/                    # Django 项目配置
│   ├── __init__.py
│   ├── asgi.py                # ASGI 配置（WebSocket）
│   ├── celery.py              # Celery 配置
│   ├── settings.py            # 项目设置
│   ├── urls.py                # 主路由
│   └── wsgi.py                # WSGI 配置
├── lottery_app/               # 抽奖应用
│   ├── migrations/            # 数据库迁移
│   ├── management/            # 管理命令
│   │   └── commands/
│   │       ├── init_admin.py
│   │       └── sync_stock_to_redis.py
│   ├── admin.py               # Django Admin 配置
│   ├── consumers.py           # WebSocket 消费者
│   ├── lottery_algorithm.py   # 抽奖算法核心
│   ├── middleware.py          # 限流中间件
│   ├── models.py              # 数据模型
│   ├── redis_service.py       # Redis 服务
│   ├── routing.py             # WebSocket 路由
│   ├── tasks.py               # Celery 异步任务
│   ├── urls.py                # 应用路由
│   └── views.py               # 视图函数
├── templates/                 # 模板文件
│   ├── admin/                 # Admin 自定义模板
│   ├── base.html
│   ├── index.html             # 抽奖主页面
│   └── login.html             # 登录页面
├── static/                    # 静态文件
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── common.js
│       └── lottery.js         # 转盘核心逻辑
├── manage.py
├── requirements.txt
├── .env.example
├── start.bat                  # Windows 启动脚本
└── start_celery.bat           # Celery 启动脚本
```

## 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6.0+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd lottery-system
```

2. **配置环境变量**
```bash
copy .env.example .env
```

编辑 `.env` 文件，配置数据库和 Redis 连接信息。

3. **一键启动（Windows）**
```bash
start.bat
```

4. **手动安装**
```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建管理员
python manage.py init_admin

# 同步库存到 Redis
python manage.py sync_stock_to_redis
```

### 启动服务

1. **启动 Django**
```bash
python manage.py runserver
```

2. **启动 Celery（新终端）**
```bash
celery -A lottery worker -l info --pool=solo
```

3. **访问应用**
- 前台页面: http://localhost:8000/
- 管理后台: http://localhost:8000/admin/
- 默认账号: admin / admin123456

## 核心模块说明

### 抽奖算法 ([lottery_algorithm.py](lottery_app/lottery_algorithm.py))
- 概率区间计算：将奖品概率转换为连续区间
- 随机数抽取：生成 0-100 随机数匹配对应区间
- 库存检查：Redis 原子操作 DECR 扣减库存
- 自动重抽：库存不足时自动重试，最多 5 次
- 兜底机制：重试失败时从高到低等级抽取有库存奖品

### Redis 服务 ([redis_service.py](lottery_app/redis_service.py))
- Key 设计:
  - `prize:stock:{prize_id}` - 奖品库存
  - `rate_limit:user:{user_id}` - 用户限流
  - `daily_chance:user:{user_id}:{date}` - 每日抽奖次数
- 限流：滑动窗口，每秒 1 次
- 抽奖次数：每日 3 次，自动过期

### 限流中间件 ([middleware.py](lottery_app/middleware.py))
- 针对 `/api/draw/` 和 `/draw/` 的 POST 请求
- 返回 429 状态码和等待时间

### 异步任务 ([tasks.py](lottery_app/tasks.py))
- 抽奖记录异步写入 PostgreSQL
- WebSocket 实时推送中奖结果
- 库存同步任务
- 缓存清除任务

### WebSocket ([consumers.py](lottery_app/consumers.py))
- 实时推送剩余抽奖次数
- 实时推送中奖结果
- 自动重连机制

### 前端转盘 ([lottery.js](static/js/lottery.js))
- Canvas 动态绘制转盘
- 缓动动画效果
- WebSocket 连接管理
- 抽奖记录分页加载

## API 接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 抽奖主页 | 是 |
| GET/POST | `/login/` | 用户登录 | 否 |
| GET | `/logout/` | 用户登出 | 是 |
| GET | `/api/prizes/` | 获取奖品列表 | 是 |
| GET | `/api/chances/` | 获取剩余次数 | 是 |
| POST | `/api/draw/` | 执行抽奖 | 是 |
| GET | `/api/records/` | 获取抽奖记录 | 是 |

### 抽奖接口响应
```json
{
    "success": true,
    "message": "抽奖成功",
    "prize": {
        "id": 1,
        "name": "iPhone 15 Pro",
        "prize_type": 1,
        "prize_type_display": "一等奖",
        "points_value": 10000,
        "is_win": true
    },
    "remaining_chances": 2,
    "prize_index": 0
}
```

## 管理后台功能

### 奖品管理
- 奖品名称、描述、图片
- 概率配置（0-100%）
- 总库存、当前库存
- 积分价值
- 启用/禁用状态
- 排序设置
- 批量操作：同步库存、清除缓存、启用/禁用

### 抽奖记录管理
- 今日统计面板（总次数、中奖次数、中奖率、各奖项分布）
- 按奖项、中奖状态、时间筛选
- 用户、奖品、IP、时间展示
- 只读模式，防止篡改

### 用户管理
- 用户基本信息
- 积分管理
- 权限配置

## 部署建议

### 生产环境配置
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']

# 使用 Uvicorn 部署 ASGI
# pip install uvicorn
# uvicorn lottery.asgi:application --host 0.0.0.0 --port 8000
```

### Nginx 配置
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 常见问题

### Q: 如何修改每日免费抽奖次数？
A: 在 `settings.py` 中修改 `DAILY_FREE_CHANCES` 配置。

### Q: 如何添加新的奖品？
A: 在 Django Admin 后台的奖品管理中添加，设置好概率和库存后会自动生效。

### Q: Redis 中的库存和数据库不一致怎么办？
A: 在 Admin 后台执行"同步所有奖品库存到 Redis"操作，或执行命令：
```bash
python manage.py sync_stock_to_redis
```

### Q: 如何防止用户刷奖？
A: 系统已内置多层防护：
1. Redis 限流（每秒 1 次）
2. 每日次数限制（3 次）
3. 用户登录验证
4. IP 地址记录

## License

MIT License
