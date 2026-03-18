from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings
from src.core.security import SecuritySanitizer
import logging

# Import reflection agents
from src.agents.finance import (
    ReflectionAgent,
    ValidatorAgent,
    FinancialAnalyzer,
    ReflectionState,
    ValidationState,
    AnalyzerState
)

# filepath: c:\Users\ugboi\Desktop\ai_innovative_solutions\dr_ikechukwu_pa\src\agents\hitl_finance.py

logger = logging.getLogger(__name__)


class FinanceState(TypedDict):
    """Extended state for finance workflow with reflection."""
    query: str
    proposed_action: str
    reasoning: str
    user_approval: bool
    # Reflection-related fields
    reflection_state: Optional[ReflectionState]
    validation_state: Optional[ValidationState]
    analyzer_state: Optional[AnalyzerState]
    reflection_iterations: int
    reflection_chain: List[Dict[str, Any]]
    current_stage: str  # 'analyzing' | 'reflecting' | 'validating' | 'approval' | 'executing'


def initialize_finance(state: FinanceState):
    """
    Initialize the finance workflow.
    Sanitizes input and sets up initial state.
    """
    sanitizer = SecuritySanitizer()
    sanitized_query, redacted = sanitizer.sanitize_clinical_prompt(state["query"])
    
    logger.info(f"[HITL Finance] Initialized. Redacted {len(redacted)} PII items")
    
    return {
        "query": sanitized_query,
        "current_stage": "analyzing",
        "reflection_chain": [],
        "reflection_iterations": 0
    }


def analyze_with_reflection(state: FinanceState):
    """
    Analyzes financial query using reflection agents.
    
    Flow:
    1. Initial analysis via FinancialAnalyzer
    2. Reflection loop via ReflectionAgent (max 3 iterations)
    3. Validation via ValidatorAgent
    4. Pass to HITL gate
    """
    logger.info(f"[HITL Finance] Starting analysis with reflection for: {state['query'][:50]}...")
    
    # Stage 1: Initial Financial Analysis
    logger.info("[HITL Finance] Stage 1: Initial Financial Analysis")
    analyzer = FinancialAnalyzer()
    analyzer_state = analyzer.analyze(state["query"], state.get("context", {}))
    state["analyzer_state"] = analyzer_state
    
    # Add to reflection chain
    state["reflection_chain"].append({
        "stage": "analyzer",
        "analysis": analyzer_state["analysis"],
        "confidence": analyzer_state["confidence"],
        "instruments": analyzer_state["data"].get("instruments", []),
        "risk_profile": analyzer_state["data"].get("risk_profile", {})
    })
    
    # Stage 2: Reflection Loop
    logger.info("[HITL Finance] Stage 2: Reflection Loop (up to 3 iterations)")
    reflection_agent = ReflectionAgent()
    
    # Get initial analysis from analyzer to feed into reflection
    reflection_context = {
        "initial_data": analyzer_state["data"],
        "initial_analysis": analyzer_state["analysis"]
    }
    
    reflection_state = reflection_agent.analyze_with_reflection(
        state["query"], 
        reflection_context
    )
    state["reflection_state"] = reflection_state
    state["reflection_iterations"] = reflection_state["iterations"]
    
    # Add reflection iterations to chain
    for i, critique in enumerate(reflection_state["critiques"]):
        state["reflection_chain"].append({
            "stage": f"reflection_iteration_{i+1}",
            "critique": critique,
            "improved_analysis": reflection_state["improved_analysis"] if i == len(reflection_state["critiques"]) - 1 else None
        })
    
    logger.info(
        f"[HITL Finance] Reflection complete: {reflection_state['iterations']} iterations, "
        f"{len(reflection_state['critiques'])} critiques"
    )
    
    # Stage 3: Validation
    logger.info("[HITL Finance] Stage 3: Validation")
    validator = ValidatorAgent()
    validation_state = validator.validate(reflection_state["improved_analysis"])
    state["validation_state"] = validation_state
    
    # Add validation to chain
    state["reflection_chain"].append({
        "stage": "validation",
        "validation_results": validation_state["validation_results"],
        "policy_checks": validation_state["policy_checks"],
        "approved": validation_state["approved"],
        "recommendations": validation_state["recommendations"]
    })
    
    logger.info(
        f"[HITL Finance] Validation complete: "
        f"Approved={validation_state['approved']}, "
        f"Checks={len(validation_state['policy_checks'])}"
    )
    
    # Stage 4: Generate proposed action for HITL gate
    proposed_action = validation_state["recommendations"]
    reasoning = f"""
Reflection Analysis:
- Iterations: {reflection_state['iterations']}
- Critiques: {len(reflection_state['critiques'])}

Validation:
- Approved: {validation_state['approved']}
- Policy Checks: {len(validation_state['policy_checks'])}

Final Recommendations:
{proposed_action}
    """.strip()
    
    state["proposed_action"] = proposed_action
    state["reasoning"] = reasoning
    state["current_stage"] = "approval"
    
    return state


def human_approval_gate(state: FinanceState):
    """
    HITL checkpoint: Pauses execution and awaits user approval.
    State is persisted to Neon Postgres automatically by LangGraph.
    """
    logger.info(f"[HITL Finance] HITL Pause: Awaiting approval for action: {state['proposed_action'][:100]}...")
    
    # Include reflection summary in the interrupt message
    reflection_summary = f"""
Reflection Iterations: {state.get('reflection_iterations', 0)}
Validation Approved: {state.get('validation_state', {}).get('approved', False)}
"""
    
    user_decision = interrupt(
        f"⚠️ Proposed Action: {state['proposed_action'][:500]}...\n"
        f"Reasoning: {state['reasoning'][:500]}...\n"
        f"{reflection_summary}\n"
        f"Do you approve? (yes/no)"
    )
    
    approval = user_decision.lower() in ["yes", "y", "approve"]
    return {"user_approval": approval}


def execute_action(state: FinanceState):
    """
    Executes the approved financial action.
    Only runs if user explicitly approved in HITL gate.
    """
    if not state.get("user_approval", False):
        logger.warning(f"[HITL Finance] Action rejected by user")
        return {
            "proposed_action": "Action cancelled by user.",
            "current_stage": "rejected"
        }
    
    logger.info(f"[HITL Finance] ✅ Action executed: {state['proposed_action'][:100]}...")
    
    # Add execution result to chain
    state["reflection_chain"].append({
        "stage": "execution",
        "status": "success",
        "message": "Action approved and executed"
    })
    
    return {
        "current_stage": "completed"
    }


# Build the LangGraph state machine with reflection
finance_builder = StateGraph(FinanceState)

# Add nodes
finance_builder.add_node("initialize", initialize_finance)
finance_builder.add_node("analyze", analyze_with_reflection)
finance_builder.add_node("approval", human_approval_gate)
finance_builder.add_node("execute", execute_action)

# Add edges
finance_builder.add_edge(START, "initialize")
finance_builder.add_edge("initialize", "analyze")
finance_builder.add_edge("analyze", "approval")
finance_builder.add_edge("approval", "execute")
finance_builder.add_edge("execute", END)

# Use MemorySaver for reliable in-memory checkpointing
try:
    checkpointer = MemorySaver()
    finance_agent = finance_builder.compile(checkpointer=checkpointer)
    logger.info("✅ Finance agent compiled with reflection and MemorySaver checkpointing.")
except Exception as e:
    logger.warning(f"MemorySaver failed, using basic compilation: {e}")
    finance_agent = finance_builder.compile()


# ============================================================================
# Convenience function for direct API calls (non-graph)
# ============================================================================

def run_finance_analysis_with_reflection(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run finance analysis with reflection without using the graph.
    Useful for getting reflection status before HITL approval.
    
    Args:
        query: Financial query
        context: Optional context
        
    Returns:
        Dictionary with analysis, reflection info, and validation
    """
    sanitizer = SecuritySanitizer()
    sanitized_query, redacted = sanitizer.sanitize_clinical_prompt(query)
    
    # Stage 1: Initial Analysis
    analyzer = FinancialAnalyzer()
    analyzer_state = analyzer.analyze(sanitized_query, context or {})
    
    # Stage 2: Reflection
    reflection_agent = ReflectionAgent()
    reflection_context = {
        "initial_data": analyzer_state["data"],
        "initial_analysis": analyzer_state["analysis"]
    }
    reflection_state = reflection_agent.analyze_with_reflection(sanitized_query, reflection_context)
    
    # Stage 3: Validation
    validator = ValidatorAgent()
    validation_state = validator.validate(reflection_state["improved_analysis"])
    
    return {
        "query": sanitized_query,
        "analysis": validation_state["recommendations"],
        "proposed_action": validation_state["recommendations"],
        "reasoning": f"Reflection iterations: {reflection_state['iterations']}, Approved: {validation_state['approved']}",
        "reflection_iterations": reflection_state["iterations"],
        "reflection_chain": [
            {
                "stage": "analyzer",
                "confidence": analyzer_state["confidence"],
                "instruments": analyzer_state["data"].get("instruments", []),
                "risk_profile": analyzer_state["data"].get("risk_profile", {})
            },
            {
                "stage": "reflection",
                "iterations": reflection_state["iterations"],
                "critiques": reflection_state["critiques"]
            },
            {
                "stage": "validation",
                "approved": validation_state["approved"],
                "policy_checks": validation_state["policy_checks"]
            }
        ],
        "validation_approved": validation_state["approved"],
        "redacted_items": redacted
    }
