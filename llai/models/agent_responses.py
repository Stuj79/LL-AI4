"""
Pydantic models for validating the structure of responses from agent tools.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from typing import ClassVar

# --- ContentInventoryAgent Responses ---

class CatalogContentItem(BaseModel):
    """Model for a single item in the content catalog."""
    title: Optional[str] = None
    type: Optional[str] = None
    platform: Optional[str] = None
    publish_date: Optional[str] = None
    # Allow other metadata fields
    metadata: Dict[str, Any] = Field(default_factory=dict)

    agent_config: ClassVar[dict] = ConfigDict(extra='allow')
    # model_config = {
    #     "extra": "allow" # Allow fields like 'url', etc. if extracted
    # }

class CatalogContentResponse(BaseModel):
    """Response model for the catalog_content tool."""
    catalog: List[CatalogContentItem]

class CategorizeContentResponse(BaseModel):
    """
    Response model for the categorize_content tool.
    Represents the original content item dictionary with added category fields.
    """
    # Include fields typically found in content_item, plus new categories
    title: Optional[str] = None
    type: Optional[str] = None
    platform: Optional[str] = None
    # ... other potential original fields ...

    # Added fields
    practice_area: List[str] = Field(default_factory=list)
    target_audience: List[str] = Field(default_factory=list)
    format: Optional[str] = None # Assuming format is a single string based on prompt

    agent_config: ClassVar[dict] = ConfigDict(extra='allow')
    # model_config = {
    #     "extra": "allow" # Allow original fields not explicitly defined
    # }

class ContentCoverageMetrics(BaseModel):
    """Metrics for content coverage per practice area."""
    # Dynamically allow practice area names as keys
    agent_config: ClassVar[dict] = ConfigDict(extra='allow')
    # model_config = {
    #     "extra": "allow"
    # }
    # Example structure (actual fields depend on practice areas):
    # litigation: Optional[int] = 0
    # corporate: Optional[int] = 0

class AnalyzeContentGapsResponse(BaseModel):
    """Response model for the analyze_content_gaps tool."""
    covered_areas: List[str]
    gap_areas: List[str]
    coverage_metrics: Dict[str, int] # Maps practice area to content count

# --- Add other agent response models below as needed ---
