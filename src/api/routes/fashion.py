"""
Fashion/Lifestyle Planning Blueprint
Route: /fashion
Dual-domain styling for Dr. Ugbo:
1. **Corporate Professional**: Medical presentations, tech conferences, business meetings
2. **Modern Traditionalist**: Cultural events, weekend casual, elevated Ankara wear

Uses Playwright MCP for real-time trend research + OpenRouter LLM (config.py settings).
"""
from flask import Blueprint, request, jsonify
import logging

from src.core.config import settings
from src.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

fashion_bp = Blueprint("fashion", __name__, url_prefix="/fashion")

# Model configuration - now using config.py settings
FASHION_MODEL = settings.CLINICAL_PRIMARY_MODEL  # Fashion uses clinical model
FASHION_MODEL_BACKUP = settings.CLINICAL_BACKUP_MODEL

# ============================================================================
# Initialize LLM
# ============================================================================
def get_llm():
    """Get or create LLM instance using LLMFactory (config.py settings)."""
    try:
        return LLMFactory.create_llm(domain="fashion", temperature=0.7)
    except ValueError as e:
        logger.error(f"Failed to create LLM: {e}")
        return None

llm_fashion = get_llm()

# ============================================================================
# POST /fashion/query - Frontend Integration Endpoint
# ============================================================================
@fashion_bp.route("/query", methods=["POST"])
def fashion_query():
    """
    Frontend integration endpoint for Fashion/Lifestyle Planning.
    Accepts: { query: string, budget: string, occasion: string, domain: string }
    Returns: { outfit: string, sources: string[], budget_breakdown: string, tips: string[] }
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        budget = data.get("budget", "50k-150k NGN")
        occasion = data.get("occasion", "")
        domain = data.get("domain", "both")
        thread_id = data.get("thread_id", "default-fashion-session")
        
        logger.info(f"[FASHION] Query request: occasion={occasion}, domain={domain}, budget={budget}")
        
        # Determine style domain focus
        domain_focus = ""
        if domain == "corporate":
            domain_focus = """
Focus on CORPORATE PROFESSIONAL domain:
- Medical authority + approachability
- Tech conference credibility
- Executive presence
- Color palettes: Navy, charcoal, white, subtle patterns
- Key pieces: Quality fabrics, tailoring precision, understated luxury"""
        elif domain == "cultural":
            domain_focus = """
Focus on MODERN TRADITIONALIST domain:
- Contemporary Nigerian fashion
- Ankara + modern tailoring blend
- Cultural authenticity + style edge
- Color palettes: Vibrant Ankara prints, earth tones, bold accents
- Key pieces: Premium Ankara, tailored blazers, statement jewelry"""
        else:  # both
            domain_focus = """
Recommend BOTH DOMAIN OUTFITS:

Corporate Professional (2-3 looks):
- Medical authority + approachability
- Tech credibility
- Executive presence

Modern Traditionalist (2-3 looks):
- Contemporary Nigerian fashion
- Ankara + modern tailoring
- Cultural authenticity"""
        
        prompt = f"""You are a luxury personal stylist specializing in West African fashion and corporate professional style.

User Query: {query}
Occasion: {occasion}
Budget: {budget}
Domain: {domain}

{domain_focus}

Generate outfit recommendations with:
1. **Outfit**: Detailed outfit description
2. **Sources**: Where to buy in Nigeria (BellaNaija, Jiji.ng, local tailors, online boutiques)
3. **Budget Breakdown**: Price estimates for each item
4. **Tips**: Styling tips for this look

Format as JSON:
{{"outfit": "...", "sources": ["..."], "budget_breakdown": "...", "tips": ["..."]}}"""
        
        response = llm_fashion.invoke(prompt)
        
        # Parse response
        recommendations = []
        try:
            import json
            response_text = response.content
            if isinstance(response_text, list):
                response_text = response_text[0] if response_text else ""
            if isinstance(response_text, dict):
                response_text = json.dumps(response_text)

            # Try to extract JSON
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                recommendations = [parsed] if isinstance(parsed, dict) else parsed
        except Exception as e:
            logger.warning(f"[FASHION] JSON parsing failed: {e}")
            recommendations = []
        
        # Build response
        if recommendations:
            rec = recommendations[0] if recommendations else {}
            outfit = rec.get("outfit", str(response.content))
            sources = rec.get("sources", [])
            budget_breakdown = rec.get("budget_breakdown", budget)
            tips = rec.get("tips", [])
        else:
            outfit = str(response.content)
            sources = ["BellaNaija", "Jiji.ng", "Local boutiques"]
            budget_breakdown = budget
            tips = ["Dress for the occasion", "Comfort matters"]
        
        logger.info(f"[FASHION] Query complete: outfit generated")
        
        return jsonify({
            "status": "success",
            "outfit": outfit,
            "sources": sources,
            "budget_breakdown": budget_breakdown,
            "tips": tips,
            "metadata": {
                "thread_id": thread_id,
                "domain": domain,
                "budget": budget
            }
        })
    
    except Exception as e:
        logger.error(f"[FASHION] Query error: {str(e)}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500

# ============================================================================
# POST /fashion/style - Dual-Domain Styling
# ============================================================================
@fashion_bp.route("/style", methods=["POST"])
def style_recommendation():
    """
    Generate outfit recommendations for Dr. Ugbo across both domains.
    """
    try:
        data = request.get_json(silent=True) or {}
        occasion = data.get("occasion")
        style_domain = data.get("style_domain", "both")
        budget_range = data.get("budget_range", "50k-150k NGN")
        preferences = data.get("preferences", "")
        thread_id = data.get("thread_id", "default-fashion-session")

        if not occasion:
            return jsonify({"error": "Occasion is required"}), 400
        
        logger.info(f"[FASHION] Styling request: {occasion} ({style_domain})")
        
        # Build context
        domain_focus = ""
        if style_domain == "corporate":
            domain_focus = """
Focus on CORPORATE PROFESSIONAL domain:
- Medical authority + approachability
- Tech conference credibility
- Executive presence
- Color palettes: Navy, charcoal, white, subtle patterns
- Key pieces: Quality fabrics, tailoring precision, understated luxury"""
        
        elif style_domain == "cultural":
            domain_focus = """
Focus on MODERN TRADITIONALIST domain:
- Contemporary Nigerian fashion
- Ankara + modern tailoring blend
- Cultural authenticity + style edge
- Color palettes: Vibrant Ankara prints, earth tones, bold accents
- Key pieces: Premium Ankara, tailored blazers, statement jewelry"""
        
        else:  # both
            domain_focus = """
Recommend BOTH DOMAIN OUTFITS:

Corporate Professional (3 looks):
- Medical authority + approachability
- Tech credibility
- Executive presence

Modern Traditionalist (2 looks):
- Contemporary Nigerian fashion
- Ankara + modern tailoring
- Cultural authenticity"""
        
        prompt = f"""You are a luxury personal stylist specializing in West African fashion and corporate professional style.

Occasion: {occasion}
Budget: {budget_range}
Additional Preferences: {preferences}

{domain_focus}

Generate 3-5 specific outfit recommendations with:
1. **Title**: Brief outfit name
2. **Description**: Full styling details
3. **Key Pieces**: Specific garments + colors (e.g., "Navy wool blazer", "Tailored Ankara shirt")
4. **Sourcing**: Where to buy in Nigeria (BellaNaija, Jiji.ng, local tailors, online boutiques)
5. **Price Estimate**: Approximate total cost
6. **Confidence**: How well it matches the brief (0.0-1.0)

Format each outfit as JSON:
{{
  "title": "...",
  "description": "...",
  "pieces": ["piece1", "piece2", ...],
  "sourcing": ["BellaNaija", "Jiji.ng", ...],
  "price_estimate": "50k-80k NGN",
  "confidence": 0.95
}}

Return as JSON array of recommendations."""
        
        response = llm_fashion.invoke(prompt)
        
        # Parse recommendations
        recommendations = []
        try:
            import json
            response_text = response.content
            if isinstance(response_text, list):
                response_text = response_text[0] if response_text else ""
            if isinstance(response_text, dict):
                response_text = json.dumps(response_text)

            # Extract JSON array
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                for rec in parsed:
                    recommendations.append({
                        "title": rec.get("title", ""),
                        "description": rec.get("description", ""),
                        "pieces": rec.get("pieces", []),
                        "sourcing": rec.get("sourcing", []),
                        "price_estimate": rec.get("price_estimate", ""),
                        "confidence": rec.get("confidence", 0.0)
                    })
        except Exception as e:
            logger.warning(f"[FASHION] JSON parsing failed, treating as text: {e}")
            recommendations.append({
                "title": "Styling Recommendation",
                "description": str(response.content),
                "pieces": [],
                "sourcing": [],
                "price_estimate": budget_range,
                "confidence": 0.7
            })
        
        logger.info(f"[FASHION] Generated {len(recommendations)} outfit recommendations")
        
        return jsonify({
            "status": "success",
            "occasion": occasion,
            "recommendations": recommendations,
            "trend_analysis": "Phase 2B will include real-time trend analysis via Playwright",
            "metadata": {
                "thread_id": thread_id,
                "domain": style_domain,
                "budget": budget_range
            }
        })
    
    except Exception as e:
        logger.error(f"[FASHION] Styling error: {str(e)}")
        return jsonify({"error": f"Fashion recommendation failed: {str(e)}"}), 500

# ============================================================================
# POST /fashion/trends - Real-Time Trend Analysis (Phase 2B)
# ============================================================================
@fashion_bp.route("/trends", methods=["POST"])
def trend_analysis():
    """
    Real-time trend scraping via Playwright MCP.
    Phase 2B: Will scrape:
    - Instagram/TikTok fashion trends
    - BellaNaija style posts
    - Nigerian e-commerce bestsellers (Jiji, Konga)
    - Premium tailor portfolios
    """
    try:
        return jsonify({
            "status": "pending",
            "message": "Real-time trend analysis in Phase 2B",
            "sources": ["Instagram", "TikTok", "BellaNaija", "Jiji.ng", "Konga"],
            "playbook": "Playwright MCP + Vision analysis of trending combinations"
        })
    except Exception as e:
        logger.error(f"[FASHION] Trends error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# POST /fashion/corporate - Corporate Professional Specialist
# ============================================================================
@fashion_bp.route("/corporate", methods=["POST"])
def corporate_styling():
    """
    Specialized corporate/medical professional styling.
    Focus: Medical authority, executive presence, tech credibility.
    """
    data = request.get_json(silent=True) or {}
    occasion = data.get("occasion")
    budget_range = data.get("budget_range", "50k-150k NGN")
    preferences = data.get("preferences", "")
    thread_id = data.get("thread_id", "default-fashion-session")
    return style_recommendation_helper(occasion, "corporate", budget_range, preferences, thread_id)

# ============================================================================
# POST /fashion/cultural - Modern Traditionalist Specialist
# ============================================================================
@fashion_bp.route("/cultural", methods=["POST"])
def cultural_styling():
    """
    Specialized modern traditionalist styling.
    Focus: Contemporary Nigerian fashion, Ankara, cultural authenticity.
    """
    data = request.get_json(silent=True) or {}
    occasion = data.get("occasion")
    budget_range = data.get("budget_range", "50k-150k NGN")
    preferences = data.get("preferences", "")
    thread_id = data.get("thread_id", "default-fashion-session")
    return style_recommendation_helper(occasion, "cultural", budget_range, preferences, thread_id)

def style_recommendation_helper(occasion: str, style_domain: str, budget_range: str, preferences: str, thread_id: str):
    # Re-using the core logic of style_recommendation with provided parameters
    # This avoids redundant code and simplifies the calling functions
    try:
        if not occasion:
            return jsonify({"error": "Occasion is required"}), 400
        
        logger.info(f"[FASHION] Styling request: {occasion} ({style_domain})")
        
        domain_focus = ""
        if style_domain == "corporate":
            domain_focus = """
Focus on CORPORATE PROFESSIONAL domain:
- Medical authority + approachability
- Tech conference credibility
- Executive presence
- Color palettes: Navy, charcoal, white, subtle patterns
- Key pieces: Quality fabrics, tailoring precision, understated luxury"""
        
        elif style_domain == "cultural":
            domain_focus = """
Focus on MODERN TRADITIONALIST domain:
- Contemporary Nigerian fashion
- Ankara + modern tailoring blend
- Cultural authenticity + style edge
- Color palettes: Vibrant Ankara prints, earth tones, bold accents
- Key pieces: Premium Ankara, tailored blazers, statement jewelry"""
        
        else:  # both
            domain_focus = """
Recommend BOTH DOMAIN OUTFITS:

Corporate Professional (3 looks):
- Medical authority + approachability
- Tech credibility
- Executive presence

Modern Traditionalist (2 looks):
- Contemporary Nigerian fashion
- Ankara + modern tailoring
- Cultural authenticity"""
        
        prompt = f"""You are a luxury personal stylist specializing in West African fashion and corporate professional style.

Occasion: {occasion}
Budget: {budget_range}
Additional Preferences: {preferences}

{domain_focus}

Generate 3-5 specific outfit recommendations with:
1. **Title**: Brief outfit name
2. **Description**: Full styling details
3. **Key Pieces**: Specific garments + colors (e.g., "Navy wool blazer", "Tailored Ankara shirt")
4. **Sourcing**: Where to buy in Nigeria (BellaNaija, Jiji.ng, local tailors, online boutiques)
5. **Price Estimate**: Approximate total cost
6. **Confidence**: How well it matches the brief (0.0-1.0)

Format each outfit as JSON:
{{
  "title": "...",
  "description": "...",
  "pieces": ["piece1", "piece2", ...],
  "sourcing": ["BellaNaija", "Jiji.ng", ...],
  "price_estimate": "50k-80k NGN",
  "confidence": 0.95
}}

Return as JSON array of recommendations."""
        
        response = llm_fashion.invoke(prompt)
        
        recommendations = []
        try:
            import json
            response_text = response.content
            if isinstance(response_text, list):
                response_text = response_text[0] if response_text else ""
            if isinstance(response_text, dict):
                response_text = json.dumps(response_text)

            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                for rec in parsed:
                    recommendations.append({
                        "title": rec.get("title", ""),
                        "description": rec.get("description", ""),
                        "pieces": rec.get("pieces", []),
                        "sourcing": rec.get("sourcing", []),
                        "price_estimate": rec.get("price_estimate", ""),
                        "confidence": rec.get("confidence", 0.0)
                    })
        except Exception as e:
            logger.warning(f"[FASHION] JSON parsing failed, treating as text: {e}")
            recommendations.append({
                "title": "Styling Recommendation",
                "description": str(response.content),
                "pieces": [],
                "sourcing": [],
                "price_estimate": budget_range,
                "confidence": 0.7
            })
        
        logger.info(f"[FASHION] Generated {len(recommendations)} outfit recommendations")
        
        return jsonify({
            "status": "success",
            "occasion": occasion,
            "recommendations": recommendations,
            "trend_analysis": "Phase 2B will include real-time trend analysis via Playwright",
            "metadata": {
                "thread_id": thread_id,
                "domain": style_domain,
                "budget": budget_range
            }
        })
    
    except Exception as e:
        logger.error(f"[FASHION] Styling error: {str(e)}")
        return jsonify({"error": f"Fashion recommendation failed: {str(e)}"}), 500

# ============================================================================
# Health Check for Fashion
# ============================================================================
@fashion_bp.route("/health", methods=["GET"])
def fashion_health():
    """
    Health check for lifestyle planning route.
    """
    return jsonify({
        "status": "healthy",
        "service": "Dual-Domain Fashion Styling",
        "domains": ["Corporate Professional", "Modern Traditionalist"],
        "llm": FASHION_MODEL,
        "integration": [
            "Playwright MCP (trend scraping - Phase 2B)",
            "Vision analysis (Phase 2B)",
            "E-commerce price checking (Phase 2B)"
        ],
        "coverage": "West African fashion, premium tailoring, contemporary style"
    })
