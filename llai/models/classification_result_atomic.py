"""
Atomic Agents BaseIOSchema model for content classification results.
This is the migrated version of classification_result.py using BaseIOSchema.
"""

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import Dict, List, Any, Optional
import json

class ClassificationResult(BaseIOSchema):
    """Schema for content classification result with confidence scoring."""
    
    content_item_id: str = Field(..., description="Unique identifier for the content item")
    raw_classification: Dict[str, Any] = Field(..., description="Raw classification data from the classifier")
    taxonomy_mapping: Dict[str, Any] = Field(..., description="Mapped taxonomy categories and subcategories")
    confidence_data: Dict[str, Any] = Field(..., description="Confidence scoring and reliability metrics")
    
    def get_primary_category(self) -> Optional[Dict[str, Any]]:
        """Get the primary (highest confidence) parent category."""
        if not self.taxonomy_mapping.get("parent_categories"):
            return None
        return self.taxonomy_mapping["parent_categories"][0]
        
    def get_primary_subcategories(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get the primary subcategories for the highest confidence parent."""
        primary = self.get_primary_category()
        if not primary:
            return []
        return primary.get("subcategories", [])[:limit]
        
    def get_confidence_level(self) -> str:
        """Get the confidence level (high, medium, low)."""
        return self.confidence_data.get("confidence_level", "low")
        
    def is_reliable(self) -> bool:
        """Check if the classification is considered reliable."""
        return self.confidence_data.get("is_reliable", False)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        result = {
            "content_item_id": self.content_item_id,
            "primary_category": self.get_primary_category(),
            "subcategories": self.get_primary_subcategories(),
            "confidence": {
                "score": self.confidence_data.get("confidence_score", 0.0),
                "level": self.get_confidence_level(),
                "is_reliable": self.is_reliable()
            },
            "topics": self.raw_classification.get("topics", []),
            "target_audience": self.raw_classification.get("target_audience", []),
            "content_type": self.raw_classification.get("content_type", "unknown"),
            "complexity_level": self.raw_classification.get("complexity_level", "unknown")
        }
        
        # Add secondary categories if available
        if len(self.taxonomy_mapping.get("parent_categories", [])) > 1:
            result["secondary_categories"] = self.taxonomy_mapping["parent_categories"][1:]
            
        return result
        
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

class ClassificationConfidence(BaseIOSchema):
    """Schema for classification confidence metrics."""
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numerical confidence score between 0 and 1")
    confidence_level: str = Field(..., description="Categorical confidence level (high, medium, low)")
    is_reliable: bool = Field(..., description="Whether the classification is considered reliable")
    factors: List[str] = Field(default_factory=list, description="Factors that influenced confidence scoring")

class TaxonomyMapping(BaseIOSchema):
    """Schema for taxonomy mapping results."""
    parent_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Mapped parent categories with confidence scores")
    subcategories: List[Dict[str, Any]] = Field(default_factory=list, description="Mapped subcategories with confidence scores")
    mapping_method: str = Field(..., description="Method used for taxonomy mapping")
