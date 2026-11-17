# Career Elevate Backend

**Career Elevate** is a comprehensive career development platform built with modern web technologies. This FastAPI backend provides authentication, AI-powered career tools, learning management, and payment integration services.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Database Setup](#database-setup)
- [Authentication & Authorization](#authentication--authorization)
- [Core Modules](#core-modules)
  - [User Management](#user-management)
  - [AI Services](#ai-services)
  - [Course Management](#course-management)
  - [Job Application Tracking](#job-application-tracking)
  - [Payment Processing](#payment-processing)
  - [Profession Management](#profession-management)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Development Workflow](#development-workflow)
- [Security Considerations](#security-considerations)

---

## Overview

Career Elevate is designed to help users advance their careers through:

- **AI-Powered Resume Analysis**: Upload and analyze CVs to identify strengths and areas for improvement
- **Interview Practice**: Practice interview responses with AI feedback using audio transcription
- **Structured Learning Paths**: Access courses, modules, and learning resources
- **Job Application Tracking**: Manage job applications with detailed activity logs
- **Credit-Based System**: Separate credit balances for CV analysis and interview practice features
- **Secure Authentication**: JWT-based authentication with Google OAuth 2.0 integration
- **Payment Integration**: Stripe-powered credit package purchasing

---

## System Architecture

The application follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────────┐
│                      Controllers                         │
│  (HTTP Request Handlers - FastAPI Routes)               │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                      Services                            │
│  (Business Logic - AI, Auth, Payments, etc.)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Repositories                          │
│  (Data Access Layer - Database Operations)              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Database Models                          │
│  (SQLAlchemy ORM - PostgreSQL)                          │
└─────────────────────────────────────────────────────────┘
```

**Key Design Patterns:**
- **Dependency Injection**: Services and repositories are injected via FastAPI's Depends
- **Repository Pattern**: Abstracts database operations for testability
- **Service Layer**: Encapsulates business logic and external API interactions
- **Schema Validation**: Pydantic models for request/response validation

---

## Technology Stack

### Backend Framework
- **FastAPI 0.116+**: Modern async web framework
- **Python 3.11+**: Core programming language
- **Uvicorn**: ASGI server for production deployment

### Database
- **PostgreSQL 14+**: Primary relational database
- **SQLAlchemy 2.0+**: ORM for database interactions
- **Alembic 1.16+**: Database migration management
- **psycopg2**: PostgreSQL database adapter

### Authentication & Security
- **JWT (PyJWT)**: Token-based authentication
- **Bcrypt**: Password hashing
- **Google OAuth 2.0**: Third-party authentication
- **python-jose**: JOSE token handling

### External Services
- **OpenAI API**: GPT-4.5-mini for analysis, Whisper-1 for transcription
- **AWS S3 + CloudFront**: File storage and CDN
- **Stripe API**: Payment processing
- **Resend API**: Email notifications

### Development Tools
- **Docker & Docker Compose**: Containerization
- **pgAdmin**: Database management UI
- **Python-dotenv**: Environment variable management

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Docker (optional, for containerized deployment)
- AWS Account (for S3 storage)
- Stripe Account (for payments)
- OpenAI API Key
- Resend API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/career_elevate

# JWT Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
CLOUDFRONT_DOMAIN=your-cloudfront-domain

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key

# Email
RESEND_API_KEY=your-resend-api-key

# Application
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

### Database Setup

1. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

2. **Seed initial data** (optional):
   ```bash
   python seed_db.py
   ```

3. **Using Docker Compose**:
   ```bash
   docker-compose up -d
   ```

---

## Authentication & Authorization

### Authentication Flow

1. **Registration**:
   - User provides email and password
   - Password is hashed using bcrypt (12 rounds)
   - User record created in database
   - Email verification sent via Resend

2. **Login**:
   - User provides credentials
   - Password verified against stored hash
   - JWT access token generated (15 min expiry)
   - Refresh token stored in HTTP-only cookie (30 days)

3. **Google OAuth**:
   - User redirects to Google consent screen
   - Authorization code exchanged for tokens
   - User profile retrieved from Google
   - Account created or linked in database

### JWT Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Protected Routes

All routes requiring authentication use the `get_current_user` dependency:

```python
@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(auth_middleware.get_current_user)
):
    return current_user
```

---

## Core Modules

### User Management

**Location**: `controllers/user_controller.py`, `services/user_service.py`, `repositories/user_repository.py`

**Features**:
- User profile management (CRUD operations)
- Email verification and password reset
- Credit balance tracking (CV analyzer, interview practice)
- Activity history and analytics

**Key Endpoints**:
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/me/credits` - Get credit balances
- `POST /users/verify-email` - Verify email address

### AI Services

**Location**: `services/ai_service.py`

**Features**:

1. **CV Analysis**:
   - Extract text from PDF/DOCX resumes
   - Analyze with GPT-4.5-mini
   - Store analysis results and file in S3
   - Deduct credits from user balance

2. **Interview Practice**:
   - Upload audio responses (MP3/MP4/WAV)
   - Transcribe with Whisper-1
   - Analyze response quality with GPT
   - Store audio in S3 with metadata
   - Track practice sessions

**Key Endpoints**:
- `POST /ai/analyze-cv` - Upload and analyze resume
- `GET /ai/cv-analyses` - Get user's CV analysis history
- `POST /ai/interview/analyze` - Analyze interview response
- `GET /ai/interview/questions` - Get practice questions by profession

### Course Management

**Location**: `controllers/course_controller.py`, `services/course_service.py`

**Features**:
- Browse available courses
- Enroll in courses
- Track course progress
- Module completion tracking
- Certificate generation upon completion

**Key Endpoints**:
- `GET /courses` - List all courses
- `GET /courses/{id}` - Get course details
- `POST /courses/{id}/enroll` - Enroll in course
- `GET /courses/my-courses` - Get user's enrolled courses

### Job Application Tracking

**Location**: `controllers/job_application_controller.py`, `services/job_application_service.py`

**Features**:
- Create and manage job applications
- Track application status (Applied, Interview, Offer, Rejected)
- Log application activities (Phone screen, On-site, Follow-up)
- Application statistics and analytics

**Key Endpoints**:
- `POST /job-applications` - Create new application
- `GET /job-applications` - List user's applications
- `PUT /job-applications/{id}` - Update application
- `POST /job-applications/{id}/activities` - Log activity

### Payment Processing

**Location**: `services/user_service.py` (purchase methods)

**Features**:
- Stripe Checkout integration
- Credit package purchasing
- Payment history tracking
- Webhook handling for payment events

**Credit Packages**:
- CV Analyzer Credits: 10, 25, 50 credits
- Interview Practice Credits: 5, 15, 30 sessions

**Key Endpoints**:
- `POST /users/purchase/cv-credits` - Buy CV analysis credits
- `POST /users/purchase/interview-credits` - Buy interview credits
- `POST /webhooks/stripe` - Stripe webhook handler

### Profession Management

**Location**: `controllers/profession_controller.py`, `services/profession_service.py`

**Features**:
- Predefined profession categories
- Interview question banks by profession
- Profession-specific learning paths

**Key Endpoints**:
- `GET /professions` - List all professions
- `GET /professions/{id}` - Get profession details

---

## Database Schema

### Core Tables

1. **users**:
   - `Id` (UUID, PK)
   - `email` (String, unique)
   - `full_name` (String)
   - `password_hash` (String, nullable for OAuth users)
   - `is_verified` (Boolean)
   - `is_active` (Boolean)
   - `created_at`, `updated_at` (Timestamp)

2. **cv_analyzer_balances**:
   - `Id` (UUID, PK)
   - `user_id` (UUID, FK → users)
   - `available_credits` (Integer)
   - `created_at`, `updated_at` (Timestamp)

3. **interview_practice_balances**:
   - `Id` (UUID, PK)
   - `user_id` (UUID, FK → users)
   - `available_credits` (Integer)
   - `created_at`, `updated_at` (Timestamp)

4. **cv_analyses**:
   - `Id` (UUID, PK)
   - `user_id` (UUID, FK → users)
   - `file_key` (String, S3 key)
   - `original_filename` (String)
   - `analysis_result` (JSON)
   - `created_at` (Timestamp)

5. **interview_practice_sessions**:
   - `Id` (UUID, PK)
   - `user_id` (UUID, FK → users)
   - `question_id` (UUID, FK → interview_questions)
   - `audio_file_url` (String)
   - `transcript` (Text)
   - `analysis_result` (JSON)
   - `duration_seconds` (Integer)
   - `created_at` (Timestamp)

6. **courses**:
   - `Id` (UUID, PK)
   - `title`, `description` (String)
   - `thumbnail_url` (String)
   - `difficulty_level` (Enum)
   - `estimated_duration_hours` (Integer)
   - `is_published` (Boolean)
   - `created_at`, `updated_at` (Timestamp)

7. **job_applications**:
   - `Id` (UUID, PK)
   - `user_id` (UUID, FK → users)
   - `company_name`, `position` (String)
   - `status` (Enum)
   - `application_date` (Date)
   - `created_at`, `updated_at` (Timestamp)

### Relationships

- **One-to-One**: `users` ↔ `cv_analyzer_balances`, `users` ↔ `interview_practice_balances`
- **One-to-Many**: `users` → `cv_analyses`, `users` → `job_applications`, `courses` → `modules`
- **Many-to-Many**: `users` ↔ `courses` (via `user_courses` junction table)

---

## API Documentation

### Interactive Documentation

Once the server is running, access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Common Response Formats

**Success Response**:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

**Error Response**:
```json
{
  "error": true,
  "message": "Error description",
  "details": { ... }
}
```

### Rate Limiting

- CV Analysis: Limited by credit balance
- Interview Practice: Limited by credit balance
- API requests: No global rate limit (implement if needed)

---

## Development Workflow

### Running Migrations

**Create a new migration**:
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback migrations**:
```bash
alembic downgrade -1  # Rollback one version
```

### Seeding Data

The `seeds/` directory contains seeders for:
- Age groups
- Content types
- Course statuses
- Credit packages
- Interview questions
- Job activity types
- Professions

Run all seeds:
```bash
python seed_db.py
```

### Testing

```bash
pytest tests/ -v
```

### Code Style

Follow PEP 8 guidelines. Use formatters:
```bash
black .
isort .
flake8 .
```

---

## Security Considerations

### Implemented Security Measures

1. **Password Security**:
   - Bcrypt hashing with 12 rounds
   - Minimum password strength requirements
   - Secure password reset flow

2. **Token Security**:
   - Short-lived access tokens (15 min)
   - HTTP-only refresh tokens
   - Token rotation on refresh

3. **CORS Configuration**:
   - Restricted origins in production
   - Credentials allowed only for trusted domains

4. **Input Validation**:
   - Pydantic models for request validation
   - SQL injection prevention via ORM
   - File type and size validation

5. **Environment Isolation**:
   - Secrets stored in environment variables
   - `.env` file excluded from version control

6. **Rate Limiting**:
   - Credit-based system prevents abuse of AI features

### Production Deployment Best Practices

1. **Use HTTPS**: Always serve over TLS in production
2. **Database Security**:
   - Use connection pooling
   - Enable SSL connections
   - Restrict database access by IP
3. **Logging**: Enable structured logging for audit trails
4. **Monitoring**: Implement health checks and uptime monitoring
5. **Secrets Management**: Use AWS Secrets Manager or similar
6. **Dependency Updates**: Regularly update dependencies for security patches
7. **API Versioning**: Implement versioning to prevent breaking changes
8. **Backup Strategy**: Automate database backups
9. **CDN & Caching**: Use CloudFront for static assets
10. **Error Handling**: Never expose stack traces in production responses

### Known Limitations

- No global API rate limiting implemented (feature-level limits via credits)
- Email verification is not enforced for login (optional enhancement)
- No two-factor authentication (2FA) support yet
- File uploads limited to 10MB (configurable)

---

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

For questions or issues, contact [your-email@example.com]
