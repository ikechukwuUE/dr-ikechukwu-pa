"""
Evaluation Metrics Service
Provides in-memory storage and retrieval of evaluation metrics for interactions.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import logging

logger = logging.getLogger(__name__)


class EvaluationMetrics(TypedDict):
    """TypedDict for evaluation metrics for each interaction."""
    user_id: str
    interaction_id: str
    domain: str
    agent_id: str
    user_rating: int  # 1-5
    helpful: bool
    feedback_text: Optional[str]
    response_time_ms: int
    tokens_used: int
    accuracy_score: Optional[float]  # Future: model-predicted accuracy
    created_at: str


class EvaluationService:
    """
    Service for collecting and retrieving evaluation metrics.
    Uses in-memory storage (can be swapped to PostgreSQL later with Neon).
    """
    
    def __init__(self):
        # In-memory storage: list of all interactions
        self._interactions: List[EvaluationMetrics] = []
        # Indexes for faster lookups
        self._by_agent: Dict[str, List[EvaluationMetrics]] = defaultdict(list)
        self._by_domain: Dict[str, List[EvaluationMetrics]] = defaultdict(list)
        self._by_user: Dict[str, List[EvaluationMetrics]] = defaultdict(list)
        self._by_interaction: Dict[str, EvaluationMetrics] = {}
        
        logger.info("EvaluationService initialized with in-memory storage")
    
    def record_interaction(
        self,
        user_id: str,
        domain: str,
        agent_id: str,
        user_rating: int,
        helpful: bool,
        response_time_ms: int,
        tokens_used: int,
        feedback_text: Optional[str] = None,
        accuracy_score: Optional[float] = None,
        interaction_id: Optional[str] = None
    ) -> EvaluationMetrics:
        """
        Record a new interaction with metrics.
        
        Args:
            user_id: Unique identifier for the user
            domain: Domain of the interaction (finance, fashion, ai_dev, clinical, etc.)
            agent_id: Identifier for the agent that handled the interaction
            user_rating: User rating from 1-5
            helpful: Whether the user found the response helpful
            response_time_ms: Response time in milliseconds
            tokens_used: Number of tokens used for the response
            feedback_text: Optional user feedback text
            accuracy_score: Optional model-predicted accuracy score
            interaction_id: Optional custom interaction ID (generated if not provided)
            
        Returns:
            The recorded interaction metrics
        """
        # Validate rating
        if not 1 <= user_rating <= 5:
            raise ValueError("user_rating must be between 1 and 5")
        
        # Generate interaction ID if not provided
        if interaction_id is None:
            interaction_id = str(uuid.uuid4())
        
        # Create metrics entry
        metrics: EvaluationMetrics = {
            "user_id": user_id,
            "interaction_id": interaction_id,
            "domain": domain,
            "agent_id": agent_id,
            "user_rating": user_rating,
            "helpful": helpful,
            "feedback_text": feedback_text,
            "response_time_ms": response_time_ms,
            "tokens_used": tokens_used,
            "accuracy_score": accuracy_score,
            "created_at": datetime.now().isoformat()
        }
        
        # Store the interaction
        self._interactions.append(metrics)
        self._by_agent[agent_id].append(metrics)
        self._by_domain[domain].append(metrics)
        self._by_user[user_id].append(metrics)
        self._by_interaction[interaction_id] = metrics
        
        logger.info(
            f"Recorded interaction {interaction_id}: "
            f"domain={domain}, agent={agent_id}, rating={user_rating}"
        )
        
        return metrics
    
    def get_metrics(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 100
    ) -> List[EvaluationMetrics]:
        """
        Retrieve metrics with optional filtering.
        
        Args:
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            domain: Filter by domain
            limit: Maximum number of results to return
            
        Returns:
            List of matching evaluation metrics
        """
        results = self._interactions
        
        if user_id:
            results = [m for m in results if m["user_id"] == user_id]
        
        if agent_id:
            results = [m for m in results if m["agent_id"] == agent_id]
        
        if domain:
            results = [m for m in results if m["domain"] == domain]
        
        # Return most recent first, limited
        results = sorted(results, key=lambda x: x["created_at"], reverse=True)
        return results[:limit]
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """
        Get aggregated performance metrics for a specific agent.
        
        Args:
            agent_id: The agent to get metrics for
            
        Returns:
            Dictionary with aggregated metrics
        """
        interactions = self._by_agent.get(agent_id, [])
        
        if not interactions:
            return {
                "agent_id": agent_id,
                "total_interactions": 0,
                "message": "No interactions found for this agent"
            }
        
        # Calculate aggregations
        total = len(interactions)
        ratings = [m["user_rating"] for m in interactions]
        helpful_count = sum(1 for m in interactions if m["helpful"])
        response_times = [m["response_time_ms"] for m in interactions]
        tokens_used = [m["tokens_used"] for m in interactions]
        
        # Rating distribution
        rating_distribution = defaultdict(int)
        for r in ratings:
            rating_distribution[r] += 1
        
        return {
            "agent_id": agent_id,
            "total_interactions": total,
            "average_rating": sum(ratings) / total,
            "rating_distribution": dict(rating_distribution),
            "helpfulness_rate": helpful_count / total,
            "average_response_time_ms": sum(response_times) / total,
            "total_tokens_used": sum(tokens_used),
            "average_tokens_per_response": sum(tokens_used) / total,
            "domains_served": list(set(m["domain"] for m in interactions))
        }
    
    def get_domain_performance(self, domain: str) -> Dict[str, Any]:
        """
        Get aggregated performance metrics for a specific domain.
        
        Args:
            domain: The domain to get metrics for
            
        Returns:
            Dictionary with aggregated metrics
        """
        interactions = self._by_domain.get(domain, [])
        
        if not interactions:
            return {
                "domain": domain,
                "total_interactions": 0,
                "message": "No interactions found for this domain"
            }
        
        # Calculate aggregations
        total = len(interactions)
        ratings = [m["user_rating"] for m in interactions]
        helpful_count = sum(1 for m in interactions if m["helpful"])
        response_times = [m["response_time_ms"] for m in interactions]
        tokens_used = [m["tokens_used"] for m in interactions]
        
        # Rating distribution
        rating_distribution = defaultdict(int)
        for r in ratings:
            rating_distribution[r] += 1
        
        # Agent breakdown
        agent_breakdown = {}
        for m in interactions:
            agent_id = m["agent_id"]
            if agent_id not in agent_breakdown:
                agent_breakdown[agent_id] = {
                    "total": 0,
                    "avg_rating": [],
                    "helpful_count": 0
                }
            agent_breakdown[agent_id]["total"] += 1
            agent_breakdown[agent_id]["avg_rating"].append(m["user_rating"])
            if m["helpful"]:
                agent_breakdown[agent_id]["helpful_count"] += 1
        
        # Finalize agent breakdown
        for agent_id in agent_breakdown:
            ratings_list = agent_breakdown[agent_id]["avg_rating"]
            agent_breakdown[agent_id]["avg_rating"] = (
                sum(ratings_list) / len(ratings_list) if ratings_list else 0
            )
            agent_breakdown[agent_id]["helpfulness_rate"] = (
                agent_breakdown[agent_id]["helpful_count"] / 
                agent_breakdown[agent_id]["total"]
            )
        
        return {
            "domain": domain,
            "total_interactions": total,
            "average_rating": sum(ratings) / total,
            "rating_distribution": dict(rating_distribution),
            "helpfulness_rate": helpful_count / total,
            "average_response_time_ms": sum(response_times) / total,
            "total_tokens_used": sum(tokens_used),
            "average_tokens_per_response": sum(tokens_used) / total,
            "agent_breakdown": agent_breakdown
        }
    
    def get_user_satisfaction_trend(self, days: int = 7) -> Dict[str, Any]:
        """
        Get historical user satisfaction trend.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with daily satisfaction metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter interactions within the time window
        recent_interactions = [
            m for m in self._interactions
            if datetime.fromisoformat(m["created_at"]) >= cutoff_date
        ]
        
        if not recent_interactions:
            return {
                "period_days": days,
                "total_interactions": 0,
                "message": "No interactions in the specified period"
            }
        
        # Group by day
        daily_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "ratings": [],
            "helpful": 0,
            "response_times": []
        })
        
        for m in recent_interactions:
            day = m["created_at"][:10]  # YYYY-MM-DD
            daily_metrics[day]["total"] += 1
            daily_metrics[day]["ratings"].append(m["user_rating"])
            if m["helpful"]:
                daily_metrics[day]["helpful"] += 1
            daily_metrics[day]["response_times"].append(m["response_time_ms"])
        
        # Calculate daily averages
        daily_trend: List[Dict[str, Any]] = []
        for day in sorted(daily_metrics.keys()):
            data = daily_metrics[day]
            ratings_list: List[int] = data["ratings"]
            times_list: List[int] = data["response_times"]
            daily_trend.append({
                "date": day,
                "total_interactions": data["total"],
                "average_rating": sum(ratings_list) / len(ratings_list) if ratings_list else 0,
                "helpfulness_rate": data["helpful"] / data["total"] if data["total"] > 0 else 0,
                "average_response_time_ms": sum(times_list) / len(times_list) if times_list else 0
            })
        
        # Overall summary
        all_ratings = [m["user_rating"] for m in recent_interactions]
        all_helpful = sum(1 for m in recent_interactions if m["helpful"])
        
        return {
            "period_days": days,
            "total_interactions": len(recent_interactions),
            "overall_average_rating": sum(all_ratings) / len(all_ratings),
            "overall_helpfulness_rate": all_helpful / len(recent_interactions),
            "daily_trend": daily_trend
        }
    
    def get_interaction(self, interaction_id: str) -> Optional[EvaluationMetrics]:
        """Get a specific interaction by ID."""
        return self._by_interaction.get(interaction_id)


# Singleton instance for shared use across the application
evaluation_service = EvaluationService()
