"""
Reflection Agent for Finance
============================
Self-critique agent that iteratively improves financial analysis.
"""

from typing import TypedDict, List, Dict, Any, Optional
import logging
from src.core.llm_factory import LLMFactory
from src.core.security import SecuritySanitizer

logger = logging.getLogger(__name__)

# Model configuration - now using config.py settings
FINANCE_MODEL = None  # Set by LLMFactory at runtime


class ReflectionState(TypedDict):
    """State for reflection agent workflow."""
    query: str
    initial_analysis: str
    critiques: List[Dict[str, str]]
    improved_analysis: str
    iterations: int
    approved: bool
    context: Optional[Dict[str, Any]]


class ReflectionAgent:
    """
    Reflection-based agent that performs self-critique on financial analysis.
    
    Loop flow:
    1. Generate initial analysis
    2. Self-critique to identify risks/gaps
    3. Improve analysis based on critique
    4. Repeat up to 3 times until no improvements needed
    """

    MAX_ITERATIONS = 3

    def __init__(self):
        self.llm = self._get_llm()
        self.sanitizer = SecuritySanitizer()
    
    def _get_llm(self):
        """Get or create LLM instance using LLMFactory."""
        try:
            return LLMFactory.create_llm(domain="finance", temperature=0.0)
        except ValueError as e:
            logger.error(f"Failed to create LLM: {e}")
            return None

    def analyze_with_reflection(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> ReflectionState:
        """
        Main entry point for reflection-based analysis.
        
        Args:
            query: Financial query to analyze
            context: Optional context for the analysis
            
        Returns:
            ReflectionState with final analysis and metadata
        """
        # Sanitize input
        sanitized_query, redacted = self.sanitizer.sanitize_clinical_prompt(query)
        
        logger.info(f"[ReflectionAgent] Starting analysis. Redacted {len(redacted)} items")
        
        # Initialize state
        state: ReflectionState = {
            "query": sanitized_query,
            "initial_analysis": "",
            "critiques": [],
            "improved_analysis": "",
            "iterations": 0,
            "approved": False,
            "context": context or {}
        }

        # Step 1: Generate initial analysis
        state["initial_analysis"] = self._initial_analysis(state)
        
        # Set initial improved analysis
        state["improved_analysis"] = state["initial_analysis"]

        # Step 2-4: Reflection loop (up to 3 iterations)
        for i in range(self.MAX_ITERATIONS):
            state["iterations"] = i + 1
            logger.info(f"[ReflectionAgent] Iteration {i + 1}/{self.MAX_ITERATIONS}")
            
            # Self-critique current analysis
            critique = self._self_critique(state)
            state["critiques"].append(critique)
            
            # Check if improvements are needed
            if not critique.get("needs_improvement", False):
                logger.info(f"[ReflectionAgent] No improvements needed at iteration {i + 1}")
                break
            
            # Generate improved analysis
            state["improved_analysis"] = self._improve_analysis(state, critique)
            logger.info(f"[ReflectionAgent] Analysis improved at iteration {i + 1}")

        logger.info(
            f"[ReflectionAgent] Completed {state['iterations']} iterations, "
            f"{len(state['critiques'])} critiques"
        )

        return state

    def _initial_analysis(self, state: ReflectionState) -> str:
        """
        Generate initial financial analysis using LLM.
        
        Args:
            state: Current reflection state
            
        Returns:
            Initial analysis as string
        """
        prompt = f"""You are a financial advisor assistant. Analyze the following financial scenario 
and provide a comprehensive initial analysis.

Query: {state['query']}

Context: {state.get('context', {})}

Provide your analysis covering:
1. Financial situation assessment
2. Key factors to consider
3. Initial recommendations
4. Risk factors to evaluate

Be thorough and professional in your response."""

        try:
            response = self.llm.invoke(prompt)
            analysis = str(response.content) if hasattr(response, 'content') else str(response)
            logger.info("[ReflectionAgent] Initial analysis generated")
            return analysis
        except Exception as e:
            logger.error(f"[ReflectionAgent] Initial analysis failed: {e}")
            return f"Analysis failed: {str(e)}"

    def _self_critique(self, state: ReflectionState) -> Dict[str, Any]:
        """
        Critique own analysis to identify risks and gaps.
        
        Args:
            state: Current reflection state
            
        Returns:
            Dictionary with critique findings
        """
        current_analysis = state.get("improved_analysis", state["initial_analysis"])
        
        prompt = f"""You are a critical financial reviewer. Review the following financial analysis 
and identify potential risks, gaps, or areas for improvement.

Current Analysis:
{current_analysis}

Original Query: {state['query']}

Evaluate the analysis for:
1. Missing information or assumptions
2. Potential risks not addressed
3. Compliance and regulatory concerns
4. Alternative perspectives not considered

Provide your critique in JSON format:
{{
    "needs_improvement": true/false,
    "risks_identified": ["risk1", "risk2", ...],
    "gaps_identified": ["gap1", "gap2", ...],
    "recommendations": ["recommendation1", ...],
    "overall_assessment": "brief assessment"
}}

If the analysis is already comprehensive and no significant improvements are needed, 
set needs_improvement to false."""

        try:
            response = self.llm.invoke(prompt)
            critique_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Parse JSON from response
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', critique_text, re.DOTALL)
            if json_match:
                try:
                    critique = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    critique = {
                        "needs_improvement": True,
                        "risks_identified": ["Unable to parse critique"],
                        "gaps_identified": [],
                        "recommendations": [],
                        "overall_assessment": critique_text[:200]
                    }
            else:
                critique = {
                    "needs_improvement": True,
                    "risks_identified": [],
                    "gaps_identified": [],
                    "recommendations": [],
                    "overall_assessment": critique_text[:200]
                }
            
            logger.info(f"[ReflectionAgent] Critique generated: needs_improvement={critique.get('needs_improvement', True)}")
            return critique
            
        except Exception as e:
            logger.error(f"[ReflectionAgent] Self-critique failed: {e}")
            return {
                "needs_improvement": False,
                "risks_identified": [],
                "gaps_identified": [],
                "recommendations": [],
                "overall_assessment": f"Critique failed: {str(e)}"
            }

    def _improve_analysis(
        self, 
        state: ReflectionState, 
        critique: Dict[str, Any]
    ) -> str:
        """
        Generate improved analysis based on critique.
        
        Args:
            state: Current reflection state
            critique: Previous critique results
            
        Returns:
            Improved analysis as string
        """
        current_analysis = state.get("improved_analysis", state["initial_analysis"])
        
        prompt = f"""You are a financial advisor improving your analysis based on feedback.

Original Query: {state['query']}

Current Analysis:
{current_analysis}

Critique/Feedback:
- Risks identified: {critique.get('risks_identified', [])}
- Gaps identified: {critique.get('gaps_identified', [])}
- Recommendations: {critique.get('recommendations', [])}
- Assessment: {critique.get('overall_assessment', '')}

Please provide an improved analysis that addresses the critique.
Incorporate the identified risks, fill the gaps, and follow the recommendations.
Maintain professional tone and ensure regulatory compliance."""

        try:
            response = self.llm.invoke(prompt)
            improved = str(response.content) if hasattr(response, 'content') else str(response)
            logger.info("[ReflectionAgent] Analysis improved based on critique")
            return improved
        except Exception as e:
            logger.error(f"[ReflectionAgent] Analysis improvement failed: {e}")
            return current_analysis  # Return current analysis if improvement fails
