# Publify MVP Design Document

**Project Name:** Publify
**Date:** 2026-03-16
**Status:** Design Approved
**Version:** 1.0

## Overview

Publify is a social media publishing API service targeting Chinese domestic platforms, enabling AI agents to automatically publish content to platforms like Xiaohongshu (Little Red Book).

**Target Users:** AI application developers, content creators, and enterprises in China.

**Core Value:** Allow AI to publish content to Chinese social media platforms via API calls.

## Project Scope (Phase 1 - MVP)

### Included Features
- User registration and authentication (username + password)
- API Key generation and management
- Xiaohongshu (Little Red Book) OAuth integration
- Content publishing: text, images, and video
- Simple web dashboard for management
- Publishing history query

### Excluded Features (Future Phases)
- Sensitive content filtering
- Scheduled publishing
- Webhook notifications
- API rate limiting
- Additional platforms (Weibo, Bilibili, Douyin, etc.)

## Architecture

### Approach: Monolithic Service

Single FastAPI application containing all functionality.

**Rationale:**
- Simplest to develop and deploy
- Sufficient for MVP scope
- Can be split into microservices later if needed

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Web Browser                         │
│  (Login, Dashboard, API Key Management, Auth Flow)      │
└──────────────────────┬──────────────────────────────────┘
                       │ HTML/JSON
                       ↓
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Authentication Middleware (Session/JWT)          │  │
│  │  Route Handlers                                   │  │
│  │  Business Logic Services                          │  │
│  └───────────────────────────────────────────────────┘  │
└────────┬──────────────────────────────┬────────────────┘
         │                              │
         ↓                              ↓
┌─────────────────┐            ┌─────────────────┐
│  PostgreSQL     │            │     Redis       │
│  - Users        │            │  - Sessions     │
│  - API Keys     │            │  - Cache        │
│  - Auth Data    │            │  - Tokens       │
│  - Posts        │            │                 │
└─────────────────┘            └─────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐      │
│  │  Qiniu     │  │ Tencent    │  │ Xiaohongshu  │      │
│  │  Cloud     │  │ COS        │  │  API         │      │
│  │ (Dev)      │  │ (Prod)     │  │              │      │
│  └────────────┘  └────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
publify/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── api_key.py          # API Key model
│   │   ├── xiaohongshu.py      # Xiaohongshu auth model
│   │   └── post.py             # Post record model
│   ├── schemas/                # Pydantic schemas (API request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── publish.py
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── auth.py             # Register/Login
│   │   ├── dashboard.py        # Dashboard
│   │   ├── api_keys.py         # API Key management
│   │   ├── xiaohongshu.py      # Xiaohongshu authorization
│   │   └── publish.py          # Publishing API
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── xiaohongshu_service.py
│   │   ├── storage_service.py  # Qiniu/Tencent cloud storage
│   │   └── publish_service.py
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   └── ...
│   └── static/                 # Static files
│       ├── css/
│       └── js/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String(50) | Unique username |
| password_hash | String(255) | Bcrypt password hash |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Update timestamp |

### API Keys Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key → users.id |
| key | String(64) | Unique API key |
| name | String(100) | Key name (e.g., "My App") |
| last_used | DateTime | Last usage timestamp |
| created_at | DateTime | Creation timestamp |
| is_active | Boolean | Active status |

### Xiaohongshu Auth Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key → users.id |
| access_token | Text | Access token |
| refresh_token | Text | Refresh token |
| expires_at | DateTime | Token expiration |
| created_at | DateTime | Creation timestamp |

### Posts Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key → users.id |
| platform | String(20) | Platform name (xiaohongshu) |
| content_type | String(10) | Type (text/image/video) |
| content | Text | Text content |
| media_urls | Text | Media URLs (JSON array) |
| status | String(20) | Status (pending/success/failed) |
| error_message | Text | Error details |
| created_at | DateTime | Creation timestamp |

## API Design

### Web Page Routes

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/` | GET | Home page | No |
| `/register` | GET/POST | Registration page | No |
| `/login` | GET/POST | Login page | No |
| `/logout` | POST | Logout | Yes |
| `/dashboard` | GET | Dashboard | Yes |
| `/api-keys` | GET | API Key management | Yes |
| `/xiaohongshu/auth` | GET | Xiaohongshu OAuth start | Yes |
| `/xiaohongshu/callback` | GET | Xiaohongshu OAuth callback | Yes |
| `/posts` | GET | Publishing history | Yes |

### REST API (API Key Authentication)

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/api/v1/publish` | POST | Publish content | Yes (API Key) |
| `/api/v1/posts` | GET | Query publishing records | Yes (API Key) |
| `/api/v1/posts/{id}` | GET | Query single record | Yes (API Key) |
| `/api/v1/auth/status` | GET | Authorization status | Yes (API Key) |

### Publish API Request Example

```json
POST /api/v1/publish
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "platform": "xiaohongshu",
  "content_type": "image",
  "text": "This is the published content",
  "media_urls": ["https://cdn.example.com/image1.jpg"]
}
```

### Publish API Response Example

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

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Please authorize Xiaohongshu account first",
    "details": {}
  }
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| AUTH_REQUIRED | Authorization required |
| INVALID_API_KEY | Invalid API key |
| INVALID_CONTENT | Invalid content format |
| MEDIA_TOO_LARGE | Media file too large |
| PLATFORM_ERROR | Platform API error |
| RATE_LIMITED | Rate limit exceeded |

## Authentication Flow

### Web Login (Session-based)

```
User enters username/password
  → Validate credentials
  → Create session
  → Store in Redis (key: session_id, value: user_id)
  → Set cookie (session_id)
  → Redirect to dashboard
```

### API Authentication (JWT/API Key)

```
Request with Header: Authorization: Bearer {api_key}
  → Middleware validates API key
  → Query key from database
  → Extract user_id
  → Store in request.state
  → Continue processing
```

### Xiaohongshu OAuth Flow

```
User clicks "Authorize Xiaohongshu"
  → Redirect to Xiaohongshu authorization page
  → User approves
  → Xiaohongshu redirects to /xiaohongshu/callback?code=xxx
  → Backend exchanges code for access_token
  → Store token in database
  → Redirect to dashboard
```

### Security Measures

- Passwords hashed with bcrypt
- API keys generated using UUID + random string
- Session expiration: 7 days
- Automatic token refresh on expiration

## Publishing Flow

### Immediate Publishing Process

```
1. Receive publish request (API or Web)
   ↓
2. Validate API Key / Session
   ↓
3. Verify user has authorized Xiaohongshu
   ↓
4. Validate content format and size limits
   ↓
5. Call Xiaohongshu API to publish
   ↓
6. Record result to database
   ↓
7. Return response
```

### Media File Handling

**Images:**
- Frontend uploads directly to Qiniu/Tencent Cloud
- Returns CDN URL
- Backend only stores URL

**Videos:**
- Frontend uploads directly to Qiniu/Tencent Cloud
- Returns CDN URL
- Validate format (MP4) and size (100MB limit)

### Error Handling

| Error Scenario | Handling |
|----------------|----------|
| Not authorized | Return 401, prompt to authorize |
| Token expired | Auto-refresh and retry |
| Content violation | Return error, log reason |
| Network timeout | Retry 3 times, then fail |
| Platform rate limit | Delay and retry |

## Technology Stack

### Backend Core Dependencies

```
fastapi              # Web framework
uvicorn              # ASGI server
sqlalchemy           # ORM
alembic              # Database migrations
pydantic             # Data validation
python-jose          # JWT handling
passlib              # Password hashing
python-multipart     # File uploads
httpx                # HTTP client (Xiaohongshu API)
redis                # Redis client
qiniu                # Qiniu cloud SDK
```

### Development Dependencies

```
pytest               # Testing
pytest-asyncio       # Async testing
black                # Code formatting
ruff                 # Code linting
```

### Environment Variables

```env
# Application
APP_NAME=Publify
APP_ENV=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///./publify.db

# Redis
REDIS_URL=redis://localhost:6379

# Qiniu Cloud (Development)
QINIU_ACCESS_KEY=your-access-key
QINIU_SECRET_KEY=your-secret-key
QINIU_BUCKET=your-bucket-name
QINIU_DOMAIN=https://cdn.example.com

# Xiaohongshu (To be filled)
XIAOHONGSHU_CLIENT_ID=
XIAOHONGSHU_CLIENT_SECRET=
XIAOHONGSHU_REDIRECT_URI=http://localhost:8000/xiaohongshu/callback
```

## Logging Strategy

- **Request logs**: All API requests (path, method, response time)
- **Error logs**: All errors with stack traces
- **Publish logs**: All publish operations (user, platform, result)
- **Log levels**: DEBUG (development), INFO (production)

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Railway Deployment

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

**Environment Variables on Railway:**
- `DATABASE_URL`: Railway Postgres
- `REDIS_URL`: Railway Redis
- `QINIU_*`: Qiniu credentials

## Testing Strategy

### Unit Tests
- Authentication logic
- Data validation
- Xiaohongshu API calls (mocked)

### Integration Tests
- API end-to-end tests
- OAuth flow (mocked)

### Manual Testing
- Frontend UI

## Cost Analysis

### Development Phase
- Domain: ¥0 (use localhost)
- Server: ¥0 (local development)
- Database: ¥0 (SQLite)
- Storage: ¥0 (Qiniu free tier)
- Redis: ¥0 (local Docker)

### Production Phase (100 Monthly Active Users)
- Server (Railway): ~¥0-50/month (free tier)
- Database (Supabase/Neon): ¥0 (free tier)
- Storage (Qiniu/Tencent): ~¥4/month
- Redis (Upstash): ¥0 (free tier)
- **Total: ~¥4/month**

## Future Phases

### Phase 2: Additional Platforms
- Weibo
- Bilibili
- Douyin

### Phase 3: Advanced Features
- Sensitive content filtering
- Scheduled publishing
- Webhook notifications
- API rate limiting

### Phase 4: Ecosystem
- Python SDK
- Dify integration plugin
- Coze integration
- FastGPT integration

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Platform API changes | High | Regular monitoring, flexible architecture |
| Content regulation changes | High | Compliance monitoring, content filtering |
| OAuth token expiration | Medium | Auto-refresh mechanism |
| High concurrent load | Medium | Redis queue, rate limiting |
| Storage cost overruns | Low | Monitoring, size limits |

## Success Criteria

- [ ] Users can register and login
- [ ] Users can generate API keys
- [ ] Users can authorize Xiaohongshu account
- [ ] API can publish text content to Xiaohongshu
- [ ] API can publish images to Xiaohongshu
- [ ] API can publish videos to Xiaohongshu
- [ ] Users can view publishing history
- [ ] Application deployed on Railway
