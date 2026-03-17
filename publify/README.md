# Publify

Publify is a publishing API service for Chinese social media platforms, enabling AI agents to automatically publish content to platforms like Xiaohongshu (Little Red Book).

## Features

- User registration and authentication (username + password)
- API Key generation and management
- Xiaohongshu OAuth integration
- Content publishing: text, images, and video
- Simple web management dashboard
- Publishing history and status tracking

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: SQLite (dev), PostgreSQL (production)
- **Cache**: Redis for sessions and rate limiting
- **Storage**: Qiniu Cloud (dev), Tencent Cloud COS (production)
- **Authentication**: Session-based (web), API Key-based (REST API)

## Project Structure

```
publify/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas
│   ├── api/                    # API routes
│   ├── services/               # Business logic
│   ├── templates/              # Jinja2 templates
│   └── static/                 # CSS, JS assets
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server
- PostgreSQL (for production) or SQLite (for development)

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd publify
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Redis (using Docker):
```bash
docker run -d -p 6379:6379 redis
```

6. Initialize the database:
```bash
alembic upgrade head
```

7. Run the development server:
```bash
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` to access the web interface.

## API Documentation

Once the server is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

### REST API Endpoints

All REST API endpoints require API Key authentication via the `Authorization: Bearer {api_key}` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/publish` | Publish content to Xiaohongshu |
| GET | `/api/v1/posts` | Query publishing history |
| GET | `/api/v1/posts/{id}` | Get specific post record |
| GET | `/api/v1/auth/status` | Check authorization status |

### Publish API Example

```bash
curl -X POST "http://localhost:8000/api/v1/publish" \
  -H "Authorization: Bearer pk_live_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "xiaohongshu",
    "content_type": "image",
    "text": "This is the content to publish",
    "media_urls": ["https://cdn.example.com/image1.jpg"]
  }'
```

## Development

### Running Tests

```bash
pytest --cov=app tests/
```

### Code Formatting

```bash
black app/ tests/
ruff check app/ tests/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Deployment

### Railway Deployment

1. Push your code to GitHub
2. Create a new project on Railway
3. Add the following environment variables in Railway:
   - `DATABASE_URL` (Railway PostgreSQL)
   - `REDIS_URL` (Railway Redis)
   - `SECRET_KEY` (generate a random string)
   - `QINIU_*` (your Qiniu credentials)
   - `XIAOHONGSHU_*` (your Xiaohongshu OAuth credentials)

4. Set the start command:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
