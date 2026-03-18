"""
CDS Agent Base Classes and Interfaces
=====================================
Defines the foundational types and abstract base class for all CDS agents.

TypedDicts:
- AgentSpec: Agent specification with ID, name, specialty, capabilities
- AgentResponse: Standardized response format from all agents

Abstract Base Class:
- BaseAgent: Base class for all specialist agents with common interface
"""

from abc import ABC, abstractmethod
from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class ExpertiseLevel(str, Enum):
    """Depth levels for agent expertise."""
    GENERAL = "general"           # Basic general knowledge
    TRAINED = "trained"           # Has received training
    SPECIALIST = "specialist"     # Board certified specialist
    EXPERT = "expert"            # Recognized expert with research background


class AgentCapability(TypedDict, total=False):
    """Individual capability definition."""
    name: str
    description: str
    keywords: List[str]           # Trigger words for this capability
    can_handle_emergency: bool


class AgentSpec(TypedDict, total=False):
    """Complete agent specification."""
    agent_id: str                 # Unique identifier (e.g., "obgyn_agent")
    name: str                     # Human-readable name
    specialty: str                # Primary medical specialty
    capabilities: List[AgentCapability]
    expertise_depth: ExpertiseLevel
    can_handoff_to: List[str]     # List of agent_ids this agent can handoff to
    description: str


class AgentResponse(TypedDict, total=False):
    """Standardized response from any CDS agent."""
    response: str                 # Main clinical response/assessment
    confidence: float             # 0.0 to 1.0 confidence score
    recommendations: List[str]    # Clinical recommendations
    references: List[Dict[str, str]]  # Citations with title, source, url
    handoff_candidates: List[str]     # Other agents that might help
    agent_id: str                 # ID of agent that generated response
    agent_name: str               # Name of agent that generated response
    processing_time_ms: int       # Time taken to generate response
    trace_id: str                 # Trace ID for tracking
    metadata: Dict[str, Any]      # Additional metadata


# =============================================================================
# CAPABILITY DEFINITIONS
# =============================================================================

class Capability:
    """Predefined capability constants for CDS agents."""
    
    # General medical capabilities
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    EMERGENCY = "emergency"
    REFERRAL = "referral"
    
    # Specialized capabilities
    IMAGING = "imaging"
    LAB_INTERPRETATION = "lab_interpretation"
    PROCEDURE = "procedure"
    FOLLOW_UP = "follow_up"
    PREVENTION = "prevention"
    
    # Assessment capabilities
    RISK_ASSESSMENT = "risk_assessment"
    PROGNOSIS = "prognosis"
    PATIENT_EDUCATION = "patient_education"


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

@dataclass
class ProcessingContext:
    """Context passed to agents during processing."""
    query: str
    patient_context: str = ""
    thread_id: str = ""
    trace_id: str = ""
    history: List[Dict[str, str]] = field(default_factory=list)
    requested_agent: Optional[str] = None
    
    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())


class BaseAgent(ABC):
    """
    Abstract base class for all Clinical Decision Support agents.
    
    All CDS agents must implement:
    - process(): Process a clinical query and return a response
    - can_handle(): Determine if this agent can handle a given query
    - get_capabilities(): Return the agent's capabilities
    
    Attributes:
        spec: Agent specification with ID, name, specialty
    """
    
    def __init__(self, spec: AgentSpec):
        """
        Initialize the agent with its specification.
        
        Args:
            spec: Agent specification containing all agent metadata
        """
        self.spec = spec
        self._llm = None
        logger.info(f"Initialized agent: {spec.get('name', 'Unknown')} ({spec.get('agent_id', 'unknown')})")
    
    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self.spec.get("agent_id", "")
    
    @property
    def name(self) -> str:
        """Get the agent's human-readable name."""
        return self.spec.get("name", "")
    
    @property
    def specialty(self) -> str:
        """Get the agent's primary specialty."""
        return self.spec.get("specialty", "")
    
    @property
    def expertise_depth(self) -> ExpertiseLevel:
        """Get the agent's expertise level."""
        return self.spec.get("expertise_depth", ExpertiseLevel.GENERAL)
    
    @property
    def can_handoff_to(self) -> List[str]:
        """Get list of agent IDs this agent can handoff to."""
        return self.spec.get("can_handoff_to", [])
    
    @abstractmethod
    def process(self, context: ProcessingContext) -> AgentResponse:
        """
        Process a clinical query and return a structured response.
        
        Args:
            context: Processing context with query and metadata
            
        Returns:
            AgentResponse with clinical assessment and recommendations
        """
        pass
    
    @abstractmethod
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        """
        Determine if this agent can handle the given query.
        
        Args:
            query: Clinical query to evaluate
            context: Optional processing context
            
        Returns:
            Confidence score from 0.0 (cannot handle) to 1.0 (can handle)
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> AgentSpec:
        """
        Return the agent's capabilities specification.
        
        Returns:
            AgentSpec with full capabilities definition
        """
        pass
    
    def _build_base_response(
        self, 
        response: str,
        confidence: float = 0.5,
        recommendations: Optional[List[str]] = None,
        references: Optional[List[Dict[str, str]]] = None,
        context: Optional[ProcessingContext] = None
    ) -> AgentResponse:
        """
        Helper to build a base AgentResponse with common fields.
        
        Args:
            response: Main clinical response
            confidence: Confidence score (0.0-1.0)
            recommendations: List of recommendations
            references: List of reference citations
            context: Processing context for trace_id
            
        Returns:
            Complete AgentResponse dictionary
        """
        trace_id = context.trace_id if context else str(uuid.uuid4())
        
        return AgentResponse(
            response=response,
            confidence=confidence,
            recommendations=recommendations or [],
            references=references or [],
            handoff_candidates=self.can_handoff_to,
            agent_id=self.agent_id,
            agent_name=self.name,
            processing_time_ms=0,  # Will be set by caller
            trace_id=trace_id,
            metadata={
                "specialty": self.specialty,
                "expertise_depth": self.expertise_depth.value
            }
        )
    
    def _create_llm_prompt(self, context: ProcessingContext, system_prompt: str) -> str:
        """
        Create a formatted prompt for the LLM.
        
        Args:
            context: Processing context
            system_prompt: System instructions for the LLM
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            system_prompt,
            "",
            "=" * 50,
            "CLINICAL QUERY:",
            context.query,
        ]
        
        if context.patient_context:
            prompt_parts.extend([
                "",
                "PATIENT CONTEXT:",
                context.patient_context
            ])
        
        if context.history:
            prompt_parts.extend([
                "",
                "PREVIOUS INTERACTIONS:",
            ])
            for h in context.history[-3:]:  # Last 3 interactions
                prompt_parts.append(f"- {h.get('role', 'unknown')}: {h.get('content', '')[:200]}")
        
        return "\n".join(prompt_parts)
    
    def set_llm(self, llm: Any) -> None:
        """
        Set the LLM instance for this agent.
        
        Args:
            llm: LangChain LLM instance (e.g., ChatGoogleGenerativeAI)
        """
        self._llm = llm
    
    def get_llm(self) -> Optional[Any]:
        """
        Get the LLM instance for this agent.
        
        Returns:
            LLM instance or None if not set
        """
        return self._llm
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name})>"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_agent_spec(
    agent_id: str,
    name: str,
    specialty: str,
    capabilities: List[AgentCapability],
    expertise_depth: ExpertiseLevel,
    can_handoff_to: Optional[List[str]] = None,
    description: str = ""
) -> AgentSpec:
    """
    Factory function to create an AgentSpec.
    
    Args:
        agent_id: Unique identifier
        name: Human-readable name
        specialty: Medical specialty
        capabilities: List of capabilities
        expertise_depth: Expertise level
        can_handoff_to: List of agent IDs for handoff
        description: Optional description
        
    Returns:
        Complete AgentSpec dictionary
    """
    return AgentSpec(
        agent_id=agent_id,
        name=name,
        specialty=specialty,
        capabilities=capabilities,
        expertise_depth=expertise_depth,
        can_handoff_to=can_handoff_to or [],
        description=description
    )


def parse_llm_json_response(content: str) -> Dict[str, Any]:
    """
    Parse LLM response as JSON with robust error handling.
    Handles markdown code blocks and various formats.
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Parsed JSON as dictionary
    """
    import json
    
    if not content:
        return {
            "response": "No response generated",
            "recommendations": ["Consult relevant clinical guidelines"],
            "references": []
        }
    
    sanitized_content = content.strip()
    
    # Try to extract JSON from markdown code blocks
    if "```json" in sanitized_content:
        try:
            json_str = sanitized_content.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
    elif "```" in sanitized_content:
        try:
            json_str = sanitized_content.split("```")[1].split("```")[0].strip()
            if '\n' in json_str:
                first_line, rest = json_str.split('\n', 1)
                json_str = rest
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
    
    # Try to parse as raw JSON
    try:
        return json.loads(sanitized_content)
    except json.JSONDecodeError:
        pass
    
    # If all parsing fails, return structured response with raw content
    logger.warning("[BaseAgent] Could not parse LLM response as JSON")
    return {
        "response": content,
        "recommendations": ["Consult relevant clinical guidelines"],
        "references": []
    }
