"""
Tests for the new Atomic Agents BaseIOSchema models.
This validates that the migrated models work correctly.
"""

import pytest
from typing import Dict, Any

# Import atomic models
from llai.models.agent_responses_atomic import (
    CatalogContentItem,
    CatalogContentResponse,
    CategorizeContentResponse,
    ContentCoverageMetrics,
    AnalyzeContentGapsResponse
)
from llai.models.classification_result_atomic import (
    ClassificationResult,
    ClassificationConfidence,
    TaxonomyMapping
)
from llai.models.agent_models_atomic import (
    StakeholderInfo,
    QualityScore,
    ContentCategorization,
    PracticeAreaGaps,
    FormatGaps,
    AgentConfig,
    ContentAgentConfig,
    AnalysisAgentConfig
)
from llai.config.settings import (
    LLMProviderConfig,
    ApplicationConfig,
    get_config,
    get_agent_config
)

class TestAtomicModels:
    """Test suite for atomic BaseIOSchema models."""
    
    def test_catalog_content_item(self):
        """Test CatalogContentItem model creation and validation."""
        item = CatalogContentItem(
            title="Test Article",
            type="article",
            platform="website",
            publish_date="2024-01-01",
            metadata={"author": "John Doe", "tags": ["legal", "marketing"]}
        )
        
        assert item.title == "Test Article"
        assert item.type == "article"
        assert item.metadata["author"] == "John Doe"
        
        # Test serialization
        item_dict = item.model_dump()
        assert "title" in item_dict
        assert "metadata" in item_dict
        
        # Test deserialization
        new_item = CatalogContentItem.model_validate(item_dict)
        assert new_item.title == item.title
    
    def test_catalog_content_response(self):
        """Test CatalogContentResponse model with list of items."""
        items = [
            CatalogContentItem(title="Article 1", type="article"),
            CatalogContentItem(title="Video 1", type="video")
        ]
        
        response = CatalogContentResponse(catalog=items)
        assert len(response.catalog) == 2
        assert response.catalog[0].title == "Article 1"
        assert response.catalog[1].type == "video"
    
    def test_categorize_content_response(self):
        """Test CategorizeContentResponse model."""
        response = CategorizeContentResponse(
            title="Legal Marketing Guide",
            type="guide",
            platform="website",
            practice_area=["corporate", "litigation"],
            target_audience=["lawyers", "marketers"],
            format="long-form"
        )
        
        assert "corporate" in response.practice_area
        assert "lawyers" in response.target_audience
        assert response.format == "long-form"
    
    def test_quality_score(self):
        """Test QualityScore model with validation."""
        score = QualityScore(
            clarity=0.8,
            accuracy=0.9,
            tone=0.7,
            overall=0.8,
            feedback=["Good clarity", "Needs more examples"]
        )
        
        assert score.clarity == 0.8
        assert len(score.feedback) == 2
        
        # Test validation - scores should be between 0 and 1
        with pytest.raises(ValueError):
            QualityScore(
                clarity=1.5,  # Invalid - greater than 1
                accuracy=0.9,
                tone=0.7,
                overall=0.8,
                feedback=[]
            )
    
    def test_classification_result(self):
        """Test ClassificationResult model with methods."""
        result = ClassificationResult(
            content_item_id="item_123",
            raw_classification={
                "topics": ["contract law", "business"],
                "target_audience": ["lawyers"],
                "content_type": "article"
            },
            taxonomy_mapping={
                "parent_categories": [
                    {"name": "Corporate Law", "confidence": 0.9, "subcategories": [
                        {"name": "Contract Law", "confidence": 0.8}
                    ]}
                ]
            },
            confidence_data={
                "confidence_score": 0.85,
                "confidence_level": "high",
                "is_reliable": True
            }
        )
        
        # Test methods
        primary = result.get_primary_category()
        assert primary["name"] == "Corporate Law"
        assert primary["confidence"] == 0.9
        
        subcategories = result.get_primary_subcategories()
        assert len(subcategories) == 1
        assert subcategories[0]["name"] == "Contract Law"
        
        assert result.get_confidence_level() == "high"
        assert result.is_reliable() == True
        
        # Test serialization
        result_dict = result.to_dict()
        assert result_dict["content_item_id"] == "item_123"
        assert result_dict["confidence"]["level"] == "high"
    
    def test_stakeholder_info(self):
        """Test StakeholderInfo model."""
        stakeholder = StakeholderInfo(
            name="Jane Smith",
            role="Marketing Director",
            contact_info="jane@example.com",
            responsibilities=["Strategy", "Budget approval"]
        )
        
        assert stakeholder.name == "Jane Smith"
        assert "Strategy" in stakeholder.responsibilities
    
    def test_practice_area_gaps(self):
        """Test PracticeAreaGaps model."""
        gaps = PracticeAreaGaps(
            gaps=["immigration", "tax"],
            covered_areas=["corporate", "litigation"],
            gap_severity={"immigration": "high", "tax": "medium"}
        )
        
        assert "immigration" in gaps.gaps
        assert gaps.gap_severity["immigration"] == "high"
    
    def test_agent_config_hierarchy(self):
        """Test agent configuration model hierarchy."""
        # Test base config
        base_config = AgentConfig(
            model="gpt-4",
            temperature=0.5,
            timeout=60
        )
        assert base_config.model == "gpt-4"
        assert base_config.temperature == 0.5
        
        # Test content agent config (inherits from base)
        content_config = ContentAgentConfig(
            model="gpt-4o-mini",
            quality_threshold=0.8,
            enable_auto_tagging=False
        )
        assert content_config.model == "gpt-4o-mini"
        assert content_config.temperature == 0.2  # Default for content agents
        assert content_config.quality_threshold == 0.8
        
        # Test analysis agent config
        analysis_config = AnalysisAgentConfig(
            gap_threshold=10,
            confidence_level="high"
        )
        assert analysis_config.temperature == 0.4  # Default for analysis agents
        assert analysis_config.gap_threshold == 10

class TestConfigurationModels:
    """Test suite for configuration models."""
    
    def test_llm_provider_config(self):
        """Test LLMProviderConfig model."""
        config = LLMProviderConfig(
            openai_api_key="test_key",
            default_model="gpt-4",
            max_retries=5,
            timeout=45
        )
        
        assert config.openai_api_key == "test_key"
        assert config.default_model == "gpt-4"
        assert config.max_retries == 5
    
    def test_application_config_structure(self):
        """Test that ApplicationConfig can be created with all required fields."""
        # This test ensures the configuration structure is valid
        # Note: We're not testing from_env() here as it requires actual env vars
        
        llm_config = LLMProviderConfig(
            openai_api_key="test_key",
            default_model="gpt-4o-mini"
        )
        
        # Test that we can create a minimal config
        from llai.config.settings import DatabaseConfig, LoggingConfig
        
        db_config = DatabaseConfig()
        log_config = LoggingConfig()
        
        app_config = ApplicationConfig(
            llm_provider=llm_config,
            database=db_config,
            logging=log_config
        )
        
        assert app_config.llm_provider.default_model == "gpt-4o-mini"
        assert app_config.app_name == "Legal AI Marketing Assistant"
        assert app_config.version == "1.0.0"

if __name__ == "__main__":
    # Run basic tests
    test_suite = TestAtomicModels()
    test_suite.test_catalog_content_item()
    test_suite.test_quality_score()
    test_suite.test_classification_result()
    test_suite.test_agent_config_hierarchy()
    
    config_suite = TestConfigurationModels()
    config_suite.test_llm_provider_config()
    config_suite.test_application_config_structure()
    
    print("All basic tests passed!")
