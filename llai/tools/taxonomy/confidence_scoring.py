from typing import Dict, List, Any, Set, Tuple
import math
import json

class ConfidenceScorer:
    """Calculates confidence scores for content classifications."""
    
    def __init__(self):
        self.minimum_threshold = 0.15
        self.high_confidence_threshold = 0.7
    
    def calculate_semantic_similarity(self, model_response: Dict[str, Any], 
                                     mapped_taxonomy: Dict[str, Any]) -> float:
        """Calculate semantic similarity between AI model classification and taxonomy mapping."""
        # This is a simplified implementation
        # In a real system, we would use embeddings and vector similarity
        
        # Extract practice areas from model response
        model_areas = set()
        if isinstance(model_response.get("practice_area"), list):
            model_areas = set(area.lower() for area in model_response["practice_area"])
        elif isinstance(model_response.get("practice_area"), str):
            model_areas = {model_response["practice_area"].lower()}
        
        # Extract practice areas from taxonomy mapping
        taxonomy_areas = set()
        for parent in mapped_taxonomy.get("parent_categories", []):
            taxonomy_areas.add(parent["name"].lower())
        
        # Calculate Jaccard similarity
        if not model_areas or not taxonomy_areas:
            return 0.0
            
        intersection = model_areas.intersection(taxonomy_areas)
        union = model_areas.union(taxonomy_areas)
        
        return len(intersection) / len(union) if union else 0.0
    
    def combine_evidence_scores(self, scores: List[float], weights: List[float] = None) -> float:
        """Combine multiple evidence scores into a final confidence score."""
        if not scores:
            return 0.0
            
        if weights is None:
            weights = [1.0] * len(scores)
            
        # Normalize weights
        weight_sum = sum(weights)
        if weight_sum == 0:
            return 0.0
            
        normalized_weights = [w / weight_sum for w in weights]
        
        # Weighted average
        weighted_score = sum(s * w for s, w in zip(scores, normalized_weights))
        
        # Apply sigmoid function to map to 0-1 range with better distribution
        confidence = 1 / (1 + math.exp(-5 * (weighted_score - 0.5)))
        
        return min(1.0, max(0.0, confidence))  # Clamp to 0-1 range
    
    def score_classification_confidence(self, 
                                       content: str,
                                       model_response: Dict[str, Any], 
                                       mapped_taxonomy: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall confidence score for a classification result."""
        # 1. Calculate keyword match strength
        keyword_score = 0.0
        if mapped_taxonomy.get("parent_categories"):
            # Use the highest parent category score
            keyword_score = mapped_taxonomy["parent_categories"][0].get("score", 0.0)
        
        # 2. Calculate semantic similarity between model and taxonomy
        semantic_score = self.calculate_semantic_similarity(model_response, mapped_taxonomy)
        
        # 3. Calculate content specificity (longer, more detailed content tends to be more classifiable)
        content_length = len(content)
        specificity_score = min(1.0, content_length / 5000)  # Cap at 5000 chars
        
        # 4. Calculate response quality score
        # Check if response has expected fields with meaningful values
        response_quality = 0.0
        expected_fields = ["practice_area", "target_audience", "topics", "content_type"]
        field_count = sum(1 for field in expected_fields if field in model_response and model_response[field])
        response_quality = field_count / len(expected_fields)
        
        # 5. Calculate classification confidence
        evidence_scores = [keyword_score, semantic_score, specificity_score, response_quality]
        weights = [0.4, 0.3, 0.1, 0.2]  # Keyword and semantic similarity are most important
        
        confidence = self.combine_evidence_scores(evidence_scores, weights)
        
        # 6. Determine confidence level
        confidence_level = "low"
        if confidence >= self.high_confidence_threshold:
            confidence_level = "high"
        elif confidence >= self.minimum_threshold:
            confidence_level = "medium"
        
        return {
            "confidence_score": confidence,
            "confidence_level": confidence_level,
            "evidence": {
                "keyword_match_score": keyword_score,
                "semantic_similarity_score": semantic_score,
                "content_specificity_score": specificity_score,
                "response_quality_score": response_quality
            },
            "is_reliable": confidence >= self.minimum_threshold
        }
