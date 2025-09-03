# Multi-Environment Configuration Management

This document describes the multi-environment configuration management system implemented for the FastAPI application.

## Overview

The configuration system supports three environments:

- **development**: Local development with debug features enabled
- **testing**: Testing environment with production-like settings but test data
- **production**: Production environment with security and performance optimizations

## Environment Files

Configuration is managed through environment-specific files:

```
backend/
├── .env.development    # Development environment
├── .env.testing       # Testing environment
├── .env.production    # Production environment
└── .env.example       # Template file
```

## Setting the Environment

Set the `ENVIRONMENT` variable to control which configuration is loaded:

```bash
# Development (default)
export ENVIRONMENT=development

# Testing
export ENVIRONMENT=testing

# Production
export ENVIRONMENT=production
```

## Configuration Structure

Each environment file contains:

### Application Settings

- `APP_NAME`: Application name (environment-specific)
- `DEBUG`: Debug mode (True for development, False for testing/production)
- `VERSION`: Application version

### Database Settings

- `DATABASE_URL`: Database connection string (environment-specific)

### Security Settings

- `SECRET_KEY`: JWT secret key (use placeholders in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

### CORS Settings

- `BACKEND_CORS_ORIGINS`: Allowed origins (localhost for dev, production domains for prod)

### Logging Settings

- `LOG_LEVEL`: Logging level (DEBUG for dev, INFO for testing/prod)
- `LOG_FILE_PATH`: Log file location
- `LOG_FORMAT`: Log format (json)

### Server Settings

- `RELOAD`: Auto-reload on changes (True for dev, False for prod)
- `WORKERS`: Number of worker processes

## Usage Examples

### Loading Configuration

```python
from app.core.config import get_settings

# Get settings for current environment
settings = get_settings()

# Check current environment
if settings.is_development():
    print("Running in development mode")
elif settings.is_production():
    print("Running in production mode")
```

### Environment Detection

```python
from app.core.environment import get_current_environment, Environment

current_env = get_current_environment()
if current_env == Environment.DEVELOPMENT:
    # Development-specific code
    pass
```

### Configuration Validation

```python
from app.core.config_validator import validate_configuration

settings = get_settings()
report = validate_configuration(settings)

if not report["valid"]:
    print("Configuration errors:")
    for error in report["errors"]:
        print(f"  - {error}")
```

## CLI Management Tool

Use the configuration management CLI for validation and inspection:

```bash
# Show environment information
python scripts/config_manager.py info

# Validate current environment
python scripts/config_manager.py validate

# Validate specific environment
python scripts/config_manager.py validate --env production

# Validate all environments
python scripts/config_manager.py validate-all

# List configuration files
python scripts/config_manager.py list
```

## Health Check Endpoint

The application provides a health check endpoint that includes configuration status:

```bash
curl http://localhost:8000/health
```

Response includes:

- Environment information
- Configuration validation status
- Errors and warnings
- Configuration summary

## Production Deployment

For production deployment:

1. Set environment variables:

   ```bash
   export ENVIRONMENT=production
   export SECRET_KEY=your-actual-secret-key
   export DB_PASSWORD=your-db-password
   ```

2. Validate configuration:

   ```bash
   python scripts/config_manager.py validate --env production
   ```

3. Start the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Configuration Validation Rules

The system validates:

### Database Configuration

- DATABASE_URL is required
- SQLite not recommended for production
- No unresolved placeholders in production

### Security Configuration

- SECRET_KEY is required
- No default/development keys in production
- Positive token expiration time

### CORS Configuration

- No localhost origins in production
- No wildcard origins in production

### Logging Configuration

- Valid log levels
- Log directory exists or can be created

### Environment-Specific Rules

- DEBUG=False in production
- RELOAD=False in production
- Appropriate log levels for each environment

## Troubleshooting

### Common Issues

1. **Configuration file not found**

   - Ensure the environment-specific file exists
   - Check file permissions
   - Verify ENVIRONMENT variable is set correctly

2. **Validation errors in production**

   - Check for unresolved placeholders (${VAR})
   - Ensure all required environment variables are set
   - Validate SECRET_KEY is not using default values

3. **Database connection issues**
   - Verify DATABASE_URL format
   - Check database server accessibility
   - Ensure credentials are correct

### Debug Commands

```bash
# Check current environment
python -c "from app.core.environment import get_environment_info; print(get_environment_info())"

# Test configuration loading
python -c "from app.core.config import get_settings; s=get_settings(); print(f'Env: {s.ENVIRONMENT}, Debug: {s.DEBUG}')"

# Validate configuration
python scripts/config_manager.py validate
```

## Best Practices

1. **Never commit sensitive data** to version control
2. **Use environment variables** for secrets in production
3. **Validate configuration** before deployment
4. **Use different databases** for each environment
5. **Test configuration changes** in staging first
6. **Monitor configuration health** using the health endpoint
7. **Keep environment files in sync** with required settings
