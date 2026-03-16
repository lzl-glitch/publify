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

### Primary Authentication Strategy

**Web Dashboard**: Session-based authentication
- All web routes use session cookies
- Sessions stored in Redis with 7-day expiration
- CSRF protection enabled for all forms

**REST API**: API Key-based authentication
- All `/api/v1/*` routes require API Key
- API Keys stored in database with last_used tracking
- No JWT used (simpler for MVP)

### Web Login (Session-based)

```
User enters username/password
  → Validate credentials against database
  → Create session with UUID
  → Store in Redis (key: session_id, value: user_id, ttl: 7 days)
  → Set secure cookie (session_id)
  → Redirect to dashboard
```

### API Authentication (API Key)

```
Request with Header: Authorization: Bearer {api_key}
  → Middleware validates API key from database
  → Check key is_active status
  → Update last_used timestamp
  → Extract user_id
  → Store in request.state.current_user
  → Continue processing
```

### Xiaohongshu OAuth Flow

**Configuration:**
- Authorization URL: `https://open.xiaohongshu.com/oauth/authorize`
- Token URL: `https://open.xiaohongshu.com/oauth/access_token`
- Required Scopes: `write_public` (publish content), `read_public` (read user info)
- Token Lifetime: Typically 30 days (configurable via refresh_token)

```
User clicks "Authorize Xiaohongshu"
  → Redirect to Xiaohongshu authorization page with client_id & redirect_uri
  → User approves authorization
  → Xiaohongshu redirects to /xiaohongshu/callback?code=xxx&state=xxx
  → Backend validates state parameter (CSRF protection)
  → Backend POSTs to token endpoint with code to get access_token
  → Store access_token, refresh_token, expires_at in database
  → Redirect to dashboard with success message
```

**Token Refresh Strategy:**
- Check token expiration before each API call
- If expired, use refresh_token to obtain new access_token
- If refresh fails, notify user to re-authorize
- Maximum 3 retry attempts for refresh operations

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
- Supported formats: JPEG, PNG, WEBP
- Size limit: 10MB per image
- Maximum 9 images per post (Xiaohongshu limit)

**Videos:**
- Frontend uploads directly to Qiniu/Tencent Cloud
- Returns CDN URL
- Validate format (MP4) and size (100MB limit)
- Duration limit: 5 minutes (Xiaohongshu recommendation)
- Resolution: 720p minimum, 1080p recommended
- Aspect ratio: 9:16 (vertical) or 1:1 (square)

**Chinese Platform Content Requirements:**
- Text length: 1-1000 characters
- Hashtags: Maximum 30 tags per post
- No external links (platform policy)
- Watermark detection: Videos may be rejected if heavily watermarked

### Error Handling

| Error Scenario | HTTP Status | Handling Strategy |
|----------------|-------------|-------------------|
| Not authorized | 401 | Return error with link to authorize page |
| Token expired | 401 | Auto-refresh and retry once |
| Invalid API Key | 403 | Log attempt, return generic error |
| Invalid content | 400 | Specific validation error message |
| Media too large | 413 | Return max size allowed |
| Content violation | 422 | Return platform rejection reason |
| Network timeout | 504 | Retry 3 times with exponential backoff |
| Platform unavailable | 503 | Retry after 60 seconds |
| Rate limit (429) | 429 | Delay using Retry-After header, retry once |
| Refresh token failed | 401 | Mark auth as invalid, notify user to re-authorize |
| Platform API error | 502 | Log error details, return generic message |

**Retry Policy:**
- Maximum retry attempts: 3
- Backoff strategy: Exponential (1s, 2s, 4s)
- Don't retry: Client errors (4xx except 429)
- Retry: Server errors (5xx) and network failures

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

## Database Migration Strategy

**Tool:** Alembic

**Migration Workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Migration Policy:**
- Never modify existing migrations (create new ones)
- Test migrations on development database first
- Backup production database before applying migrations
- Use `--autogenerate` for simple schema changes
- Manual migrations for complex data transformations

**Data Backup Strategy:**
- Development: SQLite file copied daily
- Production: Supabase/Neon automatic backups (7-day retention)
- Export schema and data weekly: `pg_dump` or SQLite `.dump`

## Security Hardening

### Authentication Security
- Password hashing: bcrypt with 12 rounds
- API Key format: `pk_live_{random_32_chars}` or `pk_test_{random_32_chars}`
- Session cookie: `Secure`, `HttpOnly`, `SameSite=Strict`
- Rate limiting per IP: 100 requests/minute for auth endpoints

### Input Validation
- Username: 3-50 alphanumeric characters only
- Password: Minimum 8 characters (enforced on frontend and backend)
- API Key validation: Format check before database query
- Content sanitization: Strip HTML tags, escape special characters

### CSRF Protection
- All state-changing web forms require CSRF token
- Token stored in session, validated on POST
- AJAX requests include `X-CSRF-Token` header

### API Security
- API Key validated against database for each request
- Last-used timestamp updated on successful auth
- Failed auth attempts logged (monitor for abuse)
- CORS configured for specific domains only

### Secrets Management
- Never commit `.env` files
- Use environment variables for all secrets
- Railway: Use secret management (never in public repo)

## Performance Considerations

### Database Indexing
```sql
-- Users table
CREATE INDEX idx_users_username ON users(username);

-- API Keys table
CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);

-- Xiaohongshu Auth table
CREATE INDEX idx_xiaohongshu_auth_user_id ON xiaohongshu_auth(user_id);

-- Posts table
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

### Caching Strategy
- User sessions: Redis with 7-day TTL
- API Key validation: Cache frequently used keys (5-minute TTL)
- Xiaohongshu auth status: Cache until token expires

### Async Operations
- All database queries use SQLAlchemy async
- External API calls (Xiaohongshu) are async with httpx
- File uploads to cloud storage are async

### Response Optimization
- Pagination for list endpoints (default: 20 items, max: 100)
- Database query result limits enforced
- Compression enabled for API responses (gzip)

## Technology Stack

### Backend Core Dependencies

```
fastapi              # Web framework
uvicorn              # ASGI server
sqlalchemy           # ORM
alembic              # Database migrations
pydantic             # Data validation
passlib[bcrypt]      # Password hashing
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

## Operational Monitoring

### Metrics to Track

**Application Metrics:**
- Request count by endpoint
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Active user count
- Publishing success/failure rate by platform

**Business Metrics:**
- Total posts published
- Posts by platform
- Posts by content type (text/image/video)
- API keys created/active

**Infrastructure Metrics:**
- CPU usage
- Memory usage
- Database connection pool utilization
- Redis memory usage

### Monitoring Setup

**Development:**
- Log to console with structured JSON
- Manual monitoring of logs

**Production (Railway):**
- Railway built-in metrics (CPU, memory)
- Log streaming via Railway CLI
- Error tracking via Sentry (optional, free tier)

### Alerting Strategy

**Critical Alerts (immediate):**
- Application crash (Railway auto-restarts)
- Database connection failures
- Redis connection failures

**Warning Alerts (daily check):**
- Error rate > 5%
- Response time p95 > 2s
- Publishing failure rate > 10%

### Log Retention

- Development: Unlimited (local disk)
- Production: 7 days (Railway logs)
- Export logs monthly for long-term storage

### Health Check Endpoint

```
GET /health
Response: {"status": "ok", "version": "1.0.0"}
```

Checks:
- Database connectivity
- Redis connectivity
- External service status (Xiaohongshu API - optional)

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
