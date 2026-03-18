"""
ACP (Agent Communication Protocol) for CDS Multi-Agent System
==============================================================
Defines standardized message formats for inter-agent communication.

This protocol enables:
- Handoff requests: Transferring a query to another specialist
- Consult requests: Requesting input from another specialist
- Response messages: Standardized responses between agents
- Trace ID tracking: Following a query across multiple agents

TypedDicts:
- ACPMessage: Base message format
- HandoffRequest: Request to transfer to another agent
- ConsultRequest: Request for specialist input
- Response: Standard response format
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# MESSAGE TYPE DEFINITIONS
# =============================================================================

from enum import Enum


class MessageType(str, Enum):
    """ACP message types."""
    HANDOFF = "handoff"
    CONSULT = "consult"
    RESPONSE = "response"
    ESCALATION = "escalation"
    ROUTING = "routing"


class ACPMessage(TypedDict, total=False):
    """Base ACP message structure."""
    message_id: str           # Unique message identifier
    trace_id: str            # Cross-agent tracking ID
    timestamp: str           # ISO 8601 timestamp
    message_type: str        # Type of message
    sender_id: str           # Agent sending the message
    sender_name: str         # Human-readable sender name
    receiver_id: str         # Agent receiving the message
    payload: Dict[str, Any] # Message content


class HandoffRequest(TypedDict, total=False):
    """Request to handoff a query to another specialist agent."""
    message_id: str
    trace_id: str
    timestamp: str
    message_type: Literal["handoff"]
    sender_id: str
    sender_name: str
    receiver_id: str
    reason: str              # Reason for handoff
    summary: str             # Summary of case/context
    query: str               # Original query
    patient_context: str     # Relevant patient context
    handoff_chain: List[str] # History of handoffs
    urgency: Literal["normal", "urgent", "emergency"]
    metadata: Dict[str, Any]


class ConsultRequest(TypedDict, total=False):
    """Request for specialist consultation/input."""
    message_id: str
    trace_id: str
    timestamp: str
    message_type: Literal["consult"]
    sender_id: str
    sender_name: str
    receiver_id: str
    question: str            # Specific question for consultant
    context: str              # Relevant clinical context
    query: str               # Original query
    required_expertise: List[str]  # Expertise areas needed
    metadata: Dict[str, Any]


class Response(TypedDict, total=False):
    """Standard response message."""
    message_id: str
    trace_id: str
    timestamp: str
    message_type: Literal["response"]
    sender_id: str
    sender_name: str
    receiver_id: str
    response: str             # Response content
    confidence: float         # Confidence score
    recommendations: List[str]
    references: List[Dict[str, str]]
    handoff_candidates: List[str]
    metadata: Dict[str, Any]


# =============================================================================
# PROTOCOL FUNCTIONS
# =============================================================================

def generate_message_id() -> str:
    """Generate a unique message ID."""
    return f"msg_{uuid.uuid4().hex[:12]}"


def generate_trace_id() -> str:
    """Generate a unique trace ID for cross-agent tracking."""
    return f"trace_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"


def get_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.now().isoformat()


def create_handoff_request(
    sender_id: str,
    sender_name: str,
    receiver_id: str,
    query: str,
    reason: str,
    summary: str,
    trace_id: str = "",
    patient_context: str = "",
    handoff_chain: Optional[List[str]] = None,
    urgency: Literal["normal", "urgent", "emergency"] = "normal",
    metadata: Optional[Dict[str, Any]] = None
) -> HandoffRequest:
    """
    Create a handoff request message.
    
    Use when transferring a query to another specialist agent.
    
    Args:
        sender_id: ID of agent initiating handoff
        sender_name: Name of agent initiating handoff
        receiver_id: ID of agent to receive handoff
        query: Original clinical query
        reason: Reason for handoff
        summary: Summary of the case
        trace_id: Trace ID for tracking (generated if not provided)
        patient_context: Relevant patient context
        handoff_chain: History of handoffs
        urgency: Urgency level
        metadata: Additional metadata
        
    Returns:
        Complete HandoffRequest dictionary
    """
    return HandoffRequest(
        message_id=generate_message_id(),
        trace_id=trace_id or generate_trace_id(),
        timestamp=get_timestamp(),
        message_type="handoff",
        sender_id=sender_id,
        sender_name=sender_name,
        receiver_id=receiver_id,
        reason=reason,
        summary=summary,
        query=query,
        patient_context=patient_context,
        handoff_chain=handoff_chain or [sender_id],
        urgency=urgency,
        metadata=metadata or {}
    )


def create_consult_request(
    sender_id: str,
    sender_name: str,
    receiver_id: str,
    question: str,
    context: str,
    query: str,
    trace_id: str = "",
    required_expertise: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ConsultRequest:
    """
    Create a consult request message.
    
    Use when requesting input from another specialist without full handoff.
    
    Args:
        sender_id: ID of agent requesting consultation
        sender_name: Name of agent requesting consultation
        receiver_id: ID of agent to consult
        question: Specific question for consultant
        context: Relevant clinical context
        query: Original query
        trace_id: Trace ID for tracking
        required_expertise: Expertise areas needed
        metadata: Additional metadata
        
    Returns:
        Complete ConsultRequest dictionary
    """
    return ConsultRequest(
        message_id=generate_message_id(),
        trace_id=trace_id or generate_trace_id(),
        timestamp=get_timestamp(),
        message_type="consult",
        sender_id=sender_id,
        sender_name=sender_name,
        receiver_id=receiver_id,
        question=question,
        context=context,
        query=query,
        required_expertise=required_expertise or [],
        metadata=metadata or {}
    )


def create_response(
    sender_id: str,
    sender_name: str,
    receiver_id: str,
    response: str,
    trace_id: str = "",
    confidence: float = 0.5,
    recommendations: Optional[List[str]] = None,
    references: Optional[List[Dict[str, str]]] = None,
    handoff_candidates: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Response:
    """
    Create a standard response message.
    
    Use for any response between agents.
    
    Args:
        sender_id: ID of agent sending response
        sender_name: Name of agent sending response
        receiver_id: ID of agent receiving response
        response: Response content
        trace_id: Trace ID for tracking
        confidence: Confidence score (0.0-1.0)
        recommendations: Clinical recommendations
        references: Reference citations
        handoff_candidates: Potential handoff candidates
        metadata: Additional metadata
        
    Returns:
        Complete Response dictionary
    """
    return Response(
        message_id=generate_message_id(),
        trace_id=trace_id or generate_trace_id(),
        timestamp=get_timestamp(),
        message_type="response",
        sender_id=sender_id,
        sender_name=sender_name,
        receiver_id=receiver_id,
        response=response,
        confidence=confidence,
        recommendations=recommendations or [],
        references=references or [],
        handoff_candidates=handoff_candidates or [],
        metadata=metadata or {}
    )


def create_escalation(
    sender_id: str,
    sender_name: str,
    receiver_id: str,
    reason: str,
    summary: str,
    query: str,
    trace_id: str = "",
    patient_context: str = "",
    urgency: Literal["normal", "urgent", "emergency"] = "urgent",
    metadata: Optional[Dict[str, Any]] = None
) -> HandoffRequest:
    """
    Create an escalation message (urgent handoff).
    
    Use for emergency or urgent escalations.
    
    Args:
        sender_id: ID of agent initiating escalation
        sender_name: Name of agent initiating escalation
        receiver_id: ID of agent to receive escalation
        reason: Reason for escalation
        summary: Summary of the case
        query: Original clinical query
        trace_id: Trace ID for tracking
        patient_context: Relevant patient context
        urgency: Urgency level
        metadata: Additional metadata
        
    Returns:
        Complete HandoffRequest (escalation)
    """
    return create_handoff_request(
        sender_id=sender_id,
        sender_name=sender_name,
        receiver_id=receiver_id,
        query=query,
        reason=reason,
        summary=summary,
        trace_id=trace_id,
        patient_context=patient_context,
        handoff_chain=None,
        urgency=urgency,
        metadata=metadata
    )


# =============================================================================
# MESSAGE PARSING AND SERIALIZATION
# =============================================================================

def serialize_message(message: Dict[str, Any]) -> str:
    """
    Serialize an ACP message to JSON string.
    
    Args:
        message: ACP message dictionary
        
    Returns:
        JSON string representation
    """
    return json.dumps(message, indent=2)


def deserialize_message(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Deserialize an ACP message from JSON string.
    
    Args:
        json_str: JSON string
        
    Returns:
        Parsed message dictionary or None if invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to deserialize message: {e}")
        return None


def get_message_type(message: Dict[str, Any]) -> Optional[str]:
    """
    Extract message type from an ACP message.
    
    Args:
        message: ACP message dictionary
        
    Returns:
        Message type string or None
    """
    return message.get("message_type")


def extract_trace_id(message: Dict[str, Any]) -> Optional[str]:
    """
    Extract trace ID from an ACP message.
    
    Args:
        message: ACP message dictionary
        
    Returns:
        Trace ID string or None
    """
    return message.get("trace_id")


# =============================================================================
# TRACE CHAIN MANAGEMENT
# =============================================================================

def add_to_trace_chain(
    trace_chain: List[str],
    agent_id: str,
    action: str
) -> Dict[str, Any]:
    """
    Add an entry to the trace chain.
    
    Args:
        trace_chain: Current trace chain
        agent_id: Agent ID to add
        action: Action performed by agent
        
    Returns:
        Trace chain entry
    """
    entry = {
        "agent_id": agent_id,
        "action": action,
        "timestamp": get_timestamp()
    }
    return entry


def build_handoff_chain(agents: List[str]) -> List[str]:
    """
    Build a handoff chain from a list of agent IDs.
    
    Args:
        agents: List of agent IDs in order of handoff
        
    Returns:
        Complete handoff chain
    """
    return agents


# =============================================================================
# VALIDATION
# =============================================================================

def validate_message(message: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate an ACP message structure.
    
    Args:
        message: Message to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    required_fields = ["message_id", "trace_id", "timestamp", "message_type", "sender_id"]
    for field in required_fields:
        if field not in message:
            errors.append(f"Missing required field: {field}")
    
    valid_types = ["handoff", "consult", "response", "escalation", "routing"]
    if "message_type" in message and message["message_type"] not in valid_types:
        errors.append(f"Invalid message_type: {message['message_type']}")
    
    return len(errors) == 0, errors


def create_routing_message(
    sender_id: str,
    sender_name: str,
    target_agent_id: str,
    query: str,
    confidence: float,
    trace_id: str = "",
    patient_context: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> ACPMessage:
    """
    Create a routing message (from triage to specialist).
    
    Args:
        sender_id: ID of routing agent (triage)
        sender_name: Name of routing agent
        target_agent_id: ID of target specialist
        query: Clinical query
        confidence: Routing confidence
        trace_id: Trace ID for tracking
        patient_context: Patient context
        metadata: Additional metadata
        
    Returns:
        Complete ACPMessage for routing
    """
    return ACPMessage(
        message_id=generate_message_id(),
        trace_id=trace_id or generate_trace_id(),
        timestamp=get_timestamp(),
        message_type="routing",
        sender_id=sender_id,
        sender_name=sender_name,
        receiver_id=target_agent_id,
        payload={
            "query": query,
            "patient_context": patient_context,
            "confidence": confidence,
            "routing_reason": f"Routed to {target_agent_id} with confidence {confidence}",
            **(metadata or {})
        }
    )
