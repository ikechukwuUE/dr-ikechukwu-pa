"""
Optimizer for Self-Improving Models
Provides analysis, improvement suggestions, and performance reports.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from src.agents.evaluation.metrics import (
    EvaluationService,
    EvaluationMetrics
)

logger = logging.getLogger(__name__)


class ImprovementSuggestion(TypedDict):
    """TypedDict for improvement suggestions."""
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    agent_id: Optional[str]
    domain: Optional[str]
    metric_impact: Optional[Dict[str, float]]


class Optimizer:
    """
    Optimizer class for analyzing performance and generating improvement suggestions.
    Uses the EvaluationService to retrieve metrics and analyze patterns.
    """
    
    def __init__(self, evaluation_service: EvaluationService):
        """
        Initialize the optimizer with an evaluation service.
        
        Args:
            evaluation_service: The evaluation service to use for metrics
        """
        self._eval_service = evaluation_service
        logger.info("Optimizer initialized")
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Perform overall performance analysis across all agents and domains.
        
        Returns:
            Dictionary with comprehensive performance analysis
        """
        # Get recent interactions for analysis
        all_metrics = self._eval_service.get_metrics(limit=1000)
        
        if not all_metrics:
            return {
                "status": "no_data",
                "message": "No evaluation data available yet"
            }
        
        # Calculate overall metrics
        total_interactions = len(all_metrics)
        ratings = [m["user_rating"] for m in all_metrics]
        helpful_count = sum(1 for m in all_metrics if m["helpful"])
        response_times = [m["response_time_ms"] for m in all_metrics]
        tokens_used = [m["tokens_used"] for m in all_metrics]
        
        # Rating distribution
        rating_distribution: Dict[int, int] = {}
        for r in ratings:
            rating_distribution[r] = rating_distribution.get(r, 0) + 1
        
        # Domain breakdown
        domain_stats: Dict[str, Dict[str, Any]] = {}
        for m in all_metrics:
            domain = m["domain"]
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "total": 0,
                    "ratings": [],
                    "helpful": 0,
                    "response_times": []
                }
            domain_stats[domain]["total"] += 1
            domain_stats[domain]["ratings"].append(m["user_rating"])
            if m["helpful"]:
                domain_stats[domain]["helpful"] += 1
            domain_stats[domain]["response_times"].append(m["response_time_ms"])
        
        # Finalize domain stats
        for domain in domain_stats:
            stats = domain_stats[domain]
            domain_stats[domain] = {
                "total_interactions": stats["total"],
                "average_rating": sum(stats["ratings"]) / len(stats["ratings"]),
                "helpfulness_rate": stats["helpful"] / stats["total"],
                "average_response_time_ms": sum(stats["response_times"]) / len(stats["response_times"])
            }
        
        # Identify performance trends
        satisfaction_trend = self._eval_service.get_user_satisfaction_trend(days=7)
        
        # Calculate overall health score (0-100)
        avg_rating = sum(ratings) / len(ratings)
        helpful_rate = helpful_count / total_interactions
        avg_response_time = sum(response_times) / len(response_times)
        
        # Health score based on multiple factors
        health_score = (
            (avg_rating / 5.0) * 40 +  # 40% weight on rating
            helpful_rate * 40 +  # 40% weight on helpfulness
            (max(0, 100 - avg_response_time / 100)) * 0.2  # 20% weight on speed
        )
        
        return {
            "status": "analyzed",
            "timestamp": datetime.now().isoformat(),
            "total_interactions": total_interactions,
            "health_score": round(health_score, 2),
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_distribution,
            "helpfulness_rate": round(helpful_rate, 2),
            "average_response_time_ms": round(avg_response_time, 2),
            "total_tokens_used": sum(tokens_used),
            "domain_breakdown": domain_stats,
            "satisfaction_trend": satisfaction_trend
        }
    
    def suggest_improvements(self, agent_id: Optional[str] = None) -> List[ImprovementSuggestion]:
        """
        Generate improvement suggestions for a specific agent or overall.
        
        Args:
            agent_id: Optional agent ID to get specific suggestions for
            
        Returns:
            List of improvement suggestions
        """
        suggestions: List[ImprovementSuggestion] = []
        
        if agent_id:
            # Get agent-specific performance
            perf = self._eval_service.get_agent_performance(agent_id)
            
            if perf.get("total_interactions", 0) == 0:
                return [{
                    "category": "data",
                    "priority": "low",
                    "title": "Insufficient Data",
                    "description": f"No interactions found for agent {agent_id}. More data is needed before meaningful improvements can be suggested.",
                    "agent_id": agent_id,
                    "domain": None,
                    "metric_impact": None
                }]
            
            # Analyze agent-specific issues
            if perf.get("average_rating", 0) < 3.5:
                suggestions.append({
                    "category": "quality",
                    "priority": "high",
                    "title": "Low Average Rating",
                    "description": f"Agent {agent_id} has a low average rating of {perf.get('average_rating', 0):.2f}. Consider reviewing response quality and accuracy.",
                    "agent_id": agent_id,
                    "domain": None,
                    "metric_impact": {"rating": 0.5}
                })
            
            if perf.get("helpfulness_rate", 0) < 0.7:
                suggestions.append({
                    "category": "helpfulness",
                    "priority": "high",
                    "title": "Low Helpfulness Rate",
                    "description": f"Agent {agent_id} has a helpfulness rate of {perf.get('helpfulness_rate', 0):.2%}. Review responses to ensure they address user needs.",
                    "agent_id": agent_id,
                    "domain": None,
                    "metric_impact": {"helpfulness": 0.3}
                })
            
            avg_response_time = perf.get("average_response_time_ms", 0)
            if avg_response_time > 5000:  # 5 seconds
                suggestions.append({
                    "category": "performance",
                    "priority": "medium",
                    "title": "Slow Response Time",
                    "description": f"Agent {agent_id} has an average response time of {avg_response_time:.0f}ms. Consider optimizing processing.",
                    "agent_id": agent_id,
                    "domain": None,
                    "metric_impact": {"response_time": -0.2}
                })
                
        else:
            # Overall suggestions
            perf = self.analyze_performance()
            
            if perf.get("status") == "no_data":
                return [{
                    "category": "data",
                    "priority": "low",
                    "title": "No Data Available",
                    "description": "Collect more user feedback to generate meaningful improvement suggestions.",
                    "agent_id": None,
                    "domain": None,
                    "metric_impact": None
                }]
            
            # Check overall rating
            if perf.get("average_rating", 0) < 3.5:
                suggestions.append({
                    "category": "quality",
                    "priority": "high",
                    "title": "Improve Overall Response Quality",
                    "description": "The system has a low average rating. Consider reviewing agent prompts and response generation.",
                    "agent_id": None,
                    "domain": None,
                    "metric_impact": {"rating": 0.5}
                })
            
            # Check response times across domains
            domain_breakdown = perf.get("domain_breakdown", {})
            for domain, stats in domain_breakdown.items():
                if stats.get("average_response_time_ms", 0) > 8000:
                    suggestions.append({
                        "category": "performance",
                        "priority": "medium",
                        "title": f"Optimize {domain.title()} Domain Speed",
                        "description": f"The {domain} domain has slow response times ({stats.get('average_response_time_ms', 0):.0f}ms avg). Consider optimization.",
                        "agent_id": None,
                        "domain": domain,
                        "metric_impact": {"response_time": -0.15}
                    })
            
            # Check domains with low ratings
            for domain, stats in domain_breakdown.items():
                if stats.get("average_rating", 0) < 3.0:
                    suggestions.append({
                        "category": "quality",
                        "priority": "high",
                        "title": f"Improve {domain.title()} Domain Quality",
                        "description": f"The {domain} domain has low ratings ({stats.get('average_rating', 0):.2f} avg). Focus on improving responses.",
                        "agent_id": None,
                        "domain": domain,
                        "metric_impact": {"rating": 0.4}
                    })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return suggestions
    
    def analyze_low_rated(self, threshold: int = 3) -> Dict[str, Any]:
        """
        Analyze patterns in low-rated interactions.
        
        Args:
            threshold: Rating threshold for \"low\" ratings (default 3)
            
        Returns:
            Dictionary with analysis of low-rated interactions
        """
        # Get all interactions
        all_metrics = self._eval_service.get_metrics(limit=1000)
        
        # Filter low-rated
        low_rated = [m for m in all_metrics if m["user_rating"] <= threshold]
        
        if not low_rated:
            return {
                "status": "no_issues",
                "message": f"No interactions with rating {threshold} or below found",
                "low_rated_count": 0
            }
        
        # Analyze patterns
        domains: Dict[str, int] = {}
        agents: Dict[str, int] = {}
        response_times: List[int] = []
        feedback_texts: List[str] = []
        
        for m in low_rated:
            # Domain distribution
            domain = m["domain"]
            domains[domain] = domains.get(domain, 0) + 1
            
            # Agent distribution
            agent = m["agent_id"]
            agents[agent] = agents.get(agent, 0) + 1
            
            # Response times
            response_times.append(m["response_time_ms"])
            
            # Collect feedback if available
            feedback = m.get("feedback_text")
            if feedback:
                feedback_texts.append(feedback)
        
        # Identify common issues
        issues: List[Dict[str, Any]] = []
        
        # Most problematic domain
        if domains:
            worst_domain = max(domains.items(), key=lambda x: x[1])
            if worst_domain[1] >= len(low_rated) * 0.3:  # 30%+ of low ratings
                issues.append({
                    "type": "domain",
                    "description": f"{worst_domain[0]} domain accounts for {worst_domain[1]} low ratings",
                    "count": worst_domain[1]
                })
        
        # Most problematic agent
        if agents:
            worst_agent = max(agents.items(), key=lambda x: x[1])
            if worst_agent[1] >= len(low_rated) * 0.3:
                issues.append({
                    "type": "agent",
                    "description": f"Agent {worst_agent[0]} has {worst_agent[1]} low ratings",
                    "count": worst_agent[1]
                })
        
        # Response time correlation
        if response_times:
            avg_low_rated_time = sum(response_times) / len(response_times)
            all_times = [m["response_time_ms"] for m in all_metrics]
            avg_all_time = sum(all_times) / len(all_times) if all_times else 0
            
            if avg_low_rated_time > avg_all_time * 1.3:  # 30% slower
                issues.append({
                    "type": "performance",
                    "description": f"Low-rated responses are {avg_low_rated_time / avg_all_time:.1f}x slower on average",
                    "count": len(response_times)
                })
        
        return {
            "status": "analyzed",
            "threshold": threshold,
            "low_rated_count": len(low_rated),
            "percentage_of_total": round(len(low_rated) / len(all_metrics) * 100, 2) if all_metrics else 0,
            "domain_distribution": domains,
            "agent_distribution": agents,
            "common_issues": issues,
            "sample_feedback": feedback_texts[:10] if feedback_texts else []
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dictionary with comprehensive performance report
        """
        # Get overall performance
        performance = self.analyze_performance()
        
        # Get improvement suggestions
        suggestions = self.suggest_improvements()
        
        # Get low-rated analysis
        low_rated_analysis = self.analyze_low_rated()
        
        # Get recent trends
        satisfaction_trend = self._eval_service.get_user_satisfaction_trend(days=7)
        
        # Get all unique agents and their performance
        all_metrics = self._eval_service.get_metrics(limit=1000)
        agent_ids = set(m["agent_id"] for m in all_metrics)
        
        agent_performances = {}
        for agent_id in agent_ids:
            agent_performances[agent_id] = self._eval_service.get_agent_performance(agent_id)
        
        # Get all domains
        domains = set(m["domain"] for m in all_metrics)
        domain_performances = {}
        for domain in domains:
            domain_performances[domain] = self._eval_service.get_domain_performance(domain)
        
        return {
            "report_type": "comprehensive",
            "generated_at": datetime.now().isoformat(),
            "performance_summary": performance,
            "improvement_suggestions": suggestions,
            "low_rated_analysis": low_rated_analysis,
            "satisfaction_trend": satisfaction_trend,
            "agent_performances": agent_performances,
            "domain_performances": domain_performances,
            "recommendations": self._generate_recommendations(
                performance,
                suggestions,
                low_rated_analysis
            )
        }
    
    def _generate_recommendations(
        self,
        performance: Dict[str, Any],
        suggestions: List[ImprovementSuggestion],
        low_rated_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis."""
        recommendations: List[Dict[str, str]] = []
        
        # High-priority recommendations based on issues
        for suggestion in suggestions:
            if suggestion["priority"] == "high":
                recommendations.append({
                    "action": suggestion["title"],
                    "rationale": suggestion["description"],
                    "priority": "high"
                })
        
        # Add recommendations based on low-rated analysis
        if low_rated_analysis.get("common_issues"):
            for issue in low_rated_analysis["common_issues"]:
                if issue.get("type") == "domain":
                    recommendations.append({
                        "action": f"Focus on improving {issue['description'].split()[0]} domain",
                        "rationale": "This domain has the highest concentration of low ratings",
                        "priority": "high"
                    })
                elif issue.get("type") == "performance":
                    recommendations.append({
                        "action": "Optimize response processing time",
                        "rationale": issue["description"],
                        "priority": "medium"
                    })
        
        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations.append({
                "action": "Continue monitoring",
                "rationale": "System is performing well, continue collecting feedback",
                "priority": "low"
            })
        
        return recommendations
