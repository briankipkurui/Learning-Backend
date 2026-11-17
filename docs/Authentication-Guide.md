# Authentication and Route Protection Guide

This guide explains how to protect routes and ensure users are logged in before accessing certain endpoints in the Career Elevate API.

## Overview

The authentication system uses JWT (JSON Web Tokens) with the following components:

1. **JWT Token Generation**: Done in `AuthService` during Google OAuth login/signup
2. **Auth Middleware**: Located in `middleware/auth_middleware.py` - handles token verification
3. **Route Protection**: Using FastAPI dependencies to protect specific routes
4. **Role-Based Access**: Different access levels for admins and learners

## Authentication Flow

1. **User Login/Signup**: User authenticates via Google OAuth (`/api/v1/auth/google/login` or `/api/v1/auth/google/signup`)
2. **Token Generation**: System generates JWT access token (15 minutes) and refresh token (30 days)
3. **Token Storage**: Access token sent in response, refresh token stored as HTTP-only cookie
4. **Protected Requests**: Client sends access token in Authorization header: `Bearer <token>`
5. **Token Verification**: Middleware verifies token and extracts user information

## Available Auth Dependencies

### 1. `get_current_user`
- Verifies JWT token and returns the user
- Throws 401 if token is invalid
- Throws 403 if user account is disabled

### 2. `get_current_active_user`  
- Same as `get_current_user` but ensures user is active
- Use this for most protected endpoints

### 3. `require_admin`
- Requires user to be authenticated AND have `user_type="Admin"`
- Throws 403 if user is not an admin

### 4. `require_learner`
- Requires user to be authenticated AND have `user_type="Learner"`
- Throws 403 if user is not a learner

## How to Protect Routes

### Method 1: Using Dependencies Parameter in Route Definition

```python
from middleware.auth_middleware import get_current_active_user, require_admin
from models.user.user import UserModel

class MyController:
    def _setup_routes(self):
        # Protect route - only authenticated users
        self.router.add_api_route(
            "/protected", 
            self.protected_endpoint, 
            methods=["GET"],
            dependencies=[Depends(get_current_active_user)]
        )
        
        # Admin only route
        self.router.add_api_route(
            "/admin-only", 
            self.admin_endpoint, 
            methods=["GET"],
            dependencies=[Depends(require_admin)]
        )
```

### Method 2: Using Dependencies in Method Parameters

```python
def protected_endpoint(
    self,
    current_user: UserModel = Depends(get_current_active_user)
):
    # Access user information
    return {
        "message": f"Hello {current_user.first_name}!",
        "user_id": str(current_user.Id),
        "user_type": current_user.user_type
    }

def admin_endpoint(
    self,
    current_user: UserModel = Depends(require_admin)
):
    # Only admins can access this
    return {"admin_data": "sensitive information"}
```

## Real Examples from the Codebase

### User Controller Route Protection

```python
# Public route (no auth required)
self.router.add_api_route("/", self.create_user, methods=["POST"])

# Admin only routes  
self.router.add_api_route("/", self.get_users, methods=["GET"], 
                         dependencies=[Depends(require_admin)])
self.router.add_api_route("/{user_id}", self.get_user, methods=["GET"], 
                         dependencies=[Depends(require_admin)])

# User's own profile (any authenticated user)
self.router.add_api_route("/me", self.get_current_user_profile, methods=["GET"])
```

### Protected Controller Examples

```python
# Any authenticated user can access
def get_my_profile(self, current_user: UserModel = Depends(get_current_active_user)):
    return {
        "user_id": str(current_user.Id),
        "email": current_user.email,
        "user_type": current_user.user_type
    }

# Admin only access
def admin_only_endpoint(self, current_user: UserModel = Depends(require_admin)):
    return {"message": "Admin access granted"}

# Learner only access  
def learner_only_endpoint(self, current_user: UserModel = Depends(require_learner)):
    return {"message": "Learner access granted"}
```

## Client-Side Usage

### 1. Login/Signup to Get Token

```javascript
// Login
const response = await fetch('/api/v1/auth/google/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: googleToken })
});

const data = await response.json();
const accessToken = data.access_token;
// Store token in memory or secure storage
```

### 2. Use Token in Protected Requests

```javascript
// Access protected endpoint
const response = await fetch('/api/v1/protected/profile', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### 3. Handle Token Expiration

```javascript
// If you get 401, refresh the token
if (response.status === 401) {
  // Use refresh token endpoint
  const refreshResponse = await fetch('/api/v1/auth/refresh', {
    credentials: 'include' // Include HTTP-only cookies
  });
  
  if (refreshResponse.ok) {
    const newTokens = await refreshResponse.json();
    accessToken = newTokens.access_token;
    // Retry original request with new token
  }
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden (Non-Admin accessing admin route)
```json
{
  "detail": "Admin access required"
}
```

### 403 Forbidden (Disabled account)
```json
{
  "detail": "User account is disabled"
}
```

## Current Protected Routes

### User Routes (`/api/v1/users`)
- `GET /` - Get all users (Admin only)
- `GET /me` - Get current user profile (Authenticated)
- `PUT /me/profile` - Update own learner profile (Authenticated learner)
- `GET /{user_id}` - Get specific user (Admin only)
- `PUT /{user_id}` - Update user (Admin only)
- `PUT /{user_id}/profile` - Update user's profile (Admin only)
- `DELETE /{user_id}` - Delete user (Admin only)

### Protected Examples (`/api/v1/protected`)
- `GET /profile` - Get own profile (Authenticated)
- `GET /admin-only` - Admin access test (Admin only)
- `GET /learner-only` - Learner access test (Learner only)

### Public Routes (No Authentication)
- `POST /api/v1/users/` - Create user
- `POST /api/v1/auth/google/login` - Login
- `POST /api/v1/auth/google/signup` - Signup
- `POST /api/v1/auth/refresh` - Refresh tokens
- `GET /health/` - Health check

## Best Practices

1. **Always use HTTPS in production** to protect JWT tokens in transit
2. **Store access tokens securely** - in memory or secure storage, not localStorage
3. **Handle token expiration gracefully** - implement automatic refresh
4. **Use appropriate auth level** - don't require admin access for user-specific operations  
5. **Validate user permissions** - check if user can access their own resources vs others'
6. **Log authentication events** - track logins, failed attempts, etc.

## Testing Authentication

You can test the authentication by:

1. **Get a token**: Login via `/api/v1/auth/google/login`
2. **Test protected routes**: Use the token with protected endpoints
3. **Test role-based access**: Try accessing admin routes with learner tokens
4. **Test token expiration**: Wait 15 minutes and try using an expired token

The system is now fully set up to protect routes and ensure proper authentication!
