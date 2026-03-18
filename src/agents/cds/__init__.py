"""
CDS (Clinical Decision Support) Multi-Agent System
=================================================

This package contains the multi-agent CDS system with:
- Base agent classes and interfaces
- Triage agent for query routing
- 7 specialist agents for different medical domains
- Agent registry for agent management
- Coordinator for multi-agent orchestration
- ACP Protocol for inter-agent communication
- PubMed search helper for evidence-based references

Exports:
- BaseAgent, AgentSpec, AgentResponse, ProcessingContext
- TriageAgent
- All specialist agents
- AgentRegistry
- CDSCoordinator
- ACP Protocol functions
- PubMed search utilities
"""

# Base classes
from src.agents.cds.base_agent import (
    BaseAgent,
    AgentSpec,
    AgentResponse,
    AgentCapability,
    ProcessingContext,
    ExpertiseLevel,
    create_agent_spec,
    parse_llm_json_response
)

# Triage Agent
from src.agents.cds.triage_agent import TriageAgent, create_triage_agent

# Specialist Agents
from src.agents.cds.specialist_agents import (
    OBGYNAgent,
    MedicineAgent,
    SurgeryAgent,
    PediatricsAgent,
    RadiologyAgent,
    PsychiatryAgent,
    ResearchAgent,
    create_specialist_agent,
    get_all_specialist_ids
)

# Registry and Coordinator
from src.agents.cds.registry import AgentRegistry, get_registry, reset_registry
from src.agents.cds.coordinator import (
    CDSCoordinator,
    get_coordinator,
    reset_coordinator,
    HandoffChain,
    CoordinationResult
)

# ACP Protocol
from src.agents.cds.acp_protocol import (
    ACPMessage,
    HandoffRequest,
    ConsultRequest,
    Response,
    MessageType,
    create_handoff_request,
    create_consult_request,
    create_response,
    create_escalation,
    create_routing_message,
    serialize_message,
    deserialize_message,
    get_message_type,
    extract_trace_id,
    validate_message,
    generate_trace_id,
    get_timestamp
)

# PubMed Search Helper
from src.agents.cds.pubmed_helper import (
    PubMedReference,
    PubMedSearchHelper,
    SyncPubMedSearch,
    pubmed_search
)


# =============================================================================
# INITIALIZATION FUNCTIONS
# =============================================================================

def initialize_cds_system(llm=None) -> tuple:
    """
    Initialize the complete CDS multi-agent system.
    
    Args:
        llm: Optional LLM instance to assign to all agents
        
    Returns:
        Tuple of (registry, coordinator)
    """
    from src.agents.cds.registry import get_registry
    from src.agents.cds.coordinator import get_coordinator
    
    registry = get_registry()
    coordinator = get_coordinator(registry)
    
    # Register triage agent
    triage = create_triage_agent()
    if llm:
        triage.set_llm(llm)
    registry.register(triage, is_triage=True)
    
    # Register all specialist agents
    for agent_id in get_all_specialist_ids():
        agent = create_specialist_agent(agent_id)
        if agent:
            if llm:
                agent.set_llm(llm)
            registry.register(agent)
    
    registry.set_initialized(True)
    
    return registry, coordinator


def get_cds_status() -> dict:
    """
    Get status of CDS system.
    
    Returns:
        Dictionary with system status
    """
    registry = get_registry()
    return {
        "registry": registry.get_registry_status(),
        "initialized": registry.is_initialized()
    }


# Default exports
__all__ = [
    # Base classes
    "BaseAgent",
    "AgentSpec", 
    "AgentResponse",
    "AgentCapability",
    "ProcessingContext",
    "ExpertiseLevel",
    "create_agent_spec",
    "parse_llm_json_response",
    
    # Triage
    "TriageAgent",
    "create_triage_agent",
    
    # Specialists
    "OBGYNAgent",
    "MedicineAgent",
    "SurgeryAgent",
    "PediatricsAgent",
    "RadiologyAgent",
    "PsychiatryAgent",
    "ResearchAgent",
    "create_specialist_agent",
    "get_all_specialist_ids",
    
    # Registry & Coordinator
    "AgentRegistry",
    "get_registry",
    "reset_registry",
    "CDSCoordinator",
    "get_coordinator",
    "reset_coordinator",
    "HandoffChain",
    "CoordinationResult",
    
    # ACP Protocol
    "ACPMessage",
    "HandoffRequest", 
    "ConsultRequest",
    "Response",
    "MessageType",
    "create_handoff_request",
    "create_consult_request",
    "create_response",
    "create_escalation",
    "create_routing_message",
    "serialize_message",
    "deserialize_message",
    "get_message_type",
    "extract_trace_id",
    "validate_message",
    "generate_trace_id",
    "get_timestamp",
    
    # PubMed Helper
    "PubMedReference",
    "PubMedSearchHelper",
    "SyncPubMedSearch",
    "pubmed_search",
    
    # Initialization
    "initialize_cds_system",
    "get_cds_status"
]
