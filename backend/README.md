# FastAPI Demo Application

This is a demo FastAPI application with a modular structure.

## Project Structure

```
backend/
├── app/
│   ├── routers/       # API routes
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic models for request/response validation
│   ├── core/          # Core application components (config, security, etc.)
│   └── utils/         # Utility functions
├── main.py            # Application entry point
└── pyproject.toml     # Project dependencies
```

## Getting Started

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run the application:
   ```bash
   fastapi dev main.py
   ```

3. Visit `http://localhost:8000` to see the API documentation.

## API Endpoints

- `/` - Root endpoint
- `/health` - Health check endpoint
- `/items` - Items management endpoints
- `/users` - Users management endpoints

## Development

This project uses:
- FastAPI for the web framework
- Pydantic for data validation
- Standard Python packaging with pyproject.toml