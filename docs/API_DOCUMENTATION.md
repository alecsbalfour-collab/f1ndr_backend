# F1NDR Backend API Documentation

## FlutterFlow Compatible Enterprise API

This API is designed to be fully compatible with FlutterFlow while maintaining DICT enterprise patterns and production-ready features.

## Base URL

```
http://localhost:8000/api/v1
```

Health probes (`/health`) are unversioned. The old unversioned paths (e.g. `/auth/login`) still work but are deprecated: they are omitted from `/openapi.json` and their responses carry `Deprecation` and `Link: </api/v1/...>; rel="successor-version"` headers. Breaking changes will ship as `/api/v2` alongside v1.

## Authentication

### User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

### User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

### FlutterFlow Webhook
```http
POST /api/v1/auth/flutterflow/webhook
Content-Type: application/json

{
  "event_type": "user.created",
  "user_data": {
    "email": "user@example.com",
    "name": "John Doe"
  },
  "api_key": "your_flutterflow_api_key"
}
```

## Standard Response Format

All endpoints return FlutterFlow-compatible JSON responses:

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00Z",
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "details": { ... },
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Module Endpoints

### TRINN (Task Orchestration)
```http
GET /api/v1/trinn/status
POST /api/v1/trinn/run
POST /api/v1/trinn/schedule
GET /api/v1/trinn/config
```

### DEALR (Dealer Management)
```http
GET /api/v1/dealr/status
POST /api/v1/dealr/inventory
GET /api/v1/dealr/inventory?page=1&page_size=20
PUT /api/v1/dealr/inventory/{id}
DELETE /api/v1/dealr/inventory/{id}
```

### SELLR (Listing Management)
```http
GET /api/v1/sellr/status
POST /api/v1/sellr/listings
GET /api/v1/sellr/listings?page=1&page_size=20&user_id={id}
GET /api/v1/sellr/listings/{id}
PUT /api/v1/sellr/listings/{id}
DELETE /api/v1/sellr/listings/{id}
```

### LISTR (Platform Integration)
```http
GET /api/v1/listr/status
POST /api/v1/listr/listings?platform=facebook
PUT /api/v1/listr/listings/{id}?platform=facebook
GET /api/v1/listr/platforms
```

### WATCHR (Alert System)
```http
GET /api/v1/watchr/status
POST /api/v1/watchr/alerts
GET /api/v1/watchr/alerts?page=1&page_size=20
DELETE /api/v1/watchr/alerts/{id}
POST /api/v1/watchr/subscriptions
```

### F1NDR (Core Intelligence)
```http
GET /api/v1/f1ndr/status
POST /api/v1/f1ndr/vin/decode
GET /api/v1/f1ndr/vehicles?page=1&page_size=20
GET /api/v1/f1ndr/market/value?vin={vin}
```

## Pagination

All list endpoints support FlutterFlow-compatible pagination:

```http
GET /api/v1/endpoint?page=1&page_size=20&sort_by=created_at&sort_order=desc
```

### Query Parameters
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 20, max: 100) - Results per page
- `sort_by` (string) - Field to sort by
- `sort_order` (string, default: "desc") - Sort direction

## Filtering

Endpoints support filtering via query parameters:

```http
GET /api/v1/endpoint?status=active&category=vehicles&min_price=1000&max_price=50000
```

## FlutterFlow Integration

### Required Headers
```
Content-Type: application/json
Authorization: Bearer <token>
X-FlutterFlow-App-ID: your_app_id
X-FlutterFlow-User-ID: user_id
```

### CORS Configuration
The API is configured to accept requests from:
- `https://flutterflow.io`
- `https://app.flutterflow.io`
- `https://*.flutterflow.app`
- `http://localhost:*` (development)

### Data Types
All responses use FlutterFlow-compatible data types:
- Strings for text fields
- Numbers for numeric fields
- Booleans for boolean fields
- Arrays for lists
- Objects for nested data
- ISO 8601 format for dates/timestamps

## Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Request validation failed |
| UNAUTHORIZED | Authentication required |
| FORBIDDEN | Access denied |
| NOT_FOUND | Resource not found |
| CONFLICT | Resource conflict |
| RATE_LIMIT_EXCEEDED | Too many requests |
| INTERNAL_ERROR | Server error |

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per user
- Standard HTTP 429 response when exceeded

## Webhooks

### FlutterFlow Webhook
```http
POST /api/v1/auth/flutterflow/webhook
```

Supported events:
- `user.created` - User created in FlutterFlow
- `user.updated` - User updated in FlutterFlow
- `user.deleted` - User deleted in FlutterFlow

## Enterprise Features

### DICT Patterns
- Feature keys and versioning
- Enterprise metadata tracking
- Comprehensive error handling
- Structured logging

### Monitoring
- Health check endpoint: `/health`
- Version endpoint: `/version`
- Performance metrics included in responses

### Security
- JWT authentication
- Password strength validation
- Rate limiting
- CORS protection
- Request ID tracking

## Testing

### Health Check
```http
GET /health
```

### Version Info
```http
GET /version
```

### Module Status
```http
GET /api/v1/trinn/status
GET /api/v1/dealr/status
GET /api/v1/sellr/status
GET /api/v1/listr/status
GET /api/v1/watchr/status
GET /api/v1/f1ndr/status
```

## Support

For issues or questions:
- Check the error response for detailed error codes
- Review the logs for server-side debugging
- Ensure proper authentication headers are set
- Verify CORS configuration for your FlutterFlow app