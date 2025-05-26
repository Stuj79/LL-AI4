"""
Comprehensive tests for Legal Marketing Agents.

This module provides comprehensive testing patterns for the new legal marketing agent
architecture, including unit tests, integration tests, and compliance validation tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from llai.agents.legal_marketing_base_agent import (
    LegalMarketingBaseAgent,
    LegalMarketingAgentConfig,
    Disclaimer,
    AdvertisingRule,
    EthicalGuideline,
    ComplianceStatus,
    AuditLogEntry
)
from llai.agents.context_providers import (
    MockDisclaimerProvider,
    MockAdvertisingRuleProvider,
    MockEthicalGuidelineProvider
)
from llai.agents.agent_factory import (
    LegalAgentFactory,
    LegalAgentFactoryConfig,
    MockLLMClientManager,
    create_legal_agent_factory
)
from llai.agents.stakeholder_identification_agent_atomic import (
    StakeholderIdentificationAgent,
    StakeholderIdentificationAgentConfig,
    StakeholderIdentificationInputSchema,
    StakeholderIdentificationOutputSchema,
    PlatformInventoryInputSchema,
    PlatformInventoryOutputSchema
)
from llai.config.settings import AppConfig
from llai.utils.exceptions_atomic import (
    LegalMarketingAgentError,
    ComplianceValidationError,
    DisclaimerInjectionError,
    AgentFactoryError
)


# --- Test Fixtures ---

@pytest.fixture
def mock_app_config():
    """Create a mock application configuration."""
    return AppConfig(
        app_name="LL-AI Test",
        environment="test",
        log_level="DEBUG"
    )

@pytest.fixture
def mock_llm_client_manager():
    """Create a mock LLM client manager."""
    return MockLLMClientManager()

@pytest.fixture
def legal_agent_config():
    """Create a test legal marketing agent configuration."""
    return LegalMarketingAgentConfig(
        client=Mock(),
        model="gpt-4o-mini",
        default_jurisdiction="ON",
        enable_strict_compliance_checks=True,
        audit_logging_level="standard",
        compliance_threshold=0.8
    )

@pytest.fixture
def stakeholder_agent_config():
    """Create a test stakeholder identification agent configuration."""
    return StakeholderIdentificationAgentConfig(
        client=Mock(),
        model="gpt-4o-mini",
        default_jurisdiction="ON",
        include_external_stakeholders=True,
        stakeholder_detail_level="standard",
        include_communication_plan=True
    )

@pytest.fixture
def mock_disclaimer_provider():
    """Create a mock disclaimer provider."""
    return MockDisclaimerProvider()

@pytest.fixture
def mock_advertising_rule_provider():
    """Create a mock advertising rule provider."""
    return MockAdvertisingRuleProvider()

@pytest.fixture
def mock_ethical_guideline_provider():
    """Create a mock ethical guideline provider."""
    return MockEthicalGuidelineProvider()

@pytest.fixture
def legal_agent_factory(mock_app_config, mock_llm_client_manager):
    """Create a legal agent factory for testing."""
    factory_config = LegalAgentFactoryConfig(
        use_mock_providers=True,
        default_jurisdiction="ON",
        enable_audit_logging=True
    )
    
    factory = LegalAgentFactory(
        global_config=mock_app_config,
        llm_client_manager=mock_llm_client_manager,
        factory_config=factory_config
    )
    
    # Register the stakeholder identification agent
    factory.register_agent_type("stakeholder_identification", StakeholderIdentificationAgent)
    
    return factory

@pytest.fixture
def sample_stakeholder_input():
    """Create sample input for stakeholder identification."""
    return StakeholderIdentificationInputSchema(
        company_structure="Mid-size law firm with 3 partners, 8 associates, and 5 support staff. Has marketing coordinator and business development manager.",
        organization_size="medium",
        industry_focus="Corporate law, real estate, family law",
        current_marketing_team="1 marketing coordinator, 1 business development manager",
        project_scope="Comprehensive digital marketing strategy overhaul"
    )

@pytest.fixture
def sample_platform_input():
    """Create sample input for platform inventory."""
    return PlatformInventoryInputSchema(
        platform_data="Website on WordPress, LinkedIn company page, Twitter account, Mailchimp for newsletters, Google Analytics",
        access_requirements="Admin access needed for website and analytics",
        integration_needs="Connect social media to analytics, integrate email with website"
    )


# --- Unit Tests for LegalMarketingBaseAgent ---

class TestLegalMarketingBaseAgent:
    """Test suite for LegalMarketingBaseAgent."""
    
    @pytest.fixture
    def base_agent(self, legal_agent_config, mock_disclaimer_provider, mock_advertising_rule_provider, mock_ethical_guideline_provider):
        """Create a base agent for testing."""
        return LegalMarketingBaseAgent(
            config=legal_agent_config,
            disclaimer_provider=mock_disclaimer_provider,
            advertising_rule_provider=mock_advertising_rule_provider,
            ethical_guideline_provider=mock_ethical_guideline_provider
        )
    
    def test_agent_initialization(self, base_agent, legal_agent_config):
        """Test that the base agent initializes correctly."""
        assert base_agent.legal_config == legal_agent_config
        assert base_agent.disclaimer_provider is not None
        assert base_agent.advertising_rule_provider is not None
        assert base_agent.ethical_guideline_provider is not None
        assert isinstance(base_agent._audit_log, list)
        assert len(base_agent._audit_log) == 0
    
    @pytest.mark.asyncio
    async def test_disclaimer_injection(self, base_agent):
        """Test disclaimer injection functionality."""
        # Create a mock response with content
        mock_response = Mock()
        mock_response.content = "This is test marketing content."
        
        # Inject disclaimers
        result = await base_agent._inject_disclaimers(mock_response, "marketing")
        
        # Verify disclaimers were added
        assert "Legal Disclaimers" in result.content
        assert "Attorney Advertising" in result.content
        
        # Verify audit log entry was created
        assert len(base_agent._audit_log) > 0
        assert base_agent._audit_log[-1].operation == "disclaimer_injection"
    
    @pytest.mark.asyncio
    async def test_compliance_validation(self, base_agent):
        """Test compliance validation functionality."""
        # Test compliant content
        compliant_content = "Our law firm provides professional legal services."
        result = await base_agent._validate_compliance(compliant_content)
        
        assert isinstance(result, ComplianceStatus)
        assert result.compliance_score >= 0.0
        assert result.compliance_score <= 1.0
        assert isinstance(result.violations, list)
        assert isinstance(result.recommendations, list)
        
        # Test content with potential violations
        violation_content = "We guarantee you will win your case! Call now for limited time offer!"
        result = await base_agent._validate_compliance(violation_content)
        
        assert len(result.violations) > 0
        assert result.compliance_score < 1.0
    
    @pytest.mark.asyncio
    async def test_confidential_data_handling(self, base_agent):
        """Test confidential data handling."""
        sensitive_data = {
            "client_name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "case_details": "Personal injury case"
        }
        
        result = await base_agent._handle_confidential_data(sensitive_data)
        
        # In strict mode, sensitive fields should be redacted
        assert result["client_name"] == "[REDACTED]"
        assert result["email"] == "[REDACTED]"
        assert result["phone"] == "[REDACTED]"
        assert result["case_details"] == "Personal injury case"  # Not in sensitive keys
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, base_agent):
        """Test audit logging functionality."""
        initial_log_count = len(base_agent._audit_log)
        
        await base_agent._audit_log_operation(
            operation="test_operation",
            input_summary="Test input",
            output_summary="Test output"
        )
        
        assert len(base_agent._audit_log) == initial_log_count + 1
        
        log_entry = base_agent._audit_log[-1]
        assert log_entry.operation == "test_operation"
        assert log_entry.input_summary == "Test input"
        assert log_entry.output_summary == "Test output"
        assert log_entry.agent_type == "LegalMarketingBaseAgent"
    
    def test_audit_log_management(self, base_agent):
        """Test audit log retrieval and clearing."""
        # Add some log entries
        base_agent._audit_log.append(AuditLogEntry(
            agent_type="TestAgent",
            operation="test_op",
            input_summary="test",
            output_summary="test"
        ))
        
        # Test retrieval
        log_copy = base_agent.get_audit_log()
        assert len(log_copy) == 1
        assert log_copy is not base_agent._audit_log  # Should be a copy
        
        # Test clearing
        base_agent.clear_audit_log()
        assert len(base_agent._audit_log) == 0


# --- Unit Tests for Context Providers ---

class TestContextProviders:
    """Test suite for context providers."""
    
    @pytest.mark.asyncio
    async def test_mock_disclaimer_provider(self, mock_disclaimer_provider):
        """Test mock disclaimer provider."""
        disclaimers = await mock_disclaimer_provider.get_disclaimers("ON", "marketing")
        
        assert isinstance(disclaimers, list)
        assert len(disclaimers) > 0
        
        disclaimer = disclaimers[0]
        assert isinstance(disclaimer, Disclaimer)
        assert disclaimer.jurisdiction == "ON"
        assert disclaimer.content_type == "marketing"
        assert disclaimer.mandatory is True
    
    @pytest.mark.asyncio
    async def test_mock_advertising_rule_provider(self, mock_advertising_rule_provider):
        """Test mock advertising rule provider."""
        rules = await mock_advertising_rule_provider.get_rules("ON", "general")
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        rule = rules[0]
        assert isinstance(rule, AdvertisingRule)
        assert rule.jurisdiction == "ON"
        assert rule.category in ["guarantees", "solicitation", "testimonials"]
    
    @pytest.mark.asyncio
    async def test_mock_ethical_guideline_provider(self, mock_ethical_guideline_provider):
        """Test mock ethical guideline provider."""
        guidelines = await mock_ethical_guideline_provider.get_guidelines("content_generation")
        
        assert isinstance(guidelines, list)
        assert len(guidelines) > 0
        
        guideline = guidelines[0]
        assert isinstance(guideline, EthicalGuideline)
        assert guideline.task_type == "content_generation"
        assert guideline.compliance_level in ["recommended", "required", "mandatory"]


# --- Unit Tests for Agent Factory ---

class TestLegalAgentFactory:
    """Test suite for LegalAgentFactory."""
    
    def test_factory_initialization(self, legal_agent_factory):
        """Test factory initialization."""
        assert legal_agent_factory.global_config is not None
        assert legal_agent_factory.llm_client_manager is not None
        assert legal_agent_factory.factory_config is not None
    
    def test_agent_registration(self, legal_agent_factory):
        """Test agent type registration."""
        initial_types = legal_agent_factory.get_available_agent_types()
        
        # Register a new agent type
        legal_agent_factory.register_agent_type("test_agent", StakeholderIdentificationAgent)
        
        updated_types = legal_agent_factory.get_available_agent_types()
        assert len(updated_types) == len(initial_types) + 1
        assert "test_agent" in updated_types
    
    def test_agent_creation(self, legal_agent_factory, stakeholder_agent_config):
        """Test agent creation through factory."""
        agent = legal_agent_factory.create_agent(
            "stakeholder_identification",
            stakeholder_agent_config
        )
        
        assert isinstance(agent, StakeholderIdentificationAgent)
        assert agent.legal_config.default_jurisdiction == "ON"
        assert agent.disclaimer_provider is not None
    
    def test_agent_creation_with_defaults(self, legal_agent_factory):
        """Test agent creation with default configuration."""
        agent = legal_agent_factory.create_agent("stakeholder_identification")
        
        assert isinstance(agent, StakeholderIdentificationAgent)
        assert agent.legal_config.default_jurisdiction == "ON"  # Factory default
    
    def test_unknown_agent_type_error(self, legal_agent_factory):
        """Test error handling for unknown agent types."""
        with pytest.raises(AgentFactoryError) as exc_info:
            legal_agent_factory.create_agent("unknown_agent_type")
        
        assert "UNKNOWN_AGENT_TYPE" in str(exc_info.value)
    
    def test_dependency_validation(self, legal_agent_factory):
        """Test dependency validation."""
        dependencies = legal_agent_factory.validate_dependencies()
        
        assert isinstance(dependencies, dict)
        assert "llm_client_manager" in dependencies
        assert "global_config" in dependencies
        assert dependencies["llm_client_manager"] is True
        assert dependencies["global_config"] is True
    
    def test_test_agent_creation(self, legal_agent_factory):
        """Test creation of agents configured for testing."""
        agent = legal_agent_factory.create_test_agent(
            "stakeholder_identification",
            enable_strict_compliance_checks=False
        )
        
        assert isinstance(agent, StakeholderIdentificationAgent)
        assert agent.legal_config.enable_strict_compliance_checks is False
        assert agent.legal_config.audit_logging_level == "minimal"


# --- Integration Tests for StakeholderIdentificationAgent ---

class TestStakeholderIdentificationAgent:
    """Test suite for StakeholderIdentificationAgent."""
    
    @pytest.fixture
    def stakeholder_agent(self, legal_agent_factory):
        """Create a stakeholder identification agent for testing."""
        return legal_agent_factory.create_test_agent("stakeholder_identification")
    
    def test_agent_initialization(self, stakeholder_agent, stakeholder_agent_config):
        """Test agent initialization."""
        assert isinstance(stakeholder_agent, StakeholderIdentificationAgent)
        assert isinstance(stakeholder_agent.agent_config, StakeholderIdentificationAgentConfig)
    
    @pytest.mark.asyncio
    async def test_stakeholder_identification(self, stakeholder_agent, sample_stakeholder_input):
        """Test stakeholder identification functionality."""
        result = await stakeholder_agent.identify_stakeholders(sample_stakeholder_input)
        
        assert isinstance(result, StakeholderIdentificationOutputSchema)
        assert len(result.internal_stakeholders) > 0
        assert len(result.external_stakeholders) > 0
        assert result.total_stakeholders > 0
        assert len(result.decision_makers) > 0
        assert len(result.communication_plan) > 0
        assert result.analysis_summary != ""
        
        # Verify stakeholder structure
        for stakeholder in result.internal_stakeholders:
            assert stakeholder.name != ""
            assert stakeholder.role != ""
            assert stakeholder.influence_level in ["low", "medium", "high"]
            assert stakeholder.involvement_type in ["decision_maker", "collaborative", "consultative", "informational"]
    
    @pytest.mark.asyncio
    async def test_platform_inventory(self, stakeholder_agent, sample_platform_input):
        """Test platform inventory compilation."""
        result = await stakeholder_agent.compile_platform_inventory(sample_platform_input)
        
        assert isinstance(result, PlatformInventoryOutputSchema)
        assert isinstance(result.platform_summary, dict)
        assert len(result.integration_opportunities) > 0
        
        # Verify platform categorization
        total_platforms = (
            len(result.website_platforms) +
            len(result.social_media_platforms) +
            len(result.email_marketing_platforms) +
            len(result.analytics_platforms) +
            len(result.other_platforms)
        )
        assert total_platforms > 0
    
    @pytest.mark.asyncio
    async def test_compliance_integration(self, stakeholder_agent, sample_stakeholder_input):
        """Test that compliance features are integrated."""
        result = await stakeholder_agent.identify_stakeholders(sample_stakeholder_input)
        
        # Check that audit log entries were created
        audit_log = stakeholder_agent.get_audit_log()
        assert len(audit_log) > 0
        
        # Verify audit log contains expected operations
        operations = [entry.operation for entry in audit_log]
        assert "identify_stakeholders" in operations
        assert "identify_stakeholders_completed" in operations


# --- Property-Based Tests ---

class TestAgentProperties:
    """Property-based tests for consistent agent behavior."""
    
    @pytest.mark.asyncio
    async def test_stakeholder_identification_properties(self, legal_agent_factory):
        """Test that stakeholder identification always has required properties."""
        agent = legal_agent_factory.create_test_agent("stakeholder_identification")
        
        # Test with various input combinations
        test_inputs = [
            StakeholderIdentificationInputSchema(
                company_structure="Small law firm with 2 partners",
                organization_size="small"
            ),
            StakeholderIdentificationInputSchema(
                company_structure="Large corporate law firm with multiple departments",
                organization_size="large",
                industry_focus="Corporate law"
            ),
            StakeholderIdentificationInputSchema(
                company_structure="Solo practitioner with virtual assistant",
                organization_size="small",
                current_marketing_team="None"
            )
        ]
        
        for input_data in test_inputs:
            result = await agent.identify_stakeholders(input_data)
            
            # Property: Result always has required fields
            assert hasattr(result, 'internal_stakeholders')
            assert hasattr(result, 'external_stakeholders')
            assert hasattr(result, 'total_stakeholders')
            assert hasattr(result, 'analysis_summary')
            
            # Property: Total stakeholders matches actual count
            actual_total = len(result.internal_stakeholders) + len(result.external_stakeholders)
            assert result.total_stakeholders == actual_total
            
            # Property: Analysis summary is not empty
            assert result.analysis_summary != ""
            
            # Property: At least one internal stakeholder is identified
            assert len(result.internal_stakeholders) > 0


# --- Performance Tests ---

class TestAgentPerformance:
    """Performance tests for agent operations."""
    
    @pytest.mark.asyncio
    async def test_stakeholder_identification_performance(self, legal_agent_factory, sample_stakeholder_input):
        """Test stakeholder identification performance."""
        agent = legal_agent_factory.create_test_agent("stakeholder_identification")
        
        import time
        start_time = time.time()
        
        result = await agent.identify_stakeholders(sample_stakeholder_input)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertion: Should complete within reasonable time
        assert execution_time < 5.0  # 5 seconds max for test environment
        assert isinstance(result, StakeholderIdentificationOutputSchema)
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self, legal_agent_factory, sample_stakeholder_input):
        """Test concurrent agent operations."""
        agent = legal_agent_factory.create_test_agent("stakeholder_identification")
        
        # Run multiple operations concurrently
        tasks = [
            agent.identify_stakeholders(sample_stakeholder_input)
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed successfully
        assert len(results) == 3
        for result in results:
            assert isinstance(result, StakeholderIdentificationOutputSchema)
            assert result.total_stakeholders > 0


# --- Compliance Validation Tests ---

class TestComplianceValidation:
    """Tests for legal marketing compliance validation."""
    
    @pytest.mark.asyncio
    async def test_disclaimer_injection_compliance(self, legal_agent_factory):
        """Test that disclaimers are properly injected for compliance."""
        agent = legal_agent_factory.create_test_agent(
            "stakeholder_identification",
            default_jurisdiction="ON"
        )
        
        # Create mock response with marketing content
        mock_response = Mock()
        mock_response.content = "Our firm provides excellent legal services."
        
        result = await agent._inject_disclaimers(mock_response, "marketing")
        
        # Verify compliance disclaimers are present
        assert "Legal Disclaimers" in result.content
        assert "Attorney Advertising" in result.content
    
    @pytest.mark.asyncio
    async def test_compliance_threshold_enforcement(self, legal_agent_factory):
        """Test that compliance thresholds are enforced."""
        agent = legal_agent_factory.create_test_agent(
            "stakeholder_identification",
            compliance_threshold=0.9,
            enable_strict_compliance_checks=True
        )
        
        # Test content that should fail compliance
        non_compliant_content = "We guarantee you will win! Call now for limited time offer!"
        compliance_status = await agent._validate_compliance(non_compliant_content)
        
        assert compliance_status.compliance_score < 0.9
        assert not compliance_status.is_compliant
        assert len(compliance_status.violations) > 0
        assert compliance_status.review_required is True


# --- Error Handling Tests ---

class TestErrorHandling:
    """Tests for error handling in legal marketing agents."""
    
    def test_agent_factory_error_handling(self, legal_agent_factory):
        """Test error handling in agent factory."""
        # Test invalid configuration
        invalid_config = LegalMarketingAgentConfig(
            client=Mock(),
            model="gpt-4o-mini",
            compliance_threshold=1.5  # Invalid threshold > 1.0
        )
        
        with pytest.raises(AgentFactoryError):
            legal_agent_factory.create_agent("stakeholder_identification", invalid_config)
    
    @pytest.mark.asyncio
    async def test_agent_error_propagation(self, legal_agent_factory):
        """Test that agent errors are properly propagated."""
        agent = legal_agent_factory.create_test_agent("stakeholder_identification")
        
        # Test with invalid input that should cause an error
        invalid_input = StakeholderIdentificationInputSchema(
            company_structure=""  # Empty structure
        )
        
        # The agent should handle this gracefully or raise appropriate error
        try:
            result = await agent.identify_stakeholders(invalid_input)
            # If no error, verify result is still valid
            assert isinstance(result, StakeholderIdentificationOutputSchema)
        except Exception as e:
            # If error occurs, it should be a proper agent error
            assert "StakeholderIdentificationError" in str(type(e)) or "LegalMarketingAgentError" in str(type(e))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
