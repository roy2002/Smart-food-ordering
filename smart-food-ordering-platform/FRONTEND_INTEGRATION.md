# Frontend Integration Guide

## Overview

Both **restaurants** and **customers** use the same registration endpoint: `/api/users/register`. After successful registration or login, a JWT token is returned which should be saved in **local storage** for subsequent authenticated requests.

---

## Authentication Flow

### 1. User Registration (Restaurant or Customer)

**Endpoint**: `POST /api/users/register`

**Request**:
```javascript
fetch('http://localhost:8000/api/users/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    username: 'username',
    password: 'SecurePassword123!',
    full_name: 'Full Name',
    phone: '+1234567890',
    address: '123 Main St, City'
  })
})
.then(response => response.json())
.then(data => {
  if (data.token) {
    // Save JWT token to local storage
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('userEmail', data.user.email);
    
    console.log('Registration successful!');
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
})
.catch(error => console.error('Error:', error));
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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDA4MjM2MDB9.abc123..."
}
```

### 2. User Login

**Endpoint**: `POST /api/users/login`

**Request**:
```javascript
fetch('http://localhost:8000/api/users/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePassword123!'
  })
})
.then(response => response.json())
.then(data => {
  if (data.token) {
    // Save JWT token to local storage
    localStorage.setItem('authToken', data.token);
    localStorage.setItem('userId', data.user.id);
    localStorage.setItem('userEmail', data.user.email);
    
    console.log('Login successful!');
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
})
.catch(error => console.error('Error:', error));
```

---

## Using the JWT Token

### Making Authenticated Requests

Once the token is saved in local storage, include it in the `Authorization` header for all authenticated requests:

```javascript
// Get token from local storage
const token = localStorage.getItem('authToken');

// Example: Get user profile
fetch(`http://localhost:8000/api/users/${userId}`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Example: Create Order

```javascript
const token = localStorage.getItem('authToken');

fetch('http://localhost:8000/api/orders', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    restaurant_id: "1",
    items: JSON.stringify([
      { item_id: 1, name: "Pizza", quantity: 2, price: 12.99 }
    ]),
    total_amount: 25.98,
    delivery_address: "123 Main St",
    payment_method: "CARD"
  })
})
.then(response => response.json())
.then(data => console.log('Order created:', data));
```

---

## Complete React/Vue/Angular Example

### React Hook for Authentication

```javascript
import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Load token from local storage on mount
    const savedToken = localStorage.getItem('authToken');
    const savedUserId = localStorage.getItem('userId');
    const savedUserEmail = localStorage.getItem('userEmail');
    
    if (savedToken) {
      setToken(savedToken);
      setUser({ id: savedUserId, email: savedUserEmail });
    }
  }, []);

  const register = async (userData) => {
    try {
      const response = await fetch('http://localhost:8000/api/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
      
      const data = await response.json();
      
      if (data.token) {
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userId', data.user.id);
        localStorage.setItem('userEmail', data.user.email);
        
        setToken(data.token);
        setUser(data.user);
        
        return { success: true, user: data.user };
      }
      
      return { success: false, error: data.error };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch('http://localhost:8000/api/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (data.token) {
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userId', data.user.id);
        localStorage.setItem('userEmail', data.user.email);
        
        setToken(data.token);
        setUser(data.user);
        
        return { success: true, user: data.user };
      }
      
      return { success: false, error: data.error };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = () => !!token;

  return { token, user, register, login, logout, isAuthenticated };
};
```

### Using the Hook

```javascript
import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';

function RegistrationForm() {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    phone: '',
    address: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const result = await register(formData);
    
    if (result.success) {
      console.log('Registration successful!');
      // Redirect or update UI
      window.location.href = '/dashboard';
    } else {
      console.error('Registration failed:', result.error);
      alert(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        placeholder="Email"
        value={formData.email}
        onChange={(e) => setFormData({...formData, email: e.target.value})}
        required
      />
      <input
        type="text"
        placeholder="Username"
        value={formData.username}
        onChange={(e) => setFormData({...formData, username: e.target.value})}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={formData.password}
        onChange={(e) => setFormData({...formData, password: e.target.value})}
        required
      />
      <input
        type="text"
        placeholder="Full Name"
        value={formData.full_name}
        onChange={(e) => setFormData({...formData, full_name: e.target.value})}
      />
      <input
        type="tel"
        placeholder="Phone"
        value={formData.phone}
        onChange={(e) => setFormData({...formData, phone: e.target.value})}
      />
      <input
        type="text"
        placeholder="Address"
        value={formData.address}
        onChange={(e) => setFormData({...formData, address: e.target.value})}
      />
      <button type="submit">Register</button>
    </form>
  );
}
```

---

## Vanilla JavaScript Example

### Complete Authentication Module

```javascript
// auth.js
class AuthService {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Register new user (restaurant or customer)
  async register(userData) {
    try {
      const response = await fetch(`${this.baseUrl}/api/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      });

      const data = await response.json();

      if (response.ok && data.token) {
        // Save to local storage
        this.saveToken(data.token);
        this.saveUser(data.user);
        return { success: true, user: data.user };
      }

      return { success: false, error: data.error || 'Registration failed' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Login existing user
  async login(email, password) {
    try {
      const response = await fetch(`${this.baseUrl}/api/users/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok && data.token) {
        // Save to local storage
        this.saveToken(data.token);
        this.saveUser(data.user);
        return { success: true, user: data.user };
      }

      return { success: false, error: data.error || 'Login failed' };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Save token to local storage
  saveToken(token) {
    localStorage.setItem('authToken', token);
  }

  // Save user info to local storage
  saveUser(user) {
    localStorage.setItem('userId', user.id);
    localStorage.setItem('userEmail', user.email);
    localStorage.setItem('userName', user.username);
    localStorage.setItem('userFullName', user.full_name);
  }

  // Get token from local storage
  getToken() {
    return localStorage.getItem('authToken');
  }

  // Get user info from local storage
  getUser() {
    return {
      id: localStorage.getItem('userId'),
      email: localStorage.getItem('userEmail'),
      username: localStorage.getItem('userName'),
      full_name: localStorage.getItem('userFullName')
    };
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getToken();
  }

  // Logout
  logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userFullName');
  }

  // Make authenticated request
  async authenticatedRequest(url, options = {}) {
    const token = this.getToken();

    if (!token) {
      throw new Error('No authentication token found');
    }

    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    const response = await fetch(`${this.baseUrl}${url}`, {
      ...options,
      headers
    });

    return response.json();
  }
}

// Export singleton instance
const authService = new AuthService();
```

### Usage in HTML/JS

```html
<!DOCTYPE html>
<html>
<head>
  <title>Food Ordering Platform</title>
</head>
<body>
  <div id="auth-section">
    <h2>Register / Login</h2>
    <form id="register-form">
      <input type="email" id="email" placeholder="Email" required>
      <input type="text" id="username" placeholder="Username" required>
      <input type="password" id="password" placeholder="Password" required>
      <input type="text" id="full_name" placeholder="Full Name">
      <input type="tel" id="phone" placeholder="Phone">
      <input type="text" id="address" placeholder="Address">
      <button type="submit">Register</button>
    </form>
  </div>

  <div id="dashboard" style="display: none;">
    <h2>Welcome, <span id="user-name"></span></h2>
    <button id="logout-btn">Logout</button>
  </div>

  <script src="auth.js"></script>
  <script>
    // Check if already logged in
    if (authService.isAuthenticated()) {
      showDashboard();
    }

    // Handle registration
    document.getElementById('register-form').addEventListener('submit', async (e) => {
      e.preventDefault();

      const userData = {
        email: document.getElementById('email').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        full_name: document.getElementById('full_name').value,
        phone: document.getElementById('phone').value,
        address: document.getElementById('address').value
      };

      const result = await authService.register(userData);

      if (result.success) {
        alert('Registration successful!');
        showDashboard();
      } else {
        alert('Registration failed: ' + result.error);
      }
    });

    // Handle logout
    document.getElementById('logout-btn').addEventListener('click', () => {
      authService.logout();
      location.reload();
    });

    function showDashboard() {
      const user = authService.getUser();
      document.getElementById('auth-section').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      document.getElementById('user-name').textContent = user.full_name || user.username;
    }

    // Example: Make authenticated request
    async function createOrder() {
      try {
        const order = await authService.authenticatedRequest('/api/orders', {
          method: 'POST',
          body: JSON.stringify({
            restaurant_id: "1",
            items: JSON.stringify([{ item_id: 1, quantity: 2 }]),
            total_amount: 25.98
          })
        });
        console.log('Order created:', order);
      } catch (error) {
        console.error('Error creating order:', error);
      }
    }
  </script>
</body>
</html>
```

---

## JWT Token Details

### Token Structure

The JWT token has the following payload:
```json
{
  "user_id": 1,
  "exp": 1700823600  // Expiration timestamp (24 hours from issue)
}
```

### Token Expiration

- **Validity**: 24 hours from issuance
- **After expiration**: User must log in again
- **Best practice**: Check expiration before making requests

### Checking Token Expiration

```javascript
function isTokenExpired(token) {
  try {
    // Decode JWT (base64)
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expirationTime = payload.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();
    
    return currentTime > expirationTime;
  } catch (error) {
    return true; // If can't decode, consider expired
  }
}

// Usage
const token = localStorage.getItem('authToken');
if (token && isTokenExpired(token)) {
  console.log('Token expired, please login again');
  authService.logout();
  window.location.href = '/login';
}
```

---

## Security Best Practices

### 1. HTTPS Only (Production)
```javascript
// Only save tokens over HTTPS in production
if (window.location.protocol !== 'https:' && !window.location.hostname.includes('localhost')) {
  console.warn('JWT tokens should only be transmitted over HTTPS');
}
```

### 2. Token Refresh (Future Enhancement)
```javascript
// Check token expiration on app load
if (authService.isAuthenticated()) {
  const token = authService.getToken();
  if (isTokenExpired(token)) {
    authService.logout();
    alert('Session expired. Please login again.');
  }
}
```

### 3. Secure Storage Options

**Local Storage** (Current implementation):
- ✅ Simple to use
- ✅ Persists across sessions
- ⚠️ Accessible by JavaScript (XSS risk)

**Session Storage** (Alternative):
- ✅ Cleared when tab closes
- ✅ More secure for sensitive apps
- ❌ Doesn't persist

**HTTP-Only Cookie** (Most secure - requires backend change):
- ✅ Not accessible by JavaScript
- ✅ More secure against XSS
- ❌ Requires backend modifications

---

## API Endpoints Summary

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/api/users/register` | POST | No | Register new user |
| `/api/users/login` | POST | No | Login existing user |
| `/api/users/{id}` | GET | Yes | Get user profile |
| `/api/users/{id}` | PUT | Yes | Update user profile |
| `/api/restaurants` | GET | No | List restaurants |
| `/api/restaurants/{id}/menu` | GET | No | Get menu |
| `/api/orders` | POST | Yes | Create order |
| `/api/orders/{id}` | GET | Yes | Get order details |
| `/api/recommendations` | POST | Yes | Get recommendations |

---

## Complete Frontend Flow

```
1. User visits site
   ↓
2. Check localStorage for authToken
   ↓
   ├─ Token exists & valid → Show Dashboard
   └─ No token → Show Registration/Login
   ↓
3. User registers/logs in
   ↓
4. Backend returns JWT token
   ↓
5. Save token to localStorage
   ↓
6. Show authenticated content
   ↓
7. Include token in all API requests
   ↓
8. On logout: Clear localStorage
```

---

## Error Handling

```javascript
async function makeAuthenticatedRequest(url, options) {
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    // No token - redirect to login
    window.location.href = '/login';
    return;
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.status === 401) {
      // Unauthorized - token invalid or expired
      localStorage.removeItem('authToken');
      alert('Session expired. Please login again.');
      window.location.href = '/login';
      return;
    }
    
    if (response.status === 403) {
      // Forbidden - user doesn't have permission
      alert('You do not have permission to perform this action');
      return;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

---

## Testing the Authentication

### Using cURL

```bash
# 1. Register
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!",
    "full_name": "Test User"
  }'

# Save the token from response

# 2. Use token for authenticated request
curl -X GET http://localhost:8000/api/users/1 \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>"
```

### Using Postman

1. **Register/Login**: Make POST request to `/api/users/register`
2. **Copy token** from response
3. **Set up Authorization**: 
   - Type: Bearer Token
   - Token: Paste the JWT token
4. **Make authenticated requests** with this setup

---

This guide provides everything needed for frontend integration with proper JWT token management!
