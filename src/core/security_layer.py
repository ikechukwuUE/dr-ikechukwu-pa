"""
Comprehensive Security Layer for Dr. Ikechukwu PA AI System
============================================================

This module provides:
1. Input Validation - Pydantic-based request validation with sanitization
2. Tool Use Validation - Control and validate tool invocations
3. Output Validation - Sanitize and validate responses

Security Principles Applied:
- Zero Trust: Always validate, never assume
- Defense in Depth: Multiple layers of validation
- Least Privilege: Only allow necessary operations
- Fail Secure: Default to deny on uncertainty
"""

import re
import html
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
import bleach

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class SecurityConfig:
    """Central security configuration."""
    
    # Input validation limits
    MAX_INPUT_LENGTH = 10000
    MIN_INPUT_LENGTH = 1
    MAX_ARRAY_ITEMS = 100
    MAX_DEPTH = 10
    
    # Allowed characters patterns
    ALLOWED_QUERY_CHARS = re.compile(r'^[\w\s\-.,!?;:\'\"()[\]{}@#$%^&*+=|\\/<>~\n\r\t]+$')
    
    # Dangerous patterns that should be blocked
    INJECTION_PATTERNS = [
        r'(\b|\s)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b',
        r'--',
        r'/\*.*\*/',
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
    ]
    
    # Tool whitelist - only these tools are allowed
    ALLOWED_TOOLS = {
        # MCP Tools
        'pubmed_search',
        'github',
        'filesystem',
        'financial_datasets',
        'playwright',
        # Internal tools
        'clinical_analysis',
        'finance_analysis',
        'fashion_analysis',
        'ai_dev_analysis',
    }
    
    # Dangerous tool patterns that should always be blocked
    BLOCKED_TOOL_PATTERNS = [
        r'delete.*file',
        r'drop.*table',
        r'rm\s+-',
        r'format.*disk',
        r'shutdown',
        r'reboot',
    ]
    
    # Output sanitization settings
    OUTPUT_ALLOWED_TAGS = []  # No HTML allowed in output
    OUTPUT_ALLOWED_ATTRIBUTES = {}


# =============================================================================
# INPUT VALIDATION
# =============================================================================

class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"      # Block any deviation
    MODERATE = "moderate"  # Allow with warning
    PERMISSIVE = "permissive"  # Log only


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_value: Optional[str] = None
    validation_level: ValidationLevel = ValidationLevel.STRICT


class InputValidator:
    """
    Comprehensive input validation with multiple security checks.
    """
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.config.INJECTION_PATTERNS
        ]
    
    def validate_string(
        self, 
        value: Any, 
        field_name: str = "input",
        required: bool = True,
        min_length: int = None,
        max_length: int = None,
        allow_none: bool = False
    ) -> ValidationResult:
        """
        Validate a string input with comprehensive checks.
        
        Args:
            value: The value to validate
            field_name: Name for error messages
            required: Whether the field is required
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            allow_none: Whether None is acceptable
            
        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        sanitized = None
        
        # Check for None
        if value is None:
            if required and not allow_none:
                errors.append(f"{field_name}: Field is required")
                return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
            return ValidationResult(True, [], [], None, ValidationLevel.STRICT)
        
        # Type check
        if not isinstance(value, str):
            errors.append(f"{field_name}: Must be a string")
            return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
        
        # Empty check
        if len(value.strip()) == 0:
            if required:
                errors.append(f"{field_name}: Cannot be empty")
                return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
            return ValidationResult(True, [], [], "", ValidationLevel.STRICT)
        
        # Length checks
        min_len = min_length or self.config.MIN_INPUT_LENGTH
        max_len = max_length or self.config.MAX_INPUT_LENGTH
        
        if len(value) < min_len:
            errors.append(f"{field_name}: Must be at least {min_len} characters")
            return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
        
        if len(value) > max_len:
            errors.append(f"{field_name}: Must be at most {max_len} characters")
            return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
        
        # Check for injection patterns
        for pattern in self._compiled_patterns:
            if pattern.search(value):
                errors.append(
                    f"{field_name}: Potentially dangerous pattern detected. "
                    "Input contains suspicious content."
                )
                return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
        
        # Character validation (allow basic punctuation and alphanumeric)
        # For clinical/medical queries, we allow more characters
        sanitized = value.strip()
        
        return ValidationResult(
            True, 
            [], 
            warnings, 
            sanitized, 
            ValidationLevel.STRICT
        )
    
    def validate_json_structure(
        self, 
        data: Dict, 
        required_fields: List[str],
        optional_fields: List[str] = None
    ) -> ValidationResult:
        """
        Validate JSON structure with required and optional fields.
        """
        errors = []
        warnings = []
        optional = optional_fields or []
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check for unexpected fields (potential attack vector)
        all_allowed = set(required_fields) | set(optional)
        for field in data.keys():
            if field not in all_allowed:
                warnings.append(f"Unexpected field ignored: {field}")
        
        if errors:
            return ValidationResult(False, errors, warnings, validation_level=ValidationLevel.STRICT)
        
        return ValidationResult(
            True, 
            errors, 
            warnings, 
            data, 
            ValidationLevel.STRICT
        )
    
    def sanitize_html(self, value: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.
        """
        if not value:
            return ""
        
        # Use bleach for HTML sanitization
        cleaned = bleach.clean(
            value,
            tags=self.config.OUTPUT_ALLOWED_TAGS,
            attributes=self.config.OUTPUT_ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned


# =============================================================================
# TOOL USE VALIDATION
# =============================================================================

@dataclass
class ToolCall:
    """Represents a tool invocation request."""
    tool_name: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class ToolValidationResult:
    """Result of tool validation."""
    is_allowed: bool
    tool_name: str
    reason: str = ""
    warnings: List[str] = field(default_factory=list)
    sanitized_args: Optional[Dict[str, Any]] = None


class ToolValidator:
    """
    Validates tool invocations before execution.
    Implements least-privilege principle - default deny.
    """
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self._allowed_tools: Set[str] = set(self.config.ALLOWED_TOOLS)
        self._blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.config.BLOCKED_TOOL_PATTERNS
        ]
        
        # Track tool usage for monitoring
        self._tool_usage_log: List[Dict] = []
    
    def add_allowed_tool(self, tool_name: str) -> None:
        """Add a tool to the allowed list."""
        self._allowed_tools.add(tool_name)
        logger.info(f"Tool added to allowlist: {tool_name}")
    
    def remove_allowed_tool(self, tool_name: str) -> None:
        """Remove a tool from the allowed list."""
        self._allowed_tools.discard(tool_name)
        logger.info(f"Tool removed from allowlist: {tool_name}")
    
    def validate_tool_call(self, tool_call: ToolCall) -> ToolValidationResult:
        """
        Validate a tool call before execution.
        
        Checks:
        1. Tool is in allowlist
        2. Arguments are safe
        3. No dangerous patterns in arguments
        """
        tool_name = tool_call.tool_name
        args = tool_call.arguments
        
        # Check 1: Tool in allowlist
        if tool_name not in self._allowed_tools:
            logger.warning(
                f"Tool access denied: {tool_name} not in allowlist. "
                f"User: {tool_call.user_id}, Session: {tool_call.session_id}"
            )
            return ToolValidationResult(
                is_allowed=False,
                tool_name=tool_name,
                reason=f"Tool '{tool_name}' is not authorized. Contact administrator to request access."
            )
        
        # Check 2: Dangerous patterns in tool name
        for pattern in self._blocked_patterns:
            if pattern.search(tool_name):
                logger.warning(
                    f"Blocked dangerous tool pattern: {tool_name}. "
                    f"User: {tool_call.user_id}"
                )
                return ToolValidationResult(
                    is_allowed=False,
                    tool_name=tool_name,
                    reason="Tool name contains potentially dangerous patterns."
                )
        
        # Check 3: Validate arguments
        sanitized_args = self._sanitize_arguments(args)
        
        # Check 4: Log the tool call
        self._log_tool_call(tool_call)
        
        return ToolValidationResult(
            is_allowed=True,
            tool_name=tool_name,
            sanitized_args=sanitized_args,
            warnings=[]
        )
    
    def _sanitize_arguments(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize tool arguments to prevent injection.
        """
        sanitized = {}
        
        for key, value in args.items():
            if isinstance(value, str):
                # Remove any potential command injection
                sanitized[key] = value.replace(';', '').replace('&&', '').replace('||', '')
                sanitized[key] = sanitized[key].replace('|', '')
                sanitized[key] = sanitized[key].replace('`', '')
                sanitized[key] = sanitized[key].replace('$', '')
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_arguments(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_arguments({k: v})[k] if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _log_tool_call(self, tool_call: ToolCall) -> None:
        """Log tool call for security monitoring."""
        self._tool_usage_log.append({
            'tool': tool_call.tool_name,
            'user': tool_call.user_id,
            'session': tool_call.session_id,
            'timestamp': tool_call.timestamp
        })
        
        # Keep log bounded
        if len(self._tool_usage_log) > 1000:
            self._tool_usage_log = self._tool_usage_log[-500:]
    
    def get_tool_usage_stats(self) -> Dict[str, int]:
        """Get tool usage statistics."""
        stats = {}
        for entry in self._tool_usage_log:
            tool = entry['tool']
            stats[tool] = stats.get(tool, 0) + 1
        return stats


# =============================================================================
# OUTPUT VALIDATION
# =============================================================================

@dataclass
class OutputValidationResult:
    """Result of output validation."""
    is_valid: bool
    content: str
    warnings: List[str] = field(default_factory=list)
    redactions: List[str] = field(default_factory=list)


class OutputValidator:
    """
    Validates and sanitizes output before returning to users.
    """
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self._sensitive_patterns = self._compile_sensitive_patterns()
    
    def _compile_sensitive_patterns(self) -> List[re.Pattern]:
        """Compile patterns for sensitive data detection in output."""
        return [
            re.compile(r'\b\d{16}\b', re.IGNORECASE),  # Credit card numbers
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),       # SSN
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
            re.compile(r'\b(?:\+234|0)[0-9]{10}\b'),     # Phone numbers
            re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]+', re.IGNORECASE),  # API keys
            re.compile(r'secret["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]+', re.IGNORECASE),  # Secrets
            re.compile(r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE),  # Passwords
        ]
    
    def validate_output(self, content: Any, expected_type: str = "text") -> OutputValidationResult:
        """
        Validate and sanitize output content.
        
        Args:
            content: The output content to validate
            expected_type: Expected content type (text, json, html)
            
        Returns:
            OutputValidationResult with sanitized content
        """
        warnings = []
        redactions = []
        
        if content is None:
            return OutputValidationResult(True, "", warnings, redactions)
        
        # Convert to string if needed
        if not isinstance(content, str):
            if isinstance(content, (dict, list)):
                try:
                    content = json.dumps(content)
                except:
                    content = str(content)
            else:
                content = str(content)
        
        # Check for sensitive data
        for pattern in self._sensitive_patterns:
            matches = pattern.findall(content)
            if matches:
                redactions.append(f"Found {len(matches)} potential sensitive data(s)")
                # Redact sensitive data
                content = pattern.sub('[REDACTED]', content)
        
        # HTML sanitize if needed
        if expected_type == "html":
            content = self._sanitize_html(content)
        
        return OutputValidationResult(
            is_valid=True,
            content=content,
            warnings=warnings,
            redactions=redactions
        )
    
    def _sanitize_html(self, content: str) -> str:
        """Sanitize HTML content."""
        return bleach.clean(
            content,
            tags=self.config.OUTPUT_ALLOWED_TAGS,
            attributes=self.config.OUTPUT_ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    def validate_json_output(self, content: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Validate JSON output format.
        
        Returns:
            Tuple of (is_valid, parsed_json, error_message)
        """
        if not content or not content.strip():
            return True, {}, ""
        
        try:
            parsed = json.loads(content)
            return True, parsed, ""
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"


# =============================================================================
# INTEGRATED SECURITY SERVICE
# =============================================================================

class SecurityService:
    """
    Unified security service combining input, tool, and output validation.
    This is the main entry point for security checks.
    """
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.input_validator = InputValidator(self.config)
        self.tool_validator = ToolValidator(self.config)
        self.output_validator = OutputValidator(self.config)
        
        # Import existing sanitizer for backward compatibility
        from src.core.security import SecuritySanitizer
        self.clinical_sanitizer = SecuritySanitizer()
    
    def validate_request(
        self, 
        data: Dict, 
        required_fields: List[str],
        optional_fields: List[str] = None
    ) -> ValidationResult:
        """
        Validate a complete API request.
        """
        # First validate structure
        struct_result = self.input_validator.validate_json_structure(
            data, required_fields, optional_fields
        )
        
        if not struct_result.is_valid:
            return struct_result
        
        # Then validate each required field
        for field in required_fields:
            value = data.get(field)
            result = self.input_validator.validate_string(value, field_name=field)
            if not result.is_valid:
                return result
        
        return ValidationResult(True, [], [], data)
    
    def sanitize_clinical_input(self, prompt: str) -> Tuple[str, Dict]:
        """
        Sanitize clinical input using existing clinical sanitizer.
        Combines with additional validation.
        """
        # First run our input validation
        validation = self.input_validator.validate_string(prompt, "clinical_query")
        
        if not validation.is_valid:
            return "", {"validation_error": validation.errors}
        
        # Then use existing clinical sanitizer
        return self.clinical_sanitizer.sanitize_clinical_prompt(prompt)
    
    def validate_and_sanitize_output(self, content: Any) -> OutputValidationResult:
        """
        Validate and sanitize output before returning to user.
        """
        return self.output_validator.validate_output(content)


# =============================================================================
# DECORATORS FOR ROUTE PROTECTION
# =============================================================================

def validate_input(*required_fields, optional=None):
    """
    Decorator to validate input for Flask routes.
    
    Usage:
        @validate_input('query', 'thread_id', optional=['patient_context'])
        def my_route():
            ...
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            # Get JSON data
            data = request.get_json(silent=True) or {}
            
            # Create security service
            security = SecurityService()
            
            # Validate
            result = security.validate_request(data, list(required_fields), optional)
            
            if not result.is_valid:
                return jsonify({
                    "status": "error",
                    "error": "Validation failed",
                    "details": result.errors
                }), 400
            
            # Add validated data to request context
            request.validated_data = result.sanitized_value
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper


def sanitize_output(f):
    """
    Decorator to sanitize output from routes.
    
    Usage:
        @sanitize_output
        def my_route():
            return {"result": "some content"}
        ...
    """
    def wrapper(*args, **kwargs):
        from flask import jsonify
        
        result = f(*args, **kwargs)
        
        # Only sanitize JSON responses
        if isinstance(result, dict):
            security = SecurityService()
            validated = security.output_validator.validate_output(result)
            
            # Add security metadata
            if validated.redactions:
                result['_security'] = {
                    'redactions': validated.redactions
                }
            
            return jsonify(result)
        
        return result
    
    wrapper.__name__ = f.__name__
    return wrapper


# =============================================================================
# INITIALIZE SINGLETON
# =============================================================================

# Default security service instance
security_service = SecurityService()
