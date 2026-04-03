"""
Fashion Domain Workflows — BeeAI Workflow Implementation
========================================================
3 BeeAI Workflows for the fashion domain as specified in ARCHITECTURE.md.

Pipelines:
1. Outfit Analysis - Image description → Outfit Descriptor → Outfit Analyzer
2. Trend Analysis - Query → Style Trend Analyzer → Trend Report
3. Outfit Recommendation - Budget + Occasion + Time + Location → Style Planner → Recommendation

Each pipeline uses BeeAI Workflow with State transitions (Workflow.NEXT, Workflow.SELF, Workflow.END).
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

# BeeAI Framework imports
from beeai_framework.workflows import Workflow

# MCP Tools from mcp_servers/server.py
from mcp_servers.server import fashion_trend_api, price_comparison

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SHARED SCHEMAS IMPORT
# ============================================================================
from shared.schemas import (
    OutfitAnalysis,
    StyleTrend,
    OutfitRecommendation,
)

# ============================================================================
# WORKFLOW STATE
# ============================================================================

class FashionWorkflowState(BaseModel):
    """State for fashion workflow execution."""
    # Input
    image_description: str = Field(default="", description="Image description or URL")
    image_base64: str = Field(default="", description="Base64 encoded image for multimodal analysis")
    query: str = Field(default="", description="Fashion query")
    budget: float = Field(default=0, description="Budget for recommendations")
    occasion: str = Field(default="", description="Occasion for outfit")
    time: str = Field(default="", description="Time of day")
    location: str = Field(default="", description="Location/region")
    
    # Analysis results
    outfit_analysis: Optional[OutfitAnalysis] = Field(default=None, description="Outfit analysis")
    style_trend: Optional[StyleTrend] = Field(default=None, description="Style trend analysis")
    outfit_recommendation: Optional[OutfitRecommendation] = Field(default=None, description="Outfit recommendation")
    
    # Final output
    final_output: str = Field(default="", description="Final output")
    
    # Execution tracking
    current_step: str = Field(default="", description="Current workflow step")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    error: Optional[str] = Field(default=None, description="Error message")
    
    # Session info
    session_id: str = Field(default="", description="Session identifier")


# ============================================================================
# WORKFLOW STEPS
# ============================================================================

async def outfit_descriptor_step(state: FashionWorkflowState) -> str:
    """Outfit Descriptor analyzes outfit from image or description using AI agent."""
    try:
        state.current_step = "outfit_descriptor"
        
        # Import agent creator
        from domains.fashion.agents.agents import create_outfit_descriptor_agent
        
        # Create the agent
        agent = create_outfit_descriptor_agent()
        if not agent:
            state.error = "Failed to create outfit descriptor agent"
            return Workflow.END
        
        # Prepare input for the agent
        if state.image_base64:
            # For multimodal analysis, include image description
            agent_input = f"Analyze this outfit from the image. Description: {state.image_description or 'No description provided'}"
        else:
            # Text-only analysis
            agent_input = f"Analyze this outfit: {state.image_description or 'No description provided'}"
        
        # Run the agent with structured output
        logger.info("Running outfit descriptor agent")
        result = await agent.run(agent_input, expected_output=OutfitAnalysis)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.outfit_analysis = result.output_structured  # type: ignore[assignment]
        else:
            # Fallback analysis
            output_text: str = ""
            if result.output and len(result.output) > 0:
                last_message = result.output[-1]
                if hasattr(last_message, 'content'):
                    output_text = str(last_message.content)
                else:
                    output_text = str(last_message)
            
            state.outfit_analysis = OutfitAnalysis(
                items_detected=["AI-analyzed items"],
                style="casual",
                colors=["Various colors"],
                occasion_fit="Appropriate for general occasions",
                suggestions=[output_text[:200] if output_text else "No suggestions available"]
            )
        
        state.completed_steps.append("outfit_descriptor")
        
        logger.info(f"Outfit descriptor completed with AI agent")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Outfit descriptor step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def outfit_analyzer_step(state: FashionWorkflowState) -> str:
    """Outfit Analyzer evaluates appropriateness and coordination."""
    try:
        state.current_step = "outfit_analyzer"
        
        # Analyze outfit coordination
        analysis = state.outfit_analysis
        
        if analysis:
            # Generate analysis output
            output = f"# Outfit Analysis\n\n"
            output += f"## Items Detected\n"
            for item in analysis.items_detected:
                output += f"- {item}\n"
            
            output += f"\n## Style Classification\n{analysis.style}\n"
            
            output += f"\n## Colors\n"
            for color in analysis.colors:
                output += f"- {color}\n"
            
            output += f"\n## Occasion Fit\n{analysis.occasion_fit}\n"
            
            output += f"\n## Suggestions\n"
            for suggestion in analysis.suggestions:
                output += f"- {suggestion}\n"
            
            state.final_output = output
        else:
            state.final_output = "No outfit analysis available"
        
        state.completed_steps.append("outfit_analyzer")
        
        logger.info("Outfit analyzer completed")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"Outfit analyzer step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def style_trend_analyzer_step(state: FashionWorkflowState) -> str:
    """Style Trend Analyzer tracks current fashion trends using AI agent."""
    try:
        state.current_step = "style_trend_analyzer"
        
        # Import agent creator
        from domains.fashion.agents.agents import create_style_trend_analyzer_agent
        
        # Create the agent
        agent = create_style_trend_analyzer_agent()
        if not agent:
            state.error = "Failed to create style trend analyzer agent"
            return Workflow.END
        
        # Get trends for the specified region
        region = state.location if state.location else "global"
        
        # Prepare input for the agent
        agent_input = f"Analyze current fashion trends for region: {region}. Query: {state.query or 'General trend analysis'}"
        
        # Run the agent with structured output
        logger.info(f"Running style trend analyzer agent for region: {region}")
        result = await agent.run(agent_input, expected_output=StyleTrend)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.style_trend = result.output_structured  # type: ignore[assignment]
        else:
            state.style_trend = StyleTrend(
                current_trends=["AI-analyzed trends"],
                trending_colors=["Various colors"],
                trending_styles=["Multiple styles"]
            )
        
        # Generate output
        output = f"# Fashion Trend Report\n\n"
        output += f"## Region: {region}\n\n"
        
        if state.style_trend:
            output += f"## Current Trends\n"
            for trend in state.style_trend.current_trends:
                output += f"- {trend}\n"
            
            output += f"\n## Trending Colors\n"
            for color in state.style_trend.trending_colors:
                output += f"- {color}\n"
            
            output += f"\n## Trending Styles\n"
            for style in state.style_trend.trending_styles:
                output += f"- {style}\n"
        else:
            output += "No trend data available"
        
        state.final_output = output
        state.completed_steps.append("style_trend_analyzer")
        
        logger.info(f"Style trend analyzer completed for region: {region}")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"Style trend analyzer step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def style_planner_step(state: FashionWorkflowState) -> str:
    """Style Planner creates personalized outfit recommendations using AI agent."""
    try:
        state.current_step = "style_planner"
        
        # Import agent creator
        from domains.fashion.agents.agents import create_style_planner_agent
        
        # Create the agent
        agent = create_style_planner_agent()
        if not agent:
            state.error = "Failed to create style planner agent"
            return Workflow.END
        
        # Prepare input for the agent
        agent_input = f"Create outfit recommendations for: Budget: ${state.budget}, Occasion: {state.occasion or 'General'}, Time: {state.time or 'Any'}, Location: {state.location or 'Global'}"
        
        # Run the agent with structured output
        logger.info(f"Running style planner agent for budget: ${state.budget}")
        result = await agent.run(agent_input, expected_output=OutfitRecommendation)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.outfit_recommendation = result.output_structured  # type: ignore[assignment]
        else:
            # Fallback recommendation
            output_text: str = ""
            if result.output and len(result.output) > 0:
                last_message = result.output[-1]
                if hasattr(last_message, 'content'):
                    output_text = str(last_message.content)
                else:
                    output_text = str(last_message)
            
            state.outfit_recommendation = OutfitRecommendation(
                recommended_items=["AI-recommended items"],
                style_notes=output_text[:500] if output_text else "Personalized style recommendation",
                estimated_cost=state.budget if state.budget > 0 else 150,
                trend_alignment="AI-analyzed trend alignment"
            )
        
        # Generate output
        output = f"# Outfit Recommendation\n\n"
        output += f"## Budget: ${state.budget:.2f}\n"
        output += f"## Occasion: {state.occasion if state.occasion else 'General'}\n"
        output += f"## Time: {state.time if state.time else 'Any'}\n"
        output += f"## Location: {state.location if state.location else 'Global'}\n\n"
        
        if state.outfit_recommendation:
            output += f"## Recommended Items\n"
            for item in state.outfit_recommendation.recommended_items:
                output += f"- {item}\n"
            
            output += f"\n## Style Notes\n{state.outfit_recommendation.style_notes}\n"
            output += f"\n## Estimated Cost\n${state.outfit_recommendation.estimated_cost:.2f}\n"
            output += f"\n## Trend Alignment\n{state.outfit_recommendation.trend_alignment}\n"
        else:
            output += "No recommendation data available"
        
        state.final_output = output
        state.completed_steps.append("style_planner")
        
        logger.info(f"Style planner completed: ${state.budget:.2f} budget")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"Style planner step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


# ============================================================================
# WORKFLOW FACTORY
# ============================================================================

def create_outfit_analysis_workflow() -> Workflow:
    """Create Outfit Analysis workflow."""
    workflow = Workflow(FashionWorkflowState)
    
    workflow.add_step("outfit_descriptor", outfit_descriptor_step)
    workflow.add_step("outfit_analyzer", outfit_analyzer_step)
    
    return workflow


def create_trend_analysis_workflow() -> Workflow:
    """Create Trend Analysis workflow."""
    workflow = Workflow(FashionWorkflowState)
    
    workflow.add_step("style_trend_analyzer", style_trend_analyzer_step)
    
    return workflow


def create_outfit_recommendation_workflow() -> Workflow:
    """Create Outfit Recommendation workflow."""
    workflow = Workflow(FashionWorkflowState)
    
    workflow.add_step("style_planner", style_planner_step)
    
    return workflow


def create_fashion_workflows() -> Dict[str, Workflow]:
    """Create all fashion domain workflows."""
    return {
        "analyze": create_outfit_analysis_workflow(),
        "trends": create_trend_analysis_workflow(),
        "recommend": create_outfit_recommendation_workflow()
    }


# ============================================================================
# WORKFLOW EXECUTOR
# ============================================================================

class FashionWorkflowExecutor:
    """Executor for fashion domain workflows."""
    
    def __init__(self):
        self.workflows = create_fashion_workflows()
    
    async def execute_workflow(self, state: FashionWorkflowState) -> Any:
        """Execute the appropriate workflow based on input."""
        try:
            # Determine workflow type from state
            if state.image_description:
                workflow_type = "analyze"
            elif state.query and not state.budget:
                workflow_type = "trends"
            elif state.budget > 0 or state.occasion:
                workflow_type = "recommend"
            else:
                workflow_type = "trends"  # Default to trends
            
            workflow = self.workflows.get(workflow_type)
            
            if not workflow:
                state.error = f"Unknown workflow type: {workflow_type}"
                return state
            
            # Run workflow - workflow.run() returns WorkflowRun, access .state for actual state
            workflow_run = await workflow.run(state)
            return workflow_run.state
            
        except Exception as e:
            state.error = f"Workflow execution failed: {str(e)}"
            logger.error(state.error)
            return state


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # State models
    "FashionWorkflowState", "OutfitAnalysis", "StyleTrend", "OutfitRecommendation",
    # Workflow steps
    "outfit_descriptor_step", "outfit_analyzer_step",
    "style_trend_analyzer_step", "style_planner_step",
    # Workflow factory
    "create_outfit_analysis_workflow", "create_trend_analysis_workflow",
    "create_outfit_recommendation_workflow", "create_fashion_workflows",
    # Executor
    "FashionWorkflowExecutor"
]
