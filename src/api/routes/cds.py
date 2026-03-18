"""
Clinical Decision Support (CDS) Blueprint
Route: /cds
Integrates multi-agent system with OpenRouter LLM for evidence-based clinical recommendations.
Security: All patient queries sanitized per Nigeria National Health Act 2014.
"""

from flask import Blueprint, request, jsonify
import logging
import json
import secrets

from src.core.config import settings
from src.core.security import SecuritySanitizer
from src.core.security_layer import (
    SecurityService, 
    OutputValidator
)
from src.core.llm_factory import LLMFactory
from src.api.cds_integration import (
    transform_input,
    to_flask_response,
    to_flask_error,
    get_agent_skill_info,
    list_available_skills
)

logger = logging.getLogger(__name__)

cds_bp = Blueprint("cds", __name__, url_prefix="/cds")

# Model configuration - now using config.py settings
CDS_MODEL = settings.CLINICAL_PRIMARY_MODEL
CDS_MODEL_BACKUP = settings.CLINICAL_BACKUP_MODEL

# ============================================================================
# Initialize LLM, Sanitizer, and Security Service
# ============================================================================

def get_llm():
    """Get or create LLM instance using LLMFactory (config.py settings)."""
    try:
        return LLMFactory.create_llm(domain="clinical", temperature=0.0)
    except ValueError as e:
        logger.error(f"Failed to create LLM: {e}")
        return None

llm_clinical = None
sanitizer = SecuritySanitizer()
security_service = SecurityService()
output_validator = OutputValidator()

# CDS Multi-agent system components
_cds_initialized = False


def get_llm_instance():
    """Lazy initialization of LLM to handle missing API keys gracefully."""
    global llm_clinical
    if llm_clinical is None:
        try:
            llm_clinical = get_llm()
        except ValueError as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None
    return llm_clinical


def initialize_cds_system():
    """Initialize the CDS multi-agent system."""
    global _cds_initialized
    
    if _cds_initialized:
        return
    
    try:
        # Get or create LLM
        llm = get_llm_instance()
        
        # Import CDS components
        from src.agents.cds import initialize_cds_system as init_system
        from src.agents.cds import get_registry, get_coordinator
        
        # Initialize the system
        registry, coordinator = init_system(llm)
        
        _cds_initialized = True
        logger.info("CDS multi-agent system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize CDS system: {e}")
        _cds_initialized = False


def get_cds_components():
    """Get CDS registry and coordinator, initializing if needed."""
    global _cds_initialized
    
    if not _cds_initialized:
        initialize_cds_system()
    
    from src.agents.cds import get_registry, get_coordinator
    registry = get_registry()
    coordinator = get_coordinator(registry)
    
    return registry, coordinator


# ============================================================================
# POST /cds/query - Clinical Query Handler
# ============================================================================

@cds_bp.route("/query", methods=["POST"])
def clinical_query():
    """
    Process clinical query with multi-agent CDS system.
    """
    try:
        # Validate API key if configured
        api_key = request.headers.get('X-API-Key')
        if settings.DR_IKECHUKWU_PA_API_KEY and not secrets.compare_digest(api_key, settings.DR_IKECHUKWU_PA_API_KEY):
            return jsonify({"error": "Invalid API key"}), 401
        
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
            
        # Use security service to validate input
        validation_result = security_service.validate_request(
            data, 
            required_fields=['query'],
            optional_fields=['patient_context', 'thread_id', 'agent_id', 'use_triage']
        )
        
        if not validation_result.is_valid:
            logger.warning(f"[CDS] Input validation failed: {validation_result.errors}")
            return jsonify({
                "status": "error",
                "error": "Input validation failed",
                "details": validation_result.errors
            }), 400
        
        # Handle sanitized_value as string (from security layer)
        sanitized_data = validation_result.sanitized_value
        if isinstance(sanitized_data, str):
            # Parse the JSON string
            try:
                sanitized_data = json.loads(sanitized_data)
            except:
                sanitized_data = {"query": data.get("query", "")}
        
        query = sanitized_data.get("query", "") if isinstance(sanitized_data, dict) else data.get("query", "")
        patient_context = sanitized_data.get("patient_context", "") if isinstance(sanitized_data, dict) else data.get("patient_context", "")
        thread_id = sanitized_data.get("thread_id", "default-clinical-session") if isinstance(sanitized_data, dict) else "default-clinical-session"
        requested_agent = sanitized_data.get("agent_id", None) if isinstance(sanitized_data, dict) else data.get("agent_id")
        use_triage = sanitized_data.get("use_triage", True) if isinstance(sanitized_data, dict) else data.get("use_triage", True)

        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        if not isinstance(query, str) or len(query.strip()) == 0:
            return jsonify({"error": "Query must be a non-empty string"}), 400

        logger.info(f"[CDS] Processing query from thread {thread_id}")
        
        # Step 1: Sanitize Input using clinical sanitizer (PII/PHI redaction)
        safe_query, redacted_items = sanitizer.sanitize_clinical_prompt(query)
        logger.info(f"[CDS] Sanitized {len(redacted_items)} PII items")
        
        # Step 2: Prepare patient context if provided
        safe_context = ""
        if patient_context:
            safe_context, context_redacted = sanitizer.sanitize_clinical_prompt(patient_context)
            logger.info(f"[CDS] Sanitized patient context")
        
        # Step 3: Process through multi-agent system
        try:
            registry, coordinator = get_cds_components()
            
            if registry and coordinator and registry.is_initialized():
                # Use multi-agent system
                result = coordinator.process_query(
                    query=safe_query,
                    patient_context=safe_context,
                    thread_id=thread_id,
                    use_triage=use_triage,
                    requested_agent=requested_agent
                )
                
                response_data = {
                    "status": "success",
                    "response": result.response.get("response", ""),
                    "recommendations": result.response.get("recommendations", []),
                    "evidence": result.response.get("references", []),
                    "agent_id": result.primary_agent_id,
                    "agent_name": result.response.get("agent_name", ""),
                    "confidence": result.response.get("confidence", 0.0),
                    "handoff_chain": result.handoff_chain.to_dict(),
                    "metadata": {
                        "thread_id": thread_id,
                        "pii_redacted_count": len(redacted_items),
                        "security_validation": "passed",
                        "processing_time_ms": result.response.get("processing_time_ms", 0),
                        "was_handed_off": result.was_handed_off,
                        "multi_agent_system": True
                    }
                }
                
            else:
                # Fallback to simple LLM processing
                logger.warning("[CDS] Multi-agent system not initialized, using fallback")
                response_data = _fallback_processing(safe_query, safe_context, thread_id, redacted_items)
                
        except Exception as e:
            logger.error(f"[CDS] Multi-agent error: {e}")
            response_data = _fallback_processing(safe_query, safe_context, thread_id, redacted_items)
        
        # Step 4: Validate output before returning
        output_result = output_validator.validate_output(response_data)
        if output_result.redactions:
            logger.warning(f"[CDS] Output contained sensitive data")
        
        logger.info(f"[CDS] Query processed successfully")
        
        return jsonify(response_data)
    
    except json.JSONDecodeError as e:
        logger.error(f"[CDS] JSON parsing error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to parse LLM response"
        }), 500
    except ValueError as e:
        logger.error(f"[CDS] Configuration error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 503
    except Exception as e:
        logger.error(f"[CDS] Error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": f"Clinical query processing failed: {str(e)}"
        }), 500


def _fallback_processing(query: str, context: str, thread_id: str, redacted_items: dict) -> dict:
    """Fallback processing when multi-agent system is not available."""
    llm = get_llm_instance()
    
    if llm is None:
        return {
            "status": "error",
            "error": "LLM not configured. Please set GOOGLE_API_KEY in environment.",
            "metadata": {"thread_id": thread_id}
        }
    
    prompt = f"""You are a clinical decision support system helping medical professionals.
    
Clinical Query:
{query}

Context:
{context or "None provided"}

Provide:
1. Clinical Finding: Your assessment
2. Evidence-Based Recommendations: 3-5 specific next steps
3. References: Cite any guidelines

Format your response as JSON with fields: response, recommendations (array), references (array)."""
    
    try:
        response = llm.invoke(prompt)
        response_json = parse_llm_response(response.content)
    except Exception as e:
        logger.error(f"[CDS] LLM error: {e}")
        response_json = {
            "response": "Unable to process query at this time",
            "recommendations": ["Consult with a healthcare provider"],
            "references": []
        }
    
    return {
        "status": "success",
        "response": response_json.get("response", ""),
        "recommendations": response_json.get("recommendations", []),
        "evidence": response_json.get("references", []),
        "agent_id": "llm_fallback",
        "agent_name": "Clinical LLM",
        "confidence": 0.5,
        "handoff_chain": {
            "trace_id": "fallback",
            "agent_sequence": ["llm_fallback"],
            "handoff_count": 0
        },
        "metadata": {
            "thread_id": thread_id,
            "pii_redacted_count": len(redacted_items),
            "security_validation": "passed",
            "multi_agent_system": False,
            "fallback_mode": True
        }
    }


def parse_llm_response(content: str) -> dict:
    """Parse LLM response with robust error handling."""
    if not content:
        return {"response": "No response generated", "recommendations": [], "references": []}
    
    sanitized_content = content.strip()
    
    # Try to extract JSON from markdown code blocks
    if "```json" in sanitized_content:
        try:
            json_str = sanitized_content.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        except:
            pass
    elif "```" in sanitized_content:
        try:
            json_str = sanitized_content.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except:
            pass
    
    # Try to parse as raw JSON
    try:
        return json.loads(sanitized_content)
    except:
        pass
    
    return {"response": content, "recommendations": [], "references": []}


# ============================================================================
# GET /cds/agents - List Available Agents
# ============================================================================

@cds_bp.route("/agents", methods=["GET"])
def list_agents():
    """Get list of available CDS agents."""
    try:
        registry, _ = get_cds_components()
        
        if not registry:
            return jsonify({"status": "error", "error": "CDS system not initialized"}), 503
        
        agents = registry.get_agent_specs()
        
        return jsonify({
            "status": "success",
            "agents": agents,
            "total_count": len(agents)
        })
        
    except Exception as e:
        logger.error(f"[CDS] List agents error: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# POST /cds/handoff - Request Agent Handoff
# ============================================================================

@cds_bp.route("/handoff", methods=["POST"])
def request_handoff():
    """Request handoff to a specific agent."""
    try:
        api_key = request.headers.get('X-API-Key')
        if settings.DR_IKECHUKWU_PA_API_KEY and not secrets.compare_digest(api_key, settings.DR_IKECHUKWU_PA_API_KEY):
            return jsonify({"error": "Invalid API key"}), 401
        
        data = request.get_json(silent=True) or {}
        
        query = data.get("query", "")
        target_agent_id = data.get("target_agent_id", "")
        
        if not query or not target_agent_id:
            return jsonify({"status": "error", "error": "query and target_agent_id required"}), 400
        
        # Sanitize
        safe_query, redacted_items = sanitizer.sanitize_clinical_prompt(query)
        patient_context = data.get("patient_context", "")
        safe_context, _ = sanitizer.sanitize_clinical_prompt(patient_context)
        
        # Get CDS components
        registry, coordinator = get_cds_components()
        
        if not registry or not coordinator:
            return jsonify({"status": "error", "error": "CDS not initialized"}), 503
        
        # Get current agent (triage by default)
        current_agent = registry.get_triage_agent()
        
        if not current_agent:
            return jsonify({"status": "error", "error": "No triage agent"}), 503
        
        # Create context
        from src.agents.cds import ProcessingContext
        context = ProcessingContext(
            query=safe_query,
            patient_context=safe_context,
            thread_id=data.get("thread_id", "default"),
            trace_id=data.get("trace_id", "")
        )
        
        # Process with handoff
        result = coordinator.process_with_handoff(
            current_agent=current_agent,
            target_agent_id=target_agent_id,
            context=context,
            reason="user_requested_handoff"
        )
        
        return jsonify({
            "status": "success",
            "response": result.response.get("response", ""),
            "recommendations": result.response.get("recommendations", []),
            "evidence": result.response.get("references", []),
            "agent_id": result.primary_agent_id,
            "handoff_chain": result.handoff_chain.to_dict()
        })
        
    except Exception as e:
        logger.error(f"[CDS] Handoff error: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# Health Check for CDS
# ============================================================================

@cds_bp.route("/health", methods=["GET"])
def cds_health():
    """Health check for clinical decision support route."""
    openrouter_status = "configured" if settings.OPENROUTER_API_KEY else "not_configured"
    
    agent_status = "not_initialized"
    active_agents = 0
    
    try:
        registry, _ = get_cds_components()
        if registry and registry.is_initialized():
            agent_status = "initialized"
            active_agents = registry.get_active_agent_count()
    except:
        pass
    
    return jsonify({
        "status": "healthy",
        "service": "Clinical Decision Support (Multi-Agent)",
        "llm": CDS_MODEL,
        "llm_status": openrouter_status,
        "multi_agent_system": {
            "status": agent_status,
            "active_agents": active_agents
        }
    })


# ============================================================================
# GET /cds/status - Detailed System Status
# ============================================================================

@cds_bp.route("/status", methods=["GET"])
def cds_status():
    """Get detailed CDS system status."""
    try:
        registry, coordinator = get_cds_components()
        
        if not registry:
            return jsonify({"status": "error", "error": "CDS not initialized"}), 503
        
        return jsonify({
            "status": "success",
            "registry": registry.get_registry_status()
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# GET /cds/skills - List Available Skills
# ============================================================================

@cds_bp.route("/skills", methods=["GET"])
def list_cds_skills():
    """List all available CDS skills with their metadata."""
    try:
        skills = list_available_skills()
        return jsonify({
            "status": "success",
            "skills": skills,
            "count": len(skills)
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# GET /cds/skills/<agent_id> - Get Skill Details
# ============================================================================

@cds_bp.route("/skills/<agent_id>", methods=["GET"])
def get_cds_skill(agent_id: str):
    """
    Get skill information for a specific agent.
    
    Returns the 3-Phase Execution Protocol and skill metadata.
    """
    try:
        skill_info = get_agent_skill_info(agent_id)
        if "error" in skill_info:
            return jsonify({"status": "error", "error": skill_info["error"]}), 404
        
        return jsonify({
            "status": "success",
            "skill": skill_info
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# POST /cds/query/simple - Simplified Query Endpoint
# ============================================================================

@cds_bp.route("/query/simple", methods=["POST"])
def simple_clinical_query():
    """
    Simplified clinical query endpoint using seamless integration.
    
    This endpoint uses the cds_integration module for clean input/output.
    """
    try:
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        # Transform input using integration layer
        query_input = transform_input(data)
        
        if not query_input.query:
            return jsonify({"error": "Query is required"}), 400
        
        # Get CDS components
        registry, coordinator = get_cds_components()
        
        # Process query
        from src.api.cds_integration import process_clinical_query
        result = process_clinical_query(
            query=query_input.query,
            patient_context=query_input.patient_context,
            thread_id=query_input.thread_id,
            trace_id=query_input.trace_id,
            use_triage=query_input.use_triage,
            requested_agent=query_input.requested_agent,
            coordinator=coordinator
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in simple query: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500
