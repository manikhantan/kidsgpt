# KidSafe AI Backend

A production-ready backend API for a kid-safe conversational AI application with parental controls. Built with FastAPI, PostgreSQL, and OpenAI.

## Features

- **JWT-based Authentication** - Secure authentication for both parents and kids
- **Role-based Access Control** - Separate endpoints and permissions for parents and kids
- **Content Filtering** - Allowlist or blocklist mode for controlling what topics kids can discuss
- **AI Chat Integration** - OpenAI-powered chat with kid-friendly system prompts
- **YouTube Video Suggestions** - Educational video recommendations for kids with every response
- **Parental Monitoring** - Parents can view complete chat history and analytics
- **Rate Limiting** - Protection against abuse
- **Database Migrations** - Alembic for version-controlled schema changes

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Migrations**: Alembic 1.12.1
- **AI Provider**: OpenAI API (easily swappable)
- **Validation**: Pydantic 2.5

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   │   ├── parent.py
│   │   ├── child.py
│   │   ├── content_rule.py
│   │   ├── chat_session.py
│   │   ├── message.py
│   │   ├── parent_chat_session.py
│   │   └── parent_message.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── auth.py
│   │   ├── parent.py
│   │   ├── child.py
│   │   ├── content_rule.py
│   │   ├── message.py
│   │   └── parent_chat.py
│   ├── api/                    # API routes
│   │   ├── deps.py            # Dependencies (auth, db session)
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── parent.py
│   │       └── kid.py
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── content_filter.py
│   │   └── ai_service.py
│   └── core/                   # Core utilities
│       ├── security.py        # JWT, password hashing
│       └── exceptions.py      # Custom exceptions
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── tests/                      # Test files
├── .env.example                # Environment variables template
├── alembic.ini                 # Alembic configuration
├── requirements.txt            # Python dependencies
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip or pipenv

### 1. Clone and Setup Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/kidsafe_ai

# JWT Configuration (generate with: openssl rand -hex 32)
SECRET_KEY=your-super-secret-key-change-this-in-production

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# YouTube Configuration (for educational video suggestions)
YOUTUBE_API_KEY=your-youtube-api-key

# CORS (adjust for your frontend URL)
CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE kidsafe_ai;

# Create user (optional)
CREATE USER kidsafe_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE kidsafe_ai TO kidsafe_user;
```

### 5. Run Database Migrations

```bash
# Apply migrations
alembic upgrade head
```

### 6. Start the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints Overview

#### Authentication
- `POST /api/auth/parent/register` - Register new parent
- `POST /api/auth/parent/login` - Parent login
- `POST /api/auth/kid/login` - Kid login
- `POST /api/auth/refresh` - Refresh JWT token

#### Parent Endpoints (requires parent JWT)
- `POST /api/parent/children` - Create child account
- `GET /api/parent/children` - List all children
- `PUT /api/parent/children/{child_id}` - Update child info
- `DELETE /api/parent/children/{child_id}` - Delete child account
- `GET /api/parent/content-rules` - Get content rules
- `PUT /api/parent/content-rules` - Update content rules
- `GET /api/parent/chat-history/{child_id}` - Get child's chat history
- `GET /api/parent/analytics/{child_id}` - Get child analytics
- `POST /api/parent/chat` - Send chat message (parent's own chat, no filtering)
- `GET /api/parent/chat-sessions/recent` - Get recent parent chat sessions
- `GET /api/parent/chat-sessions` - Get paginated parent chat sessions
- `GET /api/parent/chat-sessions/{session_id}` - Get full parent chat session
- `POST /api/parent/chat-sessions` - Create new parent chat session

#### Kid Endpoints (requires kid JWT)
- `POST /api/kid/chat` - Send chat message (with content filtering)
- `GET /api/kid/chat-history` - Get own chat history
- `GET /api/kid/current-session` - Get current chat session

#### Health Check
- `GET /health` - API health check

## Example API Calls

### Register a Parent

```bash
curl -X POST http://localhost:8000/api/auth/parent/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "securepassword123",
    "name": "John Parent"
  }'
```

Response:
```json
{
  "id": "uuid-here",
  "email": "parent@example.com",
  "name": "John Parent",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Parent Login

```bash
curl -X POST http://localhost:8000/api/auth/parent/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Create Child Account

```bash
curl -X POST http://localhost:8000/api/parent/children \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PARENT_ACCESS_TOKEN" \
  -d '{
    "email": "tommy_kid@mgail.com",
    "password": "kidpass123",
    "name": "Tommy"
  }'
```

### Update Content Rules (Allowlist Mode)

```bash
curl -X PUT http://localhost:8000/api/parent/content-rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PARENT_ACCESS_TOKEN" \
  -d '{
    "mode": "allowlist",
    "topics": ["math", "science", "art", "history", "nature"],
    "keywords": []
  }'
```

### Update Content Rules (Blocklist Mode)

```bash
curl -X PUT http://localhost:8000/api/parent/content-rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PARENT_ACCESS_TOKEN" \
  -d '{
    "mode": "blocklist",
    "topics": [],
    "keywords": ["violence", "weapons", "drugs", "explicit", "politics"]
  }'
```

### Kid Login

```bash
curl -X POST http://localhost:8000/api/auth/kid/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tommy_kid@gmail.com",
    "password": "kidpass123"
  }'
```

### Parent Send Chat Message

```bash
curl -X POST http://localhost:8000/api/parent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_PARENT_ACCESS_TOKEN" \
  -d '{
    "message": "How do I set appropriate screen time limits for my child?"
  }'
```

Response:
```json
{
  "user_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "How do I set appropriate screen time limits for my child?",
    "created_at": "2024-01-01T00:00:00"
  },
  "assistant_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Setting appropriate screen time limits depends on your child's age...",
    "created_at": "2024-01-01T00:00:01"
  },
  "session_id": "uuid",
  "session_title": "Screen Time Limits Discussion"
}
```

### Kid Send Chat Message

```bash
curl -X POST http://localhost:8000/api/kid/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_KID_ACCESS_TOKEN" \
  -d '{
    "message": "Can you help me with my math homework?"
  }'
```

Response (allowed):
```json
{
  "user_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "Can you help me with my math homework?",
    "blocked": false,
    "block_reason": null,
    "created_at": "2024-01-01T00:00:00"
  },
  "assistant_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Of course! I'd be happy to help you with your math homework...",
    "blocked": false,
    "block_reason": null,
    "created_at": "2024-01-01T00:00:01"
  },
  "was_blocked": false,
  "block_reason": null,
  "session_id": "uuid",
  "session_title": "Math Homework Help",
  "video_suggestion": {
    "video_id": "abc123xyz",
    "title": "Math Homework Made Easy - Educational Video for Kids",
    "url": "https://www.youtube.com/watch?v=abc123xyz",
    "thumbnail_url": "https://i.ytimg.com/vi/abc123xyz/hqdefault.jpg",
    "channel_title": "Kids Learning Channel"
  }
}
```

Response (blocked):
```json
{
  "user_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "Tell me about violence in video games",
    "blocked": true,
    "block_reason": "Message contains restricted content. Please rephrase your question.",
    "created_at": "2024-01-01T00:00:00"
  },
  "assistant_message": null,
  "was_blocked": true,
  "block_reason": "Message contains restricted content. Please rephrase your question."
}
```

### Get Child Analytics (Parent)

```bash
curl -X GET http://localhost:8000/api/parent/analytics/{child_id} \
  -H "Authorization: Bearer YOUR_PARENT_ACCESS_TOKEN"
```

Response:
```json
{
  "child_id": "uuid",
  "child_name": "Tommy",
  "total_sessions": 5,
  "total_messages": 42,
  "blocked_messages": 3,
  "last_activity": "2024-01-01T15:30:00"
}
```

### Refresh Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Content Filtering

The system supports two filtering modes:

### Allowlist Mode
- Only messages related to approved topics are allowed
- Best for strict control over what kids can discuss
- Example: `["math", "science", "art", "reading"]`

### Blocklist Mode (Default)
- Messages containing blocked keywords are rejected
- More permissive but blocks specific harmful content
- Example: `["violence", "drugs", "weapons", "explicit"]`

## Security Features

- **Password Hashing**: All passwords are hashed with bcrypt before storage
- **JWT Tokens**: Secure authentication with access and refresh tokens
- **Role-based Access**: Parents and kids have separate permissions
- **Parent-Child Verification**: All child data requests verify parent ownership
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Rate Limiting**: Protects against abuse (configurable)
- **CORS Configuration**: Restricts allowed origins
- **Content Filtering**: Backend-only filtering (never trust client-side)

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | 7 |
| `OPENAI_API_KEY` | OpenAI API key | Required for AI |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | Optional (for video suggestions) |
| `CORS_ORIGINS` | Allowed CORS origins | ["http://localhost:3000"] |
| `DEBUG` | Enable debug mode | False |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | 60 |

## Production Deployment

### Recommendations

1. **Use a production WSGI server**: Gunicorn with uvicorn workers
2. **Set up SSL/TLS**: Use HTTPS in production
3. **Configure proper logging**: Set up log aggregation
4. **Monitor the application**: Use tools like Prometheus/Grafana
5. **Database backups**: Regular automated backups
6. **Environment variables**: Use a secrets manager
7. **Rate limiting**: Adjust based on expected traffic
8. **Scale horizontally**: Use load balancer with multiple instances

### Example Gunicorn Command

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Troubleshooting

### Common Issues

1. **Database connection failed**: Check `DATABASE_URL` and PostgreSQL is running
2. **JWT errors**: Ensure `SECRET_KEY` is set and consistent
3. **AI service unavailable**: Verify `OPENAI_API_KEY` is valid
4. **CORS errors**: Update `CORS_ORIGINS` to include your frontend URL
5. **Migration errors**: Ensure database exists and user has permissions

### Logs

Check application logs for detailed error information. In debug mode, full stack traces are included in responses.

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and feature requests, please open a GitHub issue.
