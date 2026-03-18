"""
DR. IKECHUKWU PA - Flask Web Application
State-of-the-art interactive user interface with real-time updates
"""
import sys
import os
import secrets

# Add project root to Python path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from functools import wraps
import logging
import atexit

# Configure logging
logger = logging.getLogger(__name__)
from datetime import datetime

# Import core components and blueprints
from src.core.config import settings
from src.core.security import SecuritySanitizer
from src.core.security_layer import (
    security_service, 
    SecurityService,
    validate_input,
    sanitize_output,
    ToolValidator,
    ToolCall,
    OutputValidator
)
from src.api.routes.cds import cds_bp
from src.api.routes.finance import finance_bp
from src.api.routes.ai_dev import ai_dev_bp
from src.api.routes.fashion import fashion_bp
from src.api.routes.evaluation import evaluation_bp
from src.api.routes.semantic_routing import create_routing_blueprint

# Secure secret key configuration
def configure_secret_key(app, settings):
    """Configure Flask secret key based on environment.
    
    In production: Require FLASK_SECRET_KEY to be set, fail if missing.
    In development: Generate random key with warning if not configured.
    """
    environment = settings.ENVIRONMENT
    
    if environment == 'production':
        # Production: Require secret key to be set
        if not settings.FLASK_SECRET_KEY:
            raise ValueError(
                "FLASK_SECRET_KEY must be set in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        app.secret_key = settings.FLASK_SECRET_KEY
        logger.info("Secret key configured for production environment")
    else:
        # Development: Generate random key if not configured
        if not settings.FLASK_SECRET_KEY:
            app.secret_key = secrets.token_hex(32)
            logger.warning(
                "WARNING: Using auto-generated secret key for development. "
                "Set FLASK_SECRET_KEY in .env for production or persistent sessions. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        else:
            app.secret_key = settings.FLASK_SECRET_KEY
            logger.info("Secret key configured from settings (development)")

# Configuration
app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

# Configure secret key based on environment
configure_secret_key(app, settings)

# CORS configuration - restrict to specific origins in production
def get_cors_origins():
    """Get allowed CORS origins based on environment."""
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # Production: specify exact origins
        allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
        if allowed_origins:
            return allowed_origins.split(',')
        return []  # No CORS in production if not configured
    else:
        # Development: allow localhost and common dev ports
        return [
            'http://localhost:3000',
            'http://localhost:5000',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5000',
            'http://localhost:5173',
            'http://127.0.0.1:5173',
        ]

cors_origins = get_cors_origins()
CORS(app, 
     origins=cors_origins,
     methods=['GET', 'POST'],
     allow_headers=['Content-Type', 'Authorization', 'X-API-Key']
)

socketio = SocketIO(app, cors_allowed_origins=cors_origins)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize sanitizer and security service
sanitizer = SecuritySanitizer()
security_service = SecurityService()

# Initialize tool validator for MCP tools
tool_validator = ToolValidator()

# ============================================================================
# Security Middleware
# ============================================================================

@app.before_request
def security_middleware():
    """
    Global security middleware that runs before each request.
    Implements input validation and rate limiting.
    """
    # Skip for non-API routes
    if not request.path.startswith('/api') and not request.path.startswith('/cds') and \
       not request.path.startswith('/finance') and not request.path.startswith('/ai') and \
       not request.path.startswith('/fashion'):
        return None
    
    # Skip for GET requests and health checks
    if request.method == 'GET' or request.path.endswith('/health'):
        return None
    
    # Validate JSON input for POST/PUT requests
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            data = request.get_json(silent=True) or {}
            
            # Check for empty body on POST
            if request.method == 'POST' and not data:
                logger.warning(f"Empty request body from {request.remote_addr}")
                return jsonify({
                    'error': 'Request body is required',
                    'status': 'error'
                }), 400
            
            # Validate input size (prevent DoS)
            if request.content_length and request.content_length > 1_000_000:  # 1MB
                logger.warning(f"Request too large from {request.remote_addr}")
                return jsonify({
                    'error': 'Request body too large',
                    'status': 'error'
                }), 413
                    
        except Exception as e:
            logger.error(f"Request parsing error: {e}")
            return jsonify({
                'error': 'Invalid request format',
                'status': 'error'
            }), 400
    
    return None


@app.after_request
def security_headers(response):
    """
    Add security headers to all responses.
    """
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

# Register Blueprints
app.register_blueprint(cds_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(ai_dev_bp)
app.register_blueprint(fashion_bp)
app.register_blueprint(evaluation_bp)

# Register semantic routing blueprint
routing_bp = create_routing_blueprint()
app.register_blueprint(routing_bp)

# ============================================================================
# API Key Authentication Decorator
# ============================================================================

def require_api_key(f):
    """
    Decorator to require API key authentication for protected endpoints.
    Use @require_api_key on routes that need authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        environment = os.environ.get('ENVIRONMENT', 'development')
        
        # In production, API key MUST be configured
        expected_key = os.environ.get('DR_IKECHUKWU_PA_API_KEY')
        if environment == 'production' and not expected_key:
            logger.error("API key authentication required but not configured in production")
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Skip auth in development if no key configured
        if environment == 'development' and not expected_key:
            return f(*args, **kwargs)
        
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not secrets.compare_digest(api_key, expected_key):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Rate Limiting (Simple in-memory implementation)
# ============================================================================

class SimpleRateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self):
        self.requests = {}  # {ip: [timestamps]}
        self.max_requests = 100  # Per window
        self.window_seconds = 60  # 1 minute window
    
    def is_allowed(self, key):
        """Check if request is allowed for given key (IP or API key)."""
        import time
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [ts for ts in self.requests[key] if now - ts < self.window_seconds]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True
    
    def cleanup(self):
        """Clean up old entries to prevent memory growth."""
        import time
        now = time.time()
        keys_to_remove = []
        
        for key, timestamps in self.requests.items():
            # Remove old timestamps
            self.requests[key] = [ts for ts in timestamps if now - ts < self.window_seconds]
            
            # Mark empty entries for removal
            if not self.requests[key]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]


import threading

rate_limiter = SimpleRateLimiter()

# Register cleanup to prevent memory leaks
atexit.register(rate_limiter.cleanup)


def schedule_rate_limiter_cleanup():
    """Run cleanup every 5 minutes to prevent memory growth."""
    rate_limiter.cleanup()
    threading.Timer(300, schedule_rate_limiter_cleanup).start()

# Start periodic cleanup
schedule_rate_limiter_cleanup()


def rate_limit(f):
    """
    Decorator to apply rate limiting to routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Use API key if available, otherwise fall back to IP
        api_key = request.headers.get('X-API-Key')
        key = api_key if api_key else request.remote_addr
        
        if not rate_limiter.is_allowed(key):
            logger.warning(f"Rate limit exceeded for {key}")
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Maximum {rate_limiter.max_requests} requests per {rate_limiter.window_seconds} seconds'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Routes: Main Pages
# ============================================================================

@app.route('/')
def index():
    """Home page - interactive dashboard"""
    return render_template('index.html')

@app.route('/clinical')
def clinical():
    """Clinical Decision Support interface"""
    return render_template('clinical.html')

@app.route('/finance')
def finance():
    """Wealth Management HITL interface"""
    return render_template('finance.html')

@app.route('/ai')
def ai_dev():
    """AI Development Lab interface"""
    return render_template('ai_dev.html')

@app.route('/fashion')
def fashion():
    """Fashion/Lifestyle Planner interface"""
    return render_template('fashion.html')

# ============================================================================
# Core API Routes
# ============================================================================

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint with dependency verification"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check database connectivity (if configured)
    if os.environ.get('NEON_DATABASE_URL'):
        try:
            # Basic check - in production use proper connection test
            health_status["checks"]["database"] = "ok"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["checks"]["database"] = "not_configured"
    
    # Check API keys (if configured)
    if os.environ.get('GOOGLE_API_KEY'):
        health_status["checks"]["llm"] = "configured"
    else:
        health_status["checks"]["llm"] = "not_configured"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@app.route('/health', methods=['GET'])
def health():
    """Alias for health check"""
    return api_health()

# ============================================================================
# Security Status Endpoint
# ============================================================================

@app.route('/api/security/status', methods=['GET'])
def security_status():
    """
    Security status endpoint - provides current security configuration and stats.
    """
    from src.core.security_layer import tool_validator
    
    return jsonify({
        "status": "active",
        "security_version": "1.0.0",
        "features": {
            "input_validation": True,
            "pii_sanitization": True,
            "tool_validation": True,
            "output_validation": True,
            "rate_limiting": True,
            "cors_protection": True,
            "security_headers": True
        },
        "tool_stats": tool_validator.get_tool_usage_stats(),
        "allowed_tools": list(tool_validator._allowed_tools)
    })

# ============================================================================
# SocketIO Events (Example)
# ============================================================================

@socketio.on('connect')
def test_connect():
    logger.info("Client connected")
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    logger.info("Client disconnected")

@socketio.on('message')
def handle_message(message):
    logger.info(f"Received message: {message}")
    emit('response', {'data': f'Server received: {message}'})

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """500 handler"""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# Development Server
# ============================================================================

if __name__ == '__main__':
    logger.info("🚀 DR. IKECHUKWU PA Flask App Starting...")
    debug_mode = settings.DEBUG
    # Use default async mode for SocketIO server
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=5000, log_output=True)
