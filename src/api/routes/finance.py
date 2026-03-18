"""
Finance/Wealth Management Blueprint (Human-in-the-Loop)
Route: /finance
Integrates financial datasets MCP + HITL approval for investment decisions.
Pattern: Query → Analysis → Reflection Loop → Validation → Approval Pause → Execute
"""
from flask import Blueprint, request, jsonify
import logging

from src.core.config import settings
from src.core.security import SecuritySanitizer
from src.agents.hitl_finance import (
    finance_agent, 
    FinanceState, 
    run_finance_analysis_with_reflection
)

logger = logging.getLogger(__name__)

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

# ============================================================================
# Initialize Sanitizer
# ============================================================================
sanitizer = SecuritySanitizer()

# ============================================================================
# In-Memory Thread Store (Phase 2: Replace with Postgres)
# ============================================================================
# Temporary storage for HITL thread state
active_threads = {}

# Store for reflection-only queries (before HITL)
reflection_cache = {}


# ============================================================================
# POST /finance/query - Analyze Financial Scenario
# ============================================================================
@finance_bp.route("/query", methods=["POST"])
def analyze_finance():
    """
    Analyze financial scenario and propose action.
    Uses reflection loop for self-critique before HITL approval.
    Pauses for human approval before execution.
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        thread_id = data.get("thread_id", "default-finance-session")
        use_reflection = data.get("use_reflection", True)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        logger.info(f"[FINANCE] Analyzing query from thread {thread_id}, reflection={use_reflection}")
        
        # Sanitize query
        safe_query, redacted_items = sanitizer.sanitize_clinical_prompt(query)
        logger.info(f"[FINANCE] Sanitized {len(redacted_items)} PII items")
        
        if use_reflection:
            # Use the reflection-based analysis (non-graph version for direct response)
            result = run_finance_analysis_with_reflection(safe_query)
            
            # Store for later resumption
            active_threads[thread_id] = {
                "state": {
                    "query": safe_query,
                    "proposed_action": result.get("proposed_action", ""),
                    "reasoning": result.get("reasoning", ""),
                    "user_approval": False,
                    "reflection_state": None,
                    "validation_state": None,
                    "analyzer_state": None,
                    "reflection_iterations": result.get("reflection_iterations", 0),
                    "reflection_chain": result.get("reflection_chain", []),
                    "current_stage": "pending_approval"
                },
                "status": "pending_approval",
                "reflection_data": result
            }
            
            logger.info(f"[FINANCE] Analysis complete with reflection, awaiting approval for thread {thread_id}")
            
            return jsonify({
                "status": "pending_approval",
                "proposed_action": result.get("proposed_action", ""),
                "reasoning": result.get("reasoning", ""),
                "thread_id": thread_id,
                "reflection_iterations": result.get("reflection_iterations", 0),
                "reflection_chain": result.get("reflection_chain", []),
                "validation_approved": result.get("validation_approved", False),
                "metadata": {
                    "message": "⚠️ Please review proposed action and approve or reject via /finance/approve",
                    "stages_completed": ["analysis", "reflection", "validation"]
                }
            })
        else:
            # Use legacy non-reflection approach (backward compatibility)
            state: FinanceState = {
                "query": safe_query,
                "proposed_action": "",
                "reasoning": "",
                "user_approval": False,
                "reflection_state": None,
                "validation_state": None,
                "analyzer_state": None,
                "reflection_iterations": 0,
                "reflection_chain": [],
                "current_stage": "analyzing"
            }
            
            # Invoke finance agent (will pause at HITL gate)
            result = finance_agent.invoke(state)
            
            # Store state for later resumption
            active_threads[thread_id] = {
                "state": result,
                "status": "pending_approval"
            }
            
            logger.info(f"[FINANCE] Legacy analysis paused, awaiting approval for thread {thread_id}")
            
            return jsonify({
                "status": "pending_approval",
                "proposed_action": result.get("proposed_action", ""),
                "reasoning": result.get("reasoning", ""),
                "thread_id": thread_id,
                "metadata": {
                    "message": "⚠️ Please review proposed action and approve or reject via /finance/approve"
                }
            })
    
    except Exception as e:
        logger.error(f"[FINANCE] Analysis error: {str(e)}")
        return jsonify({"error": f"Finance analysis failed: {str(e)}"}), 500


# ============================================================================
# POST /finance/approve - Human Approval Decision
# ============================================================================
@finance_bp.route("/approve", methods=["POST"])
def approve_finance():
    """
    Resume HITL flow with user's approval decision.
    """
    try:
        data = request.get_json(silent=True) or {}
        thread_id = data.get("thread_id")
        decision = data.get("decision", "")

        if not thread_id:
            return jsonify({"error": "thread_id is required"}), 400

        logger.info(f"[FINANCE] Processing approval for thread {thread_id}: {decision}")
        
        # Validate thread exists
        if thread_id not in active_threads:
            return jsonify({"error": f"Thread {thread_id} not found"}), 404
        
        thread_data = active_threads[thread_id]
        state = thread_data["state"]
        
        # Parse approval decision
        if decision.lower() in ["approve", "yes", "y"]:
            state["user_approval"] = True
            logger.info(f"[FINANCE] Approval GRANTED for thread {thread_id}")
        else:
            state["user_approval"] = False
            logger.info(f"[FINANCE] Approval REJECTED for thread {thread_id}")
        
        # Resume graph execution (for legacy mode)
        if "current_stage" not in state or state.get("current_stage") == "analyzing":
            final_result = finance_agent.invoke(state)
        else:
            final_result = state
        
        # Clean up thread
        del active_threads[thread_id]
        
        status = "approved_and_executed" if state["user_approval"] else "rejected"
        
        return jsonify({
            "status": status,
            "result": final_result.get("proposed_action", "No action taken"),
            "metadata": {
                "thread_id": thread_id,
                "user_approval": state["user_approval"]
            }
        })
    
    except Exception as e:
        logger.error(f"[FINANCE] Approval error: {str(e)}")
        return jsonify({"error": f"Finance approval failed: {str(e)}"}), 500


# ============================================================================
# GET /finance/reflection/status - Get Reflection Status
# ============================================================================
@finance_bp.route("/reflection/status/<thread_id>", methods=["GET"])
def get_reflection_status(thread_id: str):
    """
    Get the reflection status for a thread.
    Returns detailed information about reflection iterations and validation.
    """
    try:
        if thread_id not in active_threads:
            return jsonify({"error": f"Thread {thread_id} not found"}), 404
        
        thread_data = active_threads[thread_id]
        
        # Check if we have reflection data
        if "reflection_data" in thread_data:
            reflection_data = thread_data["reflection_data"]
            return jsonify({
                "thread_id": thread_id,
                "status": thread_data.get("status", "unknown"),
                "query": thread_data["state"].get("query", ""),
                "reflection_iterations": reflection_data.get("reflection_iterations", 0),
                "reflection_chain": reflection_data.get("reflection_chain", []),
                "validation_approved": reflection_data.get("validation_approved", False),
                "stages": {
                    "analyzer": "completed",
                    "reflection": "completed",
                    "validation": "completed",
                    "approval": thread_data.get("status") == "pending_approval",
                    "execution": "pending"
                }
            })
        else:
            # Legacy thread - return basic info
            return jsonify({
                "thread_id": thread_id,
                "status": thread_data.get("status", "unknown"),
                "reflection_iterations": thread_data["state"].get("reflection_iterations", 0),
                "message": "Legacy thread - limited reflection data available"
            })
    
    except Exception as e:
        logger.error(f"[FINANCE] Reflection status error: {str(e)}")
        return jsonify({"error": f"Failed to get reflection status: {str(e)}"}), 500


# ============================================================================
# POST /finance/reflection/analyze - Analyze Only (No HITL)
# ============================================================================
@finance_bp.route("/reflection/analyze", methods=["POST"])
def analyze_with_reflection_only():
    """
    Run analysis with reflection only (no HITL gate).
    Useful for getting preliminary analysis before full workflow.
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info("[FINANCE] Running reflection-only analysis")
        
        # Sanitize query
        safe_query, redacted_items = sanitizer.sanitize_clinical_prompt(query)
        
        # Run reflection analysis
        result = run_finance_analysis_with_reflection(safe_query)
        
        # Generate a thread ID for this analysis
        import uuid
        thread_id = str(uuid.uuid4())
        
        # Cache the result
        reflection_cache[thread_id] = result
        
        return jsonify({
            "thread_id": thread_id,
            "status": "analyzed",
            "analysis": result.get("analysis", ""),
            "proposed_action": result.get("proposed_action", ""),
            "reflection_iterations": result.get("reflection_iterations", 0),
            "reflection_chain": result.get("reflection_chain", []),
            "validation_approved": result.get("validation_approved", False),
            "instruments_identified": result.get("reflection_chain", [{}])[0].get("instruments", []) if result.get("reflection_chain") else [],
            "risk_profile": result.get("reflection_chain", [{}])[0].get("risk_profile", {}) if result.get("reflection_chain") else {},
            "metadata": {
                "message": "Analysis complete. Use /finance/query for full workflow with HITL approval.",
                "redacted_items": redacted_items
            }
        })
    
    except Exception as e:
        logger.error(f"[FINANCE] Reflection analysis error: {str(e)}")
        return jsonify({"error": f"Reflection analysis failed: {str(e)}"}), 500


# ============================================================================
# GET /finance/threads - List Active Threads
# ============================================================================
@finance_bp.route("/threads", methods=["GET"])
def list_threads():
    """
    List all active finance threads.
    """
    try:
        threads = []
        for thread_id, thread_data in active_threads.items():
            state = thread_data.get("state", {})
            threads.append({
                "thread_id": thread_id,
                "status": thread_data.get("status", "unknown"),
                "query": state.get("query", "")[:100],
                "reflection_iterations": state.get("reflection_iterations", 0),
                "current_stage": state.get("current_stage", "unknown")
            })
        
        return jsonify({
            "active_threads": len(threads),
            "threads": threads
        })
    
    except Exception as e:
        logger.error(f"[FINANCE] List threads error: {str(e)}")
        return jsonify({"error": f"Failed to list threads: {str(e)}"}), 500


# ============================================================================
# Health Check for Finance
# ============================================================================
@finance_bp.route("/health", methods=["GET"])
def finance_health():
    """Health check for wealth management route."""
    return jsonify({
        "status": "healthy",
        "service": "Wealth Management (Reflection + HITL)",
        "pattern": "Query → Analysis → Reflection Loop → Validation → Pause → Approval → Execute",
        "reflection_enabled": True,
        "max_reflection_iterations": 3,
        "active_threads": len(active_threads)
    })
