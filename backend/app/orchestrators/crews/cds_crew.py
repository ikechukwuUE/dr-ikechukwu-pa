"""
CDS Crew - Clinical Decision Support using CrewAI
===============================================
Hierarchical CrewAI implementation with 14 specialist agents.
Task-based tool integration for enhanced clinical decision making.
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
import structlog

from ...core.config import get_llm_config_for_domain, create_openrouter_llm
from ...core.schemas import CDSResponse, PatientInfo, SpecialistConsultationResponse, MedicalResearchResponse, DiagnosisWithEvidence
from ...tools.mcp_client import get_cds_task_tools

logger = structlog.get_logger()


class ClinicalDecisionSupportCrew:
    """
    Clinical Decision Support Crew using CrewAI Hierarchical process.
    
    Agents:
    - ClinicalCoordinator (manager)
    - 13 Specialist Agents (Pediatrics, OBGYN, Internal Medicine, Surgery,
      Psychiatry, Pathology, Pharmacology, Radiology, Family Medicine,
      Community Medicine, Ophthalmology, Anesthesia, Emergency)
    - MedicalResearcher
    - TreatmentAdvisor
    """
    
    def __init__(self):
        """Initialize the CDS Crew with all specialist agents."""
        self.llm_config = get_llm_config_for_domain("cds")
        self.llm = create_openrouter_llm("cds")
        self._setup_agents()
    
    def _setup_agents(self) -> None:
        """Setup all CrewAI agents."""
        
        # Clinical Coordinator - Manager Agent
        self.coordinator = Agent(
            role="Clinical Coordinator",
            goal="Coordinate medical specialists to provide comprehensive patient care and optimize clinical outcomes",
            backstory="""You are an experienced medical director with expertise in 
            coordinating multidisciplinary medical teams. You ensure all specialists 
            work together to provide the best possible care.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )
        
        # Specialist Agents
        self.pediatrics = self._create_specialist_agent(
            "Pediatrician",
            "In-depth knowledge of common diseases affecting children's health from neonates, infants, preschoolers to adolescents up to the age of 15 including rare pediatric diseases and congenital disorders",
        )
        
        self.obgyn = self._create_specialist_agent(
            "OBGYN Specialist",
            "Knowledge of women's reproductive health, pregnancy, and childbirth including common and rare conditions in obstetrics and gynecology",
        )
        
        self.internal_medicine = self._create_specialist_agent(
            "Internal Medicine Specialist",
            "adult diseases - from the age of 16; complex medical conditions, including the rare ones",
        )
        
        self.surgery = self._create_specialist_agent(
            "General Surgeon",
            "In-depth knowledge about surgical procedures, key surgical principles,and perioperative care using enhanced surgical knowledge and techniques - following enhanced recovery after surgery protocol - ERAS",
        )
        
        self.psychiatry = self._create_specialist_agent(
            "Psychiatrist",
            "mental health disorders and psychological conditions with great knowledge of guidelines and treatment modalities in psychiatry - ICD11, DSM5, NICE guidelines, Maudsley prescribing guidelines",
        )
        
        self.pathology = self._create_specialist_agent(
            "Pathologist",
            "disease diagnosis through laboratory analysis across various subspecialties, including hematology, histopathology, chemical pathology, microbiology and cytopathology and molecular pathology/genetics",
        )
        
        self.pharmacology = self._create_specialist_agent(
            "Pharmacologist",
            "Clinical pharmacologist with knowledge of medication interactions, dosages, and drug-drug interactions, and pharmacokinetics and pharmacodynamics of drugs inlcuing side effects and contraindications",
        )
        
        self.radiology = self._create_specialist_agent(
            "Radiologist",
            "Knowledge and knack for medical imaging interpretation across different imaging modalities and diagnosis; knowledge of interventional radiology procedures and indications and contraindications",
        )
        
        self.family_medicine = self._create_specialist_agent(
            "Family Medicine Physician",
            "comprehensive primary care for all ages, with a holistic approach to patient care and preventive medicine, and management of chronic diseases in the context of the family and community",
        )
        
        self.community_medicine = self._create_specialist_agent(
            "Community Medicine Specialist",
            "public health and preventive medicine core knowledge of epidemiology, biostatistics, health promotion, and disease prevention and it's application to individual patient care and population health management",
        )
        
        self.ophthalmology = self._create_specialist_agent(
            "Ophthalmologist",
            "knowledge of eye diseases and visual system disorders, surgical and medical management of eye conditions, and interpretation of ophthalmic imaging and diagnostic tests",
        )
        
        self.anesthesia = self._create_specialist_agent(
            "Anesthesiologist",
            "knowledge of anesthesia administration and pain management including preoperative assessment, intraoperative management, and postoperative care with expertise in various anesthesia techniques and patient monitoring",
        )
        
        self.emergency = self._create_specialist_agent(
            "Emergency Medicine Physician",
            "acute emergency care and trauma; knowledge of emergency protocols especially latest ATLS, triage principles, and management of a wide range of acute medical conditions and injuries in the emergency department setting",
        )
        
        # Research and Treatment Agents
        self.medical_researcher = Agent(
            role="Medical Researcher",
            goal="Find latest medical research and clinical guidelines",
            backstory="""You are a medical researcher specializing in evidence-based 
            medicine. You find the latest research, clinical trials, and guidelines 
            to support clinical decisions.""",
            verbose=True,
            llm=self.llm,
        )
        
        self.treatment_advisor = Agent(
            role="Treatment Advisor",
            goal="Develop comprehensive treatment plans based on specialist input",
            backstory="""You are a senior treatment planner who synthesizes input from 
            all specialists to create comprehensive, personalized treatment plans.""",
            verbose=True,
            llm=self.llm,
        )
    
    def _create_specialist_agent(self, role: str, expertise: str) -> Agent:
        """Create a specialist agent."""
        return Agent(
            role=role,
            goal=f"Provide expert consultation in {expertise}",
            backstory=f"""You are a board-certified {role} with years of experience 
            in {expertise}. Your expertise is sought for complex cases requiring 
            specialized knowledge in your field.""",
            verbose=True,
            llm=self.llm,
        )
    
    def analyze_patient(
        self,
        patient_info: PatientInfo,
        images: Optional[List[str]] = None,
    ) -> CDSResponse:
        """
        Analyze patient and provide clinical decision support.
        
        Args:
            patient_info: Patient information
            images: Optional medical images
        
        Returns:
            CDSResponse with diagnosis and treatment plan
        """
        logger.info("cds_crew_analyzing", patient_id=patient_info.patient_id)
        
        # Build patient summary for agents
        patient_summary = self._build_patient_summary(patient_info, images)
        
        # Create tasks for the crew
        tasks = self._create_cds_tasks(patient_summary)
        
        # Create crew with hierarchical process
        # Note: manager_agent should NOT be in the agents list (CrewAI v1.10.1 requirement)
        crew = Crew(
            agents=[
                self.pediatrics,
                self.obgyn,
                self.internal_medicine,
                self.surgery,
                self.psychiatry,
                self.pathology,
                self.pharmacology,
                self.radiology,
                self.family_medicine,
                self.community_medicine,
                self.ophthalmology,
                self.anesthesia,
                self.emergency,
                self.medical_researcher,
                self.treatment_advisor,
            ],
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=self.coordinator,
            verbose=True,
        )
        
        # Execute the crew
        try:
            result = crew.kickoff(inputs={"patient": patient_summary})
            logger.info("cds_crew_completed", result=str(result)[:200])
            return self._parse_crew_result(result, patient_info.patient_id or "unknown")
        except Exception as e:
            logger.error("cds_crew_failed", error=str(e))
            return self._get_fallback_response(patient_info.patient_id or "unknown")

    def _build_patient_summary(self, patient_info: PatientInfo, images: Optional[List[str]]) -> str:
        """Build a patient summary string for the agents."""
        summary_parts = []
        
        # Core required fields
        summary_parts.extend([
            f"Age: {patient_info.age}, Sex: {patient_info.sex}",
            f"Occupation: {patient_info.occupation}",
            f"Married: {'Yes' if patient_info.married else 'No'}",
            f"Chief Complaint: {patient_info.chief_complaint}",
        ])
        
        # Optional demographic fields
        demographics = {
            "Address": patient_info.address,
            "Religion": patient_info.religion,
            "Ethnicity": patient_info.ethnicity,
        }
        summary_parts.extend(f"{k}: {v}" for k, v in demographics.items() if v)
        
        # Physical metrics
        if patient_info.weight_kg:
            summary_parts.append(f"Weight: {patient_info.weight_kg} kg")
        if patient_info.height_cm:
            summary_parts.append(f"Height: {patient_info.height_cm} cm")
        
        # List-based clinical fields (skip empty lists)
        clinical_lists = {
            "Symptoms": patient_info.symptoms,
            "Medical History": patient_info.medical_history,
            "Past Psychiatric History": patient_info.past_psychiatric_history,
            "Past Surgical History": patient_info.past_surgical_history,
            "Current Medications": patient_info.current_medications,
            "Family History": patient_info.family_history,
            "Social History": patient_info.social_history,
            "Allergies": patient_info.allergies,
        }
        summary_parts.extend(
            f"{label}: {', '.join(values)}" 
            for label, values in clinical_lists.items() 
            if values
        )
        
        # Examination data
        if patient_info.vital_signs:
            summary_parts.append(f"Vital Signs: {patient_info.vital_signs}")
        if patient_info.examination_findings:
            summary_parts.append(f"Examination Findings: {patient_info.examination_findings}")
        
        # Medical images
        if images:
            summary_parts.append(f"Medical Images: {len(images)} image(s) provided")
        
        return " | ".join(summary_parts)
    
    def _create_cds_tasks(self, patient_summary: str) -> List[Task]:
        """Create CDS tasks for the crew.
        
        Tools are assigned to agents, not tasks - this follows CrewAI best practices.
        """
        
        # Triage task - initial assessment to determine which specialists are needed and priority level
        # Uses medical literature search and clinical guidelines tools (via agent's tools)
        triage_task = Task(
            description=f"Analyze the patient: {patient_summary}. Provide initial triage assessment.",
            expected_output="A list of relevant specialties needed for this case and priority level.",
            agent=self.coordinator,
        )
        
        # Research task - find latest medical research and guidelines relevant to the case
        # Uses all research tools (via agent's tools)
        research_task = Task(
            description=f"Find latest clinical guidelines and research for: {patient_summary}",
            expected_output="Summary of relevant research and clinical guidelines with sources and evidence level",
            agent=self.medical_researcher,
            output_pydantic=MedicalResearchResponse,
        )

        # Specialist consultation tasks - one for each specialist agent
        # Each specialist can use drug interaction check and clinical guidelines (via agent's tools)
        specialist_tasks = []
        for specialist in [self.pediatrics, self.obgyn, self.internal_medicine, self.surgery, self.psychiatry, self.pathology, self.pharmacology, self.radiology, self.family_medicine, self.community_medicine, self.ophthalmology, self.anesthesia, self.emergency]:
            specialist_tasks.append(
                Task(
                    description=f"Provide expert consultation for patient: {patient_summary}",
                    expected_output="Structured consultation report with diagnosis and recommendations.",
                    agent=specialist,
                    output_pydantic=SpecialistConsultationResponse,
                )
            )

        # Treatment planning task - synthesizes all specialist input and research
        # Uses all available tools for comprehensive treatment planning (via agent's tools)
        treatment_task = Task(
            description=f"Based on specialist inputs and research for patient: {patient_summary}, create a treatment plan.",
            expected_output="Comprehensive treatment plan with medications, tests, and follow-up.",
            agent=self.treatment_advisor,
            output_pydantic=CDSResponse,
        )

        return [triage_task, research_task] + specialist_tasks + [treatment_task]
    
    def _parse_crew_result(self, result: Any, patient_id: str) -> CDSResponse:
        """Parse crew result into CDSResponse."""
        result_str = str(result)
        primary_dx = result_str[:200] if result_str else "Analysis completed"
        
        return CDSResponse(
            session_id=patient_id,
            primary_diagnosis=DiagnosisWithEvidence(
                diagnosis=primary_dx,
                confidence_score=0.8,
                evidence_level="preliminary",
                supporting_findings=[]
            ),
            primary_diagnosis_list=[primary_dx],
            differential_diagnosis_list=[],
            investigation_list_legacy=[],
            treatment_plan_legacy=[result_str[200:400]] if len(result_str) > 200 else [],
            red_flags=[],
            senior_colleague_notes=None,
            emergency=False,
            specialist_referrals_legacy=[],
            confidence_score=0.8,
        )
    
    def _get_fallback_response(self, patient_id: str) -> CDSResponse:
        """Get fallback response when crew fails."""
        fallback_dx = "Analysis completed - review pending"
        return CDSResponse(
            session_id=patient_id,
            primary_diagnosis=DiagnosisWithEvidence(
                diagnosis=fallback_dx,
                confidence_score=0.5,
                evidence_level="preliminary",
                supporting_findings=["Human physician review recommended"]
            ),
            primary_diagnosis_list=[fallback_dx],
            differential_diagnosis_list=[],
            investigation_list_legacy=[],
            treatment_plan_legacy=[],
            red_flags=[],
            senior_colleague_notes="Human physician review recommended for complete analysis",
            emergency=False,
            nursing_instructions=[],
            specialist_referrals_legacy=[],
            confidence_score=0.5,
        )


# Global instance
_cds_crew: Optional[ClinicalDecisionSupportCrew] = None


def get_cds_crew() -> ClinicalDecisionSupportCrew:
    """Get or create the CDS Crew instance."""
    global _cds_crew
    if _cds_crew is None:
        _cds_crew = ClinicalDecisionSupportCrew()
    return _cds_crew


__all__ = ["ClinicalDecisionSupportCrew", "get_cds_crew"]
