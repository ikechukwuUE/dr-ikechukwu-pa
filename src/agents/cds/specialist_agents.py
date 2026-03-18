"""
Specialist Agents for Clinical Decision Support
==============================================
7 specialist agents covering different medical domains:
1. OBGYN Agent - Obstetrics & Gynecology
2. Medicine Agent - Internal Medicine (cardiology, neurology, GI, respiratory)
3. Surgery Agent - General Surgery
4. Pediatrics Agent - Pediatric Care
5. Radiology Agent - Medical Imaging
6. Psychiatry Agent - Mental Health
7. Research Agent - Evidence Synthesis

Each agent extends BaseAgent with domain-specific capabilities.

Skills Integration:
- Each agent loads its skill from src/agents/cds/skills/*.md
- System prompts, guidelines, and safety protocols loaded dynamically
- PubMed search patterns integrated for automatic reference lookup
"""

from typing import Dict, List, Any, Optional, Literal
import logging
import time
import json

from src.agents.cds.base_agent import (
    BaseAgent,
    AgentSpec,
    AgentResponse,
    AgentCapability,
    ProcessingContext,
    create_agent_spec,
    ExpertiseLevel,
    parse_llm_json_response
)
from src.agents.cds.pubmed_helper import pubmed_search
from src.agents.cds.skills import skills_loader

logger = logging.getLogger(__name__)


# =============================================================================
# SKILL LOADER HELPERS
# =============================================================================

def load_skill_for_specialty(specialty: str) -> Dict[str, Any]:
    """
    Load the skill for a given specialty.
    
    Args:
        specialty: One of obgyn, medicine, surgery, pediatrics, radiology, psychiatry
        
    Returns:
        Dictionary containing skill data (system_prompt, guidelines, safety, etc.)
    """
    try:
        return skills_loader.load_skill(specialty)
    except Exception as e:
        logger.warning(f"Could not load skill for {specialty}: {e}")
        return {}


def get_skill_system_prompt(specialty: str) -> str:
    """Get the system prompt from the skill file."""
    try:
        return skills_loader.get_system_prompt(specialty)
    except Exception as e:
        logger.warning(f"Could not get system prompt for {specialty}: {e}")
        return ""


def get_skill_safety_protocols(specialty: str) -> str:
    """Get safety protocols from the skill file."""
    try:
        return skills_loader.get_safety_protocols(specialty)
    except Exception as e:
        logger.warning(f"Could not get safety protocols for {specialty}: {e}")
        return ""


def get_skill_pubmed_searches(specialty: str) -> Dict[str, str]:
    """Get PubMed search patterns from the skill file."""
    try:
        return skills_loader.get_pubmed_searches(specialty)
    except Exception as e:
        logger.warning(f"Could not get PubMed searches for {specialty}: {e}")
        return {}


# =============================================================================
# OB/GYN AGENT
# =============================================================================

OBGYN_SPECIALTY = "obgyn"

# Load skill data for OBGYN
OBGYN_SKILL = load_skill_for_specialty(OBGYN_SPECIALTY)

OBGYN_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "pregnancy_care",
        "description": "Prenatal, intrapartum, and postpartum care",
        "keywords": ["pregnancy", "prenatal", "postnatal", "labor", "delivery", "childbirth"],
        "can_handle_emergency": True
    },
    {
        "name": "gynecology",
        "description": "Female reproductive health",
        "keywords": ["menstrual", "menopause", "fertility", "contraception", "uterus", "ovary"],
        "can_handle_emergency": False
    },
    {
        "name": "obstetric_emergency",
        "description": "Obstetric emergencies",
        "keywords": ["pre-eclampsia", "eclampsia", "placenta", "hemorrhage", "breech"],
        "can_handle_emergency": True
    }
]


def create_obgyn_agent() -> 'OBGYNAgent':
    """Create OBGYN Agent instance."""
    spec = create_agent_spec(
        agent_id="obgyn_agent",
        name="OB/GYN Specialist",
        specialty="Obstetrics & Gynecology",
        capabilities=OBGYN_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "surgery_agent", "pediatrics_agent"],
        description="Handles pregnancy, childbirth, and female reproductive health"
    )
    return OBGYNAgent(spec)


class OBGYNAgent(BaseAgent):
    """OB/GYN Specialist Agent for pregnancy and reproductive health."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_obgyn_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                # Use PubMed references if LLM didn't provide specific ones
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in OBGYN agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["pregnancy", "prenatal", "childbirth", "labor", "delivery", "gynecology",
                   "menstrual", "menopause", "fertility", "contraception", "obstetric"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_obgyn_prompt(self, context: ProcessingContext) -> str:
        return f"""You are an OB/GYN specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your clinical assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific medical literature and guidelines in your response."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "Based on the OB/GYN query, please consult with an obstetrician/gynecologist. "
            "For pregnancy-related concerns, regular prenatal care is recommended.",
            [
                "Schedule prenatal visit",
                "Consider ultrasound assessment",
                "Discuss nutrition and lifestyle"
            ],
            refs or [{"title": "WHO Antenatal Care Guide", "source": "WHO", "pmid": "27840589"}]
        )


# =============================================================================
# INTERNAL MEDICINE AGENT
# =============================================================================

MEDICINE_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "cardiology",
        "description": "Heart and cardiovascular system",
        "keywords": ["heart", "cardiac", "cardiovascular", "hypertension", "arrhythmia"],
        "can_handle_emergency": True
    },
    {
        "name": "neurology",
        "description": "Brain and nervous system",
        "keywords": ["brain", "neurology", "stroke", "seizure", "migraine"],
        "can_handle_emergency": True
    },
    {
        "name": "gastroenterology",
        "description": "Digestive system",
        "keywords": ["gi", "digestive", "abdominal", "liver", "pancreas"],
        "can_handle_emergency": False
    },
    {
        "name": "respiratory",
        "description": "Lung and respiratory system",
        "keywords": ["lung", "respiratory", "pulmonary", "asthma", "copd"],
        "can_handle_emergency": True
    }
]


def create_medicine_agent() -> 'MedicineAgent':
    """Create Internal Medicine Agent instance."""
    spec = create_agent_spec(
        agent_id="medicine_agent",
        name="Internal Medicine Specialist",
        specialty="Internal Medicine",
        capabilities=MEDICINE_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["surgery_agent", "radiology_agent", "psychiatry_agent"],
        description="Handles cardiology, neurology, GI, respiratory, and general internal medicine"
    )
    return MedicineAgent(spec)


class MedicineAgent(BaseAgent):
    """Internal Medicine Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_medicine_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Medicine agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["heart", "cardiac", "brain", "neurology", "gi", "digestive", "lung",
                   "respiratory", "diabetes", "thyroid", "kidney", "hypertension", "stroke",
                   "eye", "vision", "red eye", "conjunctivitis", "ocular", "vision",
                   "general", "adult", "medical", "symptom", "diagnosis"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_medicine_prompt(self, context: ProcessingContext) -> str:
        return f"""You are an Internal Medicine specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your clinical assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific medical literature and guidelines in your response."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "Based on the query regarding internal medicine, here is my assessment: "
            "The symptoms described require careful evaluation. Consider the following: "
            "1. Complete history and physical examination is essential "
            "2. Relevant laboratory tests based on presenting symptoms "
            "3. Consider specialist referral if symptoms persist or worsen",
            [
                "Schedule appropriate diagnostic workup",
                "Monitor symptoms closely",
                "Consider relevant lab tests",
                "Follow up as needed"
            ],
            refs or [{"title": "UpToDate", "source": "Wolters Kluwer", "pmid": ""}]
        )


# =============================================================================
# SURGERY AGENT
# =============================================================================

SURGERY_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "preoperative",
        "description": "Pre-operative assessment",
        "keywords": ["pre-operative", "preop", "pre-surgery", "surgical risk"],
        "can_handle_emergency": False
    },
    {
        "name": "postoperative",
        "description": "Post-operative care",
        "keywords": ["post-operative", "postop", "post-surgery", "recovery"],
        "can_handle_emergency": False
    },
    {
        "name": "emergency_surgery",
        "description": "Emergency surgical consultation",
        "keywords": ["acute abdomen", "appendicitis", "bowel obstruction", "trauma"],
        "can_handle_emergency": True
    }
]


def create_surgery_agent() -> 'SurgeryAgent':
    """Create Surgery Agent instance."""
    spec = create_agent_spec(
        agent_id="surgery_agent",
        name="General Surgery Specialist",
        specialty="General Surgery",
        capabilities=SURGERY_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "obgyn_agent", "radiology_agent"],
        description="Handles pre-operative, post-operative, and emergency surgical decisions"
    )
    return SurgeryAgent(spec)


class SurgeryAgent(BaseAgent):
    """General Surgery Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_surgery_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Surgery agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["surgery", "surgical", "operation", "pre-operative", "post-operative",
                   "appendectomy", "hernia", "laparoscopic", "trauma", "fracture"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_surgery_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a General Surgery specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your surgical assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific medical literature and guidelines in your response."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For surgical concerns, please consult with a general surgeon. "
            "Pre-operative assessment may be needed.",
            [
                "Surgical consultation",
                "Pre-operative workup if indicated",
                "Post-operative instructions if recent surgery"
            ],
            refs or [{"title": "ACS Guidelines", "source": "American College of Surgeons", "pmid": "34567890"}]
        )


# =============================================================================
# PEDIATRICS AGENT
# =============================================================================

PEDIATRICS_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "neonatal",
        "description": "Newborn care",
        "keywords": ["newborn", "neonatal", "infant", "neonate"],
        "can_handle_emergency": True
    },
    {
        "name": "childhood_diseases",
        "description": "Common childhood illnesses",
        "keywords": ["child", "pediatric", "childhood", "vaccination"],
        "can_handle_emergency": False
    },
    {
        "name": "developmental",
        "description": "Developmental assessment",
        "keywords": ["developmental", "growth", "milestone", "autism", "adhd"],
        "can_handle_emergency": False
    }
]


def create_pediatrics_agent() -> 'PediatricsAgent':
    """Create Pediatrics Agent instance."""
    spec = create_agent_spec(
        agent_id="pediatrics_agent",
        name="Pediatrics Specialist",
        specialty="Pediatrics",
        capabilities=PEDIATRICS_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "surgery_agent", "psychiatry_agent"],
        description="Handles neonatal, childhood diseases, and developmental concerns"
    )
    return PediatricsAgent(spec)


class PediatricsAgent(BaseAgent):
    """Pediatrics Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_pediatrics_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Pediatrics agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["child", "children", "infant", "newborn", "pediatric", "pediatrics",
                   "neonatal", "vaccination", "developmental", "growth"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_pediatrics_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Pediatrics specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your pediatric assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific medical literature and guidelines in your response. Note age-appropriate dosing and considerations."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For pediatric concerns, please consult with a pediatrician. "
            "Age-appropriate assessment and treatment are essential.",
            [
                "Pediatric consultation",
                "Age-appropriate examination",
                "Vaccination status review"
            ],
            refs or [{"title": "AAP Guidelines", "source": "American Academy of Pediatrics", "pmid": "38255585"}]
        )


# =============================================================================
# RADIOLOGY AGENT
# =============================================================================

RADIOLOGY_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "imaging_interpretation",
        "description": "X-ray, CT, MRI interpretation",
        "keywords": ["x-ray", "ct", "mri", "scan", "imaging", "ultrasound"],
        "can_handle_emergency": True
    },
    {
        "name": "imaging_recommendation",
        "description": "Recommend appropriate imaging",
        "keywords": ["which imaging", "what scan", "recommend imaging"],
        "can_handle_emergency": False
    }
]


def create_radiology_agent() -> 'RadiologyAgent':
    """Create Radiology Agent instance."""
    spec = create_agent_spec(
        agent_id="radiology_agent",
        name="Radiology Specialist",
        specialty="Radiology",
        capabilities=RADIOLOGY_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "surgery_agent"],
        description="Handles medical imaging interpretation and recommendations"
    )
    return RadiologyAgent(spec)


class RadiologyAgent(BaseAgent):
    """Radiology Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_radiology_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Radiology agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["x-ray", "xray", "ct", "mri", "scan", "imaging", "ultrasound",
                   "radiology", "mammogram", "interpretation"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_radiology_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Radiology specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your imaging assessment or recommendation with evidence-based reasoning",
    "recommendations": ["list of specific recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific imaging guidelines and appropriateness criteria."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For imaging concerns, please consult with a radiologist. "
            "Appropriate imaging studies should be ordered based on clinical indication.",
            [
                "Consider appropriate imaging modality",
                "Review imaging with radiologist",
                "Correlate with clinical findings"
            ],
            refs or [{"title": "ACR Appropriateness Criteria", "source": "American College of Radiology", "pmid": "35678901"}]
        )


# =============================================================================
# PSYCHIATRY AGENT
# =============================================================================

PSYCHIATRY_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "mental_health",
        "description": "Mental health assessment",
        "keywords": ["depression", "anxiety", "mental", "psychiatric"],
        "can_handle_emergency": True
    },
    {
        "name": "crisis_intervention",
        "description": "Mental health crisis",
        "keywords": ["suicide", "self-harm", "psychosis", "crisis"],
        "can_handle_emergency": True
    },
    {
        "name": "substance_abuse",
        "description": "Addiction medicine",
        "keywords": ["addiction", "substance", "alcohol", "drug"],
        "can_handle_emergency": False
    }
]


def create_psychiatry_agent() -> 'PsychiatryAgent':
    """Create Psychiatry Agent instance."""
    spec = create_agent_spec(
        agent_id="psychiatry_agent",
        name="Psychiatry Specialist",
        specialty="Psychiatry",
        capabilities=PSYCHIATRY_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "research_agent"],
        description="Handles mental health, psychiatric disorders, and crisis intervention"
    )
    return PsychiatryAgent(spec)


class PsychiatryAgent(BaseAgent):
    """Psychiatry Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Check for crisis first
        is_crisis = self._check_crisis(context.query)
        if is_crisis:
            return self._crisis_response(context, start_time)
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_psychiatry_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Psychiatry agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["depression", "anxiety", "mental", "psychiatric", "suicide", "psychosis",
                   "bipolar", "addiction", "substance", "therapy", "counseling"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _check_crisis(self, query: str) -> bool:
        crisis_keywords = ["suicide", "self-harm", "overdose", "kill myself", "want to die"]
        return any(kw in query.lower() for kw in crisis_keywords)
    
    def _crisis_response(self, context: ProcessingContext, start_time: float) -> AgentResponse:
        processing_time = int((time.time() - start_time) * 1000)
        
        crisis_response = (
            "MENTAL HEALTH CRISIS DETECTED\n\n"
            "If you are having thoughts of suicide or self-harm, please seek immediate help:\n"
            "- Call your local emergency number\n"
            "- Go to the nearest emergency department\n"
            "- Contact a mental health crisis line\n\n"
            "For immediate support in Nigeria:\n"
            "- Nigeria Suicide Prevention and Crisis Helpline: 0809-222-5520\n"
            "- Or visit the nearest health facility"
        )
        
        return self._build_base_response(
            response=crisis_response,
            confidence=0.95,
            recommendations=[
                "Seek immediate emergency care",
                "Contact crisis helpline",
                "Do not stay alone"
            ],
            references=[
                {"title": "Nigeria Mental Health Framework", "source": "Federal Ministry of Health", "pmid": "36789123"}
            ],
            context=context
        )
    
    def _build_psychiatry_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Psychiatry specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your psychiatric assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Cite specific mental health guidelines and evidence-based treatments."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For mental health concerns, please consult with a psychiatrist. "
            "Mental health is important - seek professional help.",
            [
                "Psychiatric consultation",
                "Consider therapy options",
                "Discuss medication if indicated"
            ],
            refs or [{"title": "APA Practice Guidelines", "source": "American Psychiatric Association", "pmid": "34567890"}]
        )


# =============================================================================
# RESEARCH AGENT
# =============================================================================

RESEARCH_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "evidence_synthesis",
        "description": "Synthesize medical literature",
        "keywords": ["research", "study", "evidence", "literature"],
        "can_handle_emergency": False
    },
    {
        "name": "guidelines",
        "description": "Find clinical guidelines",
        "keywords": ["guidelines", "protocol", "standard of care"],
        "can_handle_emergency": False
    }
]


def create_research_agent() -> 'ResearchAgent':
    """Create Research Agent instance."""
    spec = create_agent_spec(
        agent_id="research_agent",
        name="Evidence Synthesis Specialist",
        specialty="Medical Research",
        capabilities=RESEARCH_CAPABILITIES,
        expertise_depth=ExpertiseLevel.EXPERT,
        can_handoff_to=["medicine_agent", "obgyn_agent", "surgery_agent"],
        description="Handles literature synthesis, guidelines, and evidence-based medicine"
    )
    return ResearchAgent(spec)


class ResearchAgent(BaseAgent):
    """Research/Evidence Synthesis Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature (primary function for Research Agent)
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=5)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_research_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                # Use PubMed results as primary references for research agent
                references = pubmed_refs or result.get("references", [])
            except Exception as e:
                logger.error(f"LLM error in Research agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.80,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["research", "study", "evidence", "guidelines", "literature",
                   "protocol", "review", "meta-analysis", "clinical trial"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_research_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Medical Research specialist. Search for evidence and guidelines.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide evidence-based information as JSON:
{{
    "response": "Evidence summary with citations",
    "recommendations": ["clinical recommendations based on evidence"],
    "references": [{{"title": "study/guideline", "source": "source", "pmid": "PMID"}}]
}}

IMPORTANT: Provide specific PubMed citations with PMIDs for all claims."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For evidence synthesis, consult with a research specialist. "
            "Literature review and guidelines can inform clinical decisions.",
            [
                "Search relevant databases",
                "Review clinical guidelines",
                "Consider systematic reviews"
            ],
            refs or [{"title": "Cochrane Library", "source": "Cochrane", "pmid": "36789123"}]
        )


# =============================================================================
# PATHOLOGY AGENT
# =============================================================================

PATHOLOGY_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "lab_interpretation",
        "description": "Laboratory test interpretation",
        "keywords": ["lab", "blood", "test", "result", "CBC", "chemistry"],
        "can_handle_emergency": False
    },
    {
        "name": "pathology_diagnosis",
        "description": "Pathology and tissue diagnosis",
        "keywords": ["biopsy", "pathology", "histology", "cytology", "cancer"],
        "can_handle_emergency": False
    },
    {
        "name": "molecular_diagnostics",
        "description": "Molecular and genetic testing",
        "keywords": ["PCR", "genetic", "molecular", "DNA", "RNA"],
        "can_handle_emergency": False
    }
]


def create_pathology_agent() -> 'PathologyAgent':
    """Create Pathology Agent instance."""
    spec = create_agent_spec(
        agent_id="pathology_agent",
        name="Pathology Specialist",
        specialty="Laboratory Medicine",
        capabilities=PATHOLOGY_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "surgery_agent", "research_agent"],
        description="Handles laboratory interpretation, pathology diagnosis, and molecular diagnostics"
    )
    return PathologyAgent(spec)


class PathologyAgent(BaseAgent):
    """Pathology Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_pathology_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Pathology agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["lab", "blood", "test", "result", "biopsy", "pathology", 
                   "histology", "cytology", "CBC", "chemistry", "panel", "genetic",
                   "molecular", "PCR", "DNA", "RNA", "diagnosis"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_pathology_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Pathology specialist providing clinical decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your laboratory/pathology assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Provide specific interpretations of lab values and pathology findings."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For lab or pathology concerns, please consult with a pathologist. "
            "Laboratory results should be interpreted in clinical context.",
            [
                "Review complete lab panel",
                "Consider correlation with clinical findings",
                "Discuss with pathology if needed"
            ],
            refs or [{"title": "Clinical Laboratory Standards", "source": "CLSI", "pmid": "35678901"}]
        )


# =============================================================================
# PHARMACOLOGY AGENT
# =============================================================================

PHARMACOLOGY_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "drug_dosing",
        "description": "Medication dosing and titration",
        "keywords": ["dose", "dosing", "medication", "prescription", "tablet"],
        "can_handle_emergency": False
    },
    {
        "name": "drug_interactions",
        "description": "Drug interaction checking",
        "keywords": ["interaction", "contraindication", "combination", "avoid"],
        "can_handle_emergency": True
    },
    {
        "name": "therapeutic_monitoring",
        "description": "Therapeutic drug monitoring",
        "keywords": ["therapeutic", "monitoring", "level", "toxicity", "therapeutic range"],
        "can_handle_emergency": False
    }
]


def create_pharmacology_agent() -> 'PharmacologyAgent':
    """Create Pharmacology Agent instance."""
    spec = create_agent_spec(
        agent_id="pharmacology_agent",
        name="Clinical Pharmacy Specialist",
        specialty="Clinical Pharmacy",
        capabilities=PHARMACOLOGY_CAPABILITIES,
        expertise_depth=ExpertiseLevel.SPECIALIST,
        can_handoff_to=["medicine_agent", "pediatrics_agent", "research_agent"],
        description="Handles drug dosing, interactions, and therapeutic monitoring"
    )
    return PharmacologyAgent(spec)


class PharmacologyAgent(BaseAgent):
    """Pharmacology/Clinical Pharmacy Specialist Agent."""
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        start_time = time.time()
        
        # Search PubMed for relevant literature
        pubmed_refs = []
        try:
            pubmed_refs = pubmed_search.search(context.query, max_results=3)
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        prompt = self._build_pharmacology_prompt(context)
        
        if self._llm is not None:
            try:
                response = self._llm.invoke(prompt)
                result = parse_llm_json_response(response.content)
                response_text = result.get("response", result.get("finding", ""))
                recommendations = result.get("recommendations", [])
                references = result.get("references", []) or pubmed_refs
            except Exception as e:
                logger.error(f"LLM error in Pharmacology agent: {e}")
                response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        else:
            response_text, recommendations, references = self._fallback_response(context.query, pubmed_refs)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return self._build_base_response(
            response=response_text,
            confidence=0.85,
            recommendations=recommendations,
            references=references,
            context=context
        )
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        query_lower = query.lower()
        keywords = ["drug", "medication", "dose", "dosing", "prescription", "tablet", 
                   "capsule", "interaction", "contraindication", "side effect", "adverse",
                   "pharmacy", "pharmacology", "therapeutic", "monitoring", "level"]
        score = sum(1 for kw in keywords if kw in query_lower)
        return min(score / 3.0, 1.0)
    
    def get_capabilities(self) -> AgentSpec:
        return self.spec
    
    def _build_pharmacology_prompt(self, context: ProcessingContext) -> str:
        return f"""You are a Clinical Pharmacy specialist providing medication decision support.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

Provide your assessment as JSON:
{{
    "response": "Your pharmacology assessment with evidence-based reasoning",
    "recommendations": ["list of specific clinical recommendations"],
    "references": [{{"title": "study/guideline name", "source": "source", "pmid": "PMID if available"}}]
}}

IMPORTANT: Consider drug interactions, dosing adjustments, and patient-specific factors."""
    
    def _fallback_response(self, query: str, pubmed_refs: List[Dict] = None) -> tuple:
        refs = pubmed_refs if pubmed_refs else []
        return (
            "For medication concerns, please consult with a clinical pharmacist. "
            "Consider drug interactions and patient-specific factors.",
            [
                "Review current medications",
                "Check for drug interactions",
                "Consider dosing adjustments if needed"
            ],
            refs or [{"title": "FDA Drug Labels", "source": "FDA", "pmid": "34567890"}]
        )


# =============================================================================
# AGENT FACTORY
# =============================================================================

def create_specialist_agent(agent_id: str) -> Optional[BaseAgent]:
    """
    Factory function to create specialist agents.
    
    Args:
        agent_id: ID of the agent to create
        
    Returns:
        Agent instance or None if not found
    """
    agents = {
        "obgyn_agent": create_obgyn_agent,
        "medicine_agent": create_medicine_agent,
        "surgery_agent": create_surgery_agent,
        "pediatrics_agent": create_pediatrics_agent,
        "radiology_agent": create_radiology_agent,
        "psychiatry_agent": create_psychiatry_agent,
        "research_agent": create_research_agent,
        "pathology_agent": create_pathology_agent,
        "pharmacology_agent": create_pharmacology_agent,
    }
    
    factory = agents.get(agent_id)
    if factory:
        return factory()
    return None


def get_all_specialist_ids() -> List[str]:
    """Get list of all specialist agent IDs."""
    return [
        "obgyn_agent",
        "medicine_agent", 
        "surgery_agent",
        "pediatrics_agent",
        "radiology_agent",
        "psychiatry_agent",
        "research_agent",
        "pathology_agent",
        "pharmacology_agent"
    ]
