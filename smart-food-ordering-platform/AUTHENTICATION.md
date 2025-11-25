# Authentication Guide

## Overview

This document provides a quick reference for the authentication system in the Smart Food Ordering Platform.

---

## Key Points

### 1. **Unified Registration Endpoint**

Both **restaurants** and **customers** use the **same registration endpoint**: 

```
POST /api/users/register
```

There is no separate endpoint for restaurant vs customer registration. Both user types are registered through the User Service.

### 2. **JWT Token Storage**

After successful registration or login, the JWT token **must be saved to local storage**:

```javascript
localStorage.setItem('authToken', data.token);
```

### 3. **Authentication Flow**

```
Registration/Login → Receive JWT → Save to Local Storage → Use in Headers
```

---

## Quick Reference

### Registration (Both Restaurant & Customer)

**Endpoint**: `POST http://localhost:8000/api/users/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123!",
  "full_name": "Full Name",
  "phone": "+1234567890",
  "address": "123 Main St"
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Frontend Action**:
```javascript
// Save token to local storage
localStorage.setItem('authToken', data.token);
localStorage.setItem('userId', data.user.id);
localStorage.setItem('userEmail', data.user.email);
```

---

### Login

**Endpoint**: `POST http://localhost:8000/api/users/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response**: Same structure as registration

**Frontend Action**: Save token to local storage (same as registration)

---

### Using the Token

For all authenticated requests, include the token in the `Authorization` header:

```javascript
const token = localStorage.getItem('authToken');

fetch('http://localhost:8000/api/orders', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ /* order data */ })
})
```

---

## Common Patterns

### Check if User is Logged In

```javascript
function isLoggedIn() {
  const token = localStorage.getItem('authToken');
  return token !== null;
}
```

### Get Current User

```javascript
function getCurrentUser() {
  return {
    id: localStorage.getItem('userId'),
    email: localStorage.getItem('userEmail'),
    token: localStorage.getItem('authToken')
  };
}
```

### Logout

```javascript
function logout() {
  localStorage.removeItem('authToken');
  localStorage.removeItem('userId');
  localStorage.removeItem('userEmail');
  window.location.href = '/login';
}
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/users/register` | POST | Register new user (restaurant or customer) | No |
| `/api/users/login` | POST | Login existing user | No |
| `/api/users/{id}` | GET | Get user profile | Yes |
| `/api/users/{id}` | PUT | Update user profile | Yes |
| `/api/restaurants` | POST | Create restaurant | Yes |
| `/api/restaurants` | GET | List restaurants | No |
| `/api/orders` | POST | Create order | Yes |
| `/api/orders/{id}` | GET | Get order details | Yes |

---

## Security Notes

1. **JWT Expiration**: Tokens expire after 24 hours
2. **Token Format**: `Bearer <token>` in Authorization header
3. **HTTPS**: Always use HTTPS in production
4. **Token Refresh**: Implement token refresh mechanism in production
5. **Secure Storage**: Consider using `httpOnly` cookies for enhanced security in production

---

## Testing Authentication

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'

# Use token
TOKEN="your-jwt-token-here"
curl -X GET http://localhost:8000/api/users/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Related Documentation

- [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) - Detailed frontend integration guide with React examples
- [architecture/openapi/user-service.yaml](./architecture/openapi/user-service.yaml) - Complete API specification
- [SETUP.md](./SETUP.md) - Setup and deployment instructions

---

**Last Updated**: 2024
