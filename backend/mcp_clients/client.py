"""
MCP Client Utilities
==================
Helper functions for fetching tools from MCP servers and creating agents.
Supports both sync and async usage with cached tool instances.
"""

import asyncio
import os
from typing import Optional, List, Any

from mcp.client.streamable_http import streamable_http_client

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.mcp import MCPTool
from beeai_framework.tools.think import ThinkTool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.weather import OpenMeteoTool


def _create_cache_lock() -> asyncio.Lock:
    """Create a new asyncio lock."""
    return asyncio.Lock()


# Global tool cache - lazily initialized
_mcp_tools_cache: Optional[List[Tool]] = None
_cache_lock: Optional[asyncio.Lock] = None


def _get_cache_lock() -> asyncio.Lock:
    """Get or create the cache lock."""
    global _cache_lock
    if _cache_lock is None:
        _cache_lock = _create_cache_lock()
    return _cache_lock


async def get_mcp_tools(server_url: Optional[str] = None) -> List[Tool]:
    """
    Get all tools from an MCP server with caching.
    
    Args:
        server_url: URL of the MCP server (defaults to env var MCP_SERVER_URL)
    
    Returns:
        List of Tool instances from the MCP server
    """
    global _mcp_tools_cache
    
    if _mcp_tools_cache is not None:
        return _mcp_tools_cache
    
    url = server_url or os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")
    
    try:
        async with _get_cache_lock():
            # Double-check after acquiring lock
            if _mcp_tools_cache is not None:
                return _mcp_tools_cache
            
            client = streamable_http_client(url)
            mcp_tools = await MCPTool.from_client(client)
            _mcp_tools_cache = mcp_tools  # type: ignore
            print(f"Loaded {len(mcp_tools)} tools from MCP server: {url}")
            return mcp_tools # type: ignore
    except Exception as e:
        print(f"Failed to connect to MCP server at {url}: {e}")
        # Return fallback tools if MCP server is not available
        return get_fallback_tools()


def get_fallback_tools() -> List[Tool]:
    """Get fallback tools when MCP server is not available."""
    import tempfile
    import os
    from beeai_framework.tools.code import LocalPythonStorage, PythonTool
    
    # Create a basic PythonTool with default settings
    storage = LocalPythonStorage(
        local_working_dir=tempfile.mkdtemp("fallback_code_storage"),
        interpreter_working_dir="./tmp/fallback_interpreter",
    )
    python_tool = PythonTool(
        code_interpreter_url=os.getenv("CODE_INTERPRETER_URL", "http://127.0.0.1:50081"),
        storage=storage,
    )
    
    return [
        ThinkTool(),
        DuckDuckGoSearchTool(),
        OpenMeteoTool(),
        python_tool,
    ]  # type: ignore[return-value]


async def create_mcp_agent(
    name: str,
    llm: ChatModel,
    instructions: str,
    server_url: Optional[str] = None,
    additional_tools: Optional[List[Tool]] = None,
    requirements: Optional[List[ConditionalRequirement]] = None,
) -> Optional[RequirementAgent]:
    """
    Create a RequirementAgent with tools from MCP server.
    
    Args:
        name: Agent name
        llm: ChatModel instance
        instructions: Agent instructions/prompt
        server_url: URL of the MCP server
        additional_tools: Additional tools to include beyond MCP tools
        requirements: List of ConditionalRequirements
    
    Returns:
        RequirementAgent instance or None if failed
    """
    try:
        # Get tools from MCP server
        mcp_tools = await get_mcp_tools(server_url)
        
        # Get built-in tools
        built_in_tools = get_fallback_tools()
        
        # Combine all tools: built-in + MCP + additional
        all_tools = built_in_tools + mcp_tools
        if additional_tools:
            all_tools = all_tools + additional_tools
        
        # Create agent
        agent = RequirementAgent(
            llm=llm,
            tools=all_tools,
            instructions=instructions,
            requirements=requirements or [],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        print(f"Agent '{name}' created with {len(all_tools)} tools")
        return agent
        
    except Exception as e:
        print(f"Failed to create MCP agent '{name}': {e}")
        return None


def get_domain_tools(domain: str) -> List[Tool]:
    """
    Get domain-specific tools based on domain name.
    These are the tools registered in mcp_servers/server.py
    
    Args:
        domain: Domain name (medicine, finance, coding, fashion)
    
    Returns:
        List of tool instances for the domain
    """
    # Tools will be loaded from MCP server
    # For now, return fallback tools
    return get_fallback_tools()


# Sync wrapper for getting tools (for use in sync contexts)
def get_mcp_tools_sync(server_url: Optional[str] = None) -> List[Tool]:
    """Synchronous wrapper for getting MCP tools."""
    try:
        return asyncio.run(get_mcp_tools(server_url))
    except RuntimeError:
        # If there's already an event loop, return fallback
        return get_fallback_tools()


# Clear cache function (useful for testing)
def clear_tool_cache():
    """Clear the cached MCP tools."""
    global _mcp_tools_cache
    _mcp_tools_cache = None
