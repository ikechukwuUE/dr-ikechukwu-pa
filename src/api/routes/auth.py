"""
Auth0 OAuth2 Authentication Routes
Handles authentication with Auth0 for the multi-agent backend

SECURITY FIX: This module now properly validates JWT signatures using Auth0's JWKS endpoint.
For development, use AUTH0_DEV_MODE=true with a local secret or explicitly disable auth.
"""
from flask import Blueprint, request, jsonify, session, redirect, current_app
from functools import wraps
import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import threading

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

logger = logging.getLogger(__name__)

# Auth0 Configuration
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN', 'your-domain.auth0.com')
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID', 'your-client-id')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET', 'your-client-secret')
AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE', 'https://api.dr-ikechukwu.com')
AUTH0_REDIRECT_URI = os.environ.get('AUTH0_REDIRECT_URI', 'http://localhost:5173/callback')

# Development mode settings
AUTH0_DEV_MODE = os.environ.get('AUTH0_DEV_MODE', 'false').lower() == 'true'
AUTH0_DEV_SECRET = os.environ.get('AUTH0_DEV_SECRET', '')  # For HS256 dev tokens

# Session key for user info
USER_INFO_KEY = 'user_info'

# JWKS Cache with TTL (5 minutes)
_jwks_cache: Dict[str, Any] = {
    'keys': None,
    'cached_at': 0
}
_jwks_cache_lock = threading.Lock()
JWKS_CACHE_TTL = 300  # 5 minutes


# ============================================================================
# JWKS Caching Functions
# ============================================================================

def get_jwks() -> Dict[str, Any]:
    """
    Get JWKS from Auth0 with caching.
    
    Returns:
        Dictionary containing JWKS keys
        
    Raises:
        Exception: If JWKS cannot be fetched and no cached version exists
    """
    current_time = time.time()
    
    # Check if cache is valid
    with _jwks_cache_lock:
        if _jwks_cache['keys'] is not None and (current_time - _jwks_cache['cached_at']) < JWKS_CACHE_TTL:
            return _jwks_cache
    
    # Fetch fresh JWKS
    import urllib.request
    import json
    
    jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    
    try:
        req = urllib.request.Request(jwks_url)
        req.add_header('User-Agent', 'Dr-Ikechukwu-PA/1.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            jwks = json.loads(response.read().decode())
        
        # Update cache
        with _jwks_cache_lock:
            _jwks_cache['keys'] = jwks
            _jwks_cache['cached_at'] = current_time
        
        logger.info("JWKS fetched and cached successfully")
        return jwks
        
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        
        # Return cached version if available (even if expired)
        with _jwks_cache_lock:
            if _jwks_cache['keys'] is not None:
                logger.warning("Using stale JWKS cache")
                return _jwks_cache
        
        raise Exception(f"Unable to fetch JWKS: {e}")


def clear_jwks_cache():
    """Clear the JWKS cache (useful for key rotation)."""
    with _jwks_cache_lock:
        _jwks_cache['keys'] = None
        _jwks_cache['cached_at'] = 0


# ============================================================================
# JWT Verification Functions
# ============================================================================

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token against Auth0's JWKS.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token claims
        
    Raises:
        ValueError: If token is invalid or verification fails
    """
    try:
        from jose import jwt, JWTError, jwk
        from jose.exceptions import JWKError
    except ImportError:
        raise ImportError(
            "python-jose is required for JWT verification. "
            "Install with: pip install python-jose[cryptography]"
        )
    
    # In development mode with explicit secret
    if AUTH0_DEV_MODE and AUTH0_DEV_SECRET:
        logger.warning("DEV MODE: Using local secret for JWT verification (NOT SECURE FOR PRODUCTION)")
        try:
            payload = jwt.decode(
                token,
                AUTH0_DEV_SECRET,
                algorithms=['HS256'],
                audience=AUTH0_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")
    
    # Production mode: Verify against Auth0 JWKS
    try:
        jwks = get_jwks()
    except Exception as e:
        raise ValueError(f"Failed to get JWKS for verification: {e}")
    
    try:
        # Get the JWT header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        
        # Find the matching key in JWKS
        kid = unverified_header.get('kid')
        if not kid:
            raise ValueError("Token missing key ID (kid) in header")
        
        # Find the public key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                try:
                    public_key = jwk.construct(key)
                    break
                except JWKError as e:
                    logger.warning(f"Failed to construct key {kid}: {e}")
                    continue
        
        if not public_key:
            raise ValueError(f"Unable to find matching key for kid: {kid}")
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256', 'ES256'],
            audience=AUTH0_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        
        return payload
        
    except JWTError as e:
        raise ValueError(f"JWT verification failed: {e}")


def verify_id_token(id_token: str, nonce: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify an ID token from Auth0.
    
    Args:
        id_token: ID token string
        nonce: Optional nonce for OIDC security
        
    Returns:
        Decoded token claims
        
    Raises:
        ValueError: If token is invalid or verification fails
    """
    try:
        from jose import jwt, JWTError
    except ImportError:
        raise ImportError(
            "python-jose is required for ID token verification. "
            "Install with: pip install python-jose[cryptography]"
        )
    
    # In development mode with explicit secret
    if AUTH0_DEV_MODE and AUTH0_DEV_SECRET:
        logger.warning("DEV MODE: Using local secret for ID token verification (NOT SECURE FOR PRODUCTION)")
        try:
            payload = jwt.decode(
                id_token,
                AUTH0_DEV_SECRET,
                algorithms=['HS256'],
                audience=AUTH0_CLIENT_ID,  # ID tokens use client_id as audience
                issuer=f'https://{AUTH0_DOMAIN}/'
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid ID token: {e}")
    
    # Production mode
    try:
        jwks = get_jwks()
    except Exception as e:
        raise ValueError(f"Failed to get JWKS for ID token verification: {e}")
    
    try:
        # Get the JWT header to find the key ID
        unverified_header = jwt.get_unverified_header(id_token)
        
        # Find the matching key in JWKS
        kid = unverified_header.get('kid')
        if not kid:
            raise ValueError("ID token missing key ID (kid) in header")
        
        from jose import jwk
        from jose.exceptions import JWKError
        
        # Find the public key
        public_key = None
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                try:
                    public_key = jwk.construct(key)
                    break
                except JWKError as e:
                    logger.warning(f"Failed to construct key {kid}: {e}")
                    continue
        
        if not public_key:
            raise ValueError(f"Unable to find matching key for kid: {kid}")
        
        # Decode and verify the ID token
        options = {
            'verify_aud': True,
            'verify_iss': True,
            'verify_exp': True,
            'verify_iat': True,
        }
        
        # Add nonce verification if provided
        decode_kwargs = {
            'algorithms': ['RS256', 'ES256'],
            'audience': AUTH0_CLIENT_ID,
            'issuer': f'https://{AUTH0_DOMAIN}/',
            'options': options,
        }
        
        # Only verify nonce if it was provided (for OIDC)
        if nonce:
            decode_kwargs['nonce'] = nonce
        
        payload = jwt.decode(
            id_token,
            public_key,
            **decode_kwargs
        )
        
        return payload
        
    except JWTError as e:
        raise ValueError(f"ID token verification failed: {e}")


# ============================================================================
# Authentication Decorator
# ============================================================================

def require_auth(f):
    """
    Decorator to require authentication for protected endpoints.
    Validates the JWT token from Auth0 with proper signature verification.
    
    SECURITY: This decorator now properly verifies JWT signatures against Auth0's JWKS.
    For development, set AUTH0_DEV_MODE=true and provide AUTH0_DEV_SECRET.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        
        # Verify the JWT token with Auth0
        try:
            payload = verify_jwt_token(token)
            
            # Store user info in request context (Flask allows dynamic attributes)
            # Using setattr for type safety with dynamic attribute
            setattr(request, 'user_info', payload)
            
            return f(*args, **kwargs)
            
        except ImportError as e:
            logger.error(f"JWT verification library not available: {e}")
            return jsonify({'error': 'Authentication configuration error'}), 501
        except ValueError as e:
            logger.warning(f"Token verification failed: {e}")
            return jsonify({'error': 'Invalid or expired token'}), 401
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function


# ============================================================================
# Auth Routes
# ============================================================================

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    """
    Initiate login - Redirect to Auth0 login page
    """
    if request.method == 'GET':
        # Build Auth0 authorization URL
        import urllib.parse
        
        params = {
            'response_type': 'code',
            'client_id': AUTH0_CLIENT_ID,
            'redirect_uri': AUTH0_REDIRECT_URI,
            'scope': 'openid profile email',
            'audience': AUTH0_AUDIENCE,
        }
        
        auth_url = f"https://{AUTH0_DOMAIN}/authorize?{urllib.parse.urlencode(params)}"
        return redirect(auth_url)
    
    return jsonify({
        'login_url': f"https://{AUTH0_DOMAIN}/authorize?response_type=code&client_id={AUTH0_CLIENT_ID}&redirect_uri={AUTH0_REDIRECT_URI}&scope=openid%20profile%20email&audience={AUTH0_AUDIENCE}"
    })


@auth_bp.route('/callback', methods=['POST'])
def callback():
    """
    Handle Auth0 callback - Exchange authorization code for tokens
    """
    code = request.json.get('code') if request.is_json else request.args.get('code')
    
    if not code:
        return jsonify({'error': 'Authorization code required'}), 400
    
    try:
        import urllib.request
        import urllib.parse
        import json
        
        # Exchange code for tokens
        token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': AUTH0_CLIENT_ID,
            'client_secret': AUTH0_CLIENT_SECRET,
            'code': code,
            'redirect_uri': AUTH0_REDIRECT_URI,
        }
        
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(token_data).encode(),
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode())
        
        # Store tokens in session
        session['access_token'] = tokens.get('access_token')
        session['id_token'] = tokens.get('id_token')
        session['token_type'] = tokens.get('token_type')
        session['expires_in'] = tokens.get('expires_in')
        
        # Decode ID token to get user info
        if tokens.get('id_token'):
            try:
                user_info = verify_id_token(tokens['id_token'])
                session[USER_INFO_KEY] = user_info
            except ImportError as e:
                logger.error(f"ID token verification library not available: {e}")
                return jsonify({'error': 'Authentication configuration error'}), 500
            except ValueError as e:
                logger.warning(f"Could not verify ID token: {e}")
            except Exception as e:
                logger.warning(f"Could not decode ID token: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': '/dashboard'
        })
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Clear session and redirect to Auth0 logout
    """
    # Clear session
    session.clear()
    
    # Build logout URL
    import urllib.parse
    return_to = request.json.get('return_to') if request.is_json else request.args.get('return_to', '/login')
    
    logout_params = {
        'client_id': AUTH0_CLIENT_ID,
        'returnTo': return_to,
    }
    
    logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?{urllib.parse.urlencode(logout_params)}"
    
    return jsonify({
        'success': True,
        'logout_url': logout_url
    })


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current user information
    """
    # Use getattr with default to handle the dynamic attribute safely
    user_info = getattr(request, 'user_info', None)
    
    if not user_info:
        # Try to get from session
        user_info = session.get(USER_INFO_KEY)
    
    if not user_info:
        return jsonify({'error': 'No user information available'}), 404
    
    return jsonify({
        'user': {
            'id': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'email_verified': user_info.get('email_verified'),
        }
    })


@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """
    Check authentication status
    """
    access_token = session.get('access_token')
    user_info = session.get(USER_INFO_KEY)
    
    is_authenticated = bool(access_token and user_info)
    
    return jsonify({
        'authenticated': is_authenticated,
        'user': {
            'id': user_info.get('sub') if user_info else None,
            'email': user_info.get('email') if user_info else None,
            'name': user_info.get('name') if user_info else None,
            'picture': user_info.get('picture') if user_info else None,
        } if user_info else None,
        'expires_at': session.get('expires_at'),
    })


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token
    """
    refresh_token = session.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'No refresh token available'}), 400
    
    try:
        import urllib.request
        import urllib.parse
        import json
        
        # Refresh token
        token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': AUTH0_CLIENT_ID,
            'client_secret': AUTH0_CLIENT_SECRET,
            'refresh_token': refresh_token,
        }
        
        req = urllib.request.Request(
            token_url,
            data=urllib.parse.urlencode(token_data).encode(),
            method='POST'
        )
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode())
        
        # Update session
        session['access_token'] = tokens.get('access_token')
        session['id_token'] = tokens.get('id_token')
        
        return jsonify({
            'success': True,
            'expires_in': tokens.get('expires_in')
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


# ============================================================================
# Token Validation Helper
# ============================================================================

def validate_token(token: str) -> dict:
    """
    Validate an access token and return the claims.
    
    This function properly verifies JWT signatures against Auth0's JWKS.
    For development, set AUTH0_DEV_MODE=true and provide AUTH0_DEV_SECRET.
    
    Args:
        token: JWT access token
        
    Returns:
        Dictionary of token claims
        
    Raises:
        ValueError: If token is invalid
    """
    # Check for development mode without proper configuration
    if AUTH0_DEV_MODE and not AUTH0_DEV_SECRET:
        logger.warning(
            "DEV MODE enabled but no AUTH0_DEV_SECRET provided. "
            "Token validation will fail. Set AUTH0_DEV_SECRET for local development."
        )
    
    # Use the proper verification function
    return verify_jwt_token(token)
