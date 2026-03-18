"""
Supervisor Graph: Routes queries to specialized agents based on intent.
Uses LangGraph's StateGraph pattern for multi-agent orchestration.

Hybrid Routing System:
- Combines keyword matching with LLM-based semantic routing
- Configurable confidence thresholds for routing decisions
- Falls back to clarification for ambiguous queries
"""
from typing import TypedDict, Literal, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from src.core.security import SecuritySanitizer
from src.core.config import settings
from src.core.llm_factory import LLMFactory
import logging
import re

logger = logging.getLogger(__name__)


# ============================================================================
# HybridRouter Class
# ============================================================================

class HybridRouter:
    """
    Hybrid routing system combining keyword matching with LLM-based semantic routing.
    
    Routing Strategy:
    1. First try keyword matching
    2. If confidence < 0.7, also use LLM routing
    3. Fuse results: keyword_weight=0.4, llm_weight=0.6
    4. Return domain, confidence, and reasoning
    
    Confidence Thresholds:
    - >= 0.8: High confidence, use result directly
    - 0.5-0.8: Medium, blend results
    - < 0.5: Low, use LLM result or prompt for clarification
    """
    
    # Domain keyword patterns
    KEYWORD_PATTERNS: Dict[str, list] = {
        "clinical": [
            "patient", "bp", "diagnosis", "symptom", "pregnancy", "surgery",
            "x-ray", "xray", "psychiatric", "pediatric", "medical", "doctor",
            "hospital", "clinic", "ward", "prescription", "medication",
            "treatment", "health", "disease", "condition", "symptoms",
            "blood pressure", "heart rate", "fever", "cough", "pain"
        ],
        "finance": [
            "stock", "investment", "portfolio", "wealth", "budget", "loan",
            "interest", "yield", "market", "trading", "shares", "bonds",
            "mutual fund", "pension", "retirement", "savings", "credit",
            "debt", "mortgage", "insurance", "tax", "profit", "loss",
            "dividend", "capital", "asset", "liability", "financial"
        ],
        "ai_dev": [
            "code", "python", "debug", "program", "develop", "algorithm",
            "api", "git", "software", "function", "class", "module",
            "repository", "commit", "pull request", "testing", "deployment",
            "framework", "library", "database", "server", "client",
            "frontend", "backend", "fullstack", "machine learning", "ai"
        ],
        "fashion": [
            "outfit", "style", "fashion", "clothing", "dress", "wear",
            "accessory", "suit", "tie", "shirt", "trousers", "shoes",
            "ankara", "aso oke", "traditional", "corporate", "formal",
            "casual", "appearance", "wardrobe", "look", "ensemble",
            "tailor", "design", "trend", "fashionable", "elegant"
        ]
    }
    
    # Routing weights (configurable)
    KEYWORD_WEIGHT: float = 0.4
    LLM_WEIGHT: float = 0.6
    
    # Confidence thresholds
    HIGH_CONFIDENCE: float = 0.8
    MEDIUM_CONFIDENCE: float = 0.5
    LOW_CONFIDENCE_THRESHOLD: float = 0.7  # Below this, use LLM backup
    
    def __init__(self):
        """Initialize the HybridRouter with LLM client."""
        try:
            self.llm = LLMFactory.create_llm(domain="clinical", temperature=0.3)
        except ValueError as e:
            logger.warning(f"Failed to create LLM: {e}, using default")
            self.llm = None
        self.domains = list(self.KEYWORD_PATTERNS.keys())
    
    def route(self, query: str) -> Dict[str, Any]:
        """
        Main routing method that combines keyword and LLM-based routing.
        
        Args:
            query: The user query to route
            
        Returns:
            Dictionary with domain, confidence, reasoning, and needs_clarification
        """
        # Step 1: Keyword matching
        keyword_result = self._keyword_match(query)
        logger.info(f"[HybridRouter] Keyword match: {keyword_result}")
        
        # Step 2: If keyword confidence is low, also use LLM routing
        if keyword_result["confidence"] < self.LOW_CONFIDENCE_THRESHOLD:
            llm_result = self._llm_route(query)
            logger.info(f"[HybridRouter] LLM match: {llm_result}")
            
            # Step 3: Fuse results
            fused_result = self._fuse_results(keyword_result, llm_result)
            logger.info(f"[HybridRouter] Fused result: {fused_result}")
            
            return fused_result
        else:
            # High keyword confidence, return keyword result
            return keyword_result
    
    def _keyword_match(self, query: str) -> Dict[str, Any]:
        """
        Pure keyword-based routing.
        
        Returns:
            Dictionary with domain, confidence, and reasoning
        """
        query_lower = query.lower()
        scores = {}
        
        # Calculate score for each domain
        for domain, keywords in self.KEYWORD_PATTERNS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                # Use word boundary matching for better accuracy
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query_lower):
                    score += 1
                    matched_keywords.append(keyword)
            
            # Normalize score by number of keywords
            if keywords:
                normalized_score = score / len(keywords)
                # Boost score if there are more matches
                if score > 0:
                    normalized_score = min(1.0, normalized_score * (1 + 0.2 * score))
                scores[domain] = normalized_score
        
        if not scores or max(scores.values()) == 0:
            return {
                "domain": "general",
                "confidence": 0.0,
                "reasoning": "No keyword matches found",
                "method": "keyword"
            }
        
        # Get best domain
        best_domain = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[best_domain]
        
        # Get matched keywords for reasoning
        matched = [kw for kw in self.KEYWORD_PATTERNS[best_domain] 
                   if re.search(r'\b' + re.escape(kw) + r'\b', query_lower)]
        
        return {
            "domain": best_domain,
            "confidence": confidence,
            "reasoning": f"Keyword match: {matched}",
            "method": "keyword"
        }
    
    def _llm_route(self, query: str) -> Dict[str, Any]:
        """
        LLM-based semantic routing.
        
        Returns:
            Dictionary with domain, confidence, and reasoning
        """
        # Prompt for LLM routing
        routing_prompt = f"""You are a query classifier. Classify the following query into exactly one domain.

Available domains:
- clinical: Medical, healthcare, patient care, diagnosis, symptoms
- finance: Investment, stocks, wealth management, budgeting, financial planning
- ai_dev: Software development, programming, coding, algorithms, APIs
- fashion: Clothing, styling, outfits, trends, appearance
- general: Anything that doesn't fit the above categories

Query: {query}

Respond with ONLY the domain name and a confidence score (0-1).
Format: domain:confidence

Examples:
- "My patient has fever and cough" -> clinical:0.95
- "What's the best way to invest $10,000?" -> finance:0.9
- "Write a Python function to sort a list" -> ai_dev:0.95
- "What outfit should I wear to a wedding?" -> fashion:0.9
- "What's the weather like today?" -> general:0.8
"""
        
        try:
            response = self.llm.invoke(routing_prompt)
            response_text = response.content
            # Handle different response types
            if isinstance(response_text, list):
                response_text = str(response_text[0]) if response_text else "general:0.5"
            elif hasattr(response_text, 'content'):
                response_text = response_text.content
            response_text = str(response_text).strip()
            
            # Parse LLM response
            if ":" in response_text:
                parts = response_text.split(":")
                domain = parts[0].strip().lower()
                try:
                    confidence = float(parts[1].strip())
                except (ValueError, IndexError):
                    confidence = 0.7
            else:
                # Fallback parsing
                domain = response_text.lower()
                confidence = 0.7
            
            # Validate domain
            if domain not in self.domains + ["general"]:
                domain = "general"
            
            return {
                "domain": domain,
                "confidence": confidence,
                "reasoning": f"LLM classification: {response_text}",
                "method": "llm"
            }
        except Exception as e:
            logger.error(f"[HybridRouter] LLM routing failed: {e}")
            # Fallback to general on error
            return {
                "domain": "general",
                "confidence": 0.5,
                "reasoning": f"LLM routing failed, defaulting to general",
                "method": "llm_error"
            }
    
    def _fuse_results(self, keyword_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """
        Combine keyword and LLM results with configurable weights.
        
        Args:
            keyword_result: Result from keyword matching
            llm_result: Result from LLM routing
            
        Returns:
            Fused result with domain, confidence, and reasoning
        """
        # If domains match, boost confidence
        if keyword_result["domain"] == llm_result["domain"]:
            domain = keyword_result["domain"]
            # Average the confidences with domain match boost
            confidence = (keyword_result["confidence"] * self.KEYWORD_WEIGHT + 
                         llm_result["confidence"] * self.LLM_WEIGHT)
            confidence = min(1.0, confidence + 0.1)  # Boost for agreement
            reasoning = f"Both methods agreed: {keyword_result['reasoning']}, {llm_result['reasoning']}"
        else:
            # Domains differ, use LLM result (generally more accurate)
            # But consider keyword confidence
            if keyword_result["confidence"] > 0.3:
                # Some keyword evidence, blend results
                domain = llm_result["domain"]
                confidence = (keyword_result["confidence"] * self.KEYWORD_WEIGHT + 
                             llm_result["confidence"] * self.LLM_WEIGHT)
                reasoning = f"Blended: keyword={keyword_result['domain']}({keyword_result['confidence']:.2f}), llm={llm_result['domain']}({llm_result['confidence']:.2f})"
            else:
                # Low keyword confidence, trust LLM
                domain = llm_result["domain"]
                confidence = llm_result["confidence"]
                reasoning = f"Low keyword match, using LLM: {llm_result['reasoning']}"
        
        # Determine if clarification is needed based on confidence thresholds
        needs_clarification = confidence < self.MEDIUM_CONFIDENCE
        
        return {
            "domain": domain,
            "confidence": confidence,
            "reasoning": reasoning,
            "needs_clarification": needs_clarification,
            "method": "fused"
        }


# ============================================================================
# Application State
# ============================================================================

class AppState(TypedDict):
    """Application state shared across all graph nodes."""
    user_query: str
    route: str
    response: str
    confidence: float
    reasoning: str
    needs_clarification: bool


# ============================================================================
# Initialize HybridRouter
# ============================================================================

hybrid_router = HybridRouter()


# ============================================================================
# Supervisor Router Function (wraps HybridRouter)
# ============================================================================

def supervisor_router(state: AppState) -> Literal["clinical", "finance", "ai_dev", "fashion", "general", "clarify"]:
    """
    Routes incoming queries to appropriate domain handlers using hybrid routing.
    
    Uses keyword matching + LLM semantic routing with configurable confidence thresholds.
    """
    query = state["user_query"]
    
    # Use hybrid router
    result = hybrid_router.route(query)
    
    # Update state with routing information
    state["confidence"] = result["confidence"]
    state["reasoning"] = result["reasoning"]
    state["needs_clarification"] = result.get("needs_clarification", False)
    
    # Determine routing based on confidence thresholds
    if result["confidence"] >= hybrid_router.HIGH_CONFIDENCE:
        # High confidence, route directly
        return result["domain"]
    elif result["confidence"] >= hybrid_router.MEDIUM_CONFIDENCE:
        # Medium confidence, route to domain (domain worker can handle ambiguity)
        return result["domain"]
    else:
        # Low confidence, need clarification
        return "clarify"


# ============================================================================
# Node Functions
# ============================================================================

def clinical_worker(state: AppState) -> dict:
    """Clinical Decision Support worker node."""
    sanitizer = SecuritySanitizer()
    safe_query, _ = sanitizer.sanitize_clinical_prompt(state["user_query"])
    # Phase 2: Replace with actual LLM + PubMed MCP call
    return {
        "response": f"Clinical analysis for: {safe_query}",
        "route": "clinical"
    }


def finance_worker(state: AppState) -> dict:
    """Finance/Wealth Management worker node."""
    sanitizer = SecuritySanitizer()
    safe_query, _ = sanitizer.sanitize_clinical_prompt(state["user_query"])
    # Phase 2: Replace with actual HITL graph + financial datasets MCP
    return {
        "response": f"Financial analysis for: {safe_query}",
        "route": "finance"
    }


def ai_dev_worker(state: AppState) -> dict:
    """AI Development/Virtual Lab worker node."""
    return {
        "response": f"Code analysis for: {state['user_query']}",
        "route": "ai_dev"
    }


def fashion_worker(state: AppState) -> dict:
    """Fashion/Lifestyle Planner worker node.
    Dual-domain styling for Dr. Ugbo:
    1. **Corporate Professional**: Medical coats, business suits, tech conference wear
    2. **Modern Traditionalist**: Ankara, cultural pieces, elevated casual
    
    Uses Playwright MCP for real-time trend research + Gemini 2.5-Flash vision analysis.
    """
    return {
        "response": f"Dual-domain fashion analysis for: {state['user_query']} (corporate + cultural styling)",
        "route": "fashion"
    }


def general_worker(state: AppState) -> dict:
    """General query handler (fallback for off-topic queries)."""
    return {
        "response": f"General response for: {state['user_query']}. This query doesn't match any specialized domain.",
        "route": "general"
    }


def clarify_worker(state: AppState) -> dict:
    """Clarification node for low-confidence routing cases."""
    query = state["user_query"]
    confidence = state.get("confidence", 0.0)
    reasoning = state.get("reasoning", "")
    
    clarification_prompt = f"""The system couldn't confidently determine which domain your query relates to.

Query: {query}
Confidence: {confidence:.2f}
Reasoning: {reasoning}

Please clarify which area you'd like help with:
- Clinical/Medical: For healthcare and patient-related questions
- Finance: For investment, wealth management, and financial planning
- AI/Development: For programming, coding, and software development
- Fashion: For styling, clothing, and appearance advice

How can I help you today?
"""
    
    return {
        "response": clarification_prompt,
        "route": "clarify",
        "needs_clarification": True
    }


# ============================================================================
# Build the Supervisor Graph
# ============================================================================

supervisor_builder = StateGraph(AppState)

# Add nodes for each domain
supervisor_builder.add_node("supervisor", supervisor_router)
supervisor_builder.add_node("clinical", clinical_worker)
supervisor_builder.add_node("finance", finance_worker)
supervisor_builder.add_node("ai_dev", ai_dev_worker)
supervisor_builder.add_node("fashion", fashion_worker)
supervisor_builder.add_node("general", general_worker)
supervisor_builder.add_node("clarify", clarify_worker)

# Define edges
supervisor_builder.add_edge(START, "supervisor")

# Conditional edges from supervisor
def route_to_domain(state: AppState) -> str:
    """Determine which domain to route to based on state."""
    return state.get("route", "general")

supervisor_builder.add_conditional_edges("supervisor", route_to_domain)

# Add edges from domain nodes to END
supervisor_builder.add_edge("clinical", END)
supervisor_builder.add_edge("finance", END)
supervisor_builder.add_edge("ai_dev", END)
supervisor_builder.add_edge("fashion", END)
supervisor_builder.add_edge("general", END)
supervisor_builder.add_edge("clarify", END)

# Compile the graph
master_graph = supervisor_builder.compile()


# ============================================================================
# Backward Compatibility: Original Router Function
# ============================================================================

def route_query(query: str) -> str:
    """
    Simple backward-compatible routing function.
    
    Args:
        query: User query string
        
    Returns:
        Domain name (clinical, finance, ai_dev, fashion, general)
    """
    result = hybrid_router.route(query)
    return result["domain"]


# Export for easy access
__all__ = [
    "HybridRouter",
    "master_graph", 
    "AppState", 
    "supervisor_router",
    "clinical_worker", 
    "finance_worker", 
    "ai_dev_worker", 
    "fashion_worker",
    "general_worker",
    "clarify_worker",
    "route_query"
]
