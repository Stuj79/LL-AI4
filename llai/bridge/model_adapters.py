"""
Model adapter functions for converting between Legion Pydantic models and Atomic Agents BaseIOSchema models.
These adapters enable gradual migration using the Strangler Fig pattern.
"""

from typing import Dict, Any, List, Optional
import json

# Import legacy models
from llai.models.agent_responses import (
    CatalogContentItem as LegacyCatalogContentItem,
    CatalogContentResponse as LegacyCatalogContentResponse,
    CategorizeContentResponse as LegacyCategorizeContentResponse,
    ContentCoverageMetrics as LegacyContentCoverageMetrics,
    AnalyzeContentGapsResponse as LegacyAnalyzeContentGapsResponse
)
from llai.models.classification_result import ClassificationResult as LegacyClassificationResult

# Import new atomic models
from llai.models.agent_responses_atomic import (
    CatalogContentItem,
    CatalogContentResponse,
    CategorizeContentResponse,
    ContentCoverageMetrics,
    AnalyzeContentGapsResponse
)
from llai.models.classification_result_atomic import ClassificationResult
from llai.models.agent_models_atomic import (
    StakeholderInfo,
    QualityScore,
    ContentCategorization,
    PracticeAreaGaps,
    FormatGaps
)

# --- Content Catalog Adapters ---

def legacy_catalog_item_to_atomic(legacy_item: LegacyCatalogContentItem) -> CatalogContentItem:
    """Convert legacy CatalogContentItem to atomic BaseIOSchema version."""
    return CatalogContentItem(
        title=legacy_item.title,
        type=legacy_item.type,
        platform=legacy_item.platform,
        publish_date=legacy_item.publish_date,
        metadata=legacy_item.metadata
    )

def atomic_catalog_item_to_legacy(atomic_item: CatalogContentItem) -> LegacyCatalogContentItem:
    """Convert atomic CatalogContentItem to legacy Pydantic version."""
    legacy_item = LegacyCatalogContentItem(
        title=atomic_item.title,
        type=atomic_item.type,
        platform=atomic_item.platform,
        publish_date=atomic_item.publish_date,
        metadata=atomic_item.metadata
    )
    return legacy_item

def legacy_catalog_response_to_atomic(legacy_response: LegacyCatalogContentResponse) -> CatalogContentResponse:
    """Convert legacy CatalogContentResponse to atomic BaseIOSchema version."""
    atomic_catalog = [legacy_catalog_item_to_atomic(item) for item in legacy_response.catalog]
    return CatalogContentResponse(catalog=atomic_catalog)

def atomic_catalog_response_to_legacy(atomic_response: CatalogContentResponse) -> LegacyCatalogContentResponse:
    """Convert atomic CatalogContentResponse to legacy Pydantic version."""
    legacy_catalog = [atomic_catalog_item_to_legacy(item) for item in atomic_response.catalog]
    return LegacyCatalogContentResponse(catalog=legacy_catalog)

# --- Content Categorization Adapters ---

def legacy_categorize_response_to_atomic(legacy_response: LegacyCategorizeContentResponse) -> CategorizeContentResponse:
    """Convert legacy CategorizeContentResponse to atomic BaseIOSchema version."""
    return CategorizeContentResponse(
        title=legacy_response.title,
        type=legacy_response.type,
        platform=legacy_response.platform,
        practice_area=legacy_response.practice_area,
        target_audience=legacy_response.target_audience,
        format=legacy_response.format
    )

def atomic_categorize_response_to_legacy(atomic_response: CategorizeContentResponse) -> LegacyCategorizeContentResponse:
    """Convert atomic CategorizeContentResponse to legacy Pydantic version."""
    legacy_response = LegacyCategorizeContentResponse(
        title=atomic_response.title,
        type=atomic_response.type,
        platform=atomic_response.platform,
        practice_area=atomic_response.practice_area,
        target_audience=atomic_response.target_audience,
        format=atomic_response.format
    )
    return legacy_response

# --- Coverage Metrics Adapters ---

def legacy_coverage_metrics_to_atomic(legacy_metrics: LegacyContentCoverageMetrics) -> ContentCoverageMetrics:
    """Convert legacy ContentCoverageMetrics to atomic BaseIOSchema version."""
    # Extract dynamic fields from the legacy model
    legacy_dict = legacy_metrics.model_dump()
    
    # Separate known fields from dynamic practice area counts
    known_fields = set()
    practice_area_metrics = {}
    
    for key, value in legacy_dict.items():
        if isinstance(value, int) and key not in known_fields:
            practice_area_metrics[key] = value
    
    return ContentCoverageMetrics(
        total_content=sum(practice_area_metrics.values()),
        covered_areas=list(practice_area_metrics.keys()),
        metrics=practice_area_metrics
    )

def atomic_coverage_metrics_to_legacy(atomic_metrics: ContentCoverageMetrics) -> LegacyContentCoverageMetrics:
    """Convert atomic ContentCoverageMetrics to legacy Pydantic version."""
    # Create legacy model with dynamic fields
    legacy_data = {}
    for area, count in atomic_metrics.metrics.items():
        legacy_data[area] = count
    
    return LegacyContentCoverageMetrics.model_validate(legacy_data)

# --- Gap Analysis Adapters ---

def legacy_gaps_response_to_atomic(legacy_response: LegacyAnalyzeContentGapsResponse) -> AnalyzeContentGapsResponse:
    """Convert legacy AnalyzeContentGapsResponse to atomic BaseIOSchema version."""
    return AnalyzeContentGapsResponse(
        covered_areas=legacy_response.covered_areas,
        gap_areas=legacy_response.gap_areas,
        coverage_metrics=legacy_response.coverage_metrics
    )

def atomic_gaps_response_to_legacy(atomic_response: AnalyzeContentGapsResponse) -> LegacyAnalyzeContentGapsResponse:
    """Convert atomic AnalyzeContentGapsResponse to legacy Pydantic version."""
    return LegacyAnalyzeContentGapsResponse(
        covered_areas=atomic_response.covered_areas,
        gap_areas=atomic_response.gap_areas,
        coverage_metrics=atomic_response.coverage_metrics
    )

# --- Classification Result Adapters ---

def legacy_classification_to_atomic(legacy_result: LegacyClassificationResult) -> ClassificationResult:
    """Convert legacy ClassificationResult to atomic BaseIOSchema version."""
    return ClassificationResult(
        content_item_id=legacy_result.content_item_id,
        raw_classification=legacy_result.raw_classification,
        taxonomy_mapping=legacy_result.taxonomy_mapping,
        confidence_data=legacy_result.confidence_data
    )

def atomic_classification_to_legacy(atomic_result: ClassificationResult) -> LegacyClassificationResult:
    """Convert atomic ClassificationResult to legacy version."""
    return LegacyClassificationResult(
        content_item_id=atomic_result.content_item_id,
        raw_classification=atomic_result.raw_classification,
        taxonomy_mapping=atomic_result.taxonomy_mapping,
        confidence_data=atomic_result.confidence_data
    )

# --- Utility Functions ---

def convert_dict_to_atomic_model(data: Dict[str, Any], model_class):
    """Generic function to convert dictionary data to atomic model."""
    try:
        return model_class.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to convert data to {model_class.__name__}: {e}")

def convert_atomic_model_to_dict(atomic_model) -> Dict[str, Any]:
    """Generic function to convert atomic model to dictionary."""
    return atomic_model.model_dump()

def batch_convert_legacy_to_atomic(legacy_items: List[Any], converter_func) -> List[Any]:
    """Convert a list of legacy items to atomic models using the provided converter function."""
    return [converter_func(item) for item in legacy_items]

def batch_convert_atomic_to_legacy(atomic_items: List[Any], converter_func) -> List[Any]:
    """Convert a list of atomic items to legacy models using the provided converter function."""
    return [converter_func(item) for item in atomic_items]
