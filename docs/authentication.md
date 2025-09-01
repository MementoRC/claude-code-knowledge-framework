# Authentication System Documentation

## Overview

The UCKN API authentication system provides secure API key-based authentication with role-based access control (RBAC) and rate limiting.

## Components

### 1. Core Authentication Functions

Located in `src/uckn/api/dependencies.py`:

- **`get_settings()`**: Returns cached application settings including API configuration
- **`validate_api_key(api_key: str)`**: Validates if an API key is authorized
- **`get_user_context(api_key: str)`**: Retrieves user context including roles and permissions

### 2. Authentication Middleware

Located in `src/uckn/api/middleware/auth.py`:

- **`AuthMiddleware`**: FastAPI middleware that enforces authentication on protected endpoints
- **`get_current_user(request)`**: Helper to retrieve authenticated user from request
- **`require_permission(permission)`**: Decorator for permission-based access control
- **`require_role(role)`**: Decorator for role-based access control

### 3. Rate Limiting Middleware

Located in `src/uckn/api/middleware/rate_limiting.py`:

- **`RateLimitingMiddleware`**: Enforces rate limits per user/API key
- Sliding window algorithm for accurate rate limiting
- Configurable limits per endpoint type

## Configuration

### Environment Variables

```bash
# API Key Configuration
UCKN_API_KEY_HEADER=X-API-Key          # Header name for API key
UCKN_VALID_API_KEYS=key1,key2,key3     # Comma-separated valid keys
UCKN_ADMIN_API_KEYS=admin1,admin2      # Comma-separated admin keys

# Rate Limiting
UCKN_RATE_LIMIT_ENABLED=true           # Enable/disable rate limiting
UCKN_RATE_LIMIT_REQUESTS=100           # Requests per window
UCKN_RATE_LIMIT_WINDOW=60              # Window size in seconds

# User Context
UCKN_DEFAULT_USER_ID=default-user      # Default user ID
```

## API Key Authentication

### Request Headers

The API accepts authentication via multiple header formats:

1. **X-API-Key**: `X-API-Key: your-api-key`
2. **X-Api-Key**: `X-Api-Key: your-api-key` (case variant)
3. **Authorization Bearer**: `Authorization: Bearer your-api-key`

### Public Endpoints

These endpoints don't require authentication:

- `/` - Root endpoint
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
- `/openapi.json` - OpenAPI specification
- `/health/status` - Health check
- `/health/ping` - Ping endpoint
- `/api/v1/info` - API information

### Protected Endpoints

All other endpoints require a valid API key.

## User Roles and Permissions

### Roles

- **`user`**: Standard user with basic access
- **`admin`**: Administrator with full access

### Permissions

Standard users have:
- `read`: Read access to resources
- `write`: Create and update resources

Administrators additionally have:
- `delete`: Delete resources
- `admin`: Administrative operations

## Rate Limiting

### Default Limits

- **Default**: 100 requests per 60 seconds
- **Search endpoints**: 50 requests per 60 seconds
- **Analysis endpoints**: 10 requests per 60 seconds
- **Upload endpoints**: 20 requests per 60 seconds

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
X-RateLimit-Window: 60
```

When rate limit is exceeded:
- HTTP 429 Too Many Requests
- `Retry-After` header indicates when to retry

## Security Best Practices

1. **API Key Management**:
   - Never hardcode API keys in code
   - Use environment variables for configuration
   - Rotate API keys regularly
   - Use different keys for different environments

2. **HTTPS Only**:
   - Always use HTTPS in production
   - Never transmit API keys over unencrypted connections

3. **Monitoring**:
   - Monitor failed authentication attempts
   - Track rate limit violations
   - Log suspicious activity

4. **Key Storage**:
   - In production, use secure key management services
   - Consider using JWT tokens for stateless authentication
   - Implement key rotation policies

## Testing

### Unit Tests

```bash
pytest tests/unit/api/test_dependencies.py
```

### Integration Tests

```bash
pytest tests/integration/test_auth_flow.py
```

### Manual Testing

```bash
# Test with valid API key
curl -H "X-API-Key: test-key-123" http://localhost:8000/api/v1/patterns

# Test with invalid API key
curl -H "X-API-Key: invalid-key" http://localhost:8000/api/v1/patterns

# Test rate limiting
for i in {1..110}; do
  curl -H "X-API-Key: test-key-123" http://localhost:8000/api/v1/patterns
done
```

## Future Enhancements

1. **JWT Token Support**: Add JWT-based authentication for stateless sessions
2. **OAuth2 Integration**: Support OAuth2 for third-party authentication
3. **API Key Scopes**: Fine-grained permissions per API key
4. **Distributed Rate Limiting**: Redis-based rate limiting for multi-instance deployments
5. **Audit Logging**: Comprehensive audit trail for all authenticated actions
