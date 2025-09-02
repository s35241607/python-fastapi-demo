# Python FastAPI Demo

A full-stack application demo with FastAPI backend and modern frontend.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/     # API endpoint handlers
│   │   │       │   ├── health.py
│   │   │       │   └── items.py
│   │   │       └── routers.py     # API router configuration
│   │   ├── core/
│   │   │   ├── config.py          # Application configuration
│   │   │   ├── logger.py          # Logging configuration
│   │   │   └── security.py        # Security utilities
│   │   ├── db/
│   │   │   ├── base.py            # Database base configuration
│   │   │   └── session.py         # Database session management
│   │   ├── schemas/
│   │   │   ├── item.py            # Item Pydantic models
│   │   │   └── user.py            # User Pydantic models
│   │   ├── services/
│   │   │   └── item.py            # Business logic layer
│   │   ├── repositories/
│   │   │   └── item.py            # Data access layer
│   │   └── main.py                # FastAPI application factory
│   ├── alembic/
│   │   ├── versions/              # Database migration files
│   │   └── env.py                 # Alembic configuration
│   ├── tests/
│   │   ├── api/                   # API tests
│   │   ├── services/              # Service tests
│   │   └── conftest.py            # Test configuration
│   ├── .env.example               # Environment variables template
│   ├── alembic.ini                # Alembic configuration
│   ├── main.py                    # Application entry point
│   └── pyproject.toml             # Project dependencies
└── frontend/                      # Frontend application (to be implemented)
```

## Backend Architecture

The backend follows a clean, layered architecture:

- **API Layer** (`api/`): Handles HTTP requests and responses
- **Service Layer** (`services/`): Contains business logic
- **Repository Layer** (`repositories/`): Handles data access
- **Schema Layer** (`schemas/`): Defines data models and validation
- **Core Layer** (`core/`): Contains configuration and utilities

## Getting Started

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Copy environment variables:

   ```bash
   cp .env.example .env
   ```

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Run the application:

   ```bash
   fastapi dev main.py
   ```

5. Visit `http://localhost:8000/docs` to see the API documentation.

### API Endpoints

- `/` - Root endpoint
- `/api/v1/health` - Health check endpoint
- `/api/v1/items` - Items management endpoints

## Development

### Backend Technologies

- **FastAPI** - Modern, fast web framework for building APIs
- **Pydantic** - Data validation and settings management
- **SQLAlchemy** - SQL toolkit and ORM
- **Alembic** - Database migration tool
- **pytest** - Testing framework
- **Loguru** - Modern logging library

### Testing

Run backend tests:

```bash
cd backend
pytest
```

### Code Quality

The project uses Ruff for linting and formatting:

```bash
cd backend
ruff check .
ruff format .
```

## License

This project is for demonstration purposes.
