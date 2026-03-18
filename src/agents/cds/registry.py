"""
CDS Agent Registry
=================
Central registry for all CDS agents.
Maps queries to available agents and provides agent lookup.

Features:
- Agent registration and lookup
- Query-to-agent mapping
- Agent capability matching
- Agent lifecycle management
"""

from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, field

from src.agents.cds.base_agent import BaseAgent, AgentSpec, ProcessingContext

logger = logging.getLogger(__name__)


# =============================================================================
# REGISTRY DATA STRUCTURES
# =============================================================================

@dataclass
class AgentRegistration:
    """Registration record for an agent."""
    agent: BaseAgent
    spec: AgentSpec
    is_active: bool = True
    is_triage: bool = False


class AgentRegistry:
    """
    Central registry for all CDS agents.
    
    Manages agent registration, lookup, and capability matching.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, AgentRegistration] = {}
        self._triage_agent: Optional[BaseAgent] = None
        self._initialized = False
        logger.info("AgentRegistry initialized")
    
    def register(self, agent: BaseAgent, is_triage: bool = False) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent: Agent instance to register
            is_triage: Whether this is the triage agent
        """
        agent_id = agent.agent_id
        
        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} already registered, replacing")
        
        self._agents[agent_id] = AgentRegistration(
            agent=agent,
            spec=agent.get_capabilities(),
            is_active=True,
            is_triage=is_triage
        )
        
        if is_triage:
            self._triage_agent = agent
        
        logger.info(f"Registered agent: {agent_id} (triage={is_triage})")
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            True if successful, False if not found
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of agent to retrieve
            
        Returns:
            Agent instance or None
        """
        registration = self._agents.get(agent_id)
        return registration.agent if registration else None
    
    def get_all_agents(self) -> List[BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent instances
        """
        return [reg.agent for reg in self._agents.values() if reg.is_active]
    
    def get_triage_agent(self) -> Optional[BaseAgent]:
        """
        Get the triage agent.
        
        Returns:
            Triage agent or None
        """
        return self._triage_agent
    
    def find_best_agent(
        self, 
        query: str, 
        context: Optional[ProcessingContext] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[BaseAgent]:
        """
        Find the best agent to handle a query.
        
        Uses can_handle() method to determine best match.
        
        Args:
            query: Clinical query
            context: Optional processing context
            exclude_agents: Agent IDs to exclude from consideration
            
        Returns:
            Best matching agent or None
        """
        exclude = set(exclude_agents or [])
        best_agent = None
        best_confidence = 0.0
        
        for agent_id, registration in self._agents.items():
            if not registration.is_active or agent_id in exclude:
                continue
            
            confidence = registration.agent.can_handle(query, context)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_agent = registration.agent
        
        if best_agent and best_confidence > 0.3:
            logger.info(f"Best agent for query: {best_agent.agent_id} (confidence: {best_confidence:.2f})")
            return best_agent
        
        return None
    
    def find_multiple_agents(
        self,
        query: str,
        context: Optional[ProcessingContext] = None,
        max_agents: int = 3,
        min_confidence: float = 0.2
    ) -> List[BaseAgent]:
        """
        Find multiple agents that can handle a query.
        
        Args:
            query: Clinical query
            context: Optional processing context
            max_agents: Maximum number of agents to return
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching agents sorted by confidence
        """
        matches = []
        
        for agent_id, registration in self._agents.items():
            if not registration.is_active:
                continue
            
            confidence = registration.agent.can_handle(query, context)
            
            if confidence >= min_confidence:
                matches.append((registration.agent, confidence))
        
        # Sort by confidence descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return [m[0] for m in matches[:max_agents]]
    
    def get_agent_specs(self) -> List[AgentSpec]:
        """
        Get specifications for all registered agents.
        
        Returns:
            List of agent specifications
        """
        return [reg.spec for reg in self._agents.values() if reg.is_active]
    
    def get_active_agent_count(self) -> int:
        """Get count of active agents."""
        return sum(1 for reg in self._agents.values() if reg.is_active)
    
    def set_agent_active(self, agent_id: str, is_active: bool) -> bool:
        """
        Set agent active status.
        
        Args:
            agent_id: ID of agent
            is_active: Whether agent should be active
            
        Returns:
            True if successful
        """
        if agent_id in self._agents:
            self._agents[agent_id].is_active = is_active
            return True
        return False
    
    def is_initialized(self) -> bool:
        """Check if registry is initialized."""
        return self._initialized
    
    def set_initialized(self, value: bool = True) -> None:
        """Set initialization status."""
        self._initialized = value
    
    def get_agents_by_capability(self, capability_name: str) -> List[BaseAgent]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability_name: Name of capability to search for
            
        Returns:
            List of agents with the capability
        """
        matching = []
        
        for registration in self._agents.values():
            if not registration.is_active:
                continue
            
            capabilities = registration.spec.get("capabilities", [])
            for cap in capabilities:
                if cap.get("name") == capability_name:
                    matching.append(registration.agent)
                    break
        
        return matching
    
    def get_handoff_candidates(self, agent_id: str) -> List[BaseAgent]:
        """
        Get agents that a given agent can handoff to.
        
        Args:
            agent_id: Source agent ID
            
        Returns:
            List of possible handoff candidates
        """
        registration = self._agents.get(agent_id)
        if not registration:
            return []
        
        candidate_ids = registration.spec.get("can_handoff_to", [])
        candidates = []
        
        for cid in candidate_ids:
            agent = self.get_agent(cid)
            if agent:
                candidates.append(agent)
        
        return candidates
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get registry status for monitoring.
        
        Returns:
            Dictionary with registry status
        """
        return {
            "total_agents": len(self._agents),
            "active_agents": self.get_active_agent_count(),
            "triage_agent": self._triage_agent.agent_id if self._triage_agent else None,
            "initialized": self._initialized,
            "agent_ids": list(self._agents.keys())
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Returns:
        AgentRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _registry
    _registry = None
