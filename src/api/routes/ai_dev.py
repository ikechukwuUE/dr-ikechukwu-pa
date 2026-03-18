"""
AI Development Lab Blueprint
Route: /ai
Code analysis, debugging, and optimization via GitHub MCP + DSPy loops.
"""
from flask import Blueprint, request, jsonify
import logging

from src.core.config import settings
from src.core.security import SecuritySanitizer
from src.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

ai_dev_bp = Blueprint("ai_dev", __name__, url_prefix="/ai")

# Model configuration - now using config.py settings
AI_DEV_MODEL = settings.AIDEV_PRIMARY_MODEL
AI_DEV_MODEL_BACKUP = settings.AIDEV_BACKUP_MODEL

# ============================================================================
# Initialize LLM & Sanitizer
# ============================================================================
def get_llm():
    """Get or create LLM instance using LLMFactory (config.py settings)."""
    try:
        return LLMFactory.create_llm(domain="ai_dev", temperature=0.3)
    except ValueError as e:
        logger.error(f"Failed to create LLM: {e}")
        return None

llm_code = get_llm()
sanitizer = SecuritySanitizer()

# ============================================================================
# POST /ai/query - Frontend Integration Endpoint
# ============================================================================
@ai_dev_bp.route("/query", methods=["POST"])
def ai_query():
    """
    Frontend integration endpoint for AI Development Lab.
    Accepts: { query: string, language: string }
    Returns: { code: string, explanation: string, optimizations: string[] }
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        language = data.get("language", "python")
        thread_id = data.get("thread_id", "default-ai-session")

        if not query:
            return jsonify({"error": "query is required"}), 400
        
        logger.info(f"[AI_DEV] Query request from thread {thread_id}: {query[:50]}...")
        
        # Use existing analyze logic with query as the main input
        prompt = f"""You are an expert {language} developer and code optimization specialist.

User Query: {query}

Provide:
1. **Code**: A complete, working code solution
2. **Explanation**: Detailed explanation of the solution
3. **Optimizations**: Array of 3-5 optimization suggestions

Format as JSON:
{{"code": "...", "explanation": "...", "optimizations": ["opt1", "opt2", "opt3"]}}"""
        
        response = llm_code.invoke(prompt)
        
        # Parse response
        import json
        content = response.content
        if isinstance(content, list):
            content = content[0] if content else ""
        if isinstance(content, dict):
            content = json.dumps(content)
        
        # Extract JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            response_json = json.loads(content)
        except:
            response_json = {
                "code": str(response.content),
                "explanation": "Code generated from query",
                "optimizations": []
            }
        
        logger.info(f"[AI_DEV] Query complete for thread {thread_id}")
        
        return jsonify({
            "status": "success",
            "code": response_json.get("code", ""),
            "explanation": response_json.get("explanation", ""),
            "optimizations": response_json.get("optimizations", []),
            "metadata": {"thread_id": thread_id}
        })
    
    except Exception as e:
        logger.error(f"[AI_DEV] Query error: {str(e)}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500

# ============================================================================
# POST /ai/analyze - Code Analysis & Debugging
# ============================================================================
@ai_dev_bp.route("/analyze", methods=["POST"])
def analyze_code():
    """
    Analyze code for bugs, performance issues, and best practices.
    """
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        repo = data.get("repo")
        file_path = data.get("file_path")
        code_snippet = data.get("code_snippet")
        thread_id = data.get("thread_id", "default-ai-session")

        if not query:
            return jsonify({"error": "query is required"}), 400
        
        logger.info(f"[AI_DEV] Code analysis request from thread {thread_id}")
        
        code_to_analyze = ""
        source = "unknown"
        
        # Mode 1: GitHub Repository (Phase 2B)
        if repo and file_path:
            source = f"GitHub: {repo}/{file_path}"
            logger.info(f"[AI_DEV] Analyzing GitHub file: {source}")
            # TODO: Integrate GitHub MCP
            code_to_analyze = f"[GitHub file pending MCP integration: {file_path}]"
        
        # Mode 2: Raw Code Snippet
        elif code_snippet:
            source = "uploaded code snippet"
            code_to_analyze = code_snippet
        
        else:
            return jsonify({"error": "Provide either repo/file_path or code_snippet"}), 400
        
        # Analyze code
        prompt = f"""You are an expert Python/ML engineer. Analyze this code:

Source: {source}
Query: {query}

Code to analyze:
```
{code_to_analyze[:2000]}
```

Provide:
1. **Analysis**: Overall assessment
2. **Issues** (JSON array): [{{"severity": "critical/warning/info", "issue": "...", "location": "...", "suggestion": "..."}}]
3. **Suggestions** (array): Top 3 optimization/improvement suggestions

Format as JSON."""
        
        response = llm_code.invoke(prompt)
        
        # Parse response
        try:
            import json
            content = response.content
            if isinstance(content, list):
                content = content[0] if content else ""
            if isinstance(content, dict):
                content = json.dumps(content)
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            response_json = json.loads(content)
        except:
            response_json = {
                "analysis": str(response.content),
                "issues": [],
                "suggestions": []
            }
        
        logger.info(f"[AI_DEV] Analysis complete: {len(response_json.get('issues', []))} issues found")
        
        return jsonify({
            "status": "success",
            "analysis": response_json.get("analysis", ""),
            "issues": response_json.get("issues", []),
            "suggestions": response_json.get("suggestions", []),
            "metadata": {
                "thread_id": thread_id,
                "source": source
            }
        })
    
    except Exception as e:
        logger.error(f"[AI_DEV] Analysis error: {str(e)}")
        return jsonify({"error": f"Code analysis failed: {str(e)}"}), 500

# ============================================================================
# Health Check for AI Dev
# ============================================================================
@ai_dev_bp.route("/health", methods=["GET"])
def ai_dev_health():
    """Health check for AI development lab route."""
    return jsonify({
        "status": "healthy",
        "service": "AI Development Lab",
        "llm": AI_DEV_MODEL,
        "features": [
            "Code analysis & debugging",
            "GitHub PR review (pending)",
            "DSPy evaluation loops (pending)"
        ]
    })


