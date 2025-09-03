# Integration Tests Documentation

This document describes the comprehensive integration test suite for the infrastructure setup feature.

## Overview

The integration test suite validates the complete infrastructure setup including:

- Docker containerization and service startup
- Multi-environment configuration management
- Middleware integration (error handling, logging, JWT parsing)
- End-to-end request flows
- Logging and error handling verification
- System performance and stability

## Test Structure

### Test Files

1. **`test_docker_integration.py`** - Docker container and service tests
2. **`test_integration_config.py`** - Multi-environment configuration tests
3. **`test_middleware_integration.py`** - Middleware chain integration tests
4. **`test_end_to_end_flows.py`** - Complete request flow tests
5. **`test_logging_error_verification.py`** - Logging and error handling tests
6. **`test_comprehensive_integration.py`** - Full system integration tests

### Test Categories

#### Docker Integration Tests (`test_docker_integration.py`)

- **Docker Compose Configuration Tests**

  - Validates syntax of all Docker Compose files
  - Verifies required files exist
  - Tests Dockerfile syntax validation

- **Container Startup Tests** (marked as `@pytest.mark.slow`)

  - Tests development environment startup with PostgreSQL
  - Tests production environment startup
  - Validates health checks and service dependencies

- **Docker Networking Tests**

  - Verifies network configuration
  - Tests service dependencies and communication

- **Docker Volume Tests**

  - Validates volume mounts for logs and source code
  - Tests development hot-reload configuration

- **Environment Variable Tests**
  - Verifies environment-specific configurations
  - Tests environment file loading in containers

#### Configuration Integration Tests (`test_integration_config.py`)

- **Multi-Environment Loading**

  - Tests loading of development, testing, and production configurations
  - Validates environment-specific settings (DEBUG, LOG_LEVEL, etc.)
  - Tests database URL configuration per environment

- **Configuration Validation**

  - Tests health endpoint configuration reporting
  - Validates configuration validation logic
  - Tests environment detection functions

- **Environment Switching**
  - Tests dynamic environment switching
  - Validates settings caching and reloading

#### Middleware Integration Tests (`test_middleware_integration.py`)

- **Middleware Chain Tests**

  - Tests complete middleware execution order
  - Validates middleware state management
  - Tests middleware with and without JWT tokens

- **Error Handling Integration**

  - Tests error propagation through middleware
  - Validates error context preservation
  - Tests middleware error tolerance

- **Performance Tests**
  - Tests middleware performance impact
  - Validates request state isolation
  - Tests concurrent request handling

#### End-to-End Flow Tests (`test_end_to_end_flows.py`)

- **Complete Request Lifecycle**

  - Tests authenticated and unauthenticated request flows
  - Validates complete middleware chain execution
  - Tests request state management

- **Error Handling Flows**

  - Tests error handling with full context
  - Validates error response consistency
  - Tests different error types and scenarios

- **JWT Processing Flows**

  - Tests valid, expired, and malformed JWT tokens
  - Validates non-blocking JWT error handling
  - Tests JWT context propagation

- **Performance and Concurrency**
  - Tests concurrent request handling
  - Validates request state isolation
  - Tests system performance under load

#### Logging and Error Verification Tests (`test_logging_error_verification.py`)

- **Logging Functionality**

  - Tests structured logging format (JSON)
  - Validates log levels and configuration
  - Tests logging middleware integration

- **Error Handling Functionality**

  - Tests custom exception handling
  - Validates error response formatting
  - Tests error response security (no data leakage)

- **Logging-Error Integration**
  - Tests error logging with user context
  - Validates log correlation across middleware
  - Tests log file handling and rotation

#### Comprehensive Integration Tests (`test_comprehensive_integration.py`)

- **Full System Integration**

  - Tests complete system with all components
  - Validates system resilience to failures
  - Tests production readiness checklist

- **System Performance**

  - Tests performance under load
  - Validates memory usage stability
  - Tests concurrent request handling

- **Configuration Integration**
  - Tests multi-environment behavior
  - Validates Docker integration readiness
  - Tests system startup and health checks

## Running Tests

### Prerequisites

1. Python 3.12+ with required dependencies installed
2. Docker and Docker Compose (for Docker integration tests)
3. PostgreSQL 16 (for local development tests)

### Quick Start

```bash
# Run all integration tests
cd backend
python tests/run_integration_tests.py

# Run specific test suite
python tests/run_integration_tests.py --suite configuration

# Run in fast mode (skip slow Docker tests)
python tests/run_integration_tests.py --fast

# Run with verbose output
python tests/run_integration_tests.py --verbose

# Generate detailed report
python tests/run_integration_tests.py --report integration_report.txt
```

### Using pytest directly

```bash
# Run all integration tests
pytest tests/ -v

# Run specific test file
pytest tests/test_middleware_integration.py -v

# Run tests with specific markers
pytest -m "integration" -v
pytest -m "not slow" -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run with custom configuration
pytest -c pytest.integration.ini tests/
```

### Test Markers

- `@pytest.mark.integration` - Integration tests (may be slower)
- `@pytest.mark.slow` - Slow tests (Docker startup, etc.)
- `@pytest.mark.docker` - Tests requiring Docker
- `@pytest.mark.unit` - Fast unit tests

### Environment Variables

Set these environment variables to control test behavior:

```bash
# Set environment for configuration tests
export ENVIRONMENT=testing

# Skip Docker tests in CI
export SKIP_DOCKER_TESTS=true

# Set custom log level for tests
export LOG_LEVEL=DEBUG
```

## Test Data and Fixtures

### Common Fixtures

- `client` - FastAPI test client
- `async_client` - Async test client
- `valid_jwt_token` - Valid JWT token for authentication tests
- `expired_jwt_token` - Expired JWT token for error testing
- `temp_log_file` - Temporary log file for logging tests

### Test Data

Tests use realistic but safe test data:

- User IDs: `user123`, `integration_user`
- Usernames: `testuser`, `integration_test`
- Emails: `test@example.com`, `integration@test.com`
- Roles: `["user", "admin", "tester"]`
- Permissions: `["read", "write", "delete", "test"]`

## Expected Test Results

### Success Criteria

All tests should pass with the following validations:

1. **Docker Integration**

   - All Docker Compose files have valid syntax
   - Containers start successfully in development and production modes
   - Health checks pass
   - Services communicate properly

2. **Configuration Management**

   - All environment configurations load correctly
   - Environment-specific settings are applied
   - Configuration validation passes
   - Health endpoint reports correct status

3. **Middleware Integration**

   - Middleware chain executes in correct order
   - JWT parsing works (with error tolerance)
   - Logging captures all requests and errors
   - Error handling provides consistent responses

4. **End-to-End Flows**

   - Complete request flows work with and without authentication
   - Error scenarios are handled gracefully
   - Request state is properly isolated
   - Performance is within acceptable limits

5. **Logging and Error Handling**
   - Structured logging works correctly
   - All error types are handled consistently
   - No sensitive data leaks in error responses
   - Log correlation works across middleware

### Performance Benchmarks

- Average request response time: < 100ms
- Maximum request response time: < 500ms
- Memory usage increase over 100 requests: < 50MB
- Concurrent request handling: 10+ simultaneous requests

## Troubleshooting

### Common Issues

1. **Docker Tests Failing**

   - Ensure Docker and Docker Compose are installed
   - Check that ports 8000, 5432, 5050 are available
   - Verify Docker daemon is running

2. **Configuration Tests Failing**

   - Check that all `.env.*` files exist in `backend/`
   - Verify environment variables are set correctly
   - Ensure database URLs are valid for test environment

3. **JWT Tests Failing**

   - Verify JWT token generation in fixtures
   - Check that JWT parsing middleware is configured
   - Ensure test tokens have valid structure

4. **Logging Tests Failing**

   - Check log file permissions
   - Verify logging configuration
   - Ensure log directory exists and is writable

5. **Performance Tests Failing**
   - Run tests on a machine with adequate resources
   - Check for resource contention with other processes
   - Verify network connectivity for external dependencies

### Debug Mode

Run tests with debug information:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
pytest tests/ -v -s --tb=long

# Run single test with debugging
pytest tests/test_middleware_integration.py::TestMiddlewareIntegration::test_middleware_chain_with_jwt -v -s --pdb
```

### CI/CD Considerations

For CI/CD environments:

1. Use `--fast` mode to skip slow Docker tests
2. Set appropriate timeout values
3. Ensure test database is available
4. Use test-specific environment variables
5. Generate test reports for build artifacts

## Maintenance

### Adding New Tests

1. Follow existing test patterns and naming conventions
2. Use appropriate test markers (`@pytest.mark.integration`, etc.)
3. Include proper docstrings and comments
4. Add new test files to the test runner script
5. Update this documentation

### Updating Test Data

1. Keep test data realistic but safe
2. Use consistent test user IDs and names
3. Avoid hardcoded values where possible
4. Update fixtures when adding new test scenarios

### Performance Monitoring

1. Monitor test execution times
2. Update performance benchmarks as needed
3. Optimize slow tests where possible
4. Consider parallel test execution for large suites

## Integration with Requirements

This test suite validates the following requirements from the infrastructure setup specification:

- **Requirement 1.1**: Docker containerization and service startup
- **Requirement 2.1**: Multi-environment configuration management
- **Requirement 3.1**: Error handling middleware functionality
- **Requirement 4.1**: Structured logging system
- **Requirement 5.1**: JWT user information parsing

Each test file includes requirement references in task details to maintain traceability.
