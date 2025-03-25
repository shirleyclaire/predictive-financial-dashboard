# API Reference

## Authentication

### Get JWT Token

```http
POST /api/expenses/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

#### Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## Expense Tracking

### Add Transaction

```http
POST /api/expenses/transactions/
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100.50,
  "category": "groceries",
  "description": "Weekly groceries",
  "type": "expense"
}
```

### Get Monthly Summary

```http
GET /api/expenses/transactions/summary/monthly
Authorization: Bearer <token>
```

## News API

### Get Latest News

```http
GET /api/news/
```

### Get News by Sentiment

```http
GET /api/news/sentiment/positive
```

## Predictions

### Get Expense Forecast

```http
GET /api/predictions/predict/user123?days=30
Authorization: Bearer <token>
```

## Error Responses

```json
{
  "detail": "Error message",
  "status_code": 400,
  "path": "/api/resource"
}
```

## Rate Limiting

- 100 requests per minute per IP
- Burst: 20 requests
- Status: 429 Too Many Requests
