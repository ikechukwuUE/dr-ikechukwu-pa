"""
CDS Flask Integration Layer
============================
Provides seamless integration between Flask routes and CDS agents.
Handles input/output transformation and skill integration.

Usage:
    from src.api.cds_integration import process_clinical_query
    
    # Flask calls this function
    result = process_clinical_query(
        query="Patient with chest pain...",
        patient_context="65 year old male...",
        thread_id="session-123"
    )
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
import json

from src.agents.cds.coordinator import CDSCoordinator
from src.agents.cds.registry import AgentRegistry
from src.agents.cds.skills import get_system_prompt, get_3_phase_protocol, get_safety_protocols

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClinicalQueryInput:
    """Input from Flask route to CDS system"""
    query: str
    patient_context: str = ""
    thread_id: str = "default"
    trace_id: str = ""
    use_triage: bool = True
    requested_agent: Optional[str] = None


@dataclass
class ClinicalQueryOutput:
    """Output from CDS system to Flask route"""
    response: str
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)
    agent_used: str = ""
    chain: List[str] = field(default_factory=list)
    phase_executed: str = "full"
    skill_version: str = ""


# =============================================================================
# INTEGRATION FUNCTIONS
# =============================================================================

def transform_input(data: Dict[str, Any]) -> ClinicalQueryInput:
    """
    Transform Flask JSON input to ClinicalQueryInput.
    
    Expected input format (from Flask):
    {
        "query": "clinical question",
        "patient_context": "patient info",
        "thread_id": "optional",
        "use_triage": true/false,
        "agent_id": "optional specific agent"
    }
    """
    return ClinicalQueryInput(
        query=data.get("query", ""),
        patient_context=data.get("patient_context", ""),
        thread_id=data.get("thread_id", "default-clinical-session"),
        trace_id=data.get("trace_id", ""),
        use_triage=data.get("use_triage", True),
        requested_agent=data.get("agent_id", None)
    )


def transform_output(coordination_result) -> ClinicalQueryOutput:
    """
    Transform CDS CoordinationResult to ClinicalQueryOutput.
    
    Expected output format (to Flask):
    {
        "response": "clinical response",
        "confidence": 0.85,
        "recommendations": ["rec1", "rec2"],
        "references": [{"title": "...", "pmid": "...", "url": "..."}],
        "agent_used": "obgyn_agent",
        "chain": ["triage", "obgyn_agent"],
        "phase_executed": "full",
        "skill_version": "1.0.0"
    }
    """
    # Extract references from result
    references = []
    if hasattr(coordination_result, 'references') and coordination_result.references:
        for ref in coordination_result.references:
            if isinstance(ref, dict):
                references.append({
                    "title": ref.get("title", ""),
                    "pmid": ref.get("pmid", ""),
                    "url": ref.get("url", f"https://pubmed.ncbi.nlm.nih.gov/{ref.get('pmid', '')}/")
                })
            elif hasattr(ref, 'pmid'):
                references.append({
                    "title": getattr(ref, 'title', ''),
                    "pmid": ref.pmid,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{ref.pmid}/"
                })
    
    # Extract agent chain
    chain = []
    if hasattr(coordination_result, 'chain') and coordination_result.chain:
        chain = coordination_result.chain
    elif hasattr(coordination_result, 'handoff_chain'):
        chain = [h.agent_id for h in coordination_result.handoff_chain.agents]
    
    # Get agent used
    agent_used = ""
    if hasattr(coordination_result, 'primary_agent'):
        agent_used = coordination_result.primary_agent
    elif chain:
        agent_used = chain[-1] if chain else "unknown"
    
    return ClinicalQueryOutput(
        response=getattr(coordination_result, 'response', str(coordination_result)),
        confidence=getattr(coordination_result, 'confidence', 0.0),
        recommendations=getattr(coordination_result, 'recommendations', []),
        references=references,
        agent_used=agent_used,
        chain=chain,
        phase_executed=getattr(coordination_result, 'phase_executed', 'full'),
        skill_version=getattr(coordination_result, 'skill_version', '1.0.0')
    )


def to_flask_response(output: ClinicalQueryOutput) -> Dict[str, Any]:
    """
    Convert ClinicalQueryOutput to Flask JSON response.
    """
    return {
        "status": "success",
        "response": output.response,
        "confidence": output.confidence,
        "recommendations": output.recommendations,
        "references": output.references,
        "metadata": {
            "agent_used": output.agent_used,
            "chain": output.chain,
            "phase_executed": output.phase_executed,
            "skill_version": output.skill_version
        }
    }


def to_flask_error(error: str, code: int = 500) -> tuple:
    """
    Create Flask error response.
    """
    return {"status": "error", "error": error}, code


# =============================================================================
# MAIN PROCESSOR
# =============================================================================

def process_clinical_query(
    query: str,
    patient_context: str = "",
    thread_id: str = "default-clinical-session",
    trace_id: str = "",
    use_triage: bool = True,
    requested_agent: Optional[str] = None,
    coordinator: Optional[CDSCoordinator] = None
) -> Dict[str, Any]:
    """
    Process a clinical query through the CDS system.
    
    This is the main entry point for Flask routes.
    
    Args:
        query: Clinical question
        patient_context: Patient information
        thread_id: Session ID
        trace_id: Trace ID for debugging
        use_triage: Use triage for routing
        requested_agent: Direct agent request
        coordinator: CDS Coordinator instance
        
    Returns:
        Dict suitable for Flask jsonify() - always a dict, never tuple
    """
    try:
        # Get coordinator
        if coordinator is None:
            from src.api.routes.cds import get_cds_components
            _, coordinator = get_cds_components()
        
        # Process through coordinator
        result = coordinator.process_query(
            query=query,
            patient_context=patient_context,
            thread_id=thread_id,
            trace_id=trace_id,
            use_triage=use_triage,
            requested_agent=requested_agent
        )
        
        # Transform and return
        output = transform_output(result)
        return to_flask_response(output)
        
    except Exception as e:
        logger.error(f"Error processing clinical query: {e}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# SKILL INTEGRATION HELPERS
# =============================================================================

def get_agent_skill_info(agent_id: str) -> Dict[str, Any]:
    """
    Get skill information for a specific agent.
    
    Maps agent_id to skill specialty and returns skill data.
    """
    # Map agent IDs to skill specialties
    AGENT_TO_SPECIALTY = {
        "obgyn_agent": "obgyn",
        "medicine_agent": "medicine",
        "surgery_agent": "surgery",
        "pediatrics_agent": "pediatrics",
        "radiology_agent": "radiology",
        "psychiatry_agent": "psychiatry",
        "pathology_agent": "pathology",
        "pharmacology_agent": "pharmacology"
    }
    
    specialty = AGENT_TO_SPECIALTY.get(agent_id)
    if not specialty:
        return {"error": "Unknown agent"}
    
    try:
        system_prompt = get_system_prompt(specialty)
        protocol = get_3_phase_protocol(specialty)
        safety = get_safety_protocols(specialty)
        
        return {
            "agent_id": agent_id,
            "specialty": specialty,
            "system_prompt": system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt,
            "phase1": bool(protocol.get("phase1")),
            "phase2": bool(protocol.get("phase2")),
            "phase3": bool(protocol.get("phase3")),
            "has_safety_protocols": bool(safety)
        }
    except Exception as e:
        logger.error(f"Error getting skill info: {e}")
        return {"error": str(e)}


def list_available_skills() -> List[Dict[str, str]]:
    """
    List all available CDS skills.
    """
    skills = [
        {"specialty": "obgyn", "name": "OB/GYN Specialist"},
        {"specialty": "medicine", "name": "Internal Medicine Specialist"},
        {"specialty": "surgery", "name": "General Surgery Specialist"},
        {"specialty": "pediatrics", "name": "Pediatrics Specialist"},
        {"specialty": "radiology", "name": "Radiology Specialist"},
        {"specialty": "psychiatry", "name": "Psychiatry Specialist"},
        {"specialty": "pathology", "name": "Pathology Specialist"},
        {"specialty": "pharmacology", "name": "Pharmacology Specialist"}
    ]
    return skills
