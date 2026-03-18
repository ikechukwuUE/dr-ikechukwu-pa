"""
Semantic Router using Groq LLM
Hybrid routing system that combines keyword-based routing with LLM-based semantic classification.

Routes:
- ai_dev: Code analysis, debugging, optimization
- fashion: Styling, fashion recommendations
- finance: Financial analysis, wealth management
- cds: Clinical decision support
- evaluation: Model evaluation and metrics
"""
import os
import logging
import json
from typing import Dict, List, Optional, Tuple
from flask import request, jsonify

from src.core.config import settings

logger = logging.getLogger(__name__)

# Domain definitions for keyword matching and LLM classification
DOMAINS = {
    "ai_dev": {
        "keywords": ["code", "debug", "optimize", "python", "programming", "software", "bug", "function", 
                     "class", "algorithm", "api", "refactor", "test", "git", "github", "developer", "dev",
                     "neural", "train", "data science", "script", "database", "web", "frontend", "backend"],
        "description": "Code analysis, debugging, optimization, software development",
        "endpoint": "/ai/query"
    },
    "fashion": {
        "keywords": ["fashion", "style", "outfit", "wear", "clothing", "dress", "styling", "look", 
                     "traditional", "ankara", "corporate", "attire", "appearance", "accessories", 
                     "jewelry", "shoes", "wardrobe", "suit", "blazer", "shirt", "trouser"],
        "description": "Fashion styling, outfit recommendations, wardrobe planning",
        "endpoint": "/fashion/query"
    },
    "finance": {
        "keywords": ["finance", "money", "investment", "stock", "portfolio", "wealth", "budget", 
                     "savings", "expense", "income", "trading", "crypto", "banking", "financial",
                     "analysis", "planning", "retirement", "insurance", "loan", "credit"],
        "description": "Financial analysis, wealth management, investment planning",
        "endpoint": "/finance/query"
    },
    "cds": {
        "keywords": ["medical", "health", "diagnosis", "clinical", "patient", "treatment", "doctor",
                     "symptom", "medicine", "hospital", "healthcare", "prescription", "disease",
                     "therapy", "diagnosis", "clinical decision", "triage"],
        "description": "Clinical decision support, medical triage, healthcare assistance",
        "endpoint": "/cds/query"
    },
    "evaluation": {
        "keywords": ["evaluate", "metric", "accuracy", "precision", "recall", "f1", "score",
                     "benchmark", "test", "validation", "performance", "model evaluation",
                     "comparison", "ranking", "results", "auc", "roc", "confusion matrix",
                     "loss", "training", "testing", "cross validation", "hyperparameter"],
        "description": "Model evaluation, metrics calculation, benchmark comparison",
        "endpoint": "/evaluation/query"
    }
}

# Threshold for keyword confidence
KEYWORD_CONFIDENCE_THRESHOLD = 0.7


class HybridRouter:
    """
    Hybrid routing system combining keyword matching with OpenRouter LLM semantic classification.
    
    Flow:
    1. Extract keywords from query and match against domain keywords
    2. If highest keyword confidence >= 0.7, route directly
    3. If highest confidence < 0.7, use OpenRouter LLM for semantic classification
    4. Route to appropriate domain endpoint
    """
    
    # Model configurations
    # Primary: OpenRouter Mistral Small 3.1 24B for semantic routing
    MODEL_PRIMARY = "mistralai/mistral-small-3.1-24b-instruct:free"
    # Backup: Groq Llama 3.3 70B for fallback
    MODEL_BACKUP = "llama-3.3-70b-instruct"
    
    def __init__(self):
        self.openai_client = None
        self.groq_client = None
        self._initialize_openrouter()
        self._initialize_groq()
    
    def _initialize_groq(self):
        """Initialize Groq client if API key is available."""
        groq_api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not configured - Groq fallback unavailable")
            return
        
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=groq_api_key)
            logger.info("Groq client initialized for semantic routing fallback")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
    
    def _initialize_openrouter(self):
        """Initialize OpenRouter client if API key is available."""
        openrouter_api_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY")
        
        if not openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not configured - semantic routing will fallback to keywords only")
            return
        
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter client initialized for semantic routing")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter client: {e}")
    
    def _keyword_match(self, query: str) -> Tuple[str, float]:
        """
        Perform keyword-based matching to determine the target domain.
        
        Returns:
            Tuple of (domain, confidence_score)
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        best_domain = "ai_dev"  # Default fallback
        best_score = 0.0
        
        for domain, config in DOMAINS.items():
            matches = 0
            for keyword in config["keywords"]:
                if keyword in query_lower:
                    matches += 1
            
            # Calculate confidence as ratio of matches to query length
            if query_words:
                score = matches / min(len(config["keywords"]), len(query_words)) * 3
                score = min(score, 1.0)  # Cap at 1.0
            
            if score > best_score:
                best_score = score
                best_domain = domain
        
        logger.info(f"Keyword matching: domain={best_domain}, confidence={best_score:.3f}")
        return best_domain, best_score
    
    def _semantic_classify(self, query: str) -> Optional[Dict]:
        """
        Use OpenRouter LLM for semantic intent classification with Groq fallback.
        
        Returns:
            Dict with domain and confidence, or None if both providers unavailable
        """
        # Try OpenRouter first
        if self.openai_client:
            try:
                result = self._openrouter_classify(query)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenRouter semantic classification failed: {e}")
        
        # Fallback to Groq if OpenRouter failed
        if self.groq_client:
            try:
                result = self._groq_classify(query)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Groq semantic classification failed: {e}")
        
        return None
    
    def _openrouter_classify(self, query: str) -> Optional[Dict]:
        """Classify using OpenRouter Mistral Small 3.1 24B."""
        domains_list = "\n".join([
            f"- {domain}: {config['description']}"
            for domain, config in DOMAINS.items()
        ])
        
        prompt = f"""You are a query classifier for a multi-domain AI assistant.

Classify the following user query into exactly one domain from this list:
{domains_list}

User Query: {query}

Respond with ONLY a JSON object in this exact format:
{{"domain": "domain_name", "confidence": 0.95, "reasoning": "brief explanation"}}

The confidence should be between 0 and 1. Choose the domain that best matches the query intent."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.MODEL_PRIMARY,
                messages=[
                    {"role": "system", "content": "You are a query classifier. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200,
                extra_headers={
                    "HTTP-Referer": "https://dr-ikechukwu-pa.com",
                    "X-Title": "Dr. Ikechukwu PA"
                }
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            domain = result.get("domain", "ai_dev")
            confidence = float(result.get("confidence", 0.5))
            
            # Validate domain
            if domain not in DOMAINS:
                logger.warning(f"Invalid domain from LLM: {domain}, defaulting to ai_dev")
                domain = "ai_dev"
                confidence = 0.5
            
            logger.info(f"OpenRouter semantic classification: domain={domain}, confidence={confidence:.3f}")
            return {"domain": domain, "confidence": confidence}
            
        except Exception as e:
            logger.error(f"OpenRouter semantic classification error: {e}")
            raise
    
    def _groq_classify(self, query: str) -> Optional[Dict]:
        """Classify using Groq Llama 3.3 70B."""
        domains_list = "\n".join([
            f"- {domain}: {config['description']}"
            for domain, config in DOMAINS.items()
        ])
        
        prompt = f"""You are a query classifier for a multi-domain AI assistant.

Classify the following user query into exactly one domain from this list:
{domains_list}

User Query: {query}

Respond with ONLY a JSON object in this exact format:
{{"domain": "domain_name", "confidence": 0.95, "reasoning": "brief explanation"}}

The confidence should be between 0 and 1. Choose the domain that best matches the query intent."""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.MODEL_BACKUP,
                messages=[
                    {"role": "system", "content": "You are a query classifier. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            domain = result.get("domain", "ai_dev")
            confidence = float(result.get("confidence", 0.5))
            
            # Validate domain
            if domain not in DOMAINS:
                logger.warning(f"Invalid domain from Groq: {domain}, defaulting to ai_dev")
                domain = "ai_dev"
                confidence = 0.5
            
            logger.info(f"Groq semantic classification: domain={domain}, confidence={confidence:.3f}")
            return {"domain": domain, "confidence": confidence}
            
        except Exception as e:
            logger.error(f"Groq semantic classification error: {e}")
            return None
    
    def route(self, query: str) -> Dict:
        """
        Main routing logic - determines which domain to route the query to.
        
        Args:
            query: User query string
            
        Returns:
            Dict with routing decision: {domain, endpoint, confidence, method}
        """
        # Step 1: Keyword matching
        keyword_domain, keyword_confidence = self._keyword_match(query)
        
        # Step 2: If confidence is high enough, use keyword result
        if keyword_confidence >= KEYWORD_CONFIDENCE_THRESHOLD:
            return {
                "domain": keyword_domain,
                "endpoint": DOMAINS[keyword_domain]["endpoint"],
                "confidence": keyword_confidence,
                "method": "keyword"
            }
        
        # Step 3: Confidence is low, try semantic classification with Groq
        semantic_result = self._semantic_classify(query)
        
        if semantic_result:
            return {
                "domain": semantic_result["domain"],
                "endpoint": DOMAINS[semantic_result["domain"]]["endpoint"],
                "confidence": semantic_result["confidence"],
                "method": "semantic"
            }
        
        # Step 4: Fallback to keyword result if semantic fails
        return {
            "domain": keyword_domain,
            "endpoint": DOMAINS[keyword_domain]["endpoint"],
            "confidence": keyword_confidence,
            "method": "keyword_fallback"
        }


# Global router instance
router = HybridRouter()


def create_routing_blueprint():
    """Create the routing blueprint with semantic routing endpoints."""
    from flask import Blueprint
    
    routing_bp = Blueprint("routing", __name__, url_prefix="/api")
    
    @routing_bp.route("/route", methods=["POST"])
    def route_query():
        """
        Semantic routing endpoint.
        
        Accepts: { query: string, context?: dict }
        Returns: { domain: string, endpoint: string, confidence: float, method: string }
        """
        try:
            data = request.get_json(silent=True) or {}
            query = data.get("query")
            
            if not query:
                return jsonify({"error": "query is required"}), 400
            
            result = router.route(query)
            return jsonify({
                "status": "success",
                **result
            })
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @routing_bp.route("/route/direct", methods=["POST"])
    def route_direct():
        """
        Direct routing - routes and forwards to the appropriate endpoint.
        
        Accepts: { query: string, ...other_params }
        Returns: Response from the target endpoint
        """
        try:
            from flask import current_app
            
            data = request.get_json(silent=True) or {}
            query = data.get("query")
            
            if not query:
                return jsonify({"error": "query is required"}), 400
            
            # Get routing decision
            routing = router.route(query)
            
            logger.info(f"Routing query to {routing['domain']}: {query[:50]}...")
            
            # Forward to the target endpoint
            # We need to make an internal request to the target blueprint
            endpoint = routing["endpoint"].lstrip("/")
            
            # Build the new data payload for the target service
            target_data = {**data}
            target_data["_routing_metadata"] = {
                "original_query": query,
                "confidence": routing["confidence"],
                "method": routing["method"]
            }
            
            # Use Flask's test client to make internal request
            with current_app.test_client() as client:
                response = client.post(
                    endpoint,
                    json=target_data,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.get_json()
                result["_routing"] = {
                    "domain": routing["domain"],
                    "confidence": routing["confidence"],
                    "method": routing["method"]
                }
                
                return jsonify(result), response.status_code
                
        except Exception as e:
            logger.error(f"Direct routing error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @routing_bp.route("/domains", methods=["GET"])
    def list_domains():
        """List all available domains and their keywords."""
        return jsonify({
            "domains": {
                domain: {
                    "description": config["description"],
                    "keywords": config["keywords"][:10],  # First 10 keywords
                    "endpoint": config["endpoint"]
                }
                for domain, config in DOMAINS.items()
            },
            "keyword_threshold": KEYWORD_CONFIDENCE_THRESHOLD
        })
    
    @routing_bp.route("/router/health", methods=["GET"])
    def router_health():
        """Health check for the routing system."""
        openrouter_status = "configured" if (hasattr(router, 'openai_client') and router.openai_client) else "not_configured"
        groq_status = "configured" if (hasattr(router, 'groq_client') and router.groq_client) else "not_configured"
        
        return jsonify({
            "status": "healthy",
            "router": "HybridRouter",
            "models": {
                "primary": {
                    "provider": "OpenRouter",
                    "model": router.MODEL_PRIMARY
                },
                "backup": {
                    "provider": "Groq",
                    "model": router.MODEL_BACKUP
                }
            },
            "providers": {
                "openrouter": openrouter_status,
                "groq": groq_status
            }
        })
    
    return routing_bp
