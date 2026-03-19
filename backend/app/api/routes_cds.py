"""
Clinical Decision Support (CDS) API Routes
=========================================
FastAPI routes for Clinical Decision Support using CrewAI.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import asyncio
import structlog

from ..core.schemas import (
    PatientInfo,
    CDSResponse,
    MedicalResearchRequest,
    MedicalResearchResponse,
    APIResponse,
)
from ..core.config import app_config
from ..orchestrators.crews.cds_crew import get_cds_crew
from ..tools.mcp_client import get_cds_task_tools

logger = structlog.get_logger()
router = APIRouter()


class CDSAPIRequest(BaseModel):
    """CDS API request schema."""
    patient_info: PatientInfo = Field(description="Patient information")
    images: Optional[List[str]] = Field(
        default=None,
        description="Base64 encoded images (e.g., X-rays, CT scans)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


@router.post("/analyze", response_model=APIResponse)
async def analyze_patient(request: CDSAPIRequest):
    """
    Analyze patient information and provide clinical decision support.
    
    Uses CrewAI hierarchical process with:
    - ClinicalCoordinator (manager)
    - 13 specialist agents (Pediatrics, OBGYN, Internal Medicine, Surgery,
      Psychiatry, Pathology, Pharmacology, Radiology, Family Medicine,
      Community Medicine, Ophthalmology, Anesthesia, Emergency)
    - MedicalResearcher
    - TreatmentAdvisor
    
    Returns structured clinical response with diagnosis, investigations, 
    treatment plans, and specialist referrals.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Get CDS crew
        cds_crew = get_cds_crew()
        
        # Run CrewAI analysis in thread pool to avoid blocking
        result = await asyncio.to_thread(
            cds_crew.analyze_patient,
            request.patient_info,
            request.images,
        )
        
        return APIResponse(
            success=True,
            message="Clinical analysis completed",
            data=result.model_dump(),
        )
        
    except Exception as e:
        logger.error("cds_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical analysis failed: {str(e)}",
        )


@router.get("/specialists", response_model=APIResponse)
async def list_specialists():
    """
    List available medical specialists in the CDS system.
    """
    specialists = [
        {"id": "pediatrics", "name": "Pediatrics", "description": "Children's health"},
        {"id": "obgyn", "name": "Obstetrics & Gynecology", "description": "Women's health"},
        {"id": "internal_medicine", "name": "Internal Medicine", "description": "Adult diseases"},
        {"id": "surgery", "name": "Surgery", "description": "Surgical procedures"},
        {"id": "psychiatry", "name": "Psychiatry", "description": "Mental health"},
        {"id": "pathology", "name": "Pathology", "description": "Disease diagnosis"},
        {"id": "pharmacology", "name": "Pharmacology", "description": "Medication expertise"},
        {"id": "radiology", "name": "Radiology", "description": "Imaging interpretation"},
        {"id": "family_medicine", "name": "Family Medicine", "description": "Primary care"},
        {"id": "community_medicine", "name": "Community Medicine", "description": "Public health"},
        {"id": "ophthalmology", "name": "Ophthalmology", "description": "Eye health"},
        {"id": "anesthesia", "name": "Anesthesia", "description": "Anesthesia and pain"},
        {"id": "emergency", "name": "Emergency Medicine", "description": "Emergency care"},
    ]
    
    return APIResponse(
        success=True,
        message="Specialists retrieved",
        data={"specialists": specialists},
    )


@router.post("/query", response_model=APIResponse)
async def query_medical_research(request: MedicalResearchRequest):
    """
    Query medical literature and clinical guidelines with evidence-backed responses.
    
    This endpoint allows doctors to ask specific medical questions and receive
    evidence-backed responses with citations from clinical guidelines and
    medical literature. Results are ranked by evidence level.
    
    Uses MCP tools to search medical databases and synthesize responses.
    """
    try:
        # Get CDS task tools registry directly to access TaskTool objects
        task_tools = get_cds_task_tools()
        
        # Access the internal _tools dict to get TaskTool objects with .name attribute
        available_tools = task_tools._tools
        
        # Initialize sources list
        sources = []
        
        # Search medical literature
        if "search_medical_literature" in available_tools:
            lit_tool = available_tools["search_medical_literature"]
            lit_result = await asyncio.to_thread(
                lit_tool,
                query=request.query,
                max_results=request.max_results
            )
            sources.append({
                "type": "medical_literature",
                "content": lit_result,
                "evidence_level": "rct"
            })
        
        # Lookup clinical guidelines
        if "lookup_clinical_guidelines" in available_tools:
            guideline_tool = available_tools["lookup_clinical_guidelines"]
            guideline_result = await asyncio.to_thread(
                guideline_tool,
                condition=request.query
            )
            sources.append({
                "type": "clinical_guidelines",
                "content": guideline_result,
                "evidence_level": "clinical_guidelines"
            })
        
        # Synthesize response using OpenRouter
        # In a production system, this would use an LLM to synthesize the sources
        # For now, we'll create a structured response from the tool outputs
        summary_parts = []
        for source in sources:
            summary_parts.append(f"From {source['type']}:\n{source['content']}")
        
        summary = "\n\n".join(summary_parts)
        
        # Build evidence summary
        evidence_counts = {}
        for source in sources:
            level = source['evidence_level']
            evidence_counts[level] = evidence_counts.get(level, 0) + 1
        
        # Create response
        response = MedicalResearchResponse(
            sources=sources,
            summary=summary,
            clinical_relevance=f"Evidence-backed response to query: {request.query}",
            evidence_summary=evidence_counts if evidence_counts else None
        )
        
        return APIResponse(
            success=True,
            message="Medical research query completed",
            data=response.model_dump(),
        )
        
    except Exception as e:
        logger.error("medical_research_query_failed", query=request.query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Medical research query failed: {str(e)}",
        )


__all__ = ["router"]
