"""
LLM Factory and MCP Integration
================================
Centralized LLM creation with model configuration from src/core/config.py
and MCP tools integration.

This module provides:
1. Model creation from config.py settings
2. MCP tools integration for all agents
3. Fallback chain for reliability
"""

from typing import Optional, Any, List
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory class for creating LLM instances with proper configuration.
    Uses settings from src/core/config.py for model selection.
    """
    
    # Domain to config model mapping
    DOMAIN_MODELS = {
        "clinical": {
            "primary": lambda: settings.CLINICAL_PRIMARY_MODEL,
            "backup": lambda: settings.CLINICAL_BACKUP_MODEL
        },
        "finance": {
            "primary": lambda: settings.FINANCE_PRIMARY_MODEL,
            "backup": lambda: settings.FINANCE_BACKUP_MODEL
        },
        "ai_dev": {
            "primary": lambda: settings.AIDEV_PRIMARY_MODEL,
            "backup": lambda: settings.AIDEV_BACKUP_MODEL
        },
        "fashion": {
            "primary": lambda: settings.CLINICAL_PRIMARY_MODEL,  # Use clinical model for fashion
            "backup": lambda: settings.CLINICAL_BACKUP_MODEL
        },
        "evaluation": {
            "primary": lambda: settings.FINANCE_PRIMARY_MODEL,
            "backup": lambda: settings.FINANCE_BACKUP_MODEL
        }
    }
    
    @staticmethod
    def create_llm(
        domain: str = "clinical",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_backup: bool = True
    ) -> Any:
        """
        Create an LLM instance for the specified domain.
        
        Args:
            domain: Domain name (clinical, finance, ai_dev, fashion, evaluation)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_backup: Whether to use backup model if primary fails
            
        Returns:
            LLM instance with invoke method
        """
        # Get model names from config
        domain_config = LLMFactory.DOMAIN_MODELS.get(domain, LLMFactory.DOMAIN_MODELS["clinical"])
        
        primary_model = domain_config["primary"]()
        backup_model = domain_config["backup"]()
        
        # Try primary model first
        if settings.OPENROUTER_API_KEY:
            try:
                llm = LLMFactory._create_openrouter_llm(
                    primary_model,
                    temperature,
                    max_tokens
                )
                logger.info(f"[LLMFactory] Created OpenRouter LLM for {domain}: {primary_model}")
                return llm
            except Exception as e:
                logger.warning(f"[LLMFactory] Primary model {primary_model} failed for {domain}: {e}")
                # Fall through to try backup
        
        # Try backup model if primary failed or no OpenRouter key
        if use_backup:
            if settings.OPENROUTER_API_KEY:
                try:
                    llm = LLMFactory._create_openrouter_llm(
                        backup_model,
                        temperature,
                        max_tokens
                    )
                    logger.info(f"[LLMFactory] Created OpenRouter backup LLM for {domain}: {backup_model}")
                    return llm
                except Exception as e:
                    logger.warning(f"[LLMFactory] Backup model {backup_model} also failed for {domain}: {e}")
            
            # Fallback to Gemini
            if settings.GOOGLE_API_KEY:
                try:
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash",
                        api_key=settings.GOOGLE_API_KEY,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    logger.info(f"[LLMFactory] Created Gemini fallback LLM for {domain}")
                    return llm
                except Exception as e:
                    logger.error(f"[LLMFactory] Gemini failed for {domain}: {e}")
            
            # Last resort - Groq
            if settings.GROQ_API_KEY:
                try:
                    llm = ChatOpenAI(
                        model="llama-3.1-70b-versatile",
                        api_key=settings.GROQ_API_KEY,
                        base_url="https://api.groq.com/openai/v1",
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    logger.info(f"[LLMFactory] Created Groq fallback LLM for {domain}")
                    return llm
                except Exception as e:
                    logger.error(f"[LLMFactory] Groq failed for {domain}: {e}")
        
        raise ValueError(f"No LLM available for domain {domain}. Configure at least one API key.")
    
    @staticmethod
    def _create_openrouter_llm(
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Any:
        """
        Create an OpenRouter LLM instance.
        
        Args:
            model: Model name from OpenRouter
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            OpenRouter LLM wrapper
        """
        from openai import OpenAI
        
        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        
        class OpenRouterLLM:
            def __init__(self, client, model, temperature, max_tokens):
                self.client = client
                self.model = model
                self.temperature = temperature
                self.max_tokens = max_tokens
            
            def invoke(self, prompt):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    extra_headers={
                        "HTTP-Referer": "https://dr-ikechukwu-pa.com",
                        "X-Title": "Dr. Ikechukwu PA"
                    }
                )
                
                class Response:
                    def __init__(self, content):
                        self.content = content
                return Response(response.choices[0].message.content)
        
        return OpenRouterLLM(client, model, temperature, max_tokens)


class MCPToolsManager:
    """
    Manager for MCP tools integration.
    Provides tools from configured MCP servers.
    """
    
    _tools_cache: Optional[List[Any]] = None
    _initialized: bool = False
    
    @classmethod
    async def get_tools(cls) -> List[Any]:
        """
        Get all tools from MCP servers.
        Uses caching to avoid repeated MCP connections.
        
        Returns:
            List of MCP tools
        """
        if cls._tools_cache is not None:
            return cls._tools_cache
            
        try:
            from src.agents.mcp_client import mcp_manager
            cls._tools_cache = await mcp_manager.get_all_tools()
            cls._initialized = True
            logger.info(f"[MCPToolsManager] Loaded {len(cls._tools_cache)} MCP tools")
            return cls._tools_cache
        except Exception as e:
            logger.error(f"[MCPToolsManager] Failed to load MCP tools: {e}")
            cls._tools_cache = []
            return cls._tools_cache
    
    @classmethod
    def get_tools_sync(cls) -> List[Any]:
        """
        Synchronous version of get_tools (runs in existing event loop if available).
        
        Returns:
            List of MCP tools (may be empty if not initialized)
        """
        if cls._tools_cache is not None:
            return cls._tools_cache
        
        # Try to get existing tools synchronously
        try:
            import asyncio
            # Check if there's an existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, can't use await here
                logger.warning("[MCPToolsManager] In async context, returning empty tools")
                return []
            else:
                # We can use the sync approach
                cls._tools_cache = []
                return cls._tools_cache
        except RuntimeError:
            # No event loop exists
            try:
                cls._tools_cache = []
                return cls._tools_cache
            except Exception:
                return []
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the tools cache to force reload on next access."""
        cls._tools_cache = None
        cls._initialized = False
        logger.info("[MCPToolsManager] Tools cache cleared")


# Convenience function for getting domain-specific LLM
def get_domain_llm(domain: str = "clinical", temperature: float = 0.7) -> Any:
    """
    Get an LLM configured for a specific domain.
    
    Args:
        domain: Domain name (clinical, finance, ai_dev, fashion, evaluation)
        temperature: Sampling temperature
        
    Returns:
        Configured LLM instance
    """
    return LLMFactory.create_llm(domain=domain, temperature=temperature)


# Convenience function for getting MCP tools
async def get_mcp_tools() -> List[Any]:
    """
    Get MCP tools for agent use.
    
    Returns:
        List of MCP tools
    """
    return await MCPToolsManager.get_tools()
