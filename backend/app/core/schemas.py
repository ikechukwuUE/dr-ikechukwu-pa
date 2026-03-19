"""
Centralized Pydantic Schemas
==========================
All schemas for the four domains (CDS, Finance, AI-Dev, Fashion)
using strict Pydantic V2 paradigms with model_config for extra field restriction.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime
from enum import Enum


# ============================================================================
# SHARED SCHEMAS
# ============================================================================

class DomainEnum(str, Enum):
    """Available application domains."""
    CDS = "cds"
    FINANCE = "finance"
    AIDEV = "aidev"
    FASHION = "fashion"


class ConversationContext(BaseModel):
    """Shared conversation context for memory integration."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="Unique session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    domain: DomainEnum = Field(description="Current domain")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# CLINICAL DECISION SUPPORT (CDS) SCHEMAS
# ============================================================================

class PatientInfo(BaseModel):
    """Patient information for clinical analysis."""
    model_config = ConfigDict(extra="forbid")

    patient_id: Optional[str] = Field(default=None, description="Patient identifier")
    age: int = Field(ge=0, le=150, description="Patient age in years")
    sex: Literal["male", "female", "other"] = Field(description="Patient biological sex")
    occupation: str = Field(description="Patient occupation")
    married: bool = Field(description="Marital status")
    address: Optional[str] = Field(default=None, description="Patient address")
    religion: Optional[str] = Field(default=None, description="Patient religion")
    ethnicity: Optional[str] = Field(default=None, description="Patient ethnicity")
    weight_kg: Optional[float] = Field(default=None, ge=0, description="Weight in kilograms")
    height_cm: Optional[float] = Field(default=None, ge=0, description="Height in centimeters")
    chief_complaint: str = Field(description="Primary complaint")
    symptoms: List[str] = Field(default_factory=list, description="Reported symptoms")
    medical_history: List[str] = Field(default_factory=list, description="Medical history")
    past_psychiatric_history: Optional[List[str]] = Field(default_factory=list, description="Past psychiatric history")
    past_surgical_history: Optional[List[str]] = Field(default_factory=list, description="Past surgical history")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    family_history: List[str] = Field(default_factory=list, description="Family medical history")
    social_history: List[str] = Field(default_factory=list, description="Social history")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    vital_signs: Optional[Dict[str, Any]] = Field(default=None, description="Vital signs")
    examination_findings: Optional[Dict[str, Any]] = Field(default=None, description="Physical examination findings")


# Enhanced CDS Schemas - State of the art

class DiagnosisWithEvidence(BaseModel):
    """Diagnosis with evidence level and confidence."""
    model_config = ConfigDict(extra="forbid")

    diagnosis: str = Field(description="Diagnosis name")
    icd_code: Optional[str] = Field(default=None, description="ICD-10 code")
    confidence_score: float = Field(ge=0, le=1, description="Confidence 0-1")
    evidence_level: Optional[str] = Field(default=None, description="Evidence level")
    supporting_findings: List[str] = Field(default_factory=list)


class MedicationRecommendation(BaseModel):
    """Structured medication recommendation."""
    model_config = ConfigDict(extra="forbid")

    medication: str = Field(description="Medication name")
    dosage: str = Field(description="Dosage and frequency")
    route: Literal["oral", "IV", "IM", "SC", "topical", "inhaled", "sublingual", "rectal"] = Field(default="oral")
    duration: str = Field(description="Treatment duration")
    indication: str = Field(description="Indication")
    contraindications_checked: bool = Field(default=True)
    interactions: List[str] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    monitoring: List[str] = Field(default_factory=list)


class InvestigationRecommendation(BaseModel):
    """Structured investigation recommendation."""
    model_config = ConfigDict(extra="forbid")

    test_name: str = Field(description="Test name")
    category: Literal["laboratory", "imaging", "cardiology", "pathology", "microbiology", "other"] = Field(default="laboratory")
    urgency: Literal["routine", "urgent", "emergent"] = Field(default="routine")
    rationale: str = Field(description="Clinical rationale")


class SpecialistConsultationRequest(BaseModel):
    """Request for specialist consultation."""
    model_config = ConfigDict(extra="forbid")

    specialty: str = Field(description="Medical specialty")
    urgency: Literal["routine", "urgent", "emergent"] = Field(default="routine")
    reason: str = Field(description="Reason for consultation")


class SOAPNotes(BaseModel):
    """Structured SOAP notes."""
    model_config = ConfigDict(extra="forbid")

    subjective: str = Field(default="")
    objective: str = Field(default="")
    assessment: str = Field(default="")
    plan: str = Field(default="")


class FollowUpPlan(BaseModel):
    """Structured follow-up plan."""
    model_config = ConfigDict(extra="forbid")

    timeframe: str = Field(description="Follow-up timeframe")
    reason: str = Field(description="Reason for follow-up")
    warning_signs: List[str] = Field(default_factory=list)


class SpecialistConsultationResponse(BaseModel):
    """Specialist consultation response schema."""
    model_config = ConfigDict(extra="forbid")

    specialty: str = Field(description="Specialist's medical specialty")
    diagnosis: List[str] = Field(description="Diagnostic considerations from specialist perspective")
    recommendations: List[str] = Field(description="Specialist-specific recommendations")
    additional_tests: List[str] = Field(default_factory=list, description="Additional tests or investigations recommended")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or red flags")
    confidence_score: float = Field(ge=0, le=1, description="Confidence level")


class CDSResponse(BaseModel):
    """Clinical Decision Support response schema - Enhanced with structured output."""
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Emergency assessment
    emergency: bool = Field(default=False, description="Whether this is a medical emergency")
    urgency_level: Literal["low", "moderate", "high", "critical"] = Field(default="moderate", description="Overall urgency level")
    immediate_actions: List[str] = Field(default_factory=list, description="Immediate actions required")

    # Primary diagnosis (enhanced)
    primary_diagnosis: DiagnosisWithEvidence = Field(description="Primary diagnosis with evidence")

    # Differential diagnoses
    differential_diagnoses: List[DiagnosisWithEvidence] = Field(default_factory=list, description="Differential diagnoses ranked")

    # Legacy support - kept for backward compatibility
    primary_diagnosis_list: List[str] = Field(default_factory=list)
    differential_diagnosis_list: List[str] = Field(default_factory=list)

    # Investigations
    investigations: List[InvestigationRecommendation] = Field(default_factory=list)
    investigation_list_legacy: List[str] = Field(default_factory=list)

    # Treatment
    treatment_plan: List[MedicationRecommendation] = Field(default_factory=list)
    treatment_plan_legacy: List[str] = Field(default_factory=list)
    non_pharmacological_treatment: List[str] = Field(default_factory=list)

    # Safety
    red_flags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Documentation
    soap_notes: Optional[SOAPNotes] = Field(default=None)

    # Referrals
    specialist_referrals: List[SpecialistConsultationRequest] = Field(default_factory=list)
    specialist_referrals_legacy: List[str] = Field(default_factory=list)

    # Follow-up
    follow_up: Optional[FollowUpPlan] = Field(default=None)

    # Instructions
    patient_instructions: List[str] = Field(default_factory=list)
    nursing_instructions: List[str] = Field(default_factory=list)
    senior_colleague_notes: Optional[str] = Field(default=None)

    # Confidence
    confidence_score: float = Field(ge=0, le=1, description="Overall confidence level")
    limitations: List[str] = Field(default_factory=list)


class EvidenceLevel(str, Enum):
    """
    Evidence hierarchy for medical research (Oxford Levels of Evidence).
    Lower values = stronger evidence = should appear first in results; we want to include clinical guidelines and meta-analyses of RCTs at the top of the results, followed by RCTs, then observational studies, then expert opinion."""

    CLINICAL_GUIDELINES = "clinical_guidelines"  # Authoritative clinical guidelines
    META_ANALYSIS = "meta_analysis"  # Systematic review of RCTs
    RCT = "rct"                        # Randomized controlled trial
    CONTROLLED_TRIAL = "controlled_trial"  # Controlled clinical trial
    COHORT = "cohort"                  # Cohort study
    CASE_CONTROL = "case_control"    # Case-control study
    CASE_SERIES = "case_series"       # Case series
    CASE_REPORT = "case_report"       # Single case report
    EXPERT_OPINION = "expert_opinion" # Expert opinion/committee report
    PRECLINICAL = "preclinical"       # Animal/in vitro studies
    UNKNOWN = "unknown"               # Unclassified evidence


class MedicalResearchRequest(BaseModel):
    """Medical research query schema."""
    model_config = ConfigDict(extra="forbid")
    
    query: str = Field(description="Research question")
    include_clinical_trials: bool = Field(default=False)
    max_results: int = Field(default=5, ge=1, le=20)
    sort_by_evidence: bool = Field(
        default=True,
        description="Sort results by evidence level (RCTs/meta-analyses first)"
    )
    min_evidence_level: Optional[EvidenceLevel] = Field(
        default=None,
        description="Minimum evidence level to include in results"
    )


class MedicalResearchResponse(BaseModel):
    """Medical research and clinical guidelines response schema."""
    model_config = ConfigDict(extra="forbid")
    
    sources: List[Dict[str, Any]] = Field(description="Research sources with evidence_level")
    summary: str = Field(description="Research summary")
    clinical_relevance: str = Field(description="Clinical relevance assessment")
    evidence_summary: Optional[Dict[str, int]] = Field(
        default=None,
        description="Count of sources by evidence level"
    )
    


# ============================================================================
# FINANCE SCHEMAS
# ============================================================================

class FinancialQuery(BaseModel):
    """Financial analysis query schema."""
    model_config = ConfigDict(extra="forbid")

    query_type: Literal["investment", "budget", "tax", "retirement", "debt", "general"] = Field(
        description="Type of financial query"
    )
    question: str = Field(description="User's financial question")
    financial_goals: List[str] = Field(default_factory=list, description="Financial goals")
    capital_available: Optional[float] = Field(default=None, ge=0, description="Capital available for investment")
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = Field(
        default="moderate",
        description="Risk tolerance level"
    )
    time_horizon_years: Optional[int] = Field(default=None, ge=1, description="Investment time horizon")


class RiskMetrics(BaseModel):
    """Risk metrics for financial analysis."""
    model_config = ConfigDict(extra="forbid")

    volatility: Literal["low", "medium", "high"] = Field(description="Portfolio volatility level")
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio (risk-adjusted return)")
    max_drawdown: Optional[float] = Field(default=None, description="Maximum drawdown percentage")
    beta: Optional[float] = Field(default=None, description="Portfolio beta relative to market")
    value_at_risk_95: Optional[float] = Field(default=None, description="Value at Risk at 95% confidence")
    risk_score: float = Field(ge=0, le=100, description="Overall risk score 0-100")


class AssetAllocation(BaseModel):
    """Target asset allocation recommendation."""
    model_config = ConfigDict(extra="forbid")

    asset_class: str = Field(description="Asset class name (e.g., stocks, bonds, cash)")
    percentage: float = Field(ge=0, le=100, description="Percentage of portfolio")
    amount: Optional[float] = Field(default=None, description="Dollar amount if applicable")
    rationale: str = Field(description="Reason for this allocation")


class InvestmentRecommendation(BaseModel):
    """Individual investment recommendation."""
    model_config = ConfigDict(extra="forbid")

    asset: str = Field(description="Asset name or ticker symbol")
    action: Literal["buy", "sell", "hold", "increase", "decrease"] = Field(description="Recommended action")
    allocation_percentage: float = Field(ge=0, le=100, description="Recommended allocation percentage")
    rationale: str = Field(description="Reason for recommendation")
    timeframe: str = Field(description="Investment timeframe (short/medium/long term)")
    risk_level: Literal["low", "moderate", "high"] = Field(description="Risk level of this investment")
    expected_return: Optional[str] = Field(default=None, description="Expected return range")


class RiskAssessmentResponse(BaseModel):
    """Structured risk assessment response."""
    model_config = ConfigDict(extra="forbid")

    overall_risk_level: Literal["low", "moderate", "high", "very_high"] = Field(description="Overall portfolio risk level")
    risk_metrics: RiskMetrics = Field(description="Quantitative risk metrics")
    identified_risks: List[str] = Field(description="Key risks identified")
    mitigation_strategies: List[str] = Field(description="Strategies to mitigate identified risks")
    risk_score_change: Optional[str] = Field(default=None, description="Change from previous assessment")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in risk assessment")


class FinanceResponse(BaseModel):
    """Finance response schema."""
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    analysis: str = Field(description="Financial analysis summary")
    recommendations: List[str] = Field(description="Financial recommendations")
    investment_recommendations: List[InvestmentRecommendation] = Field(default_factory=list, description="Detailed investment recommendations")
    target_allocation: List[AssetAllocation] = Field(default_factory=list, description="Target asset allocation")
    risk_assessment: RiskAssessmentResponse = Field(description="Detailed risk assessment")
    action_items: List[str] = Field(description="Action items for user")
    confidence_score: float = Field(ge=0, le=1, description="Confidence level")
    next_review_date: Optional[str] = Field(default=None, description="Recommended next review date")


class InvestmentPortfolio(BaseModel):
    """Investment portfolio schema."""
    model_config = ConfigDict(extra="forbid")
    
    stocks: Dict[str, float] = Field(default_factory=dict, description="Stock holdings by symbol")
    bonds: Dict[str, float] = Field(default_factory=dict, description="Bond holdings")
    etfs: Dict[str, float] = Field(default_factory=dict, description="ETF holdings")
    cash: float = Field(default=0.0, description="Cash holdings")
    crypto: Dict[str, float] = Field(default_factory=dict, description="Cryptocurrency holdings")


class PortfolioAnalysis(BaseModel):
    """Portfolio analysis response."""
    model_config = ConfigDict(extra="forbid")

    total_value: float = Field(description="Total portfolio value")
    asset_allocation: Dict[str, float] = Field(description="Asset allocation percentages")
    risk_metrics: Dict[str, Any] = Field(description="Risk metrics")
    suggestions: List[str] = Field(description="Portfolio improvement suggestions")


class HumanApproval(BaseModel):
    """Human approval and feedback for AI recommendations."""
    model_config = ConfigDict(extra="forbid")

    approved: bool = Field(description="Whether the user approves the recommendation")
    feedback: Optional[str] = Field(default=None, description="User feedback or modifications requested")
    modifications: Optional[List[str]] = Field(default=None, description="Specific modifications requested")
    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# AI-DEV SCHEMAS
# ============================================================================

class CodeGenerationRequest(BaseModel):
    """Code generation request schema."""
    model_config = ConfigDict(extra="forbid")
    
    language: str = Field(description="Programming language")
    task_description: str = Field(description="Task to accomplish")
    constraints: List[str] = Field(default_factory=list, description="Code constraints")
    test_cases: Optional[List[str]] = Field(default=None, description="Test cases to pass")
    framework: Optional[str] = Field(default=None, description="Framework to use")


class CodeGenerationResponse(BaseModel):
    """Code generation response schema."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    generated_code: str = Field(description="Generated code")
    explanation: str = Field(description="Code explanation")
    file_name: str = Field(description="Suggested file name")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    test_code: Optional[str] = Field(default=None, description="Test code")


class CodeDebugRequest(BaseModel):
    """Code debugging request schema."""
    model_config = ConfigDict(extra="forbid")
    
    code: str = Field(description="Code to debug")
    error_message: Optional[str] = Field(default=None, description="Error message if available")
    language: str = Field(description="Programming language")
    context: Optional[str] = Field(default=None, description="Additional context")


class CodeDebugResponse(BaseModel):
    """Code debugging response schema."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    issues_found: List[Dict[str, Any]] = Field(description="Issues identified")
    fixed_code: str = Field(description="Fixed code")
    explanation: str = Field(description="Explanation of fixes")


# ============================================================================
# FASHION SCHEMAS
# ============================================================================

class FashionQuery(BaseModel):
    """Fashion analysis query schema."""
    model_config = ConfigDict(extra="forbid")
    
    query_type: Literal["style", "trend", "outfit", "accessory", "general"] = Field(
        description="Type of fashion query"
    )
    question: str = Field(description="User's fashion question")
    occasion: Optional[str] = Field(default=None, description="Occasion (formal, casual, etc.)")
    season: Optional[str] = Field(default=None, description="Season")
    body_type: Optional[str] = Field(default=None, description="Body type description")
    personal_style: Optional[List[str]] = Field(default=None, description="Personal style preferences")


class FashionImageAnalysis(BaseModel):
    """Fashion image analysis schema."""
    model_config = ConfigDict(extra="forbid")
    
    image_data: str = Field(description="Base64 encoded image")
    analysis_type: List[Literal["style", "color", "trend", "occasion"]] = Field(
        default_factory=lambda: ["style"],
        description="Types of analysis to perform"
    )


class FashionResponse(BaseModel):
    """Fashion response schema."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    analysis: str = Field(description="Fashion analysis")
    recommendations: List[str] = Field(description="Fashion recommendations")
    style_tips: List[str] = Field(description="Style tips")
    confidence_score: float = Field(ge=0, le=1, description="Confidence level")


class OutfitRecommendation(BaseModel):
    """Outfit recommendation schema."""
    model_config = ConfigDict(extra="forbid")
    
    occasion: str = Field(description="Occasion for outfit")
    weather: Optional[str] = Field(default=None, description="Weather conditions")
    colors: List[str] = Field(description="Recommended colors")
    items: List[Dict[str, str]] = Field(description="Clothing items with descriptions")
    accessories: List[str] = Field(default_factory=list, description="Recommended accessories")


# ============================================================================
# API RESPONSE SCHEMAS
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    model_config = ConfigDict(extra="forbid")
    
    success: bool = Field(description="Whether request succeeded")
    message: str = Field(description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(extra="forbid")
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(description="Service health status")


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserLogin(BaseModel):
    """User login schema."""
    model_config = ConfigDict(extra="forbid")
    
    email: EmailStr = Field(description="User email")
    password: str = Field(min_length=8, description="User password")


class UserCreate(BaseModel):
    """User registration schema."""
    model_config = ConfigDict(extra="forbid")
    
    email: EmailStr = Field(description="User email")
    password: str = Field(min_length=8, description="User password")
    full_name: str = Field(description="User full name")
    role: Literal["user", "admin"] = Field(default="user", description="User role")


class TokenResponse(BaseModel):
    """JWT token response."""
    model_config = ConfigDict(extra="forbid")
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration in seconds")


# Export all schemas
__all__ = [
    # Shared
    "DomainEnum",
    "ConversationContext",
    "APIResponse",
    "HealthCheckResponse",
    "UserLogin",
    "UserCreate",
    "TokenResponse",
    # CDS
    "PatientInfo",
    "SpecialistConsultationResponse",
    "CDSResponse",
    "MedicalResearchRequest",
    "MedicalResearchResponse",
    "DiagnosisWithEvidence",
    "MedicationRecommendation",
    "InvestigationRecommendation",
    "SpecialistConsultationRequest",
    "SOAPNotes",
    "FollowUpPlan",
    # Finance
    "FinancialQuery",
    "FinanceResponse",
    "InvestmentPortfolio",
    "PortfolioAnalysis",
    "HumanApproval",
    "RiskMetrics",
    "AssetAllocation",
    "InvestmentRecommendation",
    "RiskAssessmentResponse",
    # AI-Dev
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    "CodeDebugRequest",
    "CodeDebugResponse",
    # Fashion
    "FashionQuery",
    "FashionImageAnalysis",
    "FashionResponse",
    "OutfitRecommendation",
]
