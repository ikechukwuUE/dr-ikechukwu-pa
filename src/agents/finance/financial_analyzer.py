"""
Financial Analyzer Agent
========================
Initial data gathering and analysis for financial queries.
"""

from typing import TypedDict, List, Dict, Any, Optional
import logging
import re
from src.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

# Model configuration - now using config.py settings
FINANCE_MODEL = None  # Set by LLMFactory at runtime


class AnalyzerState(TypedDict):
    """State for financial analyzer."""
    query: str
    data: Dict[str, Any]
    analysis: str
    confidence: float


class FinancialAnalyzer:
    """
    Financial analyzer that gathers data and creates initial analysis.
    
    Capabilities:
    - Extract financial terms and instruments
    - Assess risk profile
    - Gather relevant financial data
    - Create initial analysis
    """

    # Common financial instruments and terms
    FINANCIAL_INSTRUMENTS = [
        "stocks", "bonds", "mutual funds", "ETFs", "options", "futures",
        "derivatives", "commodities", "forex", "cryptocurrency", "real estate",
        "fixed income", "equity", "fixed deposit", "savings account",
        "pension", "annuity", "insurance", "wealth management"
    ]

    RISK_LEVELS = ["low", "medium", "medium-high", "high"]

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

    def analyze(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AnalyzerState:
        """
        Gather financial data and create initial analysis.
        
        Args:
            query: Financial query to analyze
            context: Optional context for analysis
            
        Returns:
            AnalyzerState with data, analysis, and confidence
        """
        # Sanitize input
        sanitized_query, redacted = self.sanitizer.sanitize_clinical_prompt(query)
        
        logger.info(f"[FinancialAnalyzer] Starting analysis. Redacted {len(redacted)} items")
        
        # Initialize state
        state: AnalyzerState = {
            "query": sanitized_query,
            "data": {},
            "analysis": "",
            "confidence": 0.0
        }

        # Step 1: Extract financial terms
        state["data"]["instruments"] = self._extract_financial_terms(sanitized_query)
        
        # Step 2: Assess risk profile
        state["data"]["risk_profile"] = self._assess_risk_profile(sanitized_query)
        
        # Step 3: Gather additional data from context
        if context:
            state["data"]["context_data"] = context
        
        # Step 4: Create initial analysis
        state["analysis"] = self._create_analysis(state)
        
        # Step 5: Calculate confidence
        state["confidence"] = self._calculate_confidence(state)

        logger.info(
            f"[FinancialAnalyzer] Analysis complete. "
            f"Instruments: {len(state['data'].get('instruments', []))}, "
            f"Risk: {state['data'].get('risk_profile', {}).get('level', 'unknown')}, "
            f"Confidence: {state['confidence']:.2f}"
        )

        return state

    def _extract_financial_terms(self, query: str) -> List[str]:
        """
        Identify financial instruments and terms mentioned in query.
        
        Args:
            query: Sanitized financial query
            
        Returns:
            List of identified financial instruments
        """
        query_lower = query.lower()
        found_instruments: List[str] = []
        
        for instrument in self.FINANCIAL_INSTRUMENTS:
            if instrument.lower() in query_lower:
                found_instruments.append(instrument)
        
        # Also use LLM to extract additional terms
        prompt = f"""Extract all financial instruments and products mentioned in this query.
Only include specific named financial products/instruments.

Query: {query}

Return a JSON array of instrument names:
["instrument1", "instrument2", ...]"""

        try:
            response = self.llm.invoke(prompt)
            result_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Parse JSON array from response
            import json
            import re
            
            json_match = re.search(r'\[[^\]]*\]', result_text)
            if json_match:
                try:
                    llm_instruments = json.loads(json_match.group())
                    for inst in llm_instruments:
                        if inst not in found_instruments:
                            found_instruments.append(inst)
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logger.warning(f"[FinancialAnalyzer] LLM instrument extraction failed: {e}")
        
        logger.info(f"[FinancialAnalyzer] Extracted instruments: {found_instruments}")
        return found_instruments
        
        logger.info(f"[FinancialAnalyzer] Extracted instruments: {found_instruments}")
        return found_instruments

    def _assess_risk_profile(self, query: str) -> Dict[str, Any]:
        """
        Determine risk tolerance based on query analysis.
        
        Args:
            query: Sanitized financial query
            
        Returns:
            Dictionary with risk assessment
        """
        prompt = f"""Analyze the following financial query to determine the client's risk profile.

Query: {query}

Consider:
1. Investment time horizon mentioned
2. Types of investments discussed
3. Return expectations
4. Any explicit risk tolerance statements

Provide risk assessment in JSON format:
{{
    \"level\": \"low/medium/medium-high/high\",
    \"horizon\": \"short-term/medium-term/long-term\",
    \"rationale\": \"brief explanation\",
    \"keywords\": [\"keyword1\", \"keyword2\"]
}}"""

        try:
            response = self.llm.invoke(prompt)
            result_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Parse JSON from response
            import json
            import re
            
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    profile = json.loads(json_match.group())
                except json.JSONDecodeError:
                    profile = {
                        "level": "medium",
                        "horizon": "medium-term",
                        "rationale": "Could not parse LLM response",
                        "keywords": []
                    }
            else:
                profile = {
                    "level": "medium",
                    "horizon": "medium-term",
                    "rationale": result_text[:100],
                    "keywords": []
                }
            
            logger.info(f"[FinancialAnalyzer] Risk profile: {profile.get('level', 'unknown')}")
            return profile
            
        except Exception as e:
            logger.error(f"[FinancialAnalyzer] Risk profile assessment failed: {e}")
            return {
                "level": "medium",
                "horizon": "medium-term",
                "rationale": f"Assessment failed: {str(e)}",
                "keywords": []
            }

    def _create_analysis(self, state: AnalyzerState) -> str:
        """
        Create initial financial analysis based on gathered data.
        
        Args:
            state: Current analyzer state
            
        Returns:
            Initial analysis as string
        """
        instruments = state["data"].get("instruments", [])
        risk_profile = state["data"].get("risk_profile", {})
        
        prompt = f"""Create an initial financial analysis based on the following data.

Query: {state['query']}

Identified Financial Instruments: {instruments}

Risk Profile Assessment:
- Risk Level: {risk_profile.get('level', 'unknown')}
- Investment Horizon: {risk_profile.get('horizon', 'unknown')}
- Rationale: {risk_profile.get('rationale', '')}

Provide a comprehensive initial analysis covering:
1. Financial situation summary
2. Identified instruments and their relevance
3. Risk assessment based on profile
4. Preliminary considerations
5. Areas requiring deeper analysis

Be professional and thorough."""

        try:
            response = self.llm.invoke(prompt)
            analysis = str(response.content) if hasattr(response, 'content') else str(response)
            logger.info("[FinancialAnalyzer] Initial analysis created")
            return analysis
            
        except Exception as e:
            logger.error(f"[FinancialAnalyzer] Analysis creation failed: {e}")
            return f"Initial analysis could not be completed: {str(e)}"

    def _calculate_confidence(self, state: AnalyzerState) -> float:
        """
        Calculate confidence score for the analysis.
        
        Args:
            state: Current analyzer state
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on instruments identified
        instruments = state["data"].get("instruments", [])
        if len(instruments) > 0:
            confidence += 0.1
        if len(instruments) > 2:
            confidence += 0.1
            
        # Increase confidence based on risk profile
        risk_profile = state["data"].get("risk_profile", {})
        if risk_profile.get("level"):
            confidence += 0.1
        if risk_profile.get("horizon"):
            confidence += 0.1
            
        # Cap at 1.0
        return min(confidence, 1.0)
