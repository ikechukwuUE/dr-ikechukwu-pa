"""
Finance API Routes
================
FastAPI routes for Finance using CrewAI with human-in-the-loop support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import asyncio
import structlog

from ..core.schemas import (
    FinancialQuery,
    FinanceResponse,
    InvestmentPortfolio,
    PortfolioAnalysis,
    HumanApproval,
    APIResponse,
)
from ..orchestrators.crews.finance_crew import get_finance_crew

logger = structlog.get_logger()
router = APIRouter()

# Store preliminary recommendations for human approval
_preliminary_recommendations: Dict[str, str] = {}


class FinanceAPIRequest(BaseModel):
    """Finance API request schema."""
    query: FinancialQuery = Field(description="Financial query")
    portfolio: Optional[InvestmentPortfolio] = Field(
        default=None,
        description="Investment portfolio for analysis"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


class HumanApprovalRequest(BaseModel):
    """Request for human approval of financial recommendation."""
    session_id: str = Field(description="Session ID from initial analysis")
    preliminary_recommendation: str = Field(description="The preliminary recommendation to approve/modify")
    approval: HumanApproval = Field(description="Human approval and feedback")


@router.post("/analyze", response_model=APIResponse)
async def analyze_finance(request: FinanceAPIRequest):
    """
    Analyze financial query and provide recommendations.

    Uses CrewAI hierarchical process with:
    - FinancialAnalyzer
    - InvestmentAdvisor
    - RiskAssessor (manager)
    - FinalAgent

    Returns preliminary recommendation for human approval before final summary.
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # Get finance crew
        finance_crew = get_finance_crew()

        # Run analysis (returns preliminary recommendation)
        response, preliminary = await asyncio.to_thread(
            finance_crew.analyze_finance,
            request.query,
            request.portfolio,
        )

        # Store preliminary recommendation for human approval
        _preliminary_recommendations[session_id] = preliminary

        return APIResponse(
            success=True,
            message="Preliminary financial analysis ready for human approval",
            data={
                "session_id": session_id,
                "preliminary_recommendation": preliminary,
                "response": response.model_dump(),
                "requires_approval": True,
            },
        )

    except Exception as e:
        logger.error("finance_analysis_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Financial analysis failed: {str(e)}",
        )


@router.post("/approve", response_model=APIResponse)
async def approve_recommendation(request: HumanApprovalRequest):
    """
    Process human approval for financial recommendation.

    If approved: Returns final recommendation
    If modified: Incorporates feedback and generates refined final recommendation
    """
    session_id = request.session_id

    try:
        finance_crew = get_finance_crew()

        # Process human approval
        final_response = await asyncio.to_thread(
            finance_crew.process_human_approval,
            request.preliminary_recommendation,
            request.approval,
        )

        # Clear stored preliminary after approval
        if session_id in _preliminary_recommendations:
            del _preliminary_recommendations[session_id]

        approval_status = "approved" if request.approval.approved else "rejected"

        return APIResponse(
            success=True,
            message=f"Financial recommendation {approval_status}",
            data={
                "session_id": session_id,
                "response": final_response.model_dump(),
                "human_feedback": request.approval.feedback,
                "modifications": request.approval.modifications,
            },
        )

    except Exception as e:
        logger.error("human_approval_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing human approval failed: {str(e)}",
        )


@router.post("/portfolio/analyze", response_model=APIResponse)
async def analyze_portfolio(portfolio: InvestmentPortfolio):
    """
    Analyze investment portfolio and provide recommendations.
    """
    session_id = str(uuid.uuid4())

    try:
        # Calculate total value and asset allocation
        stocks_value = sum(portfolio.stocks.values()) if portfolio.stocks else 0
        bonds_value = sum(portfolio.bonds.values()) if portfolio.bonds else 0
        etfs_value = sum(portfolio.etfs.values()) if portfolio.etfs else 0
        cash_value = portfolio.cash or 0
        crypto_value = sum(portfolio.crypto.values()) if portfolio.crypto else 0

        total_value = stocks_value + bonds_value + etfs_value + cash_value + crypto_value

        # Calculate percentages
        asset_allocation = {}
        if total_value > 0:
            asset_allocation = {
                "stocks": round((stocks_value / total_value) * 100, 2),
                "bonds": round((bonds_value / total_value) * 100, 2),
                "etfs": round((etfs_value / total_value) * 100, 2),
                "cash": round((cash_value / total_value) * 100, 2),
                "crypto": round((crypto_value / total_value) * 100, 2),
            }

        # Basic risk metrics
        risk_score = (asset_allocation.get("crypto", 0) * 1.0 +
                      asset_allocation.get("stocks", 0) * 0.7 +
                      asset_allocation.get("etfs", 0) * 0.5 +
                      asset_allocation.get("bonds", 0) * 0.3 +
                      asset_allocation.get("cash", 0) * 0.1)

        risk_metrics = {
            "risk_score": round(risk_score / 100, 2),
            "volatility": "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
            "diversification_score": round(min(100, 100 - (len([v for v in [portfolio.stocks, portfolio.bonds, portfolio.etfs, portfolio.crypto] if v]) * 20)), 2),
        }

        # Generate suggestions
        suggestions = []
        if asset_allocation.get("cash", 0) > 30:
            suggestions.append("Consider investing excess cash for better returns")
        if asset_allocation.get("crypto", 0) > 20:
            suggestions.append("High crypto allocation - consider rebalancing for risk management")
        if len(portfolio.stocks or {}) < 5:
            suggestions.append("Consider diversifying your stock holdings")
        if not suggestions:
            suggestions.append("Portfolio allocation looks balanced")

        return APIResponse(
            success=True,
            message="Portfolio analysis completed",
            data={
                "total_value": total_value,
                "asset_allocation": asset_allocation,
                "risk_metrics": risk_metrics,
                "suggestions": suggestions,
            },
        )

    except Exception as e:
        logger.error("portfolio_analysis_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio analysis failed: {str(e)}",
        )


@router.get("/query-types", response_model=APIResponse)
async def list_query_types():
    """
    List available financial query types.
    """
    query_types = [
        {"id": "investment", "name": "Investment", "description": "Investment advice and analysis"},
        {"id": "budget", "name": "Budget", "description": "Budget planning and management"},
        {"id": "tax", "name": "Tax", "description": "Tax planning and optimization"},
        {"id": "retirement", "name": "Retirement", "description": "Retirement planning"},
        {"id": "debt", "name": "Debt", "description": "Debt management strategies"},
        {"id": "general", "name": "General", "description": "General financial advice"},
    ]

    return APIResponse(
        success=True,
        message="Query types retrieved",
        data={"query_types": query_types},
    )


@router.get("/risk-levels", response_model=APIResponse)
async def list_risk_levels():
    """
    List available risk tolerance levels.
    """
    risk_levels = [
        {"id": "conservative", "name": "Conservative", "description": "Low risk, stable returns"},
        {"id": "moderate", "name": "Moderate", "description": "Balanced risk and return"},
        {"id": "aggressive", "name": "Aggressive", "description": "High risk, high potential return"},
    ]

    return APIResponse(
        success=True,
        message="Risk levels retrieved",
        data={"risk_levels": risk_levels},
    )


__all__ = ["router"]
