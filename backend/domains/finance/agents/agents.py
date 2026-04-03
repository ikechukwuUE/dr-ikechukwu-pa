"""
Finance Domain Agents — BeeAI RequirementAgent Implementation
=============================================================
6 agents for the finance domain as specified in ARCHITECTURE.md.
Uses BeeAI Framework's RequirementAgent with ConditionalRequirement for
predictable, controlled execution behavior.

State-of-the-art implementation with proper tool integration and risk assessment loops.
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
    RiskLevel,
    InvestorInfo,
    InvestmentRecommendation,
    RiskAssessment,
    InvestmentGuide,
    InvestmentPlan,
    FinancialNewsReport,
)
from shared.prompts import (
    FINANCE_FINANCIAL_COACH_PROMPT,
    FINANCE_AGGRESSIVE_PERSONA_PROMPT,
    FINANCE_CONSERVATIVE_PERSONA_PROMPT,
    FINANCE_RISK_ASSESSOR_PROMPT,
    FINANCE_NEWS_ANCHOR_PROMPT,
)

# Configuration
from app.core.config import openrouter_config

# MCP Tools - Using client helper to fetch from MCP server
from mcp_clients.client import get_mcp_tools_sync

# BeeAI built-in tools
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

# BeeAI middleware for trajectory monitoring
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# BEEAI REQUIREMENT AGENTS
# ============================================================================

def create_financial_coach_agent() -> Optional[RequirementAgent]:
    """
    Financial Coach Agent — Personalized financial guidance.
    
    Uses ThinkTool for reasoning and MCP tools for market data.
    Provides personalized investment advice based on investor profile.
    """
    
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.finance_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=FINANCE_FINANCIAL_COACH_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Financial Coach Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Financial Coach Agent: {e}")
        return None


def create_writer_agent() -> Optional[RequirementAgent]:
    """
    Writer Agent — Formats financial documents.
    
    Uses ThinkTool for document structure and formatting.
    Creates professional financial reports and summaries.
    """

    
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.finance_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions="""You are a Financial Writer Agent specializing in document formatting.

Your role:
1. Format financial documents according to professional standards
2. Create clear, concise investment reports
3. Summarize complex financial data
4. Ensure accuracy and professional tone

Document formats:
- Investment Plans: Comprehensive investment strategy documents
- Q&A Responses: Clear answers to financial questions
- Risk Reports: Detailed risk analysis reports
- News Summaries: Financial news digests

Always think through the document structure before formatting.

Output format: Return a JSON object with:
- formatted_document: The formatted financial document
- format_type: "Investment Plan" | "Q&A" | "Risk Report" | "News Summary"
- sections: Dictionary of document sections
- word_count: Document word count""",
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Writer Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Writer Agent: {e}")
        return None


def create_aggressive_persona_agent() -> Optional[RequirementAgent]:
    """
    Aggressive Persona Agent — High-growth investment recommendations.
    
    Uses ThinkTool for analysis and MCP tools for market data.
    Recommends high-risk, high-reward investment strategies.
    """
    
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.finance_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=FINANCE_AGGRESSIVE_PERSONA_PROMPT,
            requirements=[
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Aggressive Persona Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Aggressive Persona Agent: {e}")
        return None


def create_conservative_persona_agent() -> Optional[RequirementAgent]:
    """
    Conservative Persona Agent — Low-risk investment recommendations.
    
    Uses ThinkTool for analysis and MCP tools for market data.
    Recommends stable, income-generating investment strategies.
    """
    
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.finance_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool()
            ] + mcp_tools,
            instructions=FINANCE_CONSERVATIVE_PERSONA_PROMPT,
            requirements = [
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Conservative Persona Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Conservative Persona Agent: {e}")
        return None


def create_risk_assessor_agent() -> Optional[RequirementAgent]:
    """
    Risk Assessor Agent — Portfolio risk analysis with loop up to 3 iterations.
    
    Uses ThinkTool for analysis and MCP tools for risk metrics.
    Performs iterative risk assessment until resolved or max iterations reached.
    """

    
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.finance_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=FINANCE_RISK_ASSESSOR_PROMPT,
            requirements = [
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Risk Assessor Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Risk Assessor Agent: {e}")
        return None


def create_news_anchor_agent() -> Optional[RequirementAgent]:
    """
    News Anchor Agent — Financial news reporter.
    
    Uses ThinkTool for news analysis and MCP tools for market data.
    Gathers and summarizes financial news and market trends.
    """

    
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.finance_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=FINANCE_NEWS_ANCHOR_PROMPT,
            requirements = [
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
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

def create_finance_agents() -> Dict[str, Any]:
    """
    Create all finance domain agents.
    
    Returns:
        Dictionary of agent instances
    """
    agents = {}
    
    # Create agents with error handling
    agent_creators = {
        "financial_coach": create_financial_coach_agent,
        "writer": create_writer_agent,
        "aggressive_persona": create_aggressive_persona_agent,
        "conservative_persona": create_conservative_persona_agent,
        "risk_assessor": create_risk_assessor_agent,
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
    "RiskLevel", "InvestorInfo", "InvestmentRecommendation", "RiskAssessment",
    "InvestmentGuide", "InvestmentPlan", "FinancialNewsReport",
    # Agent creators
    "create_financial_coach_agent", "create_writer_agent",
    "create_aggressive_persona_agent", "create_conservative_persona_agent",
    "create_risk_assessor_agent", "create_news_anchor_agent",
    # Factory
    "create_finance_agents",
]
