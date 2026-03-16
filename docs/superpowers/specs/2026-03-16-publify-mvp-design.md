# Publify MVP 设计文档

**项目名称：** Publify
**日期：** 2026-03-16
**状态：** 设计已批准
**版本：** 1.0

## 概述

Publify 是一个面向中国国内社交媒体平台的发布 API 服务，让 AI 代理能够自动发布内容到小红书等平台。

**目标用户：** 中国的 AI 应用开发者、内容创作者和企业。

**核心价值：** 让 AI 能够通过 API 调用发布内容到中国社交媒体平台。

## 项目范围（第一阶段 - MVP）

### 包含功能
- 用户注册和认证（用户名 + 密码）
- API Key 生成和管理
- 小红书 OAuth 集成
- 内容发布：文字、图片和视频
- 简单的 Web 管理后台
- 发布记录查询

### 不包含功能（后续阶段）
- 敏感内容过滤
- 定时发布
- Webhook 通知
- API 速率限制
- 其他平台（微博、B站、抖音等）

## 架构设计

### 方案：单体服务

单个 FastAPI 应用包含所有功能。

**理由：**
- 开发和部署最简单
- MVP 范围足够
- 需要时可以拆分为微服务

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      Web 浏览器                           │
│  (登录、仪表盘、API Key 管理、授权流程)                   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTML/JSON
                       ↓
┌─────────────────────────────────────────────────────────┐
│                    FastAPI 应用                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  认证中间件 (Session/JWT)                         │  │
│  │  路由处理器                                        │  │
│  │  业务逻辑服务                                      │  │
│  └───────────────────────────────────────────────────┘  │
└────────┬──────────────────────────────┬────────────────┘
         │                              │
         ↓                              ↓
┌─────────────────┐            ┌─────────────────┐
│  PostgreSQL     │            │     Redis       │
│  - 用户数据      │            │  - 会话         │
│  - API Keys     │            │  - 缓存         │
│  - 授权信息      │            │  - 令牌         │
│  - 发布记录      │            │                 │
└─────────────────┘            └─────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│              外部服务                                     │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐      │
│  │  七牛云    │  │ 腾讯云     │  │   小红书      │      │
│  │  存储      │  │ COS        │  │   API         │      │
│  │ (开发)     │  │ (生产)     │  │               │      │
│  └────────────┘  └────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
publify/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── models/                 # 数据库模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型
│   │   ├── api_key.py          # API Key 模型
│   │   ├── xiaohongshu.py      # 小红书授权模型
│   │   └── post.py             # 发布记录模型
│   ├── schemas/                # Pydantic 模式（API 请求/响应）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── publish.py
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py             # 注册/登录
│   │   ├── dashboard.py        # 仪表盘
│   │   ├── api_keys.py         # API Key 管理
│   │   ├── xiaohongshu.py      # 小红书授权
│   │   └── publish.py          # 发布 API
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── xiaohongshu_service.py
│   │   ├── storage_service.py  # 七牛云/腾讯云存储
│   │   └── publish_service.py
│   ├── templates/              # Jinja2 模板
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   └── ...
│   └── static/                 # 静态文件
│       ├── css/
│       └── js/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 数据库设计

### 用户表 (users)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(50) | 唯一用户名 |
| password_hash | String(255) | Bcrypt 密码哈希 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### API Keys 表 (api_keys)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 外键 → users.id |
| key | String(64) | 唯一 API key |
| name | String(100) | Key 名称（如"我的应用"） |
| last_used | DateTime | 最后使用时间 |
| created_at | DateTime | 创建时间 |
| is_active | Boolean | 启用状态 |

### 小红书授权表 (xiaohongshu_auth)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 外键 → users.id |
| access_token | Text | 访问令牌 |
| refresh_token | Text | 刷新令牌 |
| expires_at | DateTime | 令牌过期时间 |
| created_at | DateTime | 创建时间 |

### 发布记录表 (posts)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 外键 → users.id |
| platform | String(20) | 平台名称（xiaohongshu） |
| content_type | String(10) | 类型（text/image/video） |
| content | Text | 文字内容 |
| media_urls | Text | 媒体 URL（JSON 数组） |
| status | String(20) | 状态（pending/success/failed） |
| error_message | Text | 错误详情 |
| created_at | DateTime | 创建时间 |

## API 设计

### Web 页面路由

| 路由 | 方法 | 说明 | 需要认证 |
|------|------|------|----------|
| `/` | GET | 首页 | 否 |
| `/register` | GET/POST | 注册页面 | 否 |
| `/login` | GET/POST | 登录页面 | 否 |
| `/logout` | POST | 登出 | 是 |
| `/dashboard` | GET | 仪表盘 | 是 |
| `/api-keys` | GET | API Key 管理 | 是 |
| `/xiaohongshu/auth` | GET | 小红书 OAuth 开始 | 是 |
| `/xiaohongshu/callback` | GET | 小红书 OAuth 回调 | 是 |
| `/posts` | GET | 发布历史 | 是 |

### REST API（API Key 认证）

| 路由 | 方法 | 说明 | 需要认证 |
|------|------|------|----------|
| `/api/v1/publish` | POST | 发布内容 | 是（API Key） |
| `/api/v1/posts` | GET | 查询发布记录 | 是（API Key） |
| `/api/v1/posts/{id}` | GET | 查询单条记录 | 是（API Key） |
| `/api/v1/auth/status` | GET | 授权状态 | 是（API Key） |

### 发布 API 请求示例

```json
POST /api/v1/publish
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "platform": "xiaohongshu",
  "content_type": "image",
  "text": "这是要发布的内容",
  "media_urls": ["https://cdn.example.com/image1.jpg"]
}
```

### 发布 API 响应示例

```json
{
  "success": true,
  "data": {
    "post_id": 123,
    "platform": "xiaohongshu",
    "status": "pending",
    "created_at": "2026-03-16T12:00:00Z"
  }
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "请先授权小红书账号",
    "details": {}
  }
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| AUTH_REQUIRED | 需要授权 |
| INVALID_API_KEY | API Key 无效 |
| INVALID_CONTENT | 内容格式无效 |
| MEDIA_TOO_LARGE | 媒体文件过大 |
| PLATFORM_ERROR | 平台 API 错误 |
| RATE_LIMITED | 超出速率限制 |

## 认证流程

### 主要认证策略

**Web 仪表盘：** 基于 Session 的认证
- 所有 Web 路由使用 session cookies
- Session 存储在 Redis 中，7天过期
- 所有表单启用 CSRF 保护

**REST API：** 基于 API Key 的认证
- 所有 `/api/v1/*` 路由需要 API Key
- API Keys 存储在数据库中，跟踪最后使用时间
- 不使用 JWT（MVP 简化）

### Web 登录（基于 Session）

```
用户输入用户名/密码
  → 从数据库验证凭据
  → 使用 UUID 创建 session
  → 存储到 Redis（key: session_id, value: user_id, ttl: 7天）
  → 设置安全 cookie（session_id）
  → 重定向到仪表盘
```

### API 认证（API Key）

```
请求头：Authorization: Bearer {api_key}
  → 中间件从数据库验证 API key
  → 检查 key 的 is_active 状态
  → 更新 last_used 时间戳
  → 提取 user_id
  → 存储到 request.state.current_user
  → 继续处理请求
```

### 小红书 OAuth 流程

**配置：**
- 授权 URL：`https://open.xiaohongshu.com/oauth/authorize`
- 令牌 URL：`https://open.xiaohongshu.com/oauth/access_token`
- 必需权限：`write_public`（发布内容）、`read_public`（读取用户信息）
- 令牌有效期：通常 30 天（可通过 refresh_token 配置）

```
用户点击"授权小红书"
  → 重定向到小红书授权页面（带 client_id 和 redirect_uri）
  → 用户同意授权
  → 小红书重定向到 /xiaohongshu/callback?code=xxx&state=xxx
  → 后端验证 state 参数（CSRF 保护）
  → 后端使用 code 向令牌端点 POST 请求获取 access_token
  → 将 access_token、refresh_token、expires_at 存储到数据库
  → 重定向到仪表盘并显示成功消息
```

**令牌刷新策略：**
- 每次 API 调用前检查令牌过期时间
- 如果过期，使用 refresh_token 获取新的 access_token
- 如果刷新失败，通知用户重新授权
- 刷新操作最多重试 3 次

### 安全措施

- 密码使用 bcrypt 哈希
- API Key 使用 UUID + 随机字符串生成
- Session 过期时间：7天
- 令牌过期时自动刷新

## 发布流程

### 立即发布流程

```
1. 接收发布请求（API 或 Web）
   ↓
2. 验证 API Key / Session
   ↓
3. 验证用户已授权小红书
   ↓
4. 验证内容格式和大小限制
   ↓
5. 调用小红书 API 发布
   ↓
6. 记录结果到数据库
   ↓
7. 返回响应
```

### 媒体文件处理

**图片：**
- 前端直接上传到七牛云/腾讯云
- 返回 CDN URL
- 后端只存储 URL
- 支持格式：JPEG、PNG、WEBP
- 大小限制：每张图片 10MB
- 最多 9 张图片（小红书限制）

**视频：**
- 前端直接上传到七牛云/腾讯云
- 返回 CDN URL
- 验证格式（MP4）和大小（100MB 限制）
- 时长限制：5分钟（小红书建议）
- 分辨率：最低 720p，推荐 1080p
- 纵横比：9:16（竖屏）或 1:1（方形）

**国内平台内容要求：**
- 文字长度：1-1000 字符
- 话题标签：每条最多 30 个
- 不允许外部链接（平台政策）
- 水印检测：带明显水印的视频可能被拒绝

### 错误处理

| 错误场景 | HTTP 状态 | 处理策略 |
|----------|-----------|----------|
| 未授权 | 401 | 返回错误并附上授权页面链接 |
| 令牌过期 | 401 | 自动刷新并重试一次 |
| API Key 无效 | 403 | 记录尝试，返回通用错误 |
| 内容无效 | 400 | 返回具体的验证错误信息 |
| 媒体过大 | 413 | 返回允许的最大大小 |
| 内容违规 | 422 | 返回平台拒绝原因 |
| 网络超时 | 504 | 使用指数退避重试 3 次 |
| 平台不可用 | 503 | 60秒后重试 |
| 速率限制 (429) | 429 | 使用 Retry-After 头延迟，重试一次 |
| 刷新令牌失败 | 401 | 标记授权无效，通知用户重新授权 |
| 平台 API 错误 | 502 | 记录错误详情，返回通用消息 |

**重试策略：**
- 最大重试次数：3次
- 退避策略：指数退避（1秒、2秒、4秒）
- 不重试：客户端错误（4xx 除 429 外）
- 重试：服务器错误（5xx）和网络故障

## 数据库迁移策略

**工具：** Alembic

**迁移工作流：**
```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚一个迁移
alembic downgrade -1
```

**迁移策略：**
- 永不修改现有迁移（创建新的）
- 先在开发数据库上测试迁移
- 应用迁移前备份生产数据库
- 简单模式变更使用 `--autogenerate`
- 复杂数据转换使用手动迁移

**数据备份策略：**
- 开发环境：SQLite 文件每日复制
- 生产环境：Supabase/Neon 自动备份（7天保留）
- 每周导出架构和数据：`pg_dump` 或 SQLite `.dump`

## 安全加固

### 认证安全
- 密码哈希：bcrypt 12 轮
- API Key 格式：`pk_live_{随机32字符}` 或 `pk_test_{随机32字符}`
- Session cookie：`Secure`、`HttpOnly`、`SameSite=Strict`
- 每个 IP 的速率限制：认证端点 100 请求/分钟

### 输入验证
- 用户名：3-50 个字母数字字符
- 密码：最少 8 个字符（前端和后端都强制）
- API Key 验证：数据库查询前进行格式检查
- 内容清理：去除 HTML 标签，转义特殊字符

### CSRF 保护
- 所有状态变更的 Web 表单都需要 CSRF 令牌
- 令牌存储在 session 中，POST 时验证
- AJAX 请求包含 `X-CSRF-Token` 头

### API 安全
- 每次请求都从数据库验证 API Key
- 成功认证时更新最后使用时间戳
- 记录失败的认证尝试（监控滥用）
- 为特定域名配置 CORS

### 密钥管理
- 永不提交 `.env` 文件
- 所有密钥使用环境变量
- Railway：使用密钥管理（绝不放在公开仓库）

## API 速率限制

### 速率限制策略

**实现方式：** 基于Redis的滑动窗口速率限制

**各端点类型的限制：**

| 端点类型 | 速率限制 | 时间窗口 |
|----------|----------|----------|
| 认证（登录、注册） | 10 请求 | 每 IP 每分钟 |
| API Key 创建 | 5 请求 | 每用户每小时 |
| 发布 API | 60 请求 | 每 API Key 每分钟 |
| 查询 API（发布历史） | 100 请求 | 每 API Key 每分钟 |
| Web 仪表盘 | 120 请求 | 每会话每分钟 |

### 速率限制响应

超出速率限制时：
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "超出速率限制",
    "details": {
      "limit": 60,
      "remaining": 0,
      "reset_at": "2026-03-16T12:01:00Z"
    }
  }
}
```

HTTP 头：
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1678966860
Retry-After: 30
```

### 实现说明
- 速率限制键格式：`ratelimit:{端点}:{标识符}`（如 `ratelimit:publish:pk_live_abc123`）
- 使用 Redis INCR 和 TTL 进行原子操作
- 速率限制可通过环境变量配置

### 国内平台内容审核

**重要说明：** 虽然 MVP 不包含自动化敏感内容过滤，但以下指南已记录在案，供未来实施和用户了解。

### 禁止内容类别

**法律要求（中国）：**
- 违反国家法律法规的内容
- 色情或低俗材料
- 虚假信息或谣言
- 危害国家安全的内容
- 暴力或恐怖主义相关内容

**平台特定规则：**
- 小红书：不允许推广链接、不允许过多话题标签
- 所有平台：帖子中不允许外部链接（平台政策）

### 推荐的发布前检查

**用户内容：**
1. 文字长度验证（1-1000 字符）
2. 图片格式和大小验证
3. 视频格式、大小和时长验证
4. 从文字内容中去除 HTML 标签
5. 转义特殊字符

**未来增强 - 自动化过滤：**
- 集成内容审核 API（阿里云、腾讯云）
- 基于关键词的过滤
- 不当内容的图像识别
- 标记内容的审核队列

### 用户责任

用户负责：
- 确保其内容符合中国法律
- 遵循平台特定的内容指南
- 了解违规内容可能导致：
  - 平台拒绝发布
  - 账号暂停
  - 法律后果

**发布时显示的免责声明：**
"用户负责确保其内容符合所有适用法律和平台指南。"

## 性能考虑

### 数据库索引
```sql
-- 用户表
CREATE INDEX idx_users_username ON users(username);

-- API Keys 表
CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- 小红书授权表
CREATE INDEX idx_xiaohongshu_auth_user_id ON xiaohongshu_auth(user_id);

-- 发布记录表
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

### 缓存策略
- 用户会话：Redis，7天 TTL
- API Key 验证：缓存常用 Key（5分钟 TTL）
- 小红书授权状态：缓存直到令牌过期

### 异步操作
- 所有数据库查询使用 SQLAlchemy 异步
- 外部 API 调用（小红书）使用 httpx 异步
- 云存储文件上传是异步的

### 响应优化
- 列表端点分页（默认 20 项，最多 100）
- 强制执行数据库查询结果限制
- API 响应启用压缩（gzip）

## 技术栈

### 后端核心依赖

```
fastapi              # Web 框架
uvicorn              # ASGI 服务器
sqlalchemy           # ORM
alembic              # 数据库迁移
pydantic             # 数据验证
passlib[bcrypt]      # 密码哈希
python-multipart     # 文件上传
httpx                # HTTP 客户端（小红书 API）
redis                # Redis 客户端
qiniu                # 七牛云 SDK
```

### 开发依赖

```
pytest               # 测试
pytest-asyncio       # 异步测试
black                # 代码格式化
ruff                 # 代码检查
```

### 环境变量

```env
# 应用配置
APP_NAME=Publify
APP_ENV=development
SECRET_KEY=your-secret-key-here

# 数据库
DATABASE_URL=sqlite:///./publify.db

# Redis
REDIS_URL=redis://localhost:6379

# 七牛云（开发环境）
QINIU_ACCESS_KEY=your-access-key
QINIU_SECRET_KEY=your-secret-key
QINIU_BUCKET=your-bucket-name
QINIU_DOMAIN=https://cdn.example.com

# 小红书（待填写）
XIAOHONGSHU_CLIENT_ID=
XIAOHONGSHU_CLIENT_SECRET=
XIAOHONGSHU_REDIRECT_URI=http://localhost:8000/xiaohongshu/callback
```

## 运维监控

### 需要跟踪的指标

**应用指标：**
- 各端点请求数
- 响应时间百分位数（p50、p95、p99）
- 各端点错误率
- 活跃用户数
- 各平台发布成功/失败率

**业务指标：**
- 总发布数
- 各平台发布数
- 各内容类型发布数（文字/图片/视频）
- 创建/活跃的 API Keys

**基础设施指标：**
- CPU 使用率
- 内存使用率
- 数据库连接池利用率
- Redis 内存使用率

### 监控设置

**开发环境：**
- 以结构化 JSON 格式记录到控制台
- 手动监控日志

**生产环境（Railway）：**
- Railway 内置指标（CPU、内存）
- 通过 Railway CLI 进行日志流式传输
- 通过 Sentry 进行错误跟踪（可选，免费层）

### 告警策略

**关键告警（立即）：**
- 应用崩溃（Railway 自动重启）
- 数据库连接失败
- Redis 连接失败

**警告告警（每日检查）：**
- 错误率 > 5%
- 响应时间 p95 > 2秒
- 发布失败率 > 10%

### 日志保留

- 开发环境：无限制（本地磁盘）
- 生产环境：7天（Railway 日志）
- 每月导出日志进行长期存储

### 健康检查端点

```
GET /health
响应：{"status": "ok", "version": "1.0.0"}
```

检查项：
- 数据库连接性
- Redis 连接性
- 外部服务状态（小红书 API - 可选）

## 日志策略

- **请求日志：** 所有 API 请求（路径、方法、响应时间）
- **错误日志：** 所有错误及堆栈跟踪
- **发布日志：** 所有发布操作（用户、平台、结果）
- **日志级别：** DEBUG（开发）、INFO（生产）

## 部署

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Redis
docker run -d -p 6379:6379 redis

# 运行开发服务器
uvicorn app.main:app --reload --port 8000
```

### Railway 部署

```json
{
  "build": {
    "commands": ["pip install -r requirements.txt"]
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

**Railway 上的环境变量：**
- `DATABASE_URL`：Railway Postgres
- `REDIS_URL`：Railway Redis
- `QINIU_*`：七牛云凭据

## 测试策略

### 单元测试
- 认证逻辑
- 数据验证
- 小红书 API 调用（模拟）

### 集成测试
- API 端到端测试
- OAuth 流程（模拟）

### 手动测试
- 前端 UI

## 成本分析

### 开发阶段
- 域名：¥0（使用 localhost）
- 服务器：¥0（本地开发）
- 数据库：¥0（SQLite）
- 存储：¥0（七牛云免费层）
- Redis：¥0（本地 Docker）

### 生产阶段（100 月活用户）
- 服务器（Railway）：约 ¥0-50/月（免费层）
- 数据库（Supabase/Neon）：¥0（免费层）
- 存储（七牛云/腾讯云）：约 ¥4/月
- Redis（Upstash）：¥0（免费层）
- **总计：约 ¥4/月**

## 后续阶段

### 阶段 2：更多平台
- 微博
- B站
- 抖音

### 阶段 3：高级功能
- 敏感内容过滤
- 定时发布
- Webhook 通知
- API 速率限制

### 阶段 4：生态系统
- Python SDK
- Dify 集成插件
- Coze 集成
- FastGPT 集成

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 平台 API 变化 | 高 | 定期监控，灵活架构 |
| 内容监管变化 | 高 | 合规监控，内容过滤 |
| OAuth 令牌过期 | 中 | 自动刷新机制 |
| 高并发负载 | 中 | Redis 队列，速率限制 |
| 存储成本超支 | 低 | 监控，大小限制 |

## 成功标准

- [ ] 用户可以注册和登录
- [ ] 用户可以生成 API Keys
- [ ] 用户可以授权小红书账号
- [ ] API 可以发布文字内容到小红书
- [ ] API 可以发布图片到小红书
- [ ] API 可以发布视频到小红书
- [ ] 用户可以查看发布历史
- [ ] 应用部署到 Railway
