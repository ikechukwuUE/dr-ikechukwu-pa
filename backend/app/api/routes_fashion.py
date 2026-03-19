"""
Fashion API Routes
==================
FastAPI routes for Fashion using direct langchain + OpenRouter.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import asyncio
import structlog
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

from ..core.schemas import (
    FashionQuery,
    FashionImageAnalysis,
    FashionResponse,
    OutfitRecommendation,
    APIResponse,
)
from ..core.config import get_llm_config_for_domain, create_openrouter_llm
from ..tools.mcp_client import get_fashion_task_tools

logger = structlog.get_logger()
router = APIRouter()


class FashionAPIRequest(BaseModel):
    """Fashion API request schema."""
    query: FashionQuery = Field(description="Fashion query")
    image_analysis: Optional[FashionImageAnalysis] = Field(
        default=None,
        description="Image analysis request"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


@router.post("/analyze", response_model=APIResponse)
async def analyze_fashion(request: FashionAPIRequest):
    """
    Analyze fashion query and provide recommendations.
    
    Uses direct langchain with OpenRouter (google/gemma-3-27b-it:free).
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        result = await asyncio.to_thread(
            _run_fashion_analysis,
            request.query.model_dump(),
            request.image_analysis.model_dump() if request.image_analysis else None,
            session_id,
        )
        
        return APIResponse(
            success=True,
            message="Fashion analysis completed",
            data=result,
        )
        
    except Exception as e:
        logger.error("fashion_analysis_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fashion analysis failed: {str(e)}",
        )


@router.post("/outfit", response_model=APIResponse)
async def get_outfit_recommendation(occasion: str, weather: Optional[str] = None):
    """
    Get outfit recommendations for a specific occasion.
    """
    session_id = str(uuid.uuid4())
    
    try:
        result = await asyncio.to_thread(
            _get_outfit_recommendation,
            {"occasion": occasion, "weather": weather},
            session_id,
        )
        
        return APIResponse(
            success=True,
            message="Outfit recommendation generated",
            data=result,
        )
        
    except Exception as e:
        logger.error("outfit_recommendation_failed", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outfit recommendation failed: {str(e)}",
        )


@router.get("/query-types", response_model=APIResponse)
async def list_fashion_query_types():
    """
    List available fashion query types.
    """
    query_types = [
        {"id": "style", "name": "Style", "description": "Style advice and recommendations"},
        {"id": "trend", "name": "Trend", "description": "Latest fashion trends"},
        {"id": "outfit", "name": "Outfit", "description": "Outfit recommendations"},
        {"id": "accessory", "name": "Accessory", "description": "Accessory recommendations"},
        {"id": "general", "name": "General", "description": "General fashion advice"},
    ]
    
    return APIResponse(
        success=True,
        message="Query types retrieved",
        data={"query_types": query_types},
    )


@router.get("/occasions", response_model=APIResponse)
async def list_occasions():
    """
    List available occasions for outfit recommendations.
    """
    occasions = [
        "formal", "casual", "business", "party", "wedding",
        "date_night", "workout", "beach", "winter", "summer", "conferences"]
    
    return APIResponse(
        success=True,
        message="Occasions retrieved",
        data={"occasions": occasions},
    )


def _run_fashion_analysis(
    query_data: Dict[str, Any],
    image_data: Optional[Dict[str, Any]],
    session_id: str,
) -> Dict[str, Any]:
    """
    Run fashion analysis using langchain + OpenRouter with MCP tools.
    
    Args:
        query_data: Fashion query data
        image_data: Optional image analysis data
        session_id: Session ID for tracking
    
    Returns:
        Fashion analysis results
    """
    logger.info("fashion_analysis_started", session_id=session_id)
    
    # Get fashion LLM
    llm = create_openrouter_llm("fashion")
    
    # Get and bind MCP tools to the LLM
    try:
        task_tools = get_fashion_task_tools()
        langchain_tools = task_tools.get_langchain_tools()
        if langchain_tools:
            # Bind tools to LLM for function calling
            llm = llm.bind_tools(langchain_tools)
            logger.info("fashion_tools_bound", tool_count=len(langchain_tools))
    except Exception as e:
        logger.warning("fashion_tools_not_available", error=str(e))
    
    # Build prompt based on query type
    query = FashionQuery(**query_data)
    query_type = query.query_type
    query_text = query.question
    
    # System prompt for fashion assistant
    system_prompt = """You are a professional fashion stylist and style consultant with extensive knowledge 
    of current trends, classic styles, and personalized fashion advice. You provide detailed, actionable 
    recommendations based on the user's preferences, body type, and occasion.
    
    Always respond with practical, specific advice. Format your response as a JSON object with the following structure:
    {
        "analysis": "Brief analysis of the query",
        "recommendations": ["Recommendation 1", "Recommendation 2", ...],
        "style_tips": ["Tip 1", "Tip 2", ...],
        "confidence_score": 0.0-1.0
    }
    """
    
    # Build user message
    user_message = f"Query Type: {query_type}\nQuery: {query_text}"
    
    if image_data:
        user_message += f"\n\nImage provided for analysis."
    
    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    # Invoke LLM
    response = llm.invoke(messages)
    
    # Parse response
    try:
        # Get content as string
        content_str = str(response.content)
        # Try to parse as JSON
        result_data = json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        # If not valid JSON, extract text
        result_data = {
            "analysis": response.content[:500],
            "recommendations": [],
            "style_tips": [],
            "confidence_score": 0.5,
        }
    
    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "query_type": query_type,
        "analysis": result_data.get("analysis", ""),
        "recommendations": result_data.get("recommendations", []),
        "style_tips": result_data.get("style_tips", []),
        "confidence_score": result_data.get("confidence_score", 0.7),
    }


def _get_outfit_recommendation(params: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """
    Get outfit recommendation using langchain + OpenRouter.
    
    Args:
        params: Parameters including occasion and weather
        session_id: Session ID for tracking
    
    Returns:
        Outfit recommendation
    """
    logger.info("outfit_recommendation_started", session_id=session_id)
    
    occasion = params.get("occasion", "casual")
    weather = params.get("weather")
    
    # Get fashion LLM
    llm = create_openrouter_llm("fashion")
    
    # System prompt
    system_prompt = """You are a professional fashion stylist. Provide outfit recommendations 
    based on the occasion and weather. Return a JSON object with:
    {
        "colors": ["color1", "color2", ...],
        "items": ["item1", "item2", ...],
        "accessories": ["accessory1", ...],
        "tips": ["tip1", ...]
    }
    """
    
    # Build user message
    user_message = f"Occasion: {occasion}"
    if weather:
        user_message += f"\nWeather: {weather}"
    user_message += "\nProvide outfit recommendations."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    
    response = llm.invoke(messages)
    
    try:
        content_str = str(response.content)
        result_data = json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        result_data = {
            "colors": [],
            "items": [],
            "accessories": [],
            "tips": [],
        }
    
    return {
        "occasion": occasion,
        "weather": weather,
        "colors": result_data.get("colors", []),
        "items": result_data.get("items", []),
        "accessories": result_data.get("accessories", []),
        "tips": result_data.get("tips", []),
    }


__all__ = ["router"]
