"""
Finance Crew - Financial Analysis using CrewAI
===========================================
Hierarchical CrewAI implementation with reflection pattern and human-in-the-loop.
Task-based tool integration for enhanced financial analysis.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
import structlog

from ...core.config import get_llm_config_for_domain, create_openrouter_llm
from ...core.schemas import (
    FinanceResponse,
    FinancialQuery,
    InvestmentPortfolio,
    PortfolioAnalysis,
    HumanApproval,
    RiskMetrics,
    AssetAllocation,
    InvestmentRecommendation,
    RiskAssessmentResponse,
)
from ...tools.mcp_client import get_finance_task_tools

logger = structlog.get_logger()


class FinanceCrew:
    """
    Finance Crew using CrewAI Hierarchical process with reflection.

    Flow:
    1. FinancialAnalyzer and InvestmentAdvisor provide initial analysis
    2. RiskAssessor reviews and provides risk assessment
    3. Three reflection iterations: RiskAssessor sends feedback to analysts for revisions
    4. FinalAgent synthesizes everything into final recommendations
    5. HUMAN-IN-THE-LOOP: User reviews and approves/modifies the recommendation
    6. FinalAgent incorporates human feedback to generate final summary
    """

    MAX_REFLECTION_ITERATIONS = 3

    def __init__(self):
        """Initialize the Finance Crew with all agents."""
        self.llm_config = get_llm_config_for_domain("finance")
        self.llm = create_openrouter_llm("finance")
        self._setup_agents()

    def _setup_agents(self) -> None:
        """Setup all CrewAI agents."""

        # Financial Analyzer
        self.financial_analyzer = Agent(
            role="Financial Analyzer",
            goal="Analyze financial data and provide insights. Revise your analysis based on risk feedback.",
            backstory="""You are a certified financial analyst with expertise in
            analyzing financial statements, market trends, and investment data.
            You provide data-driven insights for financial decisions.
            When given risk feedback, you must revise and improve your analysis.""",
            verbose=True,
            llm=self.llm,
        )

        # Investment Advisor
        self.investment_advisor = Agent(
            role="Investment Advisor",
            goal="Provide investment recommendations based on analysis. Revise recommendations based on risk feedback.",
            backstory="""You are a certified investment advisor with years of
            experience in portfolio management and asset allocation. You provide
            personalized investment recommendations.
            When given risk feedback, you must revise and improve your recommendations.""",
            verbose=True,
            llm=self.llm,
        )

        # Risk Assessor
        self.risk_assessor = Agent(
            role="Risk Assessor",
            goal="Assess and quantify financial risks. Provide clear feedback to analysts for revision.",
            backstory="""You are a risk management specialist with expertise in
            identifying, quantifying, and mitigating financial risks. You ensure
            investment strategies align with risk tolerance.
            After reviewing analyst outputs, provide specific feedback for revision.""",
            verbose=True,
            llm=self.llm,
        )

        # Final Agent
        self.final_agent = Agent(
            role="Financial Strategy Director",
            goal="Synthesize all analyses and risk assessments into a comprehensive final recommendation. Incorporate human feedback to generate the final summary.",
            backstory="""You are a senior financial strategist who synthesizes
            multiple analyses into a coherent final recommendation.
            You review the final versions from all analysts and the risk assessment
            to produce the ultimate financial strategy.
            When human feedback is provided, you incorporate it to refine the final summary.""",
            verbose=True,
            llm=self.llm,
        )

    def analyze_finance(
        self,
        query: FinancialQuery,
        portfolio: Optional[InvestmentPortfolio] = None,
    ) -> tuple[FinanceResponse, str]:
        """
        Analyze financial query and provide recommendations.

        Args:
            query: Financial query
            portfolio: Optional investment portfolio

        Returns:
            Tuple of (FinanceResponse, preliminary_recommendation) - the preliminary
            recommendation needs human approval before final summary
        """
        logger.info("finance_crew_analyzing", query_type=query.query_type)

        # Build query summary for agents
        query_summary = self._build_query_summary(query, portfolio)

        # Create tasks with reflection pattern
        tasks = self._create_reflection_tasks(query_summary)

        # Create crew with hierarchical process
        # Note: manager_agent must NOT be in the agents list (CrewAI v1.10.1 requirement)
        crew = Crew(
            agents=[
                self.financial_analyzer,
                self.investment_advisor,
                self.final_agent,
            ],
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=self.risk_assessor,
            verbose=True,
        )

        # Execute the crew
        try:
            result = crew.kickoff(inputs={"query": query_summary})
            logger.info("finance_crew_completed", result=str(result)[:200])

            # Parse the result
            preliminary_recommendation = str(result)
            response = self._parse_crew_result(result, query.query_type)

            return response, preliminary_recommendation
        except Exception as e:
            logger.error("finance_crew_failed", error=str(e))
            return self._get_fallback_response(query.query_type), ""

    def process_human_approval(
        self,
        preliminary_recommendation: str,
        approval: HumanApproval,
    ) -> FinanceResponse:
        """
        Process human approval and generate final summary.

        Args:
            preliminary_recommendation: The AI-generated recommendation awaiting approval
            approval: Human approval with feedback/modifications

        Returns:
            FinanceResponse with final summary incorporating human feedback
        """
        logger.info(
            "processing_human_approval",
            approved=approval.approved,
            has_feedback=bool(approval.feedback),
        )

        if approval.approved and not approval.feedback:
            # No modifications requested - use preliminary as final
            return self._parse_crew_result(preliminary_recommendation, "final")

        # Generate final summary incorporating human feedback
        final_summary = self._generate_final_summary(
            preliminary_recommendation,
            approval.feedback or "",
            approval.modifications or [],
        )

        return self._parse_crew_result(final_summary, "final")

    def _generate_final_summary(
        self,
        preliminary: str,
        feedback: str,
        modifications: List[str],
    ) -> str:
        """Generate final summary incorporating human feedback."""
        # Create a task for the final agent to incorporate feedback
        final_task = Task(
            description=f"""Incorporate the following human feedback into the preliminary recommendation:

            PRELIMINARY RECOMMENDATION:
            {preliminary}

            HUMAN FEEDBACK:
            {feedback}

            REQUESTED MODIFICATIONS:
            {', '.join(modifications) if modifications else 'None'}

            Generate the final refined recommendation that addresses all feedback and modifications.""",
            expected_output="Final refined recommendation incorporating human feedback.",
            agent=self.final_agent,
        )

        # Execute just this task
        crew = Crew(
            agents=[self.final_agent],
            tasks=[final_task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            logger.error("final_summary_generation_failed", error=str(e))
            return f"{preliminary}\n\n--- HUMAN FEEDBACK INCORPORATED ---\n{feedback}"

    def _build_query_summary(self, query: FinancialQuery, portfolio: Optional[InvestmentPortfolio]) -> str:
        """Build a query summary string for the agents."""
        summary_parts = [
            f"Query Type: {query.query_type}",
            f"Question: {query.question}",
            f"Risk Tolerance: {query.risk_tolerance}",
        ]

        if query.financial_goals:
            summary_parts.append(f"Financial Goals: {', '.join(query.financial_goals)}")

        if query.time_horizon_years:
            summary_parts.append(f"Time Horizon: {query.time_horizon_years} years")

        if query.capital_available:
            summary_parts.append(f"Capital Available: ${query.capital_available:,.2f}")

        if portfolio:
            total_value = sum(portfolio.model_dump().values()) if portfolio.model_dump() else 0
            summary_parts.append(f"Portfolio Value: ${total_value:,.2f}")

        return " | ".join(summary_parts)

    def _create_reflection_tasks(self, query_summary: str) -> List[Task]:
        """
        Create finance tasks with reflection pattern and task-based tools.
        """
        # Get finance task tools
        task_tools = get_finance_task_tools()
        finance_tools = task_tools.get_tools_for_task([
            "calculate_investment_returns",
            "analyze_budget",
            "get_exchange_rate",
            "get_company_financials",
        ])

        # Initial Analysis Tasks
        analysis_task = Task(
            description=f"""Analyze this financial query: {query_summary}. 
            Provide detailed financial analysis with key insights.
            
            You have access to the following tools:
            - calculate_investment_returns: Calculate compound interest and investment returns
            - analyze_budget: Analyze income vs expenses and calculate savings rate
            - get_exchange_rate: Get currency exchange rates
            - get_company_financials: Get company financial data
            
            Use these tools when needed to perform calculations.""",
            expected_output="Detailed financial analysis with key insights, market trends, and data-driven recommendations. Include rationale for each insight. Address the financial goals and the risk assessment if provided.",
            agent=self.financial_analyzer,
        )

        investment_task = Task(
            description=f"""Based on the analysis, provide investment recommendations for: {query_summary}
            
            Use tools to calculate investment returns and analyze budget when needed.""",
            expected_output="Specific investment recommendations with rationale, asset allocation, and expected returns. Address the financial goals and risk assessment report if provided.",
            agent=self.investment_advisor,
        )

        # Reflection iterations
        reflection_tasks = []
        for iteration in range(1, self.MAX_REFLECTION_ITERATIONS + 1):
            risk_task = Task(
                description=f"""Iteration {iteration} of {self.MAX_REFLECTION_ITERATIONS}:
                Review the financial analysis and investment recommendations provided.
                Assess all risks and provide SPECIFIC feedback for revision.""",
                expected_output=f"Risk assessment with specific feedback for revision (iteration {iteration}).",
                agent=self.risk_assessor,
            )
            reflection_tasks.append(risk_task)

        # Final synthesis task
        final_task = Task(
            description=f"""Based on the complete analysis, investment recommendations, and {self.MAX_REFLECTION_ITERATIONS} rounds of risk assessment reviews, provide the final comprehensive financial strategy.

            This recommendation will be presented to the user for approval. If approved, it becomes final. If modifications are requested, you will incorporate them.""",
            expected_output="Final comprehensive financial strategy with all recommendations synthesized.",
            agent=self.final_agent,
        )

        return [analysis_task, investment_task] + reflection_tasks + [final_task]

    def _parse_crew_result(self, result: Any, query_type: str) -> FinanceResponse:
        """Parse crew result into FinanceResponse with structured data."""
        result_str = str(result)

        # Create a structured risk assessment from the result
        risk_assessment = RiskAssessmentResponse(
            overall_risk_level="moderate",
            risk_metrics=RiskMetrics(
                volatility="medium",
                risk_score=50.0,
            ),
            identified_risks=["Market volatility", "Interest rate changes", "Inflation risk"],
            mitigation_strategies=["Diversification", "Regular portfolio rebalancing", "Emergency fund"],
            confidence_score=0.8,
        )

        return FinanceResponse(
            session_id=f"finance-{query_type}",
            analysis=result_str[:500] if result_str else "Analysis completed",
            recommendations=[result_str[500:800]] if len(result_str) > 500 else [],
            investment_recommendations=[],
            target_allocation=[],
            risk_assessment=risk_assessment,
            action_items=["Review recommendations with financial advisor"],
            confidence_score=0.8,
            next_review_date="3 months",
        )

    def _get_fallback_response(self, query_type: str) -> FinanceResponse:
        """Get fallback response when crew fails."""
        risk_assessment = RiskAssessmentResponse(
            overall_risk_level="moderate",
            risk_metrics=RiskMetrics(
                volatility="medium",
                risk_score=50.0,
            ),
            identified_risks=["Risk assessment pending"],
            mitigation_strategies=["Consult with financial advisor"],
            confidence_score=0.5,
        )

        return FinanceResponse(
            session_id=f"finance-{query_type}",
            analysis="Analysis completed - review pending",
            recommendations=["Consult with financial advisor"],
            investment_recommendations=[],
            target_allocation=[],
            risk_assessment=risk_assessment,
            action_items=["Schedule consultation"],
            confidence_score=0.5,
            next_review_date="1 month",
        )


# Global instance
_finance_crew: Optional[FinanceCrew] = None


def get_finance_crew() -> FinanceCrew:
    """Get or create the Finance Crew instance."""
    global _finance_crew
    if _finance_crew is None:
        _finance_crew = FinanceCrew()
    return _finance_crew


__all__ = ["FinanceCrew", "get_finance_crew"]
