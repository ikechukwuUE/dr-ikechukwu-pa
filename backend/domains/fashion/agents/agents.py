"""
Fashion Domain Agents — BeeAI RequirementAgent Implementation
=============================================================
4 agents for the fashion domain as specified in ARCHITECTURE.md.
Uses BeeAI Framework's RequirementAgent with ConditionalRequirement for
predictable, controlled execution behavior.

State-of-the-art implementation with proper tool integration and vision capabilities.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

# BeeAI Framework imports
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool

# Shared schemas and prompts
from shared.schemas import (
    OutfitAnalysis,
    StyleTrend,
    OutfitRecommendation,
)
from shared.prompts import (
    FASHION_OUTFIT_DESCRIPTOR_PROMPT,
    FASHION_OUTFIT_ANALYZER_PROMPT,
    FASHION_STYLE_TREND_ANALYZER_PROMPT,
    FASHION_STYLE_PLANNER_PROMPT,
)

# Configuration
from app.core.config import openrouter_config

# Image utilities for multimodal support
from shared.image_utils import (
    encode_image_to_base64,
    create_openrouter_multimodal_message,
)

# MCP Tools (imported from mcp_servers/server.py)
from mcp_servers.server import fashion_trend_api, price_comparison

# BeeAI weather tool for location-based recommendations
from beeai_framework.tools.weather import OpenMeteoTool

# BeeAI middleware for trajectory monitoring
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# BEEAI REQUIREMENT AGENTS
# ============================================================================

def create_outfit_descriptor_agent() -> Optional[RequirementAgent]:
    """
    Outfit Descriptor Agent — Describes outfits from images.
    
    Uses ThinkTool for analysis and fashion_trend_api for context.
    Provides detailed outfit descriptions with style classification.
    """
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.fashion_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                fashion_trend_api,
            ],
            instructions=FASHION_OUTFIT_DESCRIPTOR_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(fashion_trend_api, min_invocations=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Outfit Descriptor Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Outfit Descriptor Agent: {e}")
        return None


def create_outfit_analyzer_agent() -> Optional[RequirementAgent]:
    """
    Outfit Analyzer Agent — Evaluates appropriateness and coordination.
    
    Uses ThinkTool for analysis and fashion_trend_api for trend context.
    Provides comprehensive outfit evaluation and improvement suggestions.
    """
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.fashion_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                fashion_trend_api,
            ],
            instructions=FASHION_OUTFIT_ANALYZER_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(fashion_trend_api, min_invocations=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Outfit Analyzer Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Outfit Analyzer Agent: {e}")
        return None


def create_style_trend_analyzer_agent() -> Optional[RequirementAgent]:
    """
    Style Trend Analyzer Agent — Tracks current fashion trends.
    
    Uses ThinkTool for analysis and fashion_trend_api for trend data.
    Provides comprehensive trend analysis across categories and regions.
    """
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.fashion_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                fashion_trend_api,
            ],
            instructions=FASHION_STYLE_TREND_ANALYZER_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(fashion_trend_api, min_invocations=2, max_invocations=4),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Style Trend Analyzer Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Style Trend Analyzer Agent: {e}")
        return None


def create_style_planner_agent() -> Optional[RequirementAgent]:
    """
    Style Planner Agent — Personal stylist for outfit recommendations.
    
    Uses ThinkTool for planning, fashion_trend_api for trends, price_comparison for budgeting,
    and OpenMeteoTool for weather-aware recommendations.
    Creates personalized outfit recommendations based on budget, occasion, weather, and preferences.
    """
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.fashion_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                fashion_trend_api,
                price_comparison,
                OpenMeteoTool(),
            ],
            instructions=FASHION_STYLE_PLANNER_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ConditionalRequirement(fashion_trend_api, min_invocations=1),
                ConditionalRequirement(price_comparison, min_invocations=1, max_invocations=3),
                ConditionalRequirement(OpenMeteoTool, min_invocations=0, max_invocations=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Style Planner Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Style Planner Agent: {e}")
        return None


# ============================================================================
# AGENT FACTORY
# ============================================================================

def create_fashion_agents() -> Dict[str, Any]:
    """
    Create all fashion domain agents.
    
    Returns:
        Dictionary of agent instances
    """
    agents = {}
    
    # Create agents with error handling
    agent_creators = {
        "outfit_descriptor": create_outfit_descriptor_agent,
        "outfit_analyzer": create_outfit_analyzer_agent,
        "style_trend_analyzer": create_style_trend_analyzer_agent,
        "style_planner": create_style_planner_agent,
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
    "OutfitAnalysis", "StyleTrend", "OutfitRecommendation",
    # Tools (re-exported from mcp_servers)
    "fashion_trend_api", "price_comparison",
    # Image utilities
    "encode_image_to_base64", "create_openrouter_multimodal_message",
    # Agent creators
    "create_outfit_descriptor_agent", "create_outfit_analyzer_agent",
    "create_style_trend_analyzer_agent", "create_style_planner_agent",
    # Factory
    "create_fashion_agents",
]
