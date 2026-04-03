"""
Coding Domain Agents — BeeAI RequirementAgent Implementation
=============================================================
4 agents for the coding domain as specified in ARCHITECTURE.md.
Uses BeeAI Framework's RequirementAgent with ConditionalRequirement for
predictable, controlled execution behavior.

State-of-the-art implementation with proper tool integration and code review loops.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

# BeeAI Framework imports
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

# Shared schemas and prompts
from shared.schemas import (
    GeneratedCode,
    CodeReview,
    DebugResult,
    CodingNewsReport,
)
from shared.prompts import (
    CODING_CODE_GENERATOR_PROMPT,
    CODING_CODE_REVIEWER_PROMPT,
    CODING_CODE_DEBUGGER_PROMPT,
    CODING_NEWS_ANCHOR_PROMPT,
)

# Configuration
from app.core.config import openrouter_config

# MCP Tools - Using client helper to fetch from MCP server
from mcp_clients.client import get_mcp_tools_sync, get_fallback_tools

# BeeAI middleware for trajectory monitoring
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# BEEAI REQUIREMENT AGENTS
# ============================================================================

def create_code_generator_agent() -> Optional[RequirementAgent]:
    """
    Code Generator Agent — Generates production-quality code.
    
    Uses ThinkTool for reasoning, documentation_search for API references
    """
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.aidev_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=(
                [ThinkTool(), DuckDuckGoSearchTool() ] + mcp_tools
            ),
            instructions=CODING_CODE_GENERATOR_PROMPT,
            requirements = [ ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2) ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Code Generator Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Code Generator Agent: {e}")
        return None


def create_code_reviewer_agent() -> Optional[RequirementAgent]:
    """
    Code Reviewer Agent — Reviews code for bugs, security, style.
    
    Uses ThinkTool for analysis, documentation_search for best practices,
    and PythonTool for testing code.
    """
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.aidev_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=CODING_CODE_REVIEWER_PROMPT,
            requirements = [ ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2) ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Code Reviewer Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Code Reviewer Agent: {e}")
        return None


def create_code_debugger_agent() -> Optional[RequirementAgent]:
    """
    Code Debugger Agent — Fixes issues based on review feedback.
    
    Uses ThinkTool for systematic debugging and PythonTool for verification.
    Implements systematic debugging approach with root cause analysis.
    """
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.aidev_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=CODING_CODE_DEBUGGER_PROMPT,
            requirements = [ ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2) ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Code Debugger Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Code Debugger Agent: {e}")
        return None

def create_news_anchor_agent() -> Optional[RequirementAgent]:
    """
    News Anchor Agent — AI, Data Science, and ML news.
    
    Uses ThinkTool for news analysis and MCP tools for context.
    Gathers and summarizes latest developments in AI and software engineering.
    """
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.aidev_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=CODING_NEWS_ANCHOR_PROMPT,
            requirements = [ ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2) ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("News Anchor Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create News Anchor Agent: {e}")
        return None


# ============================================================================
# AGENT FACTORY
# ============================================================================

def create_coding_agents() -> Dict[str, Any]:
    """
    Create all coding domain agents.
    
    Returns:
        Dictionary of agent instances
    """
    agents = {}
    
    # Create agents with error handling
    agent_creators = {
        "code_generator": create_code_generator_agent,
        "code_reviewer": create_code_reviewer_agent,
        "code_debugger": create_code_debugger_agent,
        "news_anchor": create_news_anchor_agent,
    }
    
    for name, creator in agent_creators.items():
        try:
            agent = creator()
            if agent:
                agents[name] = agent
                logger.info(f"Created {name} agent successfully")
            else:
                logger.warning(f"Failed to create {name} agent")
        except Exception as e:
            logger.error(f"Error creating {name} agent: {e}")
    
    return agents


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Schemas (re-exported from shared)
    "GeneratedCode", "CodeReview", "DebugResult", "CodingNewsReport",
    # Tools (re-exported from mcp_servers)
    # Agent creators
    "create_code_generator_agent", "create_code_reviewer_agent",
    "create_code_debugger_agent", "create_news_anchor_agent",
    # Factory
    "create_coding_agents",
]
