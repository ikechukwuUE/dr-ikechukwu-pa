"""
CDS Coordinator
===============
Orchestrates multi-agent handoffs and query processing.

Features:
- Query routing to appropriate agents
- Multi-agent coordination
- Handoff chain tracking
- Response aggregation
"""

from typing import Dict, List, Any, Optional
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.agents.cds.base_agent import BaseAgent, AgentResponse, ProcessingContext
from src.agents.cds.registry import AgentRegistry, get_registry
from src.agents.cds.a2a_protocol import (
    create_handoff_request,
    create_response_message,
    generate_trace_id,
    get_timestamp,
    A2AMessage
)

logger = logging.getLogger(__name__)


# =============================================================================
# COORDINATOR DATA STRUCTURES
# =============================================================================

@dataclass
class HandoffChain:
    """Tracks the sequence of agents that handled a query."""
    trace_id: str
    agents: List[str] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    handoff_reasons: List[str] = field(default_factory=list)
    
    def add_handoff(self, agent_id: str, reason: str = "") -> None:
        """Add a handoff to the chain."""
        self.agents.append(agent_id)
        self.timestamps.append(get_timestamp())
        self.handoff_reasons.append(reason)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "agent_sequence": self.agents,
            "handoff_count": len(self.agents) - 1,
            "handoff_reasons": self.handoff_reasons
        }


@dataclass
class CoordinationResult:
    """Result of coordination process."""
    response: AgentResponse
    handoff_chain: HandoffChain
    primary_agent_id: str
    was_handed_off: bool
    processing_time_ms: int


# =============================================================================
# COORDINATOR CLASS
# =============================================================================

class CDSCoordinator:
    """
    Coordinates multi-agent processing for clinical queries.
    
    Handles:
    - Initial routing to triage
    - Specialist routing
    - Handoff orchestration
    - Response aggregation
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        """
        Initialize the coordinator.
        
        Args:
            registry: Agent registry (uses global if not provided)
        """
        self._registry = registry or get_registry()
        self._active_chains: Dict[str, HandoffChain] = {}
        logger.info("CDSCoordinator initialized")
    
    def process_query(
        self,
        query: str,
        patient_context: str = "",
        thread_id: str = "",
        trace_id: str = "",
        use_triage: bool = True,
        requested_agent: Optional[str] = None
    ) -> CoordinationResult:
        """
        Process a clinical query through the multi-agent system.
        
        Args:
            query: Clinical query
            patient_context: Patient context information
            thread_id: Session/thread ID
            trace_id: Existing trace ID (generated if not provided)
            use_triage: Whether to use triage for routing
            requested_agent: Specific agent to route to
            
        Returns:
            CoordinationResult with response and chain info
        """
        start_time = time.time()
        
        # Generate or use trace ID
        if not trace_id:
            trace_id = generate_trace_id()
        
        # Create processing context
        context = ProcessingContext(
            query=query,
            patient_context=patient_context,
            thread_id=thread_id,
            trace_id=trace_id
        )
        
        # Initialize handoff chain
        chain = HandoffChain(trace_id=trace_id)
        self._active_chains[trace_id] = chain
        
        # Determine primary agent
        if requested_agent:
            # Direct routing to specific agent
            primary_agent = self._registry.get_agent(requested_agent)
            chain.add_handoff(requested_agent, "direct_request")
            logger.info(f"Direct routing to {requested_agent}")
            
        elif use_triage:
            # Use triage agent for routing
            triage_agent = self._registry.get_triage_agent()
            
            if triage_agent is None:
                logger.warning("No triage agent available, falling back to best match")
                primary_agent = self._registry.find_best_agent(query, context)
                if primary_agent:
                    chain.add_handoff(primary_agent.agent_id, "fallback_no_triage")
            else:
                # Process through triage
                triage_response = triage_agent.process(context)
                
                # Get routed agents from triage
                routed_agents = triage_response.get("handoff_candidates", [])
                
                if routed_agents:
                    primary_agent_id = routed_agents[0]
                    primary_agent = self._registry.get_agent(primary_agent_id)
                    chain.add_handoff(primary_agent_id, "triage_routing")
                    
                    # Add triage to chain
                    if triage_agent.agent_id not in chain.agents:
                        chain.agents.insert(0, triage_agent.agent_id)
                else:
                    # No routing, use best match
                    primary_agent = self._registry.find_best_agent(query, context)
                    if primary_agent:
                        chain.add_handoff(primary_agent.agent_id, "fallback_no_routing")
        else:
            # Direct best match without triage
            primary_agent = self._registry.find_best_agent(query, context)
            if primary_agent:
                chain.add_handoff(primary_agent.agent_id, "direct_best_match")
        
        # Process with primary agent
        if primary_agent is None:
            # No agent found - return error response
            error_response = AgentResponse(
                response="No suitable agent found for this query. Please try again or rephrase.",
                confidence=0.0,
                recommendations=["Consult with a general practitioner"],
                references=[],
                handoff_candidates=[],
                agent_id="coordinator",
                agent_name="CDS Coordinator",
                processing_time_ms=int((time.time() - start_time) * 1000),
                trace_id=trace_id,
                metadata={"error": "no_agent_found"}
            )
            
            return CoordinationResult(
                response=error_response,
                handoff_chain=chain,
                primary_agent_id="none",
                was_handed_off=False,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Process with specialist agent
        specialist_response = primary_agent.process(context)
        
        # Update chain with final agent if not already added
        if primary_agent.agent_id not in chain.agents:
            chain.add_handoff(primary_agent.agent_id, "specialist_processing")
        
        # Add agent info to response
        specialist_response["handoff_candidates"] = self._get_handoff_candidates(
            primary_agent.agent_id
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        specialist_response["processing_time_ms"] = processing_time
        
        return CoordinationResult(
            response=specialist_response,
            handoff_chain=chain,
            primary_agent_id=primary_agent.agent_id,
            was_handed_off=len(chain.agents) > 1,
            processing_time_ms=processing_time
        )
    
    def process_with_handoff(
        self,
        current_agent: BaseAgent,
        target_agent_id: str,
        context: ProcessingContext,
        reason: str
    ) -> CoordinationResult:
        """
        Process query with handoff from one agent to another.
        
        Args:
            current_agent: Current agent processing the query
            target_agent_id: ID of agent to handoff to
            context: Processing context
            reason: Reason for handoff
            
        Returns:
            CoordinationResult from target agent
        """
        start_time = time.time()
        
        # Get or create trace ID
        trace_id = context.trace_id or generate_trace_id()
        
        # Get or create chain
        if trace_id in self._active_chains:
            chain = self._active_chains[trace_id]
        else:
            chain = HandoffChain(trace_id=trace_id)
            self._active_chains[trace_id] = chain
        
        # Add current agent if not in chain
        if current_agent.agent_id not in chain.agents:
            chain.add_handoff(current_agent.agent_id, "initial_processing")
        
        # Get target agent
        target_agent = self._registry.get_agent(target_agent_id)
        
        if target_agent is None:
            # Target not found - return error
            error_response = AgentResponse(
                response=f"Cannot handoff to {target_agent_id}: Agent not found",
                confidence=0.0,
                recommendations=["Try a different specialist"],
                references=[],
                handoff_candidates=[],
                agent_id=current_agent.agent_id,
                agent_name=current_agent.name,
                processing_time_ms=int((time.time() - start_time) * 1000),
                trace_id=trace_id,
                metadata={"error": "target_agent_not_found", "target": target_agent_id}
            )
            
            return CoordinationResult(
                response=error_response,
                handoff_chain=chain,
                primary_agent_id=current_agent.agent_id,
                was_handed_off=True,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Add handoff to chain
        chain.add_handoff(target_agent_id, reason)
        
        # Process with target agent
        context.trace_id = trace_id
        target_response = target_agent.process(context)
        
        # Add candidates
        target_response["handoff_candidates"] = self._get_handoff_candidates(target_agent_id)
        
        processing_time = int((time.time() - start_time) * 1000)
        target_response["processing_time_ms"] = processing_time
        
        return CoordinationResult(
            response=target_response,
            handoff_chain=chain,
            primary_agent_id=target_agent_id,
            was_handed_off=True,
            processing_time_ms=processing_time
        )
    
    def process_multiple_agents(
        self,
        query: str,
        agent_ids: List[str],
        patient_context: str = "",
        thread_id: str = "",
        trace_id: str = ""
    ) -> List[CoordinationResult]:
        """
        Process query with multiple agents (for complex cases).
        
        Args:
            query: Clinical query
            agent_ids: List of agent IDs to process with
            patient_context: Patient context
            thread_id: Session ID
            trace_id: Trace ID
            
        Returns:
            List of coordination results from each agent
        """
        if not trace_id:
            trace_id = generate_trace_id()
        
        results = []
        
        for agent_id in agent_ids:
            agent = self._registry.get_agent(agent_id)
            
            if agent is None:
                continue
            
            context = ProcessingContext(
                query=query,
                patient_context=patient_context,
                thread_id=thread_id,
                trace_id=trace_id
            )
            
            chain = HandoffChain(trace_id=trace_id)
            chain.add_handoff(agent_id, "multi_agent_processing")
            
            start_time = time.time()
            response = agent.process(context)
            response["handoff_candidates"] = self._get_handoff_candidates(agent_id)
            response["processing_time_ms"] = int((time.time() - start_time) * 1000)
            
            results.append(CoordinationResult(
                response=response,
                handoff_chain=chain,
                primary_agent_id=agent_id,
                was_handed_off=False,
                processing_time_ms=response["processing_time_ms"]
            ))
        
        return results
    
    def _get_handoff_candidates(self, agent_id: str) -> List[str]:
        """Get list of possible handoff candidates for an agent."""
        candidates = self._registry.get_handoff_candidates(agent_id)
        return [c.agent_id for c in candidates]
    
    def get_chain(self, trace_id: str) -> Optional[HandoffChain]:
        """Get handoff chain for a trace ID."""
        return self._active_chains.get(trace_id)
    
    def aggregate_responses(
        self,
        results: List[CoordinationResult]
    ) -> AgentResponse:
        """
        Aggregate responses from multiple agents.
        
        Args:
            results: List of coordination results
            
        Returns:
            Aggregated response
        """
        if not results:
            return AgentResponse(
                response="No responses to aggregate",
                confidence=0.0,
                recommendations=[],
                references=[],
                agent_id="coordinator",
                agent_name="CDS Coordinator"
            )
        
        # Get the best response (highest confidence)
        best = max(results, key=lambda r: r.response.get("confidence", 0))
        
        # Aggregate recommendations
        all_recommendations = []
        for r in results:
            all_recommendations.extend(r.response.get("recommendations", []))
        
        # Deduplicate recommendations
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec.lower() not in seen:
                seen.add(rec.lower())
                unique_recommendations.append(rec)
        
        # Aggregate references
        all_references = []
        for r in results:
            all_references.extend(r.response.get("references", []))
        
        # Build aggregated response
        aggregated = AgentResponse(
            response=best.response.get("response", ""),
            confidence=best.response.get("confidence", 0.5),
            recommendations=unique_recommendations[:10],  # Limit to 10
            references=all_references[:5],  # Limit to 5
            handoff_candidates=list(set(
                c for r in results 
                for c in r.response.get("handoff_candidates", [])
            )),
            agent_id="coordinator",
            agent_name="CDS Coordinator",
            processing_time_ms=sum(r.processing_time_ms for r in results),
            trace_id=best.response.get("trace_id", ""),
            metadata={
                "aggregation": "multi_agent",
                "agents_consulted": [r.primary_agent_id for r in results],
                "handoff_chain": results[0].handoff_chain.to_dict() if results else {}
            }
        )
        
        return aggregated
    
    def clear_chains(self, older_than_seconds: int = 3600) -> int:
        """
        Clear old handoff chains to save memory.
        
        Args:
            older_than_seconds: Clear chains older than this
            
        Returns:
            Number of chains cleared
        """
        current_time = datetime.now()
        to_clear = []
        
        for trace_id, chain in self._active_chains.items():
            if chain.timestamps:
                last_time = datetime.fromisoformat(chain.timestamps[-1])
                age = (current_time - last_time).total_seconds()
                
                if age > older_than_seconds:
                    to_clear.append(trace_id)
        
        for trace_id in to_clear:
            del self._active_chains[trace_id]
        
        return len(to_clear)


# =============================================================================
# COORDINATOR FACTORY
# =============================================================================

_coordinator: Optional[CDSCoordinator] = None


def get_coordinator(registry: Optional[AgentRegistry] = None) -> CDSCoordinator:
    """
    Get the global coordinator instance.
    
    Args:
        registry: Optional registry to use
        
    Returns:
        CDSCoordinator singleton
    """
    global _coordinator
    if _coordinator is None:
        _coordinator = CDSCoordinator(registry)
    return _coordinator


def reset_coordinator() -> None:
    """Reset the coordinator (useful for testing)."""
    global _coordinator
    _coordinator = None
