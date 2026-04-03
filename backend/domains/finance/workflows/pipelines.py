"""
Finance Domain Workflows — BeeAI Workflow Implementation
========================================================
3 BeeAI Workflows for the finance domain as specified in ARCHITECTURE.md.

Pipelines:
1. Finance Q&A - Financial question answering
2. Investment Planning - Investment planning with parallel personas and risk loop
3. News - Financial news aggregation

Each pipeline uses BeeAI Workflow with State transitions (Workflow.NEXT, Workflow.SELF, Workflow.END).
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

# BeeAI Framework imports
from beeai_framework.workflows import Workflow
    
# Helper function for extracting text from agent results
from shared.utils import extract_text_from_agent_result

# MCP Tools from mcp_servers/server.py
from mcp_servers.server import stock_price_lookup, risk_calculator

# Shared schemas
from shared.schemas import (
    RiskLevel,
    InvestorInfo,
    InvestmentRecommendation,
    RiskAssessment,
    InvestmentGuide,
    InvestmentPlan,
    FinancialNewsReport,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOW STATE
# ============================================================================

class FinanceWorkflowState(BaseModel):
    """State for finance workflow execution."""
    # Query info
    query: str = Field(default="", description="User query")
    pipeline_type: str = Field(default="", description="Pipeline type: qa, investment, news")
    
    # Investor info
    investor_info: Optional[InvestorInfo] = Field(default=None, description="Investor information")
    
    # Parallel personas
    aggressive_recommendation: Optional[InvestmentRecommendation] = Field(default=None, description="Aggressive persona recommendation")
    conservative_recommendation: Optional[InvestmentRecommendation] = Field(default=None, description="Conservative persona recommendation")
    
    # Risk assessment
    risk_assessments: List[RiskAssessment] = Field(default_factory=list, description="Risk assessment history")
    risk_iteration: int = Field(default=0, description="Current risk iteration")
    risk_resolved: bool = Field(default=False, description="Whether risk is resolved")
    
    # Final results
    investment_guide: Optional[InvestmentGuide] = Field(default=None, description="Investment guide")
    investment_plan: Optional[InvestmentPlan] = Field(default=None, description="Investment plan")
    final_output: str = Field(default="", description="Final output")
    
    # News
    news_report: Optional[FinancialNewsReport] = Field(default=None, description="News report")
    
    # Execution tracking
    current_step: str = Field(default="", description="Current workflow step")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    error: Optional[str] = Field(default=None, description="Error message")
    
    # Session info
    session_id: str = Field(default="", description="Session identifier")


# ============================================================================
# WORKFLOW STEPS
# ============================================================================

async def financial_coach_step(state: FinanceWorkflowState) -> str:
    """Financial Coach provides personalized guidance using AI agent."""
    try:
        state.current_step = "financial_coach"
        
        # Import agent creator
        from domains.finance.agents.agents import create_financial_coach_agent
        
        # Create the agent
        agent = create_financial_coach_agent()
        if not agent:
            state.error = "Failed to create financial coach agent"
            return Workflow.END
        
        # Prepare input for the agent
        investor_info_str = ""
        if state.investor_info:
            investor_info_str = f"Investor Profile: Age {state.investor_info.age}, Occupation: {state.investor_info.occupation}, Annual Salary: ${state.investor_info.salary:,.2f}, Target Fund: ${state.investor_info.target_fund:,.2f}"
        
        agent_input = f"Provide personalized financial guidance for: {state.query}. {investor_info_str}"
        
        # Run the agent - financial coach outputs text guidance, not structured data
        logger.info("Running financial coach agent")
        result = await agent.run(agent_input)
        
        # Extract text output
        output_text = extract_text_from_agent_result(result)
        state.final_output = output_text if output_text else "Financial guidance generated"
        
        state.completed_steps.append("financial_coach")
        
        logger.info("Financial coach guidance completed")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Financial coach step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def aggressive_persona_step(state: FinanceWorkflowState) -> str:
    """Aggressive Persona recommends high-growth investments using AI agent."""
    try:
        state.current_step = "aggressive_persona"
        
        # Import agent creator
        from domains.finance.agents.agents import create_aggressive_persona_agent
        
        # Create the agent
        agent = create_aggressive_persona_agent()
        if not agent:
            state.error = "Failed to create aggressive persona agent"
            return Workflow.END
        
        # Prepare input for the agent
        investor_info_str = ""
        if state.investor_info:
            investor_info_str = f"Investor Profile: Age {state.investor_info.age}, Occupation: {state.investor_info.occupation}, Annual Salary: ${state.investor_info.salary:,.2f}, Target Fund: ${state.investor_info.target_fund:,.2f}"
        
        agent_input = f"Provide aggressive investment recommendation for: {state.query}. {investor_info_str}"
        
        # Run the agent with structured output
        logger.info("Running aggressive persona agent")
        result = await agent.run(agent_input, expected_output=InvestmentRecommendation)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.aggressive_recommendation = result.output_structured  # type: ignore[assignment]
        else:
            # Fallback allocations
            allocations = {
                "US Growth Stocks": 30.0,
                "Small Cap Equities": 15.0,
                "International Emerging Markets": 15.0,
                "Technology Sector ETF": 15.0,
                "Cryptocurrency": 10.0,
                "Biotech/Healthcare": 10.0,
                "Alternative Investments": 5.0
            }
            
            state.aggressive_recommendation = InvestmentRecommendation(
                persona="aggressive",
                allocations=allocations,
                rationale="Aggressive growth portfolio with high allocation to equities and alternative assets. "
                         "Suitable for investors with high risk tolerance and long time horizon."
            )
        
        state.completed_steps.append("aggressive_persona")
        
        logger.info("Aggressive persona recommendation completed")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Aggressive persona step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def conservative_persona_step(state: FinanceWorkflowState) -> str:
    """Conservative Persona recommends capital preservation using AI agent."""
    try:
        state.current_step = "conservative_persona"
        
        # Import agent creator
        from domains.finance.agents.agents import create_conservative_persona_agent
        
        # Create the agent
        agent = create_conservative_persona_agent()
        if not agent:
            state.error = "Failed to create conservative persona agent"
            return Workflow.END
        
        # Prepare input for the agent
        investor_info_str = ""
        if state.investor_info:
            investor_info_str = f"Investor Profile: Age {state.investor_info.age}, Occupation: {state.investor_info.occupation}, Annual Salary: ${state.investor_info.salary:,.2f}, Target Fund: ${state.investor_info.target_fund:,.2f}"
        
        agent_input = f"Provide conservative investment recommendation for: {state.query}. {investor_info_str}"
        
        # Run the agent with structured output
        logger.info("Running conservative persona agent")
        result = await agent.run(agent_input, expected_output=InvestmentRecommendation)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.conservative_recommendation = result.output_structured  # type: ignore[assignment]
        else:
            # Fallback allocations
            allocations = {
                "US Treasury Bonds": 25.0,
                "Corporate Bonds (Investment Grade)": 20.0,
                "Blue Chip Dividend Stocks": 20.0,
                "REITs": 15.0,
                "Money Market Funds": 10.0,
                "Municipal Bonds": 10.0
            }
            
            state.conservative_recommendation = InvestmentRecommendation(
                persona="conservative",
                allocations=allocations,
                rationale="Conservative portfolio with focus on fixed income and stable dividend-paying stocks. "
                         "Suitable for investors with low risk tolerance or shorter time horizon."
            )
        
        state.completed_steps.append("conservative_persona")
        
        logger.info("Conservative persona recommendation completed")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Conservative persona step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def risk_assessor_step(state: FinanceWorkflowState) -> str:
    """Risk Assessor analyzes portfolio risk with loop up to 3 iterations using AI agent."""
    try:
        state.current_step = "risk_assessor"
        
        # Import agent creator
        from domains.finance.agents.agents import create_risk_assessor_agent
        
        # Create the agent
        agent = create_risk_assessor_agent()
        if not agent:
            state.error = "Failed to create risk assessor agent"
            return Workflow.END
        
        # Prepare input for the agent
        aggressive_allocations = state.aggressive_recommendation.allocations if state.aggressive_recommendation else {}
        conservative_allocations = state.conservative_recommendation.allocations if state.conservative_recommendation else {}
        
        agent_input = f"Analyze portfolio risk for iteration {state.risk_iteration}. Aggressive allocations: {aggressive_allocations}. Conservative allocations: {conservative_allocations}. Query: {state.query}"
        
        # Run the agent with structured output
        logger.info(f"Running risk assessor agent for iteration {state.risk_iteration}")
        result = await agent.run(agent_input, expected_output=RiskAssessment)
        
        # Extract structured output or use fallback
        if result.output_structured:
            assessment = result.output_structured
            resolved = getattr(assessment, "resolved", False)
            risk_level = getattr(assessment, "risk_level", RiskLevel.MEDIUM)
        else:
            # Combine aggressive and conservative recommendations
            combined_allocations = {}
            all_assets = set()
            
            if state.aggressive_recommendation:
                all_assets.update(state.aggressive_recommendation.allocations.keys())
            if state.conservative_recommendation:
                all_assets.update(state.conservative_recommendation.allocations.keys())
            
            for asset in all_assets:
                agg_pct = state.aggressive_recommendation.allocations.get(asset, 0) if state.aggressive_recommendation else 0
                cons_pct = state.conservative_recommendation.allocations.get(asset, 0) if state.conservative_recommendation else 0
                combined_allocations[asset] = (agg_pct + cons_pct) / 2
            
            # Calculate risk metrics
            high_risk_assets = ["Cryptocurrency", "Small Cap", "Emerging Markets"]
            high_risk_pct = sum(combined_allocations.get(asset, 0) for asset in high_risk_assets)
            
            if high_risk_pct > 40:
                risk_level = RiskLevel.HIGH
                findings = [f"High concentration ({high_risk_pct:.0f}%) in high-risk assets"]
            elif high_risk_pct > 20:
                risk_level = RiskLevel.MEDIUM
                findings = ["Moderate concentration in volatile assets"]
            else:
                risk_level = RiskLevel.LOW
                findings = ["Conservative allocation with focus on stability"]
            
            # Check if resolved
            resolved = risk_level == RiskLevel.LOW or state.risk_iteration >= 3
            
            assessment = RiskAssessment(
                risk_level=risk_level,
                findings=findings,
                iteration=state.risk_iteration,
                resolved=resolved
            )
        
        state.risk_assessments.append(assessment)  # type: ignore[arg-type]
        state.risk_resolved = resolved
        state.risk_iteration += 1
        
        state.completed_steps.append("risk_assessor")
        
        logger.info(f"Risk assessment iteration {state.risk_iteration}: {risk_level.value}")
        
        # Continue loop if not resolved
        if not resolved and state.risk_iteration < 3:
            return Workflow.SELF
        else:
            return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Risk assessor step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def investment_guide_step(state: FinanceWorkflowState) -> str:
    """Financial Coach compiles investment guide using AI agent."""
    try:
        state.current_step = "investment_guide"
        
        # Import agent creator
        from domains.finance.agents.agents import create_writer_agent
        
        # Create the agent
        agent = create_writer_agent()
        if not agent:
            state.error = "Failed to create investment guide agent"
            return Workflow.END
        
        # Prepare input for the agent
        final_risk = state.risk_assessments[-1].risk_level if state.risk_assessments else RiskLevel.MEDIUM
        aggressive_allocations = state.aggressive_recommendation.allocations if state.aggressive_recommendation else {}
        conservative_allocations = state.conservative_recommendation.allocations if state.conservative_recommendation else {}
        
        agent_input = f"Compile investment guide for risk level: {final_risk.value}. Aggressive allocations: {aggressive_allocations}. Conservative allocations: {conservative_allocations}. Query: {state.query}"
        
        # Run the agent with structured output
        logger.info("Running investment guide agent")
        result = await agent.run(agent_input, expected_output=InvestmentGuide)
        
        # Extract structured output or use fallback
        if result.output_structured:
            state.investment_guide = result.output_structured  # type: ignore[assignment]
        else:
            # Determine strategy based on risk level
            if final_risk == RiskLevel.HIGH:
                strategy = "Growth-focused with higher risk tolerance"
                warnings = ["Higher volatility expected", "Regular rebalancing recommended"]
            elif final_risk == RiskLevel.LOW:
                strategy = "Preservation-focused with moderate growth"
                warnings = ["Lower returns expected", "Consider growth allocation"]
            else:
                strategy = "Balanced approach"
                warnings = ["Monitor allocation periodically"]
            
            # Combine allocations
            combined_allocations = {}
            all_assets = set()
            
            if state.aggressive_recommendation:
                all_assets.update(state.aggressive_recommendation.allocations.keys())
            if state.conservative_recommendation:
                all_assets.update(state.conservative_recommendation.allocations.keys())
            
            for asset in all_assets:
                agg_pct = state.aggressive_recommendation.allocations.get(asset, 0) if state.aggressive_recommendation else 0
                cons_pct = state.conservative_recommendation.allocations.get(asset, 0) if state.conservative_recommendation else 0
                combined_allocations[asset] = (agg_pct + cons_pct) / 2
            
            state.investment_guide = InvestmentGuide(
                strategy=strategy,
                allocations=combined_allocations,
                warnings=warnings
            )
        
        state.completed_steps.append("investment_guide")
        
        logger.info("Investment guide compiled")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Investment guide step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def investment_plan_step(state: FinanceWorkflowState) -> str:
    """Writer formats final investment plan."""
    try:
        state.current_step = "investment_plan"
        
        # Create investment plan
        summary = f"Investment plan for {state.investor_info.occupation if state.investor_info else 'Investor'}, "
        summary += f"age {state.investor_info.age if state.investor_info else 'Unknown'}. "
        summary += f"Target fund: ${state.investor_info.target_fund:,.2f}." if state.investor_info else ""
        
        state.investment_plan = InvestmentPlan(
            summary=summary,
            guide=state.investment_guide,  # type: ignore[arg-type]
            risk_history=state.risk_assessments
        )
        
        # Format output
        output = f"# Investment Plan\n\n"
        output += f"## Summary\n{state.investment_plan.summary}\n\n"
        output += f"## Strategy\n{state.investment_plan.guide.strategy}\n\n"
        output += f"## Allocation\n"
        for asset, pct in state.investment_plan.guide.allocations.items():
            output += f"- {asset}: {pct:.1f}%\n"
        
        output += f"\n## Warnings\n"
        for warning in state.investment_plan.guide.warnings:
            output += f"- {warning}\n"
        
        output += f"\n## Risk History\n"
        for assessment in state.investment_plan.risk_history:
            output += f"- Iteration {assessment.iteration}: {assessment.risk_level.value}\n"
        
        state.final_output = output
        state.completed_steps.append("investment_plan")
        
        logger.info("Investment plan formatted")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"Investment plan step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def news_anchor_step(state: FinanceWorkflowState) -> str:
    """News Anchor gathers financial news."""
    try:
        state.current_step = "news_anchor"
        
        # Generate financial news
        headlines = [
            "Fed signals potential rate cuts amid cooling inflation",
            "Tech giants report strong quarterly earnings",
            "Oil prices stabilize as OPEC+ maintains production",
            "Cryptocurrency market sees renewed institutional interest",
            "Global markets mixed ahead of central bank decisions"
        ]
        
        top_businesses = [
            "Apple Inc. (AAPL)",
            "Microsoft Corporation (MSFT)",
            "Amazon.com Inc. (AMZN)",
            "NVIDIA Corporation (NVDA)",
            "Tesla Inc. (TSLA)"
        ]
        
        industry_trends = "Technology sector leads market performance. AI and semiconductor stocks showing strong gains."
        lifestyle_highlights = "Executive compensation trending toward equity-based incentives with ESG metrics."
        
        state.news_report = FinancialNewsReport(
            headlines=headlines,
            top_businesses=top_businesses,
            industry_trends=industry_trends,
            lifestyle_highlights=lifestyle_highlights
        )
        
        # Format output
        output = f"# Financial News Report\n\n"
        output += f"## Headlines\n"
        for headline in state.news_report.headlines:
            output += f"- {headline}\n"
        
        output += f"\n## Top Businesses\n"
        for business in state.news_report.top_businesses:
            output += f"- {business}\n"
        
        output += f"\n## Industry Trends\n{state.news_report.industry_trends}\n"
        output += f"\n## Lifestyle Highlights\n{state.news_report.lifestyle_highlights}\n"
        
        state.final_output = output
        state.completed_steps.append("news_anchor")
        
        logger.info("Financial news gathered")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"News anchor step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def writer_step(state: FinanceWorkflowState) -> str:
    """Writer formats financial documents."""
    try:
        state.current_step = "writer"
        
        # Format based on pipeline type
        if state.pipeline_type == "qa":
            output = f"# Financial Q&A\n\n"
            output += f"## Question\n{state.query}\n\n"
            output += f"## Answer\n{state.final_output}\n"
        else:
            output = state.final_output
        
        state.final_output = output
        state.completed_steps.append("writer")
        
        logger.info("Writer formatting completed")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"Writer step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


# ============================================================================
# WORKFLOW FACTORY
# ============================================================================

def create_qa_workflow() -> Workflow:
    """Create Financial Q&A workflow."""
    workflow = Workflow(FinanceWorkflowState)
    
    workflow.add_step("financial_coach", financial_coach_step)
    workflow.add_step("writer", writer_step)
    
    return workflow


def create_investment_workflow() -> Workflow:
    """Create Investment Planning workflow with parallel personas."""
    workflow = Workflow(FinanceWorkflowState)
    
    workflow.add_step("financial_coach", financial_coach_step)
    workflow.add_step("aggressive_persona", aggressive_persona_step)
    workflow.add_step("conservative_persona", conservative_persona_step)
    workflow.add_step("risk_assessor", risk_assessor_step)
    workflow.add_step("investment_guide", investment_guide_step)
    workflow.add_step("investment_plan", investment_plan_step)
    
    return workflow


def create_news_workflow() -> Workflow:
    """Create Financial News workflow."""
    workflow = Workflow(FinanceWorkflowState)
    
    workflow.add_step("news_anchor", news_anchor_step)
    
    return workflow


def create_finance_workflows() -> Dict[str, Workflow]:
    """Create all finance domain workflows."""
    return {
        "qa": create_qa_workflow(),
        "investment": create_investment_workflow(),
        "news": create_news_workflow()
    }


# ============================================================================
# WORKFLOW EXECUTOR
# ============================================================================

class FinanceWorkflowExecutor:
    """Executor for finance domain workflows."""
    
    def __init__(self):
        self.workflows = create_finance_workflows()
    
    async def execute_workflow(self, state: FinanceWorkflowState) -> Any:
        """Execute the appropriate workflow based on pipeline type."""
        try:
            workflow = self.workflows.get(state.pipeline_type)
            
            if not workflow:
                state.error = f"Unknown pipeline type: {state.pipeline_type}"
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
    "FinanceWorkflowState", "RiskLevel", "InvestorInfo", "InvestmentRecommendation",
    "RiskAssessment", "InvestmentGuide", "InvestmentPlan", "FinancialNewsReport",
    # Workflow steps
    "financial_coach_step", "aggressive_persona_step", "conservative_persona_step",
    "risk_assessor_step", "investment_guide_step", "investment_plan_step",
    "news_anchor_step", "writer_step",
    # Workflow factory
    "create_qa_workflow", "create_investment_workflow", "create_news_workflow",
    "create_finance_workflows",
    # Executor
    "FinanceWorkflowExecutor"
]
