"""
Evaluation System API Routes
Provides endpoints for feedback submission, metrics retrieval, and performance analysis.
"""

from flask import Blueprint, request, jsonify
import logging

from src.agents.evaluation.metrics import EvaluationService, evaluation_service
from src.agents.evaluation.optimizer import Optimizer

logger = logging.getLogger(__name__)

# Create blueprint
evaluation_bp = Blueprint("evaluation", __name__, url_prefix="/evaluation")

# Initialize optimizer with evaluation service
optimizer = Optimizer(evaluation_service)


# ============================================================================
# POST /evaluation/feedback - Submit feedback for an interaction
# ============================================================================
@evaluation_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    """
    Submit feedback for an interaction.
    
    Request body:
    {
        "user_id": str,           # Required: User identifier
        "interaction_id": str,   # Optional: Interaction ID (generated if not provided)
        "domain": str,            # Required: Domain (finance, fashion, ai_dev, clinical, etc.)
        "agent_id": str,          # Required: Agent identifier
        "user_rating": int,       # Required: Rating 1-5
        "helpful": bool,          # Required: Whether response was helpful
        "feedback_text": str,     # Optional: User feedback
        "response_time_ms": int,  # Required: Response time in milliseconds
        "tokens_used": int,       # Required: Tokens used
        "accuracy_score": float   # Optional: Model-predicted accuracy
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate required fields
        required_fields = [
            "user_id", "domain", "agent_id", "user_rating", 
            "helpful", "response_time_ms", "tokens_used"
        ]
        
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "status": "error"
            }), 400
        
        # Validate rating range
        rating = data["user_rating"]
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            return jsonify({
                "error": "user_rating must be an integer between 1 and 5",
                "status": "error"
            }), 400
        
        # Record the interaction
        metrics = evaluation_service.record_interaction(
            user_id=data["user_id"],
            interaction_id=data.get("interaction_id"),
            domain=data["domain"],
            agent_id=data["agent_id"],
            user_rating=rating,
            helpful=bool(data["helpful"]),
            feedback_text=data.get("feedback_text"),
            response_time_ms=int(data["response_time_ms"]),
            tokens_used=int(data["tokens_used"]),
            accuracy_score=data.get("accuracy_score")
        )
        
        logger.info(
            f"Feedback recorded: interaction={metrics['interaction_id']}, "
            f"rating={rating}, helpful={data['helpful']}"
        )
        
        return jsonify({
            "status": "success",
            "message": "Feedback recorded successfully",
            "data": {
                "interaction_id": metrics["interaction_id"],
                "created_at": metrics["created_at"]
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 400
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/metrics - Get aggregated metrics
# ============================================================================
@evaluation_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Get evaluation metrics with optional filtering.
    
    Query parameters:
    - user_id: Filter by user ID
    - agent_id: Filter by agent ID  
    - domain: Filter by domain
    - limit: Maximum results (default 100)
    """
    try:
        # Get query parameters
        user_id = request.args.get("user_id")
        agent_id = request.args.get("agent_id")
        domain = request.args.get("domain")
        
        try:
            limit = int(request.args.get("limit", 100))
            limit = min(max(limit, 1), 1000)  # Clamp between 1 and 1000
        except ValueError:
            limit = 100
        
        # Get metrics
        metrics = evaluation_service.get_metrics(
            user_id=user_id,
            agent_id=agent_id,
            domain=domain,
            limit=limit
        )
        
        return jsonify({
            "status": "success",
            "data": {
                "metrics": metrics,
                "count": len(metrics)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/agent/<agent_id> - Agent performance
# ============================================================================
@evaluation_bp.route("/agent/<agent_id>", methods=["GET"])
def get_agent_performance(agent_id: str):
    """
    Get aggregated performance metrics for a specific agent.
    
    Path parameter:
    - agent_id: The agent identifier
    """
    try:
        perf = evaluation_service.get_agent_performance(agent_id)
        
        return jsonify({
            "status": "success",
            "data": perf
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/domain/<domain> - Domain performance
# ============================================================================
@evaluation_bp.route("/domain/<domain>", methods=["GET"])
def get_domain_performance(domain: str):
    """
    Get aggregated performance metrics for a specific domain.
    
    Path parameter:
    - domain: The domain identifier
    """
    try:
        perf = evaluation_service.get_domain_performance(domain)
        
        return jsonify({
            "status": "success",
            "data": perf
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting domain performance: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/trend - User satisfaction trend
# ============================================================================
@evaluation_bp.route("/trend", methods=["GET"])
def get_satisfaction_trend():
    """
    Get historical user satisfaction trend.
    
    Query parameters:
    - days: Number of days to look back (default 7)
    """
    try:
        try:
            days = int(request.args.get("days", 7))
            days = min(max(days, 1), 90)  # Clamp between 1 and 90
        except ValueError:
            days = 7
        
        trend = evaluation_service.get_user_satisfaction_trend(days=days)
        
        return jsonify({
            "status": "success",
            "data": trend
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting satisfaction trend: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/improvements - Improvement suggestions
# ============================================================================
@evaluation_bp.route("/improvements", methods=["GET"])
def get_improvements():
    """
    Get improvement suggestions.
    
    Query parameters:
    - agent_id: Optional agent ID to get specific suggestions for
    """
    try:
        agent_id = request.args.get("agent_id")
        
        suggestions = optimizer.suggest_improvements(agent_id=agent_id)
        
        return jsonify({
            "status": "success",
            "data": {
                "suggestions": suggestions,
                "count": len(suggestions)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/analyze/low-rated - Analyze low-rated interactions
# ============================================================================
@evaluation_bp.route("/analyze/low-rated", methods=["GET"])
def analyze_low_rated():
    """
    Analyze patterns in low-rated interactions.
    
    Query parameters:
    - threshold: Rating threshold for low ratings (default 3)
    """
    try:
        try:
            threshold = int(request.args.get("threshold", 3))
            threshold = min(max(threshold, 1), 5)
        except ValueError:
            threshold = 3
        
        analysis = optimizer.analyze_low_rated(threshold=threshold)
        
        return jsonify({
            "status": "success",
            "data": analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing low-rated: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/report - Performance report
# ============================================================================
@evaluation_bp.route("/report", methods=["GET"])
def get_report():
    """
    Get comprehensive performance report.
    """
    try:
        report = optimizer.generate_report()
        
        return jsonify({
            "status": "success",
            "data": report
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/dashboard - Dashboard data
# ============================================================================
@evaluation_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """
    Get dashboard data for visualization.
    Includes overall performance, trends, and key metrics.
    """
    try:
        # Get overall performance
        performance = optimizer.analyze_performance()
        
        # Get satisfaction trend
        trend = evaluation_service.get_user_satisfaction_trend(days=7)
        
        # Get improvement suggestions
        suggestions = optimizer.suggest_improvements()[:5]  # Top 5
        
        # Get domain breakdown
        all_metrics = evaluation_service.get_metrics(limit=1000)
        domains = set(m["domain"] for m in all_metrics)
        domain_data = {}
        for domain in domains:
            domain_data[domain] = evaluation_service.get_domain_performance(domain)
        
        # Build dashboard response
        dashboard = {
            "overview": {
                "health_score": performance.get("health_score", 0),
                "total_interactions": performance.get("total_interactions", 0),
                "average_rating": performance.get("average_rating", 0),
                "helpfulness_rate": performance.get("helpfulness_rate", 0),
                "average_response_time_ms": performance.get("average_response_time_ms", 0)
            },
            "rating_distribution": performance.get("rating_distribution", {}),
            "satisfaction_trend": trend,
            "top_improvements": suggestions,
            "domains": domain_data,
            "generated_at": performance.get("timestamp")
        }
        
        return jsonify({
            "status": "success",
            "data": dashboard
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500


# ============================================================================
# GET /evaluation/analyze/performance - Overall performance analysis
# ============================================================================
@evaluation_bp.route("/analyze/performance", methods=["GET"])
def analyze_performance():
    """
    Get overall performance analysis.
    """
    try:
        analysis = optimizer.analyze_performance()
        
        return jsonify({
            "status": "success",
            "data": analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing performance: {e}")
        return jsonify({
            "error": "Internal server error",
            "status": "error"
        }), 500
