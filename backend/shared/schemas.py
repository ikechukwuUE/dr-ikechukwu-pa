"""
Unified Pydantic Schemas
=======================
Consolidated schemas for Vogue Space - Dr. Ikechukwu's Personal Assistant.
Merged from core/schemas.py and shared/schemas.py using modern Pydantic V2 best practices.

All inter-agent payloads defined in ARCHITECTURE.md.
Using strict Pydantic V2 paradigms with ConfigDict for extra field restriction.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime, timezone
from enum import Enum


def _utc_now() -> datetime:
    """Get current UTC time (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


# ============================================================================
# ENUMS
# ============================================================================

class DomainEnum(str, Enum):
    """Available application domains."""
    MEDICINE = "medicine"
    FINANCE = "finance"
    CODING = "coding"
    FASHION = "fashion"


class Urgency(str, Enum):
    """Urgency levels for medical triage."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class RiskLevel(str, Enum):
    """Risk levels for financial assessments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# SHARED / COMMON SCHEMAS
# ============================================================================

class ConversationContext(BaseModel):
    """Shared conversation context for memory integration."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str = Field(description="Unique session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    domain: DomainEnum = Field(description="Current domain")
    created_at: datetime = Field(default_factory=_utc_now)


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
    timestamp: datetime = Field(default_factory=_utc_now)
    services: Dict[str, str] = Field(description="Service health status")


class HumanApproval(BaseModel):
    """Human approval for AI recommendations (CDS pipeline gate)."""
    model_config = ConfigDict(extra="forbid")
    
    approved: bool = Field(description="Whether the user approves the recommendation")
    feedback: Optional[str] = Field(default=None, description="User feedback")
    modifications: Optional[List[str]] = Field(default=None, description="Specific modifications requested")
    session_id: str = Field(description="Session identifier")


# ============================================================================
# MEDICINE / CDS SCHEMAS
# ============================================================================

class UserQuery(BaseModel):
    """User query schema for medicine domain."""
    model_config = ConfigDict(extra="forbid")
    
    text: str = Field(description="Query text")
    domain: str = Field(default="medicine", description="Domain identifier")


class TriageNote(BaseModel):
    """Triage note with urgency assessment."""
    model_config = ConfigDict(extra="forbid")
    
    query: str = Field(description="Original query")
    urgency: Urgency = Field(description="Urgency level")
    suggested_specialty: str = Field(description="Suggested medical specialty")
    triage_summary: str = Field(description="Triage summary")


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


class SpecialistResponse(BaseModel):
    """Specialist consultation response."""
    model_config = ConfigDict(extra="forbid")
    
    assessment: str = Field(description="Clinical assessment")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    specialist_type: str = Field(description="Specialist type")


class SpecialistConsultationResponse(BaseModel):
    """Specialist consultation response schema."""
    model_config = ConfigDict(extra="forbid")

    specialty: str = Field(description="Specialist's medical specialty")
    diagnosis: List[str] = Field(description="Diagnostic considerations from specialist perspective")
    recommendations: List[str] = Field(description="Specialist-specific recommendations")
    additional_tests: List[str] = Field(default_factory=list, description="Additional tests or investigations recommended")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or red flags")
    confidence_score: float = Field(ge=0, le=1, description="Confidence level")


class PatientInfo(BaseModel):
    """Patient information for clinical analysis."""
    model_config = ConfigDict(extra="forbid")
    
    history: str = Field(description="Patient history")
    examination: str = Field(description="Physical examination")
    investigations: Dict[str, Any] = Field(default_factory=dict, description="Investigations")


class ManagementPlan(BaseModel):
    """Clinical management plan."""
    model_config = ConfigDict(extra="forbid")
    
    evidence_based_guidelines: List[str] = Field(default_factory=list, description="Evidence-based guidelines")
    personalized_plan: str = Field(description="Personalized plan")
    follow_up: Optional[str] = Field(default=None, description="Follow-up instructions")


class CDSResponse(BaseModel):
    """Clinical Decision Support response schema."""
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(description="Session identifier")
    timestamp: datetime = Field(default_factory=_utc_now)

    emergency: bool = Field(default=False, description="Whether this is a medical emergency")
    urgency_level: Literal["low", "moderate", "high", "critical"] = Field(default="moderate")
    immediate_actions: List[str] = Field(default_factory=list)

    primary_diagnosis: DiagnosisWithEvidence = Field(description="Primary diagnosis with evidence")
    differential_diagnoses: List[DiagnosisWithEvidence] = Field(default_factory=list)

    investigations: List[InvestigationRecommendation] = Field(default_factory=list)
    treatment_plan: List[MedicationRecommendation] = Field(default_factory=list)
    non_pharmacological_treatment: List[str] = Field(default_factory=list)

    red_flags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    soap_notes: Optional[SOAPNotes] = Field(default=None)
    specialist_referrals: List[SpecialistConsultationRequest] = Field(default_factory=list)
    follow_up: Optional[FollowUpPlan] = Field(default=None)

    patient_instructions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)


class ResearchQuestion(BaseModel):
    """Medical research question."""
    model_config = ConfigDict(extra="forbid")
    
    question: str = Field(description="Research question")
    scope: Literal["broad", "narrow", "systematic"] = Field(default="broad")


class ResearchManuscript(BaseModel):
    """Research manuscript output."""
    model_config = ConfigDict(extra="forbid")
    
    title: str = Field(description="Manuscript title")
    abstract: str = Field(description="Abstract")
    sections: Dict[str, str] = Field(default_factory=dict)
    references: List[str] = Field(default_factory=list)


class MedicalNewsReport(BaseModel):
    """Medical news report."""
    model_config = ConfigDict(extra="forbid")
    
    headlines: List[str] = Field(default_factory=list)
    summary: str = Field(description="News summary")
    sources: List[str] = Field(default_factory=list)


class MedicalResearchRequest(BaseModel):
    """Medical research request."""
    model_config = ConfigDict(extra="forbid")
    
    question: str = Field(description="Research question")
    scope: Literal["broad", "narrow", "systematic"] = Field(default="broad")
    session_id: str = Field(description="Session identifier")


class MedicalResearchResponse(BaseModel):
    """Medical research response."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    title: str
    abstract: str
    sections: Dict[str, str]
    references: List[str]
    confidence_score: float = Field(ge=0, le=1)


# ============================================================================
# FINANCE SCHEMAS
# ============================================================================

class InvestorInfo(BaseModel):
    """Investor information for financial planning."""
    model_config = ConfigDict(extra="forbid")
    
    age: int = Field(ge=18, le=100)
    salary: float = Field(ge=0)
    occupation: str
    target_fund: float = Field(ge=0)


class InvestmentRecommendation(BaseModel):
    """Investment recommendation with allocation."""
    model_config = ConfigDict(extra="forbid")
    
    persona: Literal["aggressive", "conservative"]
    allocations: Dict[str, float] = Field(default_factory=dict)
    rationale: str


class RiskAssessment(BaseModel):
    """Risk assessment with iteration tracking."""
    model_config = ConfigDict(extra="forbid")
    
    risk_level: RiskLevel
    findings: List[str] = Field(default_factory=list)
    iteration: int = Field(ge=0, le=3)
    resolved: bool = Field(default=False)


class InvestmentGuide(BaseModel):
    """Investment guide with strategy."""
    model_config = ConfigDict(extra="forbid")
    
    strategy: str
    allocations: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class InvestmentPlan(BaseModel):
    """Complete investment plan."""
    model_config = ConfigDict(extra="forbid")
    
    summary: str
    guide: InvestmentGuide
    risk_history: List[RiskAssessment] = Field(default_factory=list)


class FinancialNewsReport(BaseModel):
    """Financial news report."""
    model_config = ConfigDict(extra="forbid")
    
    headlines: List[str] = Field(default_factory=list)
    top_businesses: List[str] = Field(default_factory=list)
    industry_trends: str = ""
    lifestyle_highlights: str = ""


class FinancialQuery(BaseModel):
    """Financial query schema."""
    model_config = ConfigDict(extra="forbid")
    
    query: str = Field(description="User's financial question")
    context: Optional[Dict[str, Any]] = Field(default=None)


class FinanceResponse(BaseModel):
    """Finance response schema."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    response: str
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)


class InvestmentPortfolio(BaseModel):
    """Investment portfolio schema."""
    model_config = ConfigDict(extra="forbid")
    
    name: str
    assets: Dict[str, float] = Field(description="Asset allocation percentages")
    risk_tolerance: RiskLevel


class PortfolioAnalysis(BaseModel):
    """Portfolio analysis schema."""
    model_config = ConfigDict(extra="forbid")
    
    portfolio: InvestmentPortfolio
    risk_metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class RiskMetrics(BaseModel):
    """Risk metrics schema."""
    model_config = ConfigDict(extra="forbid")
    
    sharpe_ratio: float
    volatility: float
    beta: float
    value_at_risk: float


class AssetAllocation(BaseModel):
    """Asset allocation schema."""
    model_config = ConfigDict(extra="forbid")
    
    asset_class: str
    percentage: float = Field(ge=0, le=100)
    rationale: str


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    risk_level: RiskLevel
    findings: List[str]
    iteration: int
    resolved: bool
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# CODING SCHEMAS
# ============================================================================

class CodeGenInput(BaseModel):
    """Code generation input."""
    model_config = ConfigDict(extra="forbid")
    
    description: str
    language: str = Field(default="python")
    constraints: List[str] = Field(default_factory=list)


class GeneratedCode(BaseModel):
    """Generated code output."""
    model_config = ConfigDict(extra="forbid")
    
    code: str
    language: str
    explanation: str


class CodeReview(BaseModel):
    """Code review output."""
    model_config = ConfigDict(extra="forbid")
    
    approved: bool
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class DebugResult(BaseModel):
    """Debug result output."""
    model_config = ConfigDict(extra="forbid")
    
    fixed_code: str
    bugs_found: List[str] = Field(default_factory=list)
    explanation: str


class CodingNewsReport(BaseModel):
    """Coding/AI news report."""
    model_config = ConfigDict(extra="forbid")
    
    headlines: List[str] = Field(default_factory=list)
    trends: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class CodeGenerationRequest(BaseModel):
    """Code generation request."""
    model_config = ConfigDict(extra="forbid")
    
    description: str
    language: str = Field(default="python")
    constraints: List[str] = Field(default_factory=list)
    session_id: str


class CodeGenerationResponse(BaseModel):
    """Code generation response."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    code: str
    language: str
    explanation: str
    confidence_score: float = Field(ge=0, le=1)


class CodeDebugRequest(BaseModel):
    """Code debugging request."""
    model_config = ConfigDict(extra="forbid")
    
    code: str
    error_message: Optional[str] = Field(default=None)
    language: str
    context: Optional[str] = Field(default=None)


class CodeDebugResponse(BaseModel):
    """Code debugging response."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    issues_found: List[Dict[str, Any]]
    fixed_code: str
    explanation: str


# ============================================================================
# FASHION SCHEMAS
# ============================================================================

class OutfitAnalysis(BaseModel):
    """Outfit analysis output."""
    model_config = ConfigDict(extra="forbid")
    
    items_detected: List[str] = Field(default_factory=list)
    style: str
    colors: List[str] = Field(default_factory=list)
    occasion_fit: str
    suggestions: List[str] = Field(default_factory=list)


class StyleTrend(BaseModel):
    """Style trend output."""
    model_config = ConfigDict(extra="forbid")
    
    current_trends: List[str] = Field(default_factory=list)
    trending_colors: List[str] = Field(default_factory=list)
    trending_styles: List[str] = Field(default_factory=list)


class OutfitRecommendationInput(BaseModel):
    """Outfit recommendation input."""
    model_config = ConfigDict(extra="forbid")
    
    budget: float = Field(ge=0)
    occasion: str
    time: str  # morning, afternoon, evening, night
    location: str


class OutfitRecommendation(BaseModel):
    """Outfit recommendation output."""
    model_config = ConfigDict(extra="forbid")
    
    recommended_items: List[str] = Field(default_factory=list)
    style_notes: str
    estimated_cost: float
    trend_alignment: str


class FashionQuery(BaseModel):
    """Fashion analysis query schema."""
    model_config = ConfigDict(extra="forbid")
    
    query_type: Literal["style", "trend", "outfit", "accessory", "general"]
    question: str
    occasion: Optional[str] = Field(default=None)
    season: Optional[str] = Field(default=None)
    body_type: Optional[str] = Field(default=None)
    personal_style: Optional[List[str]] = Field(default=None)


class FashionImageAnalysis(BaseModel):
    """Fashion image analysis schema."""
    model_config = ConfigDict(extra="forbid")
    
    image_data: str = Field(description="Base64 encoded image")
    analysis_type: List[Literal["style", "color", "trend", "occasion"]] = Field(
        default_factory=lambda: ["style"]
    )


class FashionResponse(BaseModel):
    """Fashion response schema."""
    model_config = ConfigDict(extra="forbid")
    
    session_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    analysis: str
    recommendations: List[str] = Field(default_factory=list)
    style_tips: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserLogin(BaseModel):
    """User login schema."""
    model_config = ConfigDict(extra="forbid")
    
    email: EmailStr
    password: str = Field(min_length=8)


class UserCreate(BaseModel):
    """User registration schema."""
    model_config = ConfigDict(extra="forbid")
    
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: Literal["user", "admin"] = Field(default="user")


class TokenResponse(BaseModel):
    """JWT token response."""
    model_config = ConfigDict(extra="forbid")
    
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "DomainEnum",
    "Urgency",
    "RiskLevel",
    
    # Shared
    "ConversationContext",
    "APIResponse",
    "HealthCheckResponse",
    "HumanApproval",
    
    # Medicine / CDS
    "UserQuery",
    "TriageNote",
    "DiagnosisWithEvidence",
    "MedicationRecommendation",
    "InvestigationRecommendation",
    "SpecialistConsultationRequest",
    "SOAPNotes",
    "FollowUpPlan",
    "SpecialistResponse",
    "SpecialistConsultationResponse",
    "PatientInfo",
    "ManagementPlan",
    "CDSResponse",
    "ResearchQuestion",
    "ResearchManuscript",
    "MedicalNewsReport",
    "MedicalResearchRequest",
    "MedicalResearchResponse",
    
    # Finance
    "InvestorInfo",
    "InvestmentRecommendation",
    "RiskAssessment",
    "InvestmentGuide",
    "InvestmentPlan",
    "FinancialNewsReport",
    "FinancialQuery",
    "FinanceResponse",
    "InvestmentPortfolio",
    "PortfolioAnalysis",
    "RiskMetrics",
    "AssetAllocation",
    "RiskAssessmentResponse",
    
    # Coding
    "CodeGenInput",
    "GeneratedCode",
    "CodeReview",
    "DebugResult",
    "CodingNewsReport",
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    "CodeDebugRequest",
    "CodeDebugResponse",
    
    # Fashion
    "OutfitAnalysis",
    "StyleTrend",
    "OutfitRecommendationInput",
    "OutfitRecommendation",
    "FashionQuery",
    "FashionImageAnalysis",
    "FashionResponse",
    
    # Auth
    "UserLogin",
    "UserCreate",
    "TokenResponse",
]
