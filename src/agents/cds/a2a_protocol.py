"""
Simplified A2A (Agent-to-Agent) Protocol
=========================================
Google's Agent-to-Agent protocol for seamless agent communication.
Simplified implementation for direct agent handoffs.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class A2AMessage:
    """
    Simplified A2A message for agent communication.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: str = "request"  # request, response, handoff, consult
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, urgent
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class A2AProtocol:
    """
    Simplified Agent-to-Agent protocol for direct communication.
    Replaces complex ACP with simple message passing.
    """
    
    @staticmethod
    def create_request(
        sender_id: str,
        receiver_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """Create a request message."""
        return A2AMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type="request",
            content=content,
            context=context or {}
        )
    
    @staticmethod
    def create_response(
        sender_id: str,
        receiver_id: str,
        content: str,
        original_message: Optional[A2AMessage] = None
    ) -> A2AMessage:
        """Create a response message."""
        return A2AMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type="response",
            content=content,
            trace_id=original_message.trace_id if original_message else "",
            context=original_message.context if original_message else {}
        )
    
    @staticmethod
    def create_handoff(
        from_agent: str,
        to_agent: str,
        content: str,
        reason: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """Create a handoff message for agent transfer."""
        ctx = context or {}
        ctx["handoff_reason"] = reason
        return A2AMessage(
            sender_id=from_agent,
            receiver_id=to_agent,
            message_type="handoff",
            content=content,
            context=ctx
        )
    
    @staticmethod
    def create_consult(
        from_agent: str,
        to_agent: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """Create a consultation request."""
        return A2AMessage(
            sender_id=from_agent,
            receiver_id=to_agent,
            message_type="consult",
            content=query,
            context=context or {}
        )


# Convenience functions
def create_handoff_request(
    from_agent: str,
    to_agent: str,
    content: str,
    reason: str = ""
) -> A2AMessage:
    """Create a simple handoff request."""
    return A2AProtocol.create_handoff(from_agent, to_agent, content, reason)


def create_response_message(
    sender: str,
    receiver: str,
    content: str,
    original: Optional[A2AMessage] = None
) -> A2AMessage:
    """Create a response to a message."""
    return A2AProtocol.create_response(sender, receiver, content, original)


# Helper for generating trace IDs
def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Get current timestamp."""
    return datetime.utcnow().isoformat()
