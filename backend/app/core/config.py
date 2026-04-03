"""
OpenRouter LLM Factory Configuration
=====================================
Centralized configuration for routing tasks to specific free models
based on domain and required modality.
"""

from typing import Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import ChatOpenAI
import os
import structlog
from dotenv import load_dotenv

# Load .env file from project root
_current_file = os.path.abspath(__file__)
_backend_dir = os.path.dirname(os.path.dirname(_current_file))
_project_root = os.path.dirname(_backend_dir)
_env_path = os.path.join(_project_root, '.env')
load_dotenv(_env_path)


class OpenRouterConfig(BaseSettings):
    """OpenRouter API configuration with domain-specific model routing."""
    
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False
    )
    
    api_key: str = Field(
        default="",
        description="OpenRouter API key for LLM inference",
        alias="OPENROUTER_API_KEY"
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    
    # MCP Server URL for domain tools
    mcp_server_url: str = Field(
        default="http://127.0.0.1:8001/mcp",
        description="MCP server URL for domain tools"
    )
    
    # Domain-specific model configurations using verified TOP FREE models
    # Models prefixed with "openai:" for ChatModel.from_name() compatibility
    medicine_model: str = Field(
        default="openai:nvidia/nemotron-nano-12b-v2-vl:free",
        description="Medicine - clinical decision support and diagnosis"
    )
    finance_model: str = Field(
        default="openai:stepfun/step-3.5-flash:free",
        description="Finance - high-reasoning reflection workflows"
    )
    aidev_model: str = Field(
        default="openai:stepfun/step-3.5-flash:free",
        description="AI-Dev - fast, high-context coding and tool execution"
    )
    fashion_model: str = Field(
        default="openai:nvidia/nemotron-nano-12b-v2-vl:free",
        description="Fashion - rapid multi-image styling analysis"
    )
    
    # Model parameters
    max_tokens: int = Field(default=4096, description="Maximum tokens to generate")
    
    # Enable parallel tool calls for all agents
    allow_parallel_tool_calls: bool = Field(
        default=True,
        description="Enable parallel tool calls for agents"
    )
    
    # Tool choice support - needed for some models
    tool_choice_support: str = Field(
        default="auto",
        description="Tool choice support: auto, none, single"
    )
    
    # Domain-specific temperatures for optimal performance
    medicine_temperature: float = Field(default=0.0, description="Medicine - Deterministic")
    finance_temperature: float = Field(default=0.0, description="Finance - Deterministic")
    aidev_temperature: float = Field(default=0.25, description="AI-Dev - Slightly creative")
    fashion_temperature: float = Field(default=0.8, description="Fashion - Creative")
    temperature: float = Field(default=0.7, description="Default sampling temperature")


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=_env_path,
        env_file_encoding="utf-8",
        extra="allow"
    )
    
    app_name: str = Field(default="Vogue Space: Personal Assistant by Ikechukwu, MD.")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    rate_limit_requests: int = Field(default=10)
    rate_limit_window_seconds: int = Field(default=60)
    
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_collection: str = Field(default="dr_ikechukwu_pa")
    
    redis_url: str = Field(default="redis://localhost:6379")
    
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )


# Global configuration instances
openrouter_config = OpenRouterConfig()
app_config = AppConfig()

# Debug logging
logger = structlog.get_logger()
logger.info(
    "openrouter_config_loaded",
    medicine_model=openrouter_config.medicine_model,
    finance_model=openrouter_config.finance_model,
    aidev_model=openrouter_config.aidev_model,
    fashion_model=openrouter_config.fashion_model,
    api_key_present=bool(openrouter_config.api_key),
    api_key_masked=f"{openrouter_config.api_key[:10]}..." if openrouter_config.api_key else "NOT_SET",
    base_url=openrouter_config.base_url,
    mcp_server_url=openrouter_config.mcp_server_url,
)


def get_domain_temperature(domain: str) -> float:
    """Get the temperature setting for a specific domain."""
    temperature_map = {
        "medicine": openrouter_config.medicine_temperature,
        "finance": openrouter_config.finance_temperature,
        "aidev": openrouter_config.aidev_temperature,
        "fashion": openrouter_config.fashion_temperature,
    }
    
    if domain not in temperature_map:
        return openrouter_config.temperature
    
    return _validate_temperature(temperature_map[domain])


def _validate_max_tokens(value: int) -> int:
    """Validate and normalize max_tokens value."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"max_tokens must be a positive integer, got: {value}")
    return min(max(value, 1), 32768)


def _validate_temperature(value: float) -> float:
    """Validate and normalize temperature value."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"temperature must be a number, got: {value}")
    return float(max(0.0, min(value, 2.0)))


def get_llm_config_for_domain(domain: str) -> Dict[str, Any]:
    """Get LLM configuration mapping for a specific domain."""
    temperature = get_domain_temperature(domain)
    
    domain_configs = {
        "medicine": {
            "model": openrouter_config.medicine_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
            "temperature": temperature,
        },
        "finance": {
            "model": openrouter_config.finance_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
            "temperature": temperature,
        },
        "aidev": {
            "model": openrouter_config.aidev_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
            "temperature": temperature,
        },
        "fashion": {
            "model": openrouter_config.fashion_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
            "temperature": temperature,
        },
    }
    
    if domain not in domain_configs:
        raise ValueError(f"Unknown domain: {domain}. Available: {list(domain_configs.keys())}")
    
    return domain_configs[domain]


# Export configuration
__all__ = [
    "OpenRouterConfig",
    "AppConfig",
    "openrouter_config",
    "app_config",
    "get_llm_config_for_domain",
    "get_domain_temperature",
]
