"""
OpenRouter LLM Factory Configuration
=====================================
Centralized configuration for routing tasks to specific free models
based on domain and required modality.
"""

from typing import Dict, Optional, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import ChatOpenAI
import os


class OpenRouterConfig(BaseSettings):
    """OpenRouter API configuration with domain-specific model routing."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )
    
    api_key: str = Field(
        default="",
        description="OpenRouter API key for LLM inference",
        alias="OPENROUTER_API_KEY"  # Match .env variable name
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    
    # Domain-specific model configurations
    cds_model: str = Field(
        # Gemma-3-12b-it is a strong choice for clinical decision support due to its multimodal capabilities and large context window, which are essential for processing complex medical information and images.
        default="google/gemma-3-12b-it:free",
        description="Clinical Decision Support - multimodal (text + vision)"
    )
    finance_model: str = Field(
        # Minimax-M2.5 is optimized for high-reasoning tasks and can handle complex financial data and queries effectively, making it a suitable choice for finance-related applications.
        default="minimax/minimax-m2.5:free",
        description="Finance - high-reasoning reflection workflows"
    )
    aidev_model: str = Field(
        # Minimax-M2.5 is optimized for high-reasoning tasks and can handle complex coding queries effectively, making it a strong choice for AI development assistance.
        default="minimax/minimax-m2.5:free",
        description="AI-Dev - fast, high-context coding"
    )
    fashion_model: str = Field(
        # Gemma-3-4b-it is a good choice for fashion-related applications due to its multimodal capabilities, allowing it to analyze both text and images effectively, which is crucial for fashion analysis and recommendations.
        default="google/gemma-3-4b-it:free",
        description="Fashion - text + vision analysis"
    )
    
    # Model parameters
    max_tokens: int = Field(default=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Sampling temperature")


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )
    
    # Application settings
    app_name: str = Field(default="Vogue Space: Personal Assistant by Ikechukwu, MD.", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode flag")
    
    # Security settings
    secret_key: str = Field(
        default="change-me-in-production",
        description="JWT secret key"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    
    # Rate limiting
    rate_limit_requests: int = Field(
        default=10,
        description="Rate limit - requests per window"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit - window in seconds"
    )
    
    # Qdrant settings
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection: str = Field(
        default="dr_ikechukwu_pa",
        description="Qdrant collection name"
    )
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )


# Global configuration instances
openrouter_config = OpenRouterConfig()
app_config = AppConfig()


def create_openrouter_llm(domain: str) -> ChatOpenAI:
    """
    Create an OpenRouter LLM instance for a specific domain.
    
    Args:
        domain: Domain name (cds, finance, aidev, fashion)
    
    Returns:
        ChatOpenAI instance configured for the domain
    
    Raises:
        ValueError: If domain is invalid or parameters are out of range
    """
    config = get_llm_config_for_domain(domain)
    
    # Validate configuration parameters
    max_tokens = _validate_max_tokens(openrouter_config.max_tokens)
    temperature = _validate_temperature(openrouter_config.temperature)
    
    return ChatOpenAI(
        model=config["model"],
        base_url=config["base_url"],
        api_key=config["api_key"],
        max_tokens=max_tokens,  # type: ignore[call-arg]
        temperature=temperature,
    )


def _validate_max_tokens(value: int) -> int:
    """Validate and normalize max_tokens value."""
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"max_tokens must be a positive integer, got: {value}")
    return min(max(value, 1), 32768)  # Clamp to reasonable range


def _validate_temperature(value: float) -> float:
    """Validate and normalize temperature value."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"temperature must be a number, got: {value}")
    return float(max(0.0, min(value, 2.0)))  # Clamp to valid OpenAI range


def get_llm_config_for_domain(domain: str) -> Dict[str, Any]:
    """
    Get LLM configuration for a specific domain.
    
    Args:
        domain: Domain name (cds, finance, aidev, fashion)
    
    Returns:
        Dictionary with model, base_url, and api_key
    """
    domain_configs = {
        "cds": {
            "model": openrouter_config.cds_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
        },
        "finance": {
            "model": openrouter_config.finance_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
        },
        "aidev": {
            "model": openrouter_config.aidev_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
        },
        "fashion": {
            "model": openrouter_config.fashion_model,
            "base_url": openrouter_config.base_url,
            "api_key": openrouter_config.api_key,
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
    "create_openrouter_llm",
    "get_llm_config_for_domain",
]
