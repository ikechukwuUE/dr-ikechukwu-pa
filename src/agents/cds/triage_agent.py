"""
Triage Agent for Clinical Decision Support
==========================================
Analyzes clinical queries and determines which specialist(s) should handle the case.

Key Features:
- Uses LLM to analyze clinical queries
- Multi-specialty detection for complex cases
- Returns routing decision with confidence score
- Supports emergency detection

Extends:
- BaseAgent: Abstract base class for all CDS agents
"""

from typing import Dict, List, Any, Optional, Literal
import logging
import time
import json
import re

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

logger = logging.getLogger(__name__)


# =============================================================================
# TRIAGE CAPABILITIES
# =============================================================================

TRIAGE_CAPABILITIES: List[AgentCapability] = [
    {
        "name": "clinical_routing",
        "description": "Analyze clinical queries and determine appropriate specialist",
        "keywords": ["routing", "triage", "specialist", "referral", "which doctor"],
        "can_handle_emergency": True
    },
    {
        "name": "multi_specialty_detection",
        "description": "Identify cases requiring multiple specialists",
        "keywords": ["complex", "multiple", "combined", "multidisciplinary"],
        "can_handle_emergency": True
    },
    {
        "name": "emergency_detection",
        "description": "Detect urgent and emergency cases",
        "keywords": ["emergency", "urgent", "critical", "immediate", "life-threatening"],
        "can_handle_emergency": True
    },
    {
        "name": "general_assessment",
        "description": "Provide initial general clinical assessment",
        "keywords": ["symptoms", "diagnosis", "treatment", "advice"],
        "can_handle_emergency": False
    }
]


# =============================================================================
# SPECIALTY MAPPING
# =============================================================================

SPECIALTY_KEYWORDS = {
    "obgyn_agent": [
        "pregnancy", "prenatal", "postnatal", "childbirth", "labor", "delivery",
        "gynecology", "gynecological", "menstrual", "menopause", "fertility",
        "infertility", "ivf", "contraception", "contraceptive", "abortion",
        "miscarriage", "uterus", "ovary", "cervical", "vaginal", "breast",
        "obstetric", "ob", "maternal", "fetal", "胎", "pregnant", "conception",
        "reproductive", "birth", "antenatal", "natal", "postpartum", "lactation"
    ],
    "medicine_agent": [
        "internal medicine", "cardiology", "heart", "cardiovascular", "neurology",
        "brain", "gastroenterology", "gi", "digestive", "respiratory", "lung",
        "pulmonary", "diabetes", "endocrinology", "thyroid", "kidney", "renal",
        "hypertension", "blood pressure", "arrhythmia", "stroke", "seizure",
        "migraine", "headache", "fatigue", "fever", "infection", "viral",
        "bacterial", "immune", "rheumatology", "arthritis", "lupus", "hiv",
        "aids", "tuberculosis", "malaria", "typhoid", "cholera", "diarrhea",
        "vomiting", "nausea", "abdominal pain", "chest pain", "shortness of breath"
    ],
    "surgery_agent": [
        "surgery", "surgical", "operation", "pre-operative", "preop", "post-operative",
        "postop", "pre-surgery", "post-surgery", "appendectomy", "cholecystectomy",
        "hernia", "laparoscopic", "open surgery", "incision", "wound", "trauma",
        "fracture", "orthopedic", "orthopaedic", "bone", "joint", "tendon",
        "ligament", "plastic", "reconstructive", "cosmetic", "vascular",
        "thoracic", "abdominal surgery", "bowel", "intestinal"
    ],
    "pediatrics_agent": [
        "pediatric", "paediatric", "child", "children", "infant", "neonatal",
        "newborn", "baby", "toddler", "adolescent", "teenager", "youth",
        "developmental", "growth", "vaccination", "immunization", "vaccine",
        "pediatric", "childhood", "congenital", "birth defect", "genetic",
        "syndrome", "autism", "adhd", "developmental delay", "pediatrics"
    ],
    "radiology_agent": [
        "x-ray", "xray", "ct", "cat scan", "mri", "ultrasound", "sonography",
        "imaging", "radiograph", "radiology", "scan", "mammogram", "mammography",
        "pet scan", "nuclear medicine", "angiography", "fluoroscopy",
        "interventional", "contrast", "findings", "interpretation", "report"
    ],
    "psychiatry_agent": [
        "psychiatry", "psychological", "mental", "depression", "anxiety", "stress",
        "mental health", "psychosis", "schizophrenia", "bipolar", "personality",
        "disorder", "trauma", "ptsd", "ptsd", " OCD", "panic", "phobia",
        "suicide", "self-harm", "addiction", "substance", "alcohol", "drug",
        "therapy", "counseling", "counselling", "psychotherapy", "medication",
        "antidepressant", "antipsychotic", "mood", "behavior", "behaviour"
    ],
    "research_agent": [
        "research", "study", "evidence", "guidelines", "protocol", "literature",
        "pubmed", "clinical trial", "systematic review", "meta-analysis",
        "journal", "article", "paper", "publication", "reference", "citation",
        "treatment guidelines", "clinical practice", "standard of care",
        "evidence-based", "review", "synthesis"
    ]
}


# =============================================================================
# EMERGENCY PATTERNS
# =============================================================================

EMERGENCY_PATTERNS = [
    r"\b(emergency|urgent|critical|life-threatening|immediate)\b",
    r"\b(chest pain|heart attack|myocardial infarction)\b",
    r"\b(stroke| cerebrovascular accident|cva)\b",
    r"\b(severe bleeding|hemorrhage)\b",
    r"\b(difficulty breathing|respiratory distress|suffocation)\b",
    r"\b(unconscious|unresponsive|coma)\b",
    r"\b(suicide|self-harm|overdose)\b",
    r"\b(seizure|convulsion)\b",
    r"\b(severe burns|shock)\b",
    r"\b(acute abdomen|peritonitis)\b"
]


# =============================================================================
# TRIAGE AGENT CLASS
# =============================================================================

class TriageAgent(BaseAgent):
    """
    Triage Agent for Clinical Decision Support.
    
    Analyzes clinical queries and determines:
    - Which specialist(s) should handle the case
    - Whether it's an emergency/urgent case
    - Confidence score for routing
    
    Extends:
        BaseAgent: Abstract base class for all CDS agents
    """
    
    def __init__(self, spec: Optional[AgentSpec] = None):
        """
        Initialize the Triage Agent.
        
        Args:
            spec: Agent specification (created default if not provided)
        """
        if spec is None:
            spec = create_agent_spec(
                agent_id="triage_agent",
                name="Triage Agent",
                specialty="Clinical Routing & Triage",
                capabilities=TRIAGE_CAPABILITIES,
                expertise_depth=ExpertiseLevel.SPECIALIST,
                can_handoff_to=["obgyn_agent", "medicine_agent", "surgery_agent", 
                               "pediatrics_agent", "radiology_agent", "psychiatry_agent", 
                               "research_agent"],
                description="Analyzes clinical queries and routes to appropriate specialists"
            )
        super().__init__(spec)
        self._emergency_patterns = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
        self._llm = None  # type: ignore
    
    def process(self, context: ProcessingContext) -> AgentResponse:
        """
        Process a clinical query and determine routing.
        
        Args:
            context: Processing context with query
            
        Returns:
            AgentResponse with routing decision
        """
        start_time = time.time()
        
        query_lower = context.query.lower()
        
        # Step 1: Check for emergency
        is_emergency, emergency_reason = self._detect_emergency(query_lower)
        if is_emergency:
            response_text = (
                f"EMERGENCY DETECTED: {emergency_reason}\n\n"
                "This appears to be an urgent/emergency case. "
                "Please seek immediate medical attention at the nearest emergency department "
                "or call emergency services.\n\n"
                f"For general guidance: {context.query}"
            )
            
            return self._build_base_response(
                response=response_text,
                confidence=0.95,
                recommendations=[
                    "Seek immediate emergency care",
                    "Call emergency services",
                    "Do not delay treatment"
                ],
                references=self._get_emergency_references(),
                context=context
            )
        
        # Step 2: Analyze query and detect specialties
        detected_specialties = self._detect_specialties(query_lower)
        
        # Step 3: Use LLM for complex analysis
        if self._llm is not None:
            routing_result = self._llm_triage_analysis(context, detected_specialties)
        else:
            routing_result = self._keyword_based_triage(query_lower, detected_specialties)
        
        # Step 4: Build response
        processing_time = int((time.time() - start_time) * 1000)
        
        response = AgentResponse(
            response=routing_result["response"],
            confidence=routing_result["confidence"],
            recommendations=routing_result["recommendations"],
            references=routing_result.get("references", []),
            handoff_candidates=routing_result["routed_agents"],
            agent_id=self.agent_id,
            agent_name=self.name,
            processing_time_ms=processing_time,
            trace_id=context.trace_id,
            metadata={
                "specialty": self.specialty,
                "expertise_depth": self.expertise_depth.value,
                "detected_specialties": detected_specialties,
                "is_emergency": is_emergency,
                "routing_method": "llm" if self._llm else "keyword"
            }
        )
        
        return response
    
    def can_handle(self, query: str, context: Optional[ProcessingContext] = None) -> float:
        """
        Determine if this agent can handle the query.
        
        Triage agent can always handle initial routing queries.
        
        Args:
            query: Clinical query
            context: Optional processing context
            
        Returns:
            1.0 (always can handle triage)
        """
        return 1.0
    
    def get_capabilities(self) -> AgentSpec:
        """
        Return the agent's capabilities specification.
        
        Returns:
            Complete AgentSpec
        """
        return self.spec
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    def _detect_emergency(self, query: str) -> tuple[bool, str]:
        """
        Detect if query describes an emergency.
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (is_emergency, reason)
        """
        for pattern in self._emergency_patterns:
            match = pattern.search(query)
            if match:
                return True, match.group(0)
        return False, ""
    
    def _detect_specialties(self, query: str) -> List[tuple[str, float]]:
        """
        Detect which specialties match the query using keyword matching.
        
        Args:
            query: Lowercase query string
            
        Returns:
            List of (agent_id, confidence) tuples sorted by confidence
        """
        matches = []
        
        for agent_id, keywords in SPECIALTY_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in query:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Normalize score to 0-1 range
                confidence = min(score / 3.0, 1.0)
                matches.append((agent_id, confidence, matched_keywords))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return [(m[0], m[1]) for m in matches]
    
    def _llm_triage_analysis(
        self, 
        context: ProcessingContext,
        keyword_matches: List[tuple[str, float]]
    ) -> Dict[str, Any]:
        """
        Use LLM for more sophisticated triage analysis.
        
        Args:
            context: Processing context
            keyword_matches: Initial keyword-based matches
            
        Returns:
            Triage analysis results
        """
        # Early return if no LLM available
        if self._llm is None:
            return self._keyword_based_triage(context.query.lower(), keyword_matches)
        
        # Get top keyword matches for context
        top_matches = keyword_matches[:3] if keyword_matches else []
        match_summary = ", ".join([f"{m[0]} ({m[1]:.2f})" for m in top_matches]) or "None"
        
        prompt = f"""You are a clinical triage specialist. Analyze this query and determine 
which medical specialist(s) should handle it.

CLINICAL QUERY:
{context.query}

PATIENT CONTEXT:
{context.patient_context or "None provided"}

KEYWORD-BASED INITIAL MATCHES:
{match_summary}

Provide your analysis as JSON:
{{
    "primary_specialist": "agent_id of best match",
    "confidence": 0.0-1.0,
    "secondary_specialists": ["list of other possible specialists"],
    "reasoning": "brief explanation",
    "recommendations": ["list of recommendations"],
    "is_complex": true/false (true if multiple specialists needed)
}}

Available agents: obgyn_agent, medicine_agent, surgery_agent, pediatrics_agent, 
radiology_agent, psychiatry_agent, research_agent"""

        try:
            response = self._llm.invoke(prompt)
            result = parse_llm_json_response(response.content)
            
            # Extract results
            primary = result.get("primary_specialist", "medicine_agent")
            confidence = result.get("confidence", 0.5)
            
            # Build list of routed agents
            routed_agents = [primary]
            if result.get("is_complex"):
                routed_agents.extend(result.get("secondary_specialists", []))
            
            return {
                "response": result.get("reasoning", f"Routed to {primary}"),
                "confidence": confidence,
                "recommendations": result.get("recommendations", []),
                "references": [],
                "routed_agents": routed_agents[:3]  # Max 3 agents
            }
        except Exception as e:
            logger.error(f"LLM triage analysis failed: {e}")
            # Fall back to keyword-based
            return self._keyword_based_triage(context.query.lower(), keyword_matches)
    
    def _keyword_based_triage(
        self, 
        query: str, 
        keyword_matches: List[tuple[str, float]]
    ) -> Dict[str, Any]:
        """
        Fallback keyword-based triage when LLM is not available.
        
        Args:
            query: Lowercase query string
            keyword_matches: Pre-computed keyword matches
            
        Returns:
            Triage analysis results
        """
        if not keyword_matches:
            # Default to medicine_agent for unknown cases
            return {
                "response": "Query does not match a specific specialty. Defaulting to internal medicine for general assessment.",
                "confidence": 0.3,
                "recommendations": [
                    "Consult with primary care physician",
                    "Provide detailed medical history",
                    "Consider general internal medicine evaluation"
                ],
                "references": [],
                "routed_agents": ["medicine_agent"]
            }
        
        primary, confidence = keyword_matches[0]
        secondaries = [m[0] for m in keyword_matches[1:3]]
        
        # Generate response based on routing
        specialty_names = {
            "obgyn_agent": "Obstetrics & Gynecology",
            "medicine_agent": "Internal Medicine",
            "surgery_agent": "General Surgery",
            "pediatrics_agent": "Pediatrics",
            "radiology_agent": "Radiology",
            "psychiatry_agent": "Psychiatry",
            "research_agent": "Evidence-Based Research"
        }
        
        primary_name = specialty_names.get(primary, primary)
        
        if len(keyword_matches) > 1:
            response = (
                f"This query appears to be primarily related to {primary_name}. "
                f"Confidence: {confidence:.0%}. "
                f"Could also involve: {', '.join([specialty_names.get(s, s) for s in secondaries])}."
            )
            routed_agents = [primary] + secondaries
        else:
            response = (
                f"This query is clearly related to {primary_name}. "
                f"Confidence: {confidence:.0%}."
            )
            routed_agents = [primary]
        
        recommendations = [
            f"Consult with {primary_name} specialist",
            "Provide complete medical history",
            "Note any relevant medications or allergies"
        ]
        
        return {
            "response": response,
            "confidence": confidence,
            "recommendations": recommendations,
            "references": [],
            "routed_agents": routed_agents[:3]
        }
    
    def _get_emergency_references(self) -> List[Dict[str, str]]:
        """
        Get references for emergency cases.
        
        Returns:
            List of reference dictionaries
        """
        return [
            {
                "title": "Emergency Medical Services",
                "source": "Nigeria Emergency Numbers",
                "url": "https://www.ncdc.gov.ng"
            },
            {
                "title": "First Aid Guidelines",
                "source": "Red Cross Nigeria",
                "url": "https://redcrossnigeria.org"
            }
        ]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_triage_agent() -> TriageAgent:
    """
    Create and return a TriageAgent instance.
    
    Returns:
        Configured TriageAgent
    """
    return TriageAgent()
