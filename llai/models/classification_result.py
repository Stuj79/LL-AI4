from typing import Dict, List, Any, Optional
import json

class ClassificationResult:
    """Represents a content classification result with confidence scoring."""
    
    def __init__(self, 
                content_item_id: str,
                raw_classification: Dict[str, Any],
                taxonomy_mapping: Dict[str, Any],
                confidence_data: Dict[str, Any]):
        self.content_item_id = content_item_id
        self.raw_classification = raw_classification
        self.taxonomy_mapping = taxonomy_mapping
        self.confidence_data = confidence_data
        
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
