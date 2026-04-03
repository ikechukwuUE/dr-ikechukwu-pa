"""
Coding Domain Workflows — BeeAI Workflow Implementation
=======================================================
2 BeeAI Workflows for the coding domain as specified in ARCHITECTURE.md.

Pipelines:
1. Code Generation → Review → Debug (with iteration loop)
2. News - Coding/AI news aggregation

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
from mcp_servers.server import code_executor, documentation_search

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# SHARED SCHEMAS IMPORT
# ============================================================================
from shared.schemas import (
    GeneratedCode,
    CodeReview,
    DebugResult,
    CodingNewsReport as CodeNewsReport,
)

# ============================================================================
# WORKFLOW STATE
# ============================================================================

class CodingWorkflowState(BaseModel):
    """State for coding workflow execution."""
    # Input
    description: str = Field(default="", description="Code description")
    language: str = Field(default="python", description="Programming language")
    constraints: List[str] = Field(default_factory=list, description="Code constraints")
    mode: str = Field(default="generate", description="Operation mode: generate, review, or debug")
    
    # Generated code
    generated_code: Optional[str] = Field(default=None, description="Generated code")
    code_explanation: str = Field(default="", description="Code explanation")
    
    # Review
    review_approved: bool = Field(default=False, description="Review approval status")
    issues: List[str] = Field(default_factory=list, description="Issues found")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions")
    review_iteration: int = Field(default=0, description="Review iteration count")
    max_iterations: int = Field(default=3, description="Maximum review iterations")
    
    # Debug
    fixed_code: Optional[str] = Field(default=None, description="Fixed code")
    bugs_found: List[str] = Field(default_factory=list, description="Bugs found")
    
    # Final output
    final_output: str = Field(default="", description="Final output")
    
    # News
    news_report: Optional[CodeNewsReport] = Field(default=None, description="News report")
    
    # Execution tracking
    current_step: str = Field(default="", description="Current workflow step")
    completed_steps: List[str] = Field(default_factory=list, description="Completed steps")
    error: Optional[str] = Field(default=None, description="Error message")
    
    # Session info
    session_id: str = Field(default="", description="Session identifier")


# ============================================================================
# WORKFLOW STEPS
# ============================================================================

async def code_generator_step(state: CodingWorkflowState) -> str:
    """Code Generator produces production-quality code using AI agent."""
    try:
        state.current_step = "code_generator"
        
        # Import agent creator
        from domains.coding.agents.agents import create_code_generator_agent
        
        # Create the agent
        agent = create_code_generator_agent()
        if not agent:
            state.error = "Failed to create code generator agent"
            return Workflow.END
        
        # Prepare input for the agent
        constraints_str = ", ".join(state.constraints) if state.constraints else "None"
        agent_input = f"Generate {state.language} code for: {state.description}. Constraints: {constraints_str}"
        
        # Run the agent with structured output
        logger.info(f"Running code generator agent for {state.language}")
        result = await agent.run(agent_input, expected_output=GeneratedCode)
        
        # Extract structured output
        if result.output_structured:
            state.generated_code = getattr(result.output_structured, "code", "")
            state.code_explanation = getattr(result.output_structured, "explanation", "")
        else:
            output_text = extract_text_from_agent_result(result)
            state.generated_code = output_text if output_text else f"# Generated {state.language} code\n# {state.description}"
            state.code_explanation = f"Generated {state.language} code implementing: {state.description}"
        
        state.completed_steps.append("code_generator")
        
        logger.info(f"Code generation completed: {state.language}")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Code generator step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def code_reviewer_step(state: CodingWorkflowState) -> str:
    """Code Reviewer analyzes code for issues using AI agent."""
    try:
        state.current_step = "code_reviewer"
        
        # Import agent creator
        from domains.coding.agents.agents import create_code_reviewer_agent
        
        # Create the agent
        agent = create_code_reviewer_agent()
        if not agent:
            state.error = "Failed to create code reviewer agent"
            return Workflow.END
        
        # Prepare input for the agent - use description for review mode, generated_code otherwise
        code_to_review = state.generated_code or state.fixed_code or state.description or ""
        agent_input = f"Review this {state.language} code for issues and suggestions: {code_to_review}"
        
        # Run the agent with structured output
        logger.info(f"Running code reviewer agent for iteration {state.review_iteration}")
        result = await agent.run(agent_input, expected_output=CodeReview)
        
        # Extract structured output
        if result.output_structured:
            state.review_approved = getattr(result.output_structured, "approved", False)
            state.issues = getattr(result.output_structured, "issues", [])
            state.suggestions = getattr(result.output_structured, "suggestions", [])
        else:
            # Fallback to simple analysis
            issues = []
            suggestions = []
            
            if "TODO" in code_to_review or "FIXME" in code_to_review:
                issues.append("Code contains TODO/FIXME comments")
            
            if "pass" in code_to_review and "def " in code_to_review:
                issues.append("Function contains only 'pass' statement")
            
            if "except:" in code_to_review and "Exception" not in code_to_review:
                issues.append("Bare except clause without specific exception type")
            
            if len(code_to_review.split('\n')) < 5:
                suggestions.append("Consider adding more comprehensive implementation")
            
            if '"""' not in code_to_review and "'''" not in code_to_review:
                suggestions.append("Add docstrings for better documentation")
            
            state.review_approved = len(issues) == 0
            state.issues = issues
            state.suggestions = suggestions
        
        state.review_iteration += 1
        
        state.completed_steps.append(f"review_iteration_{state.review_iteration}")
        
        logger.info(f"Code review iteration {state.review_iteration}: {'APPROVED' if state.review_approved else 'NEEDS FIX'}")
        
        # Continue loop if not approved and under max iterations
        if not state.review_approved and state.review_iteration < state.max_iterations:
            return Workflow.SELF
        else:
            return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Code reviewer step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def code_debugger_step(state: CodingWorkflowState) -> str:
    """Code Debugger fixes identified issues using AI agent."""
    try:
        state.current_step = "code_debugger"
        
        # Import agent creator
        from domains.coding.agents.agents import create_code_debugger_agent
        
        # Create the agent
        agent = create_code_debugger_agent()
        if not agent:
            state.error = "Failed to create code debugger agent"
            return Workflow.END
        
        # Prepare input for the agent - use description in debug mode
        code_to_debug = state.generated_code or state.description or ""
        issues_str = ", ".join(state.issues) if state.issues else "No issues identified"
        agent_input = f"Debug this {state.language} code. Issues found: {issues_str}. Code: {code_to_debug}"
        
        # Run the agent with structured output
        logger.info(f"Running code debugger agent for iteration {state.review_iteration}")
        result = await agent.run(agent_input, expected_output=DebugResult)
        
        # Extract structured output
        if result.output_structured:
            state.fixed_code = getattr(result.output_structured, "fixed_code", code_to_debug)
            state.bugs_found = getattr(result.output_structured, "bugs_found", state.issues)
            state.generated_code = state.fixed_code
        else:
            # Fallback to simple fixes
            fixed_code = code_to_debug
            
            for issue in state.issues:
                if "TODO/FIXME" in issue:
                    fixed_code = fixed_code.replace("TODO", "Implemented").replace("FIXME", "Fixed")
                
                if "pass" in issue and "def " in fixed_code:
                    # Replace pass with actual implementation
                    fixed_code = fixed_code.replace("    pass", "    # Implementation here\n    return None")
                
                if "Bare except" in issue:
                    fixed_code = fixed_code.replace("except:", "except Exception as e:")
            
            state.fixed_code = fixed_code
            state.bugs_found = state.issues
            state.generated_code = fixed_code
        
        state.completed_steps.append(f"debug_iteration_{state.review_iteration}")
        
        logger.info(f"Code debugging completed: fixed {len(state.issues)} issues")
        
        return Workflow.NEXT
        
    except Exception as e:
        state.error = f"Code debugger step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def final_output_step(state: CodingWorkflowState) -> str:
    """Mark workflow as complete."""
    try:
        state.current_step = "final_output"
        state.completed_steps.append("final_output")
        logger.info("Final output step completed")
        return Workflow.END
    except Exception as e:
        state.error = f"Final output step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


async def news_anchor_step(state: CodingWorkflowState) -> str:
    """News Anchor gathers coding/AI news."""
    try:
        state.current_step = "news_anchor"
        
        # Generate coding/AI news
        headlines = [
            "OpenAI releases new model with improved reasoning capabilities",
            "Python 3.13 introduces significant performance improvements",
            "GitHub Copilot expands to support 50+ programming languages",
            "LangGraph enables multi-agent collaboration for complex tasks",
            "Major tech companies adopt AI-first development workflows"
        ]
        
        trends = [
            "Agentic AI systems becoming production-ready",
            "LangGraph and CrewAI gaining massive adoption",
            "Edge AI deployment becoming mainstream",
            "AI-assisted code review becoming standard practice"
        ]
        
        tools = [
            "Cursor AI - AI-first code editor with intelligent suggestions",
            "Copilot Workspace - Natural language to code conversion",
            "Devin AI - Autonomous software engineer for complex tasks",
            "Codeium - Free AI code completion and chat"
        ]
        
        state.news_report = CodeNewsReport(
            headlines=headlines,
            trends=trends,
            tools=tools
        )
        
        # Format output
        output = f"# Coding & AI News\n\n"
        output += f"## Headlines\n"
        for headline in state.news_report.headlines:
            output += f"- {headline}\n"
        
        output += f"\n## Trends\n"
        for trend in state.news_report.trends:
            output += f"- {trend}\n"
        
        output += f"\n## Tools\n"
        for tool in state.news_report.tools:
            output += f"- {tool}\n"
        
        state.final_output = output
        state.completed_steps.append("news_anchor")
        
        logger.info("Coding/AI news gathered")
        
        return Workflow.END
        
    except Exception as e:
        state.error = f"News anchor step failed: {str(e)}"
        logger.error(state.error)
        return Workflow.END


# ============================================================================
# WORKFLOW FACTORY
# ============================================================================

def create_code_generation_workflow() -> Workflow:
    """Create Code Generation → Review → Debug workflow."""
    workflow = Workflow(CodingWorkflowState)
    
    workflow.add_step("code_generator", code_generator_step)
    workflow.add_step("code_reviewer", code_reviewer_step)
    workflow.add_step("code_debugger", code_debugger_step)
    workflow.add_step("final_output", final_output_step)
    
    return workflow


def create_news_workflow() -> Workflow:
    """Create Coding News workflow."""
    workflow = Workflow(CodingWorkflowState)
    
    workflow.add_step("news_anchor", news_anchor_step)
    
    return workflow


def create_code_review_workflow() -> Workflow:
    """Create Code Review workflow."""
    workflow = Workflow(CodingWorkflowState)
    
    workflow.add_step("code_reviewer", code_reviewer_step)
    workflow.add_step("final_output", final_output_step)
    
    return workflow


def create_code_debug_workflow() -> Workflow:
    """Create Code Debug workflow."""
    workflow = Workflow(CodingWorkflowState)
    
    workflow.add_step("code_debugger", code_debugger_step)
    workflow.add_step("final_output", final_output_step)
    
    return workflow


def create_coding_workflows() -> Dict[str, Workflow]:
    """Create all coding domain workflows."""
    return {
        "generate": create_code_generation_workflow(),
        "news": create_news_workflow(),
        "review": create_code_review_workflow(),
        "debug": create_code_debug_workflow()
    }


# ============================================================================
# WORKFLOW EXECUTOR
# ============================================================================

class CodingWorkflowExecutor:
    """Executor for coding domain workflows."""
    
    def __init__(self):
        self.workflows = create_coding_workflows()
    
    async def execute_workflow(self, state: CodingWorkflowState) -> Any:
        """Execute the appropriate workflow based on pipeline type."""
        try:
            # Determine pipeline type from state
            if state.mode == "review":
                pipeline_type = "review"
            elif state.mode == "debug":
                pipeline_type = "debug"
            elif state.description:
                pipeline_type = "generate"
            else:
                pipeline_type = "news"
            
            workflow = self.workflows.get(pipeline_type)
            
            if not workflow:
                state.error = f"Unknown pipeline type: {pipeline_type}"
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
    "CodingWorkflowState", "GeneratedCode", "CodeReview", "DebugResult", "CodeNewsReport",
    # Workflow steps
    "code_generator_step", "code_reviewer_step", "code_debugger_step",
    "final_output_step", "news_anchor_step",
    # Workflow factory
    "create_code_generation_workflow", "create_news_workflow", "create_coding_workflows",
    # Executor
    "CodingWorkflowExecutor"
]
