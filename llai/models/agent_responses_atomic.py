"""
Atomic Agents BaseIOSchema models for validating the structure of responses from agent tools.
This is the migrated version of agent_responses.py using BaseIOSchema instead of BaseModel.
"""

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import List, Dict, Any, Optional

# --- ContentInventoryAgent Responses ---

class CatalogContentItem(BaseIOSchema):
    """Schema for a single item in the content catalog."""
    title: Optional[str] = Field(None, description="Title of the content item")
    type: Optional[str] = Field(None, description="Type of content (e.g., article, video, document)")
    platform: Optional[str] = Field(None, description="Platform where content is hosted")
    publish_date: Optional[str] = Field(None, description="Publication date of the content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata fields")

class CatalogContentResponse(BaseIOSchema):
    """Response schema for the catalog_content tool."""
    catalog: List[CatalogContentItem] = Field(..., description="List of cataloged content items")

class CategorizeContentResponse(BaseIOSchema):
    """
    Response schema for the categorize_content tool.
    Represents the original content item with added category fields.
    """
    title: Optional[str] = Field(None, description="Title of the content item")
    type: Optional[str] = Field(None, description="Type of content")
    platform: Optional[str] = Field(None, description="Platform where content is hosted")
    
    # Added categorization fields
    practice_area: List[str] = Field(default_factory=list, description="Legal practice areas covered")
    target_audience: List[str] = Field(default_factory=list, description="Target audience segments")
    format: Optional[str] = Field(None, description="Content format classification")

class ContentCoverageMetrics(BaseIOSchema):
    """Schema for content coverage metrics per practice area."""
    # Note: This uses a flexible approach since practice areas are dynamic
    # Actual metrics will be stored as additional fields
    total_content: int = Field(0, description="Total number of content items")
    covered_areas: List[str] = Field(default_factory=list, description="Practice areas with content")
    metrics: Dict[str, int] = Field(default_factory=dict, description="Practice area to content count mapping")

class AnalyzeContentGapsResponse(BaseIOSchema):
    """Response schema for the analyze_content_gaps tool."""
    covered_areas: List[str] = Field(..., description="Practice areas with existing content coverage")
    gap_areas: List[str] = Field(..., description="Practice areas lacking sufficient content")
    coverage_metrics: Dict[str, int] = Field(..., description="Mapping of practice area to content count")
