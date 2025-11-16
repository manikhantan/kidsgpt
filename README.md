# KidsGPT - Kid-Safe AI Chat Platform

A production-ready backend API for a kid-safe conversational AI application with comprehensive parental controls. KidsGPT provides a secure platform for children to interact with AI while parents maintain full oversight and control over content.

## Features

- **Dual-User Authentication** - Separate accounts and permissions for parents and children
- **Content Filtering** - Configurable allowlist/blocklist modes to control conversation topics
- **Multi-AI Provider Support** - OpenAI and Google Gemini integration with auto-selection
- **Parental Controls**
  - Create and manage child accounts
  - Configure content filtering rules
  - View complete chat history (including blocked attempts)
  - Access usage analytics
- **Chat Management** - Organized chat sessions with message history tracking
- **Security** - JWT-based authentication, BCrypt password hashing, rate limiting
- **Blocked Content Logging** - Track and review filtered messages for safety monitoring

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 12+ with SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose) + BCrypt
- **AI Providers**: OpenAI, Google Gemini
- **Validation**: Pydantic 2.5
- **Rate Limiting**: slowapi

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Settings management
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── api/v1/              # API route handlers
│   ├── services/            # Business logic
│   └── core/                # Security & exceptions
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── .env.example             # Environment template
├── alembic.ini              # Alembic configuration
└── requirements.txt         # Python dependencies
```

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- OpenAI API key and/or Google Gemini API key

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kidsgpt
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kidsgpt

# Security
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Providers
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
AI_PROVIDER=auto  # Options: openai, gemini, auto

# Application
APP_NAME=KidSafe AI
APP_VERSION=1.0.0
DEBUG=False
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=http://localhost:3000
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

### 5. Create Database

```bash
createdb kidsgpt
```

### 6. Run Migrations

```bash
cd backend
alembic upgrade head
```

### 7. Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, access interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/parent/register` | Register parent account |
| POST | `/api/auth/parent/login` | Parent login |
| POST | `/api/auth/kid/login` | Child login |
| POST | `/api/auth/refresh` | Refresh access token |

### Parent Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/parent/children` | Create child account |
| GET | `/api/parent/children` | List all children |
| PUT | `/api/parent/children/{child_id}` | Update child account |
| DELETE | `/api/parent/children/{child_id}` | Delete child account |
| GET | `/api/parent/content-rules` | Get content filtering rules |
| PUT | `/api/parent/content-rules` | Update filtering rules |
| GET | `/api/parent/chat-history/{child_id}` | View child's chat history |
| GET | `/api/parent/analytics/{child_id}` | Get usage analytics |

### Child Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/kid/chat` | Send message (with content filtering) |
| GET | `/api/kid/chat-history` | Get own chat history |
| GET | `/api/kid/current-session` | Get or create chat session |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health status |
| GET | `/` | API information |

## Content Filtering

KidsGPT supports two filtering modes:

### Allowlist Mode
Only pre-approved topics are allowed. Configure specific topics children can discuss.

### Blocklist Mode
Specific harmful keywords and topics are blocked. All other content is permitted.

Parents can configure these rules through the API to match their comfort level and child's needs.

## Usage Examples

### Register a Parent

```bash
curl -X POST "http://localhost:8000/api/auth/parent/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

### Create a Child Account

```bash
curl -X POST "http://localhost:8000/api/parent/children" \
  -H "Authorization: Bearer <parent_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kiddo",
    "password": "kidpassword",
    "age": 10
  }'
```

### Child Chat Message

```bash
curl -X POST "http://localhost:8000/api/kid/chat" \
  -H "Authorization: Bearer <child_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about dinosaurs!"
  }'
```

## Security Features

- **JWT Authentication** - Secure token-based authentication with refresh tokens
- **Password Hashing** - BCrypt with salt for secure password storage
- **Rate Limiting** - Protection against API abuse
- **Role-Based Access** - Strict separation between parent and child permissions
- **Parent-Child Verification** - Parents can only access their own children's data
- **Content Sanitization** - Input validation and sanitization

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | 7 |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `GEMINI_API_KEY` | Google Gemini API key | Optional |
| `AI_PROVIDER` | AI provider selection | auto |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 |
| `APP_NAME` | Application name | KidSafe AI |
| `APP_VERSION` | Version number | 1.0.0 |
| `DEBUG` | Debug mode | False |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per IP | 60 |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
