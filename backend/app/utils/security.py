"""
Security Utilities
=================
JWT authentication, password hashing, and security utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.config import app_config

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=app_config.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        app_config.secret_key,
        algorithm=app_config.algorithm,
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            app_config.secret_key,
            algorithms=[app_config.algorithm],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
    
    Returns:
        User data from token
    
    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
    }


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Require admin role.
    
    Args:
        current_user: Current user from token
    
    Returns:
        User data if admin
    
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests: int, window_seconds: int):
        """
        Initialize rate limiter.
        
        Args:
            requests: Number of requests allowed in window
            window_seconds: Time window in seconds
        """
        self.requests = requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Identifier (e.g., IP address or user ID)
        
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self._requests:
            self._requests[key] = []
        
        # Clean old requests
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > window_start
        ]
        
        if len(self._requests[key]) >= self.requests:
            return False
        
        self._requests[key].append(now)
        return True
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.
        
        Args:
            key: Identifier to reset
        """
        if key in self._requests:
            del self._requests[key]


# Global rate limiter
rate_limiter = RateLimiter(
    requests=app_config.rate_limit_requests,
    window_seconds=app_config.rate_limit_window_seconds,
)


__all__ = [
    "verify_password",
    "hash_password",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "require_admin",
    "RateLimiter",
    "rate_limiter",
    "security",
]
