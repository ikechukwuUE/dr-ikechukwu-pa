"""
Medicine Domain Agents — BeeAI RequirementAgent Implementation
=============================================================
8 agents for the medicine domain as specified in ARCHITECTURE.md.
Uses BeeAI Framework's RequirementAgent with ConditionalRequirement for
predictable, controlled execution behavior.

State-of-the-art implementation with proper tool integration and human-in-the-loop.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any

# BeeAI Framework imports
from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.agents.requirement.requirements.ask_permission import AskPermissionRequirement
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool

# Shared schemas and prompts
from shared.schemas import (
    Urgency,
    UserQuery,
    TriageNote,
    SpecialistResponse,
    PatientInfo,
    ManagementPlan,
    ResearchQuestion,
    ResearchManuscript,
    MedicalNewsReport,
)
from shared.prompts import (
    MEDICINE_COORDINATOR_PROMPT,
    MEDICINE_TRIAGE_PROMPT,
    MEDICINE_SPECIALIST_PROMPT,
    MEDICINE_EMERGENCY_PROMPT,
    MEDICINE_RESEARCHER_PROMPT,
    MEDICINE_SCIENTIFIC_WRITER_PROMPT,
    MEDICINE_CLINICAL_MANAGEMENT_PROMPT,
    # 12 New Specialist prompts
    MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
    MEDICINE_GENERAL_SURGEON_PROMPT,
    MEDICINE_PEDIATRICIAN_PROMPT,
    MEDICINE_GYNECOLOGIST_OBSTETRICIAN_PROMPT,
    MEDICINE_PHARMACIST_PROMPT,
    MEDICINE_PATHOLOGIST_PROMPT,
    MEDICINE_RADIOLOGIST_PROMPT,
    MEDICINE_ANESTHESIOLOGIST_PROMPT,
    MEDICINE_FAMILY_PHYSICIAN_PROMPT,
    MEDICINE_COMMUNITY_PHYSICIAN_PROMPT,
    MEDICINE_PSYCHIATRIST_PROMPT,
    MEDICINE_OPHTHALMOLOGIST_PROMPT,
)

# Configuration
from app.core.config import openrouter_config

# MCP Tools - Using client helper to fetch from MCP server
from mcp_clients.client import get_mcp_tools_sync, get_fallback_tools, create_mcp_agent

# BeeAI built-in tools
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

# BeeAI middleware for trajectory monitoring
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# AGENT STATE
# ============================================================================

class MedicineState:
    """State for medicine domain workflows."""
    query: str = ""
    image_base64: Optional[str] = None
    image_description: Optional[str] = None
    urgency: Optional[Urgency] = None
    specialty: Optional[str] = None
    triage_note: Optional[TriageNote] = None
    specialist_response: Optional[SpecialistResponse] = None
    patient_info: Optional[PatientInfo] = None
    management_plan: Optional[ManagementPlan] = None
    human_approved: bool = False
    human_feedback: Optional[str] = None
    final_output: Optional[str] = None


# ============================================================================
# BEEAI REQUIREMENT AGENTS
# ============================================================================

def create_coordinator_agent() -> Optional[RequirementAgent]:
    """
    Coordinator Agent — Entry point that classifies requests into pipelines.
    
    Uses ThinkTool for reasoning and DuckDuckGoSearchTool for information gathering.
    Forces thinking first, then search at least once.
    """
    
    try:
        # Load MCP tools (async but handled internally)
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=MEDICINE_COORDINATOR_PROMPT,
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Coordinator Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Coordinator Agent: {e}")
        return None


def create_triage_agent() -> Optional[RequirementAgent]:
    """
    Triage Agent — Assesses urgency and routes to specialty.
    
    Uses ThinkTool for reasoning and MCP tools for clinical context.
    """
    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=MEDICINE_TRIAGE_PROMPT,
            middlewares=[GlobalTrajectoryMiddleware()],
        )
        
        logger.info("Triage Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Triage Agent: {e}")
        return None


def create_specialist_agent(specialty: str = "General Medicine") -> Optional[RequirementAgent]:
    """
    Specialist Agent — Evidence-based specialist assessment.
    
    Uses ThinkTool for reasoning and medical_database_search for evidence.
    Supports multimodal image analysis. Routes to appropriate specialist based on specialty.
    
    Args:
        specialty: The medical specialty (Internal Medicine, Cardiology, Surgery, etc.)
    """

    # Map specialty to appropriate prompt
    specialty_prompts = {
        "Internal Medicine": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "General Surgery": MEDICINE_GENERAL_SURGEON_PROMPT,
        "Pediatrics": MEDICINE_PEDIATRICIAN_PROMPT,
        "Gynecology": MEDICINE_GYNECOLOGIST_OBSTETRICIAN_PROMPT,
        "Obstetrics": MEDICINE_GYNECOLOGIST_OBSTETRICIAN_PROMPT,
        "OB/GYN": MEDICINE_GYNECOLOGIST_OBSTETRICIAN_PROMPT,
        "Pharmacy": MEDICINE_PHARMACIST_PROMPT,
        "Pharmacology": MEDICINE_PHARMACIST_PROMPT,
        "Pathology": MEDICINE_PATHOLOGIST_PROMPT,
        "Radiology": MEDICINE_RADIOLOGIST_PROMPT,
        "Anesthesiology": MEDICINE_ANESTHESIOLOGIST_PROMPT,
        "Family Medicine": MEDICINE_FAMILY_PHYSICIAN_PROMPT,
        "Community Medicine": MEDICINE_COMMUNITY_PHYSICIAN_PROMPT,
        "Public Health": MEDICINE_COMMUNITY_PHYSICIAN_PROMPT,
        "Psychiatry": MEDICINE_PSYCHIATRIST_PROMPT,
        "Mental Health": MEDICINE_PSYCHIATRIST_PROMPT,
        "Ophthalmology": MEDICINE_OPHTHALMOLOGIST_PROMPT,
        "Eye Care": MEDICINE_OPHTHALMOLOGIST_PROMPT,
        "Cardiology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Neurology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Gastroenterology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Nephrology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Pulmonology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Endocrinology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Oncology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
        "Rheumatology": MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
    }
    
    prompt = specialty_prompts.get(specialty, MEDICINE_SPECIALIST_PROMPT)
    
    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + get_mcp_tools_sync(openrouter_config.mcp_server_url),
            instructions=prompt,
            requirements=[
                ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2),
            ],
        )
        
        logger.info(f"Specialist Agent created for {specialty}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Specialist Agent: {e}")
        return None


def create_internal_physician_agent() -> Optional[RequirementAgent]:
    """Internal Medicine Physician - Adult diseases, comprehensive care."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_INTERNAL_PHYSICIAN_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Internal Physician Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Internal Physician Agent: {e}")
        return None


def create_general_surgeon_agent() -> Optional[RequirementAgent]:
    """General Surgery Physician - Surgical consultation and management."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_GENERAL_SURGEON_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("General Surgeon Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create General Surgeon Agent: {e}")
        return None


def create_pediatrician_agent() -> Optional[RequirementAgent]:
    """Pediatrician - Infant, child, adolescent care."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_PEDIATRICIAN_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Pediatrician Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Pediatrician Agent: {e}")
        return None


def create_gynecologist_obstetrician_agent() -> Optional[RequirementAgent]:
    """Gynecologist/Obstetrician - Women's health, pregnancy care."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_GYNECOLOGIST_OBSTETRICIAN_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Gynecologist/Obstetrician Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Gynecologist/Obstetrician Agent: {e}")
        return None


def create_pharmacist_agent() -> Optional[RequirementAgent]:
    """Clinical Pharmacist - Medication expertise, drug information."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_PHARMACIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Pharmacist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Pharmacist Agent: {e}")
        return None


def create_pathologist_agent() -> Optional[RequirementAgent]:
    """Pathologist - Laboratory interpretation, pathology diagnosis."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_PATHOLOGIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Pathologist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Pathologist Agent: {e}")
        return None


def create_radiologist_agent() -> Optional[RequirementAgent]:
    """Radiologist - Medical imaging interpretation."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_RADIOLOGIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Radiologist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Radiologist Agent: {e}")
        return None


def create_anesthesiologist_agent() -> Optional[RequirementAgent]:
    """Anesthesiologist - Anesthesia and perioperative care."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_ANESTHESIOLOGIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Anesthesiologist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Anesthesiologist Agent: {e}")
        return None


def create_family_physician_agent() -> Optional[RequirementAgent]:
    """Family Medicine Physician - Comprehensive primary care."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_FAMILY_PHYSICIAN_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Family Physician Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Family Physician Agent: {e}")
        return None


def create_community_physician_agent() -> Optional[RequirementAgent]:
    """Community Medicine Physician - Population health, preventive medicine."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_COMMUNITY_PHYSICIAN_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Community Physician Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Community Physician Agent: {e}")
        return None


def create_psychiatrist_agent() -> Optional[RequirementAgent]:
    """Psychiatrist - Mental health diagnosis and treatment."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_PSYCHIATRIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Psychiatrist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Psychiatrist Agent: {e}")
        return None


def create_ophthalmologist_agent() -> Optional[RequirementAgent]:
    """Ophthalmologist - Eye care, vision services."""
    try:
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        agent = RequirementAgent(
            llm=model,
            tools=[ThinkTool(), DuckDuckGoSearchTool()],
            instructions=MEDICINE_OPHTHALMOLOGIST_PROMPT,
            requirements=[ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=0, max_invocations=2)],
        )
        logger.info("Ophthalmologist Agent created")
        return agent
    except Exception as e:
        logger.error(f"Failed to create Ophthalmologist Agent: {e}")
        return None


def create_emergency_physician_agent() -> Optional[RequirementAgent]:
    """
    Emergency Physician Agent — Handles EMERGENCY cases with ABC assessment.
    
    Uses ThinkTool for rapid assessment and medical_database_search for protocols.
    """

    try:
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                # medical_database_search,
            ],
            instructions=MEDICINE_EMERGENCY_PROMPT,
        )
        
        logger.info("Emergency Physician Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Emergency Physician Agent: {e}")
        return None


def create_doctor_user_agent() -> Optional[RequirementAgent]:
    """
    Doctor User Agent — Human-in-the-loop gate for approval.
    
    Uses AskPermissionRequirement to pause for human approval.
    """

    try:
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
            ],
            instructions="""You are a Doctor User Agent serving as a human-in-the-loop gate.

Your role:
1. Review clinical assessments and recommendations
2. Approve or request modifications to treatment plans
3. Provide feedback on AI-generated clinical decisions
4. Ensure patient safety through human oversight

When reviewing:
- Assess clinical accuracy and appropriateness
- Consider patient-specific factors
- Verify evidence-based recommendations
- Check for contraindications and interactions

Output format: Return a JSON object with:
- approved: Whether you approve the recommendation (true/false)
- feedback: Your clinical feedback
- modifications: Specific modifications requested (if any)""",
            requirements=[
                AskPermissionRequirement(),
            ],
        )
        
        logger.info("Doctor User Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Doctor User Agent: {e}")
        return None


def create_researcher_agent() -> Optional[RequirementAgent]:
    """
    Researcher Agent — Conducts literature reviews and evidence synthesis.
    
    Uses ThinkTool for research methodology, medical_database_search for clinical evidence,
    and DuckDuckGoSearchTool for latest research papers and publications.
    """

    try:
        # Get model with parallel tool calls enabled
        model = ChatModel.from_name(
            openrouter_config.medicine_model,
            api_key=openrouter_config.api_key,
            base_url=openrouter_config.base_url
        )
        model.allow_parallel_tool_calls = True
        
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=model,
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            instructions=MEDICINE_RESEARCHER_PROMPT,
            requirements=[
                ConditionalRequirement(DuckDuckGoSearchTool, min_invocations=1, max_invocations=3),
            ],
        )
        
        logger.info("Researcher Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Researcher Agent: {e}")
        return None


def create_scientific_writer_agent() -> Optional[RequirementAgent]:
    """
    Scientific Writer Agent — Formats medical documents.
    
    Uses ThinkTool for document structure and formatting.
    """

    try:
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
            ],
            requirements = [
                ConditionalRequirement(ThinkTool, force_at_step=1),
                ],
            instructions=MEDICINE_SCIENTIFIC_WRITER_PROMPT,
        )
        
        logger.info("Scientific Writer Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Scientific Writer Agent: {e}")
        return None


def create_clinical_management_agent() -> Optional[RequirementAgent]:
    """
    Clinical Management Agent — Creates personalized care plans.
    
    Uses ThinkTool for planning and MCP tools for guidelines.
    """

    try:
        mcp_tools = get_mcp_tools_sync(openrouter_config.mcp_server_url)
        
        agent = RequirementAgent(
            llm=ChatModel.from_name(
                openrouter_config.medicine_model,
                api_key=openrouter_config.api_key,
                base_url=openrouter_config.base_url
            ),
            tools=[
                ThinkTool(),
                DuckDuckGoSearchTool(),
            ] + mcp_tools,
            requirements = [
                ConditionalRequirement(ThinkTool, force_at_step=1),
            ],
            instructions=MEDICINE_CLINICAL_MANAGEMENT_PROMPT,
        )
        
        logger.info("Clinical Management Agent created successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create Clinical Management Agent: {e}")
        return None


# ============================================================================
# AGENT FACTORY
# ============================================================================

def create_medicine_agents() -> Dict[str, Any]:
    """
    Create all medicine domain agents.
    
    Returns:
        Dictionary of agent instances
    """
    agents = {}
    
    # Create agents with error handling
    agent_creators = {
        "coordinator": create_coordinator_agent,
        "triage": create_triage_agent,
        "specialist": create_specialist_agent,
        "emergency_physician": create_emergency_physician_agent,
        "doctor_user": create_doctor_user_agent,
        "researcher": create_researcher_agent,
        "scientific_writer": create_scientific_writer_agent,
        "clinical_management": create_clinical_management_agent,
    }
    
    for name, creator in agent_creators.items():
        try:
            agent = creator()
            if agent:
                agents[name] = agent
                logger.info(f"Created {name} agent successfully")
            else:
                logger.warning(f"Failed to create {name} agent")
        except Exception as e:
            logger.error(f"Error creating {name} agent: {e}")
    
    return agents


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Schemas (re-exported from shared)
    "Urgency", "UserQuery", "TriageNote", "SpecialistResponse",
    "PatientInfo", "ManagementPlan", "ResearchQuestion", "ResearchManuscript",
    "MedicalNewsReport",
    # State
    "MedicineState",
    # Tools (re-exported from mcp_servers)
    "medical_database_search", "lab_value_interpreter",
    # Agent creators
    "create_coordinator_agent", "create_triage_agent", "create_specialist_agent",
    "create_emergency_physician_agent", "create_doctor_user_agent",
    "create_researcher_agent", "create_scientific_writer_agent",
    "create_clinical_management_agent",
    # Factory
    "create_medicine_agents",
]
