"""
AI Development (AI-Dev) API Routes
=================================
FastAPI routes for AI Development using LangGraph.
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
    CodeGenerationRequest,
    CodeGenerationResponse,
    CodeDebugRequest,
    CodeDebugResponse,
    APIResponse,
)
from ..orchestrators.graphs.aidev_graph import get_aidev_graph

logger = structlog.get_logger()
router = APIRouter()


class AIDevAPIRequest(BaseModel):
    """AI-Dev API request schema."""
    request_type: str = Field(description="Type of request: generate, debug, review")
    code_request: Optional[CodeGenerationRequest] = Field(default=None)
    debug_request: Optional[CodeDebugRequest] = Field(default=None)
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


@router.post("/generate", response_model=APIResponse)
async def generate_code(request: CodeGenerationRequest, session_id: Optional[str] = None):
    """
    Generate code using LangGraph state machine.
    
    Uses LangGraph cyclic workflow:
    - Write Code -> Execute Tool -> Evaluate -> Fix (Loop)
    """
    sid = session_id or str(uuid.uuid4())
    
    try:
        aidev_graph = get_aidev_graph()
        
        result = await asyncio.to_thread(
            aidev_graph.generate_code,
            request.task_description,
            request.language,
            request.constraints,
        )
        
        return APIResponse(
            success=True,
            message="Code generation completed",
            data=result.model_dump(),
        )
        
    except Exception as e:
        logger.error("code_generation_failed", error=str(e), session_id=sid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}",
        )


@router.post("/debug", response_model=APIResponse)
async def debug_code(request: CodeDebugRequest, session_id: Optional[str] = None):
    """
    Debug code using LangGraph.
    """
    sid = session_id or str(uuid.uuid4())
    
    try:
        aidev_graph = get_aidev_graph()
        
        result = await asyncio.to_thread(
            aidev_graph.debug_code,
            request.code,
            request.error_message,
            request.language,
        )
        
        return APIResponse(
            success=True,
            message="Code debugging completed",
            data=result.model_dump(),
        )
        
    except Exception as e:
        logger.error("code_debug_failed", error=str(e), session_id=sid)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code debugging failed: {str(e)}",
        )


@router.get("/languages", response_model=APIResponse)
async def list_languages():
    """
    List supported programming languages.
    """
    languages = [
        "python", "javascript", "typescript", "java", "csharp",
        "cpp", "go", "rust", "ruby", "php", "swift", "kotlin",
    ]
    
    return APIResponse(
        success=True,
        message="Languages retrieved",
        data={"languages": languages},
    )


__all__ = ["router"]
