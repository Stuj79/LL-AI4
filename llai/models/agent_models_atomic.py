"""
Atomic Agents BaseIOSchema models for agent-specific data structures.
This consolidates and migrates models from various agent files using BaseIOSchema.
"""

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import List, Dict, Any, Optional

# --- Discovery Agent Models ---

class StakeholderInfo(BaseIOSchema):
    """Schema for stakeholder information."""
    name: str = Field(..., description="Name of the stakeholder")
    role: str = Field(..., description="Role or position of the stakeholder")
    contact_info: str = Field("", description="Contact information for the stakeholder")
    responsibilities: List[str] = Field(default_factory=list, description="List of stakeholder responsibilities")

# --- Content Agent Models ---

class QualityScore(BaseIOSchema):
    """Schema for content quality assessment scores."""
    clarity: float = Field(..., ge=0.0, le=1.0, description="Clarity score between 0 and 1")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Accuracy score between 0 and 1")
    tone: float = Field(..., ge=0.0, le=1.0, description="Tone appropriateness score between 0 and 1")
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall quality score between 0 and 1")
    feedback: List[str] = Field(..., description="List of actionable feedback items")

class ContentCategorization(BaseIOSchema):
    """Schema for content categorization results."""
    id: str = Field(..., description="Unique identifier for the content item")
    ai_categories: List[str] = Field(..., description="AI-assigned primary categories")
    ai_sub_categories: List[str] = Field(..., description="AI-assigned subcategories")

# --- Gap Analysis Agent Models ---

class PracticeAreaGaps(BaseIOSchema):
    """Schema for practice area gap analysis results."""
    gaps: List[str] = Field(..., description="List of practice areas with content gaps")
    covered_areas: List[str] = Field(default_factory=list, description="List of well-covered practice areas")
    gap_severity: Dict[str, str] = Field(default_factory=dict, description="Severity level for each gap area")

class FormatGaps(BaseIOSchema):
    """Schema for content format gap analysis results."""
    gaps: List[str] = Field(..., description="List of content formats with gaps")
    covered_formats: List[str] = Field(default_factory=list, description="List of well-covered content formats")
    priority_formats: List[str] = Field(default_factory=list, description="High-priority formats to address")

class LanguageCoverageGap(BaseIOSchema):
    """Schema for language coverage gap analysis."""
    locale: str = Field(..., description="Language/locale code (e.g., 'en-US', 'es-ES')")
    missing_count: int = Field(..., ge=0, description="Number of missing content items for this locale")
    priority_level: str = Field("medium", description="Priority level for addressing this gap")

class MultilingualNeedsAnalysis(BaseIOSchema):
    """Schema for multilingual content needs analysis."""
    target_locales: List[str] = Field(..., description="List of target locale codes")
    coverage_gaps: List[LanguageCoverageGap] = Field(..., description="Coverage gaps per locale")
    total_gap_count: int = Field(..., ge=0, description="Total number of content gaps across all locales")

# --- Agent Configuration Models ---

class AgentConfig(BaseIOSchema):
    """Base configuration schema for all agents."""
    model: str = Field("gpt-4o-mini", description="LLM model to use for the agent")
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="Temperature setting for response generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for response generation")
    timeout: int = Field(30, ge=1, description="Timeout in seconds for agent operations")
    retry_attempts: int = Field(3, ge=0, description="Number of retry attempts for failed operations")

class ContentAgentConfig(AgentConfig):
    """Configuration schema specific to content-related agents."""
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum quality score threshold")
    categorization_confidence: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence for categorization")
    enable_auto_tagging: bool = Field(True, description="Whether to enable automatic content tagging")

class AnalysisAgentConfig(AgentConfig):
    """Configuration schema specific to analysis agents."""
    gap_threshold: int = Field(5, ge=1, description="Minimum number of items to not consider a gap")
    include_secondary_analysis: bool = Field(True, description="Whether to include secondary analysis metrics")
    confidence_level: str = Field("medium", description="Required confidence level for analysis results")
