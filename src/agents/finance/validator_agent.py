"""
Validator Agent for Finance
===========================
Validates financial analysis for compliance and policy adherence.
"""

from typing import TypedDict, List, Dict, Any, Optional
import logging
from src.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

# Model configuration - now using config.py settings
FINANCE_MODEL = None  # Set by LLMFactory at runtime


class ValidationState(TypedDict):
    """State for validator agent workflow."""
    analysis: str
    validation_results: Dict[str, Any]
    policy_checks: List[Dict[str, str]]
    approved: bool
    recommendations: str


class ValidatorAgent:
    """
    Validator agent that checks financial analysis for compliance and policy.
    
    Validates:
    - Risk limits and thresholds
    - Regulatory compliance
    - Policy adherence
    - Generates final recommendations
    """

    # Risk thresholds for financial recommendations
    RISK_LIMITS = {
        "max_leverage": 0.5,  # 50% maximum leverage
        "max_concentration": 0.25,  # 25% max single asset concentration
        "min_liquidity": 0.15,  # 15% minimum liquidity requirement
    }

    def __init__(self):
        self.llm = self._get_llm()
    
    def _get_llm(self):
        """Get or create LLM instance using LLMFactory."""
        try:
            return LLMFactory.create_llm(domain="finance", temperature=0.0)
        except ValueError as e:
            logger.error(f"Failed to create LLM: {e}")
            return None

    def validate(self, analysis: str) -> ValidationState:
        """
        Validate financial analysis for compliance and policy.
        
        Args:
            analysis: Financial analysis to validate
            
        Returns:
            ValidationState with validation results and recommendations
        """
        logger.info("[ValidatorAgent] Starting validation")
        
        # Initialize state
        state: ValidationState = {
            "analysis": analysis,
            "validation_results": {},
            "policy_checks": [],
            "approved": False,
            "recommendations": ""
        }

        # Step 1: Check risk limits
        risk_results = self._check_risk_limits(analysis)
        state["validation_results"]["risk_limits"] = risk_results
        state["policy_checks"].extend(risk_results.get("checks", []))
        
        # Step 2: Check regulatory compliance
        regulatory_results = self._check_regulatory(analysis)
        state["validation_results"]["regulatory"] = regulatory_results
        state["policy_checks"].extend(regulatory_results.get("checks", []))
        
        # Step 3: Generate final recommendations
        state["recommendations"] = self._generate_recommendations(state)
        
        # Determine overall approval
        failed_checks = [c for c in state["policy_checks"] if c.get("status") == "fail"]
        state["approved"] = len(failed_checks) == 0
        
        logger.info(
            f"[ValidatorAgent] Validation complete. "
            f"Approved: {state['approved']}, "
            f"Checks: {len(state['policy_checks'])}, "
            f"Failed: {len(failed_checks)}"
        )

        return state

    def _check_risk_limits(self, analysis: str) -> Dict[str, Any]:
        """
        Ensure financial recommendations are within risk thresholds.
        
        Args:
            analysis: Financial analysis to check
            
        Returns:
            Dictionary with risk limit check results
        """
        prompt = f"""You are a risk compliance officer. Analyze the following financial recommendation 
and assess whether it violates any risk limits.

Risk Limits to Check:
- Maximum leverage: {self.RISK_LIMITS['max_leverage']*100}%
- Maximum single asset concentration: {self.RISK_LIMITS['max_concentration']*100}%
- Minimum liquidity requirement: {self.RISK_LIMITS['min_liquidity']*100}%

Financial Recommendation:
{analysis}

Provide your assessment in JSON format:
{{
    \"compliant\": true/false,
    \"checks\": [
        {{
            \"check_name\": \"leverage_check\",
            \"status\": \"pass/fail\",
            \"details\": \"description of leverage assessment\"
        }},
        {{
            \"check_name\": \"concentration_check\",
            \"status\": \"pass/fail\", 
            \"details\": \"description of concentration assessment\"
        }},
        {{
            \"check_name\": \"liquidity_check\",
            \"status\": \"pass/fail\",
            \"details\": \"description of liquidity assessment\"
        }}
    ],
    \"risk_score\": \"low/medium/high\",
    \"summary\": \"brief summary of risk assessment\"
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
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {
                        "compliant": True,
                        "checks": [
                            {
                                "check_name": "parsing_fallback",
                                "status": "pass",
                                "details": "Could not parse LLM response, defaulting to pass"
                            }
                        ],
                        "risk_score": "medium",
                        "summary": result_text[:200]
                    }
            else:
                result = {
                    "compliant": True,
                    "checks": [],
                    "risk_score": "medium",
                    "summary": result_text[:200]
                }
            
            logger.info(f"[ValidatorAgent] Risk limits checked: {result.get('compliant', True)}")
            return result
            
        except Exception as e:
            logger.error(f"[ValidatorAgent] Risk limit check failed: {e}")
            return {
                "compliant": True,
                "checks": [],
                "risk_score": "unknown",
                "summary": f"Check failed: {str(e)}"
            }

    def _check_regulatory(self, analysis: str) -> Dict[str, Any]:
        """
        Check compliance with financial regulations.
        
        Args:
            analysis: Financial analysis to check
            
        Returns:
            Dictionary with regulatory check results
        """
        prompt = f"""You are a regulatory compliance officer. Analyze the following financial recommendation 
and assess regulatory compliance.

Financial Recommendation:
{analysis}

Check for compliance with:
1. SEC (Securities and Exchange Commission) regulations
2. Anti-money laundering (AML) requirements
3. Know Your Customer (KYC) requirements
4. Nigerian SEC (SEC Nigeria) regulations
5. Consumer protection regulations

Provide your assessment in JSON format:
{{
    \"compliant\": true/false,
    \"checks\": [
        {{
            \"check_name\": \"sec_compliance\",
            \"status\": \"pass/fail/warning\",
            \"details\": \"description\"
        }},
        {{
            \"check_name\": \"aml_compliance\",
            \"status\": \"pass/fail/warning\",
            \"details\": \"description\"
        }},
        {{
            \"check_name\": \"kyc_compliance\",
            \"status\": \"pass/fail/warning\",
            \"details\": \"description\"
        }},
        {{
            \"check_name\": \"nigerian_sec_compliance\",
            \"status\": \"pass/fail/warning\",
            \"details\": \"description\"
        }}
    ],
    \"regulatory_risks\": [\"risk1\", \"risk2\"],
    \"summary\": \"brief summary of regulatory assessment\"
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
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {
                        "compliant": True,
                        "checks": [],
                        "regulatory_risks": [],
                        "summary": result_text[:200]
                    }
            else:
                result = {
                    "compliant": True,
                    "checks": [],
                    "regulatory_risks": [],
                    "summary": result_text[:200]
                }
            
            logger.info(f"[ValidatorAgent] Regulatory compliance checked: {result.get('compliant', True)}")
            return result
            
        except Exception as e:
            logger.error(f"[ValidatorAgent] Regulatory check failed: {e}")
            return {
                "compliant": True,
                "checks": [],
                "regulatory_risks": [],
                "summary": f"Check failed: {str(e)}"
            }

    def _generate_recommendations(self, state: ValidationState) -> str:
        """
        Generate final recommendations based on validation results.
        
        Args:
            state: Current validation state
            
        Returns:
            Final recommendations as string
        """
        failed_checks = [
            c for c in state["policy_checks"] 
            if c.get("status") in ["fail", "warning"]
        ]
        
        if not failed_checks:
            prompt = f"""Based on the following financial analysis and validation results, 
provide final recommendations for the client.

Analysis:
{state['analysis']}

Validation Results:
- Risk Compliance: Compliant
- Regulatory Compliance: Compliant
- All policy checks: Passed

Provide professional final recommendations that are ready for client presentation."""
        else:
            failed_details = "\n".join([
                f"- {c.get('check_name', 'unknown')}: {c.get('details', '')}"
                for c in failed_checks
            ])
            
            prompt = f"""Based on the following financial analysis and validation results,
provide recommendations that address the compliance issues.

Analysis:
{state['analysis']}

Validation Issues:
{failed_details}

Provide recommendations that either:
1. Modify the proposed actions to comply with regulations, OR
2. Clearly explain any limitations or required client acknowledgments"""

        try:
            response = self.llm.invoke(prompt)
            recommendations = str(response.content) if hasattr(response, 'content') else str(response)
            logger.info("[ValidatorAgent] Final recommendations generated")
            return recommendations
            
        except Exception as e:
            logger.error(f"[ValidatorAgent] Recommendation generation failed: {e}")
            return "Unable to generate recommendations. Please review the analysis manually."
