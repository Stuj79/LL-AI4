"""
Atomic Agents Testing Patterns Examples

This module provides reference implementations and examples for testing
Atomic Agents components, including agents, tools, and schemas.
These examples serve as templates for the team to follow when writing tests.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from pydantic import ValidationError

# Import Atomic Agents components (these will be available once we have actual implementations)
try:
    from atomic_agents.lib.base.base_agent import BaseAgent
    from atomic_agents.lib.base.base_tool import BaseTool
    from atomic_agents.lib.base.base_io_schema import BaseIOSchema
    from atomic_agents.lib.components.agent_memory import AgentMemory
    from atomic_agents.config.base_agent_config import BaseAgentConfig
except ImportError:
    # Mock imports for development phase
    BaseAgent = object
    BaseTool = object
    BaseIOSchema = object
    AgentMemory = object
    BaseAgentConfig = object

# Import our project-specific components
from llai.models.agent_models_atomic import (
    ContentAnalysisInputSchema,
    ContentAnalysisOutputSchema
)
from llai.utils.exceptions_atomic import (
    AgentExecutionError,
    ToolExecutionError,
    ValidationError as CustomValidationError
)


# =============================================================================
# 1. BaseIOSchema Testing Patterns
# =============================================================================

class TestBaseIOSchemaPatterns:
    """
    Demonstrates testing patterns for BaseIOSchema validation and serialization.
    
    These patterns should be applied to all schema classes in the project.
    """
    
    def test_valid_schema_creation(self):
        """Test successful schema creation with valid data."""
        valid_data = {
            "content": "Sample legal marketing content for analysis",
            "analysis_type": "compliance",
            "jurisdiction": "ON",
            "priority": "high"
        }
        
        schema = ContentAnalysisInputSchema(**valid_data)
        
        # Verify all fields are set correctly
        assert schema.content == valid_data["content"]
        assert schema.analysis_type == valid_data["analysis_type"]
        assert schema.jurisdiction == valid_data["jurisdiction"]
        assert schema.priority == valid_data["priority"]
    
    def test_schema_validation_errors(self):
        """Test schema validation with invalid data."""
        invalid_data = {
            "content": "",  # Too short - should fail validation
            "analysis_type": "invalid_type",  # Not in allowed values
            "jurisdiction": "INVALID",  # Invalid jurisdiction code
            "priority": "super_urgent"  # Not in allowed priority levels
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysisInputSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        
        # Check specific validation errors
        error_fields = [error["loc"][0] for error in errors]
        assert "content" in error_fields
        assert "analysis_type" in error_fields
    
    def test_schema_serialization_roundtrip(self):
        """Test schema serialization and deserialization."""
        original_data = {
            "content": "Test legal content for compliance analysis",
            "analysis_type": "compliance",
            "jurisdiction": "ON",
            "priority": "medium"
        }
        
        # Create schema instance
        schema = ContentAnalysisInputSchema(**original_data)
        
        # Test JSON serialization
        json_data = schema.model_dump()
        reconstructed = ContentAnalysisInputSchema(**json_data)
        
        # Verify data integrity
        assert reconstructed.content == schema.content
        assert reconstructed.analysis_type == schema.analysis_type
        assert reconstructed.jurisdiction == schema.jurisdiction
        assert reconstructed.priority == schema.priority
    
    def test_schema_field_descriptions(self):
        """Test that all schema fields have proper descriptions."""
        schema_fields = ContentAnalysisInputSchema.model_fields
        
        for field_name, field_info in schema_fields.items():
            assert field_info.description is not None, f"Field '{field_name}' missing description"
            assert len(field_info.description) > 10, f"Field '{field_name}' description too short"
    
    def test_schema_custom_validators(self):
        """Test custom validation logic in schemas."""
        # Test content length validation
        with pytest.raises(ValidationError):
            ContentAnalysisInputSchema(
                content="x" * 10001,  # Exceeds maximum length
                analysis_type="compliance",
                jurisdiction="ON"
            )
        
        # Test jurisdiction validation
        with pytest.raises(ValidationError):
            ContentAnalysisInputSchema(
                content="Valid content for testing",
                analysis_type="compliance",
                jurisdiction="XX"  # Invalid jurisdiction
            )


# =============================================================================
# 2. Mock Agent Testing Patterns
# =============================================================================

class MockContentAnalysisAgent:
    """
    Mock agent for testing purposes.
    
    This demonstrates how to create testable agent implementations
    that follow Atomic Agents patterns.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = config.get("client")
        self.model = config.get("model", "gpt-4")
        self.memory = config.get("memory", {})
        self.call_history = []
    
    async def aprocess(self, input_data: ContentAnalysisInputSchema) -> ContentAnalysisOutputSchema:
        """Process input and return analysis results."""
        # Record the call for testing
        self.call_history.append({
            "input": input_data.model_dump(),
            "timestamp": datetime.utcnow()
        })
        
        # Simulate processing based on mock client response
        if hasattr(self.client, 'get_next_response'):
            response_data = self.client.get_next_response()
            if isinstance(response_data, Exception):
                raise response_data
        else:
            # Default mock response
            response_data = {
                "compliance_status": "COMPLIANT",
                "confidence_score": 0.95,
                "violations": [],
                "recommendations": [],
                "analysis_summary": f"Analysis completed for: {input_data.content[:50]}..."
            }
        
        return ContentAnalysisOutputSchema(**response_data)


class TestAgentPatterns:
    """
    Demonstrates testing patterns for Atomic Agents.
    
    These patterns handle the async nature of agents and provide
    strategies for testing non-deterministic LLM responses.
    """
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client for testing."""
        client = Mock()
        client.response_queue = []
        client.error_queue = []
        
        def get_next_response():
            if client.error_queue:
                return client.error_queue.pop(0)
            if client.response_queue:
                return client.response_queue.pop(0)
            return {
                "compliance_status": "COMPLIANT",
                "confidence_score": 0.8,
                "violations": [],
                "recommendations": []
            }
        
        client.get_next_response = get_next_response
        return client
    
    @pytest.fixture
    def mock_agent(self, mock_llm_client):
        """Create agent with mock LLM provider."""
        config = {
            "client": mock_llm_client,
            "model": "gpt-4",
            "memory": AgentMemory() if AgentMemory != object else {}
        }
        return MockContentAnalysisAgent(config)
    
    @pytest.mark.asyncio
    async def test_agent_successful_execution(self, mock_agent, mock_llm_client):
        """Test successful agent execution with valid input."""
        # Setup mock response
        mock_llm_client.response_queue.append({
            "compliance_status": "NON_COMPLIANT",
            "confidence_score": 0.92,
            "violations": [
                {
                    "rule_id": "LSO_7.04",
                    "description": "Use of 'guarantee' in legal marketing",
                    "severity": "high"
                }
            ],
            "recommendations": [
                "Remove guarantee language",
                "Add appropriate disclaimers"
            ],
            "analysis_summary": "Content contains prohibited guarantee language"
        })
        
        input_data = ContentAnalysisInputSchema(
            content="We guarantee the best legal results for your case",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        result = await mock_agent.aprocess(input_data)
        
        # Test output schema compliance
        assert isinstance(result, ContentAnalysisOutputSchema)
        assert result.compliance_status in ["COMPLIANT", "NON_COMPLIANT", "REQUIRES_REVIEW"]
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.violations, list)
        assert isinstance(result.recommendations, list)
        
        # Test specific business logic
        assert result.compliance_status == "NON_COMPLIANT"
        assert len(result.violations) > 0
        assert "guarantee" in result.violations[0]["description"].lower()
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_agent, mock_llm_client):
        """Test agent error handling with API failures."""
        # Setup mock to raise an error
        mock_llm_client.error_queue.append(
            AgentExecutionError("API rate limit exceeded")
        )
        
        input_data = ContentAnalysisInputSchema(
            content="Test content for error handling",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        with pytest.raises(AgentExecutionError) as exc_info:
            await mock_agent.aprocess(input_data)
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_agent_output_characteristics(self, mock_agent):
        """Test output characteristics rather than exact content."""
        input_data = ContentAnalysisInputSchema(
            content="Professional legal services provided by experienced attorneys",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        result = await mock_agent.aprocess(input_data)
        
        # Test structural properties
        assert hasattr(result, 'compliance_status')
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'recommendations')
        
        # Test value constraints
        assert result.confidence_score >= 0.0
        assert result.confidence_score <= 1.0
        assert isinstance(result.violations, list)
        assert isinstance(result.recommendations, list)
        
        # Test business logic properties
        if result.compliance_status == "NON_COMPLIANT":
            assert len(result.violations) > 0
        
        if len(result.violations) > 0:
            for violation in result.violations:
                assert "rule_id" in violation
                assert "description" in violation
    
    @pytest.mark.asyncio
    async def test_agent_call_history_tracking(self, mock_agent):
        """Test that agent calls are properly tracked for debugging."""
        input_data = ContentAnalysisInputSchema(
            content="Test content",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        initial_call_count = len(mock_agent.call_history)
        await mock_agent.aprocess(input_data)
        
        assert len(mock_agent.call_history) == initial_call_count + 1
        
        last_call = mock_agent.call_history[-1]
        assert "input" in last_call
        assert "timestamp" in last_call
        assert last_call["input"]["content"] == input_data.content


# =============================================================================
# 3. Mock Tool Testing Patterns
# =============================================================================

class MockComplianceCheckTool:
    """
    Mock tool for testing purposes.
    
    Demonstrates how to create testable tool implementations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jurisdiction = config.get("jurisdiction", "ON")
        self.rule_set = config.get("rule_set", "law_society_ontario")
        self.call_history = []
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the compliance check tool."""
        # Record the call
        self.call_history.append({
            "input": input_data,
            "timestamp": datetime.utcnow()
        })
        
        content = input_data.get("content", "")
        
        # Simple mock compliance logic
        violations = []
        if "guarantee" in content.lower():
            violations.append({
                "rule_id": "LSO_7.04",
                "description": "Use of guarantee language prohibited",
                "severity": "high"
            })
        
        if "best lawyer" in content.lower():
            violations.append({
                "rule_id": "LSO_7.02",
                "description": "Superlative claims require substantiation",
                "severity": "medium"
            })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "recommendations": [
                "Remove guarantee language" if any("guarantee" in v["description"] for v in violations) else None,
                "Substantiate superlative claims" if any("superlative" in v["description"] for v in violations) else None
            ],
            "confidence_score": 0.95 if len(violations) == 0 else 0.85
        }


class TestToolPatterns:
    """
    Demonstrates testing patterns for Atomic Tools.
    
    These patterns focus on input validation, output verification,
    and error handling for tool implementations.
    """
    
    @pytest.fixture
    def compliance_tool(self):
        """Create compliance check tool instance."""
        config = {
            "jurisdiction": "ON",
            "rule_set": "law_society_ontario"
        }
        return MockComplianceCheckTool(config)
    
    def test_tool_successful_execution(self, compliance_tool):
        """Test successful tool execution with compliant content."""
        input_data = {
            "content": "Professional legal services provided by qualified lawyers",
            "content_type": "marketing_copy"
        }
        
        result = compliance_tool.run(input_data)
        
        # Test output structure
        assert isinstance(result, dict)
        assert "compliant" in result
        assert "violations" in result
        assert "recommendations" in result
        assert "confidence_score" in result
        
        # Test business logic
        assert result["compliant"] is True
        assert len(result["violations"]) == 0
        assert 0.0 <= result["confidence_score"] <= 1.0
    
    def test_tool_violation_detection(self, compliance_tool):
        """Test tool's ability to detect compliance violations."""
        input_data = {
            "content": "We guarantee the best legal results in the city",
            "content_type": "marketing_copy"
        }
        
        result = compliance_tool.run(input_data)
        
        # Test violation detection
        assert result["compliant"] is False
        assert len(result["violations"]) > 0
        
        # Test specific violations
        violation_descriptions = [v["description"].lower() for v in result["violations"]]
        assert any("guarantee" in desc for desc in violation_descriptions)
        
        # Test recommendations are provided
        recommendations = [r for r in result["recommendations"] if r is not None]
        assert len(recommendations) > 0
    
    def test_tool_input_validation(self, compliance_tool):
        """Test tool input validation and error handling."""
        # Test with missing required fields
        invalid_input = {}
        
        try:
            result = compliance_tool.run(invalid_input)
            # Tool should handle gracefully or raise appropriate error
            assert "content" in str(result).lower() or "error" in str(result).lower()
        except (KeyError, ValueError, ToolExecutionError):
            # Expected behavior for invalid input
            pass
    
    def test_tool_call_history(self, compliance_tool):
        """Test that tool calls are tracked for debugging."""
        input_data = {
            "content": "Test content",
            "content_type": "marketing_copy"
        }
        
        initial_call_count = len(compliance_tool.call_history)
        compliance_tool.run(input_data)
        
        assert len(compliance_tool.call_history) == initial_call_count + 1
        
        last_call = compliance_tool.call_history[-1]
        assert "input" in last_call
        assert "timestamp" in last_call


# =============================================================================
# 4. Property-Based Testing Examples
# =============================================================================

try:
    from hypothesis import given, strategies as st
    
    class TestPropertyBasedPatterns:
        """
        Demonstrates property-based testing for AI agent systems.
        
        These tests verify that agents consistently exhibit desired
        characteristics regardless of specific input variations.
        """
        
        @given(
            content=st.text(min_size=50, max_size=1000),
            jurisdiction=st.sampled_from(['ON', 'BC', 'AB', 'QC'])
        )
        @pytest.mark.asyncio
        async def test_compliance_analysis_properties(self, content, jurisdiction):
            """Test that compliance analysis always has required properties."""
            # Setup mock agent
            mock_client = Mock()
            mock_client.get_next_response = lambda: {
                "compliance_status": "COMPLIANT",
                "confidence_score": 0.8,
                "violations": [],
                "recommendations": []
            }
            
            agent = MockContentAnalysisAgent({
                "client": mock_client,
                "model": "gpt-4"
            })
            
            input_schema = ContentAnalysisInputSchema(
                content=content,
                analysis_type="compliance",
                jurisdiction=jurisdiction
            )
            
            result = await agent.aprocess(input_schema)
            
            # Property: Result always has required fields
            assert hasattr(result, 'compliance_status')
            assert hasattr(result, 'confidence_score')
            assert hasattr(result, 'violations')
            
            # Property: Confidence score is always valid
            assert 0.0 <= result.confidence_score <= 1.0
            
            # Property: Compliance status is always valid
            assert result.compliance_status in ['COMPLIANT', 'NON_COMPLIANT', 'REQUIRES_REVIEW']
            
            # Property: Violations list is always present (even if empty)
            assert isinstance(result.violations, list)
        
        @given(
            content=st.text(min_size=10, max_size=500),
            content_type=st.sampled_from(['marketing_copy', 'website_content', 'advertisement'])
        )
        def test_tool_output_properties(self, content, content_type):
            """Test that tool outputs always have consistent properties."""
            tool = MockComplianceCheckTool({
                "jurisdiction": "ON",
                "rule_set": "law_society_ontario"
            })
            
            input_data = {
                "content": content,
                "content_type": content_type
            }
            
            result = tool.run(input_data)
            
            # Property: Result always has required structure
            assert isinstance(result, dict)
            assert "compliant" in result
            assert "violations" in result
            assert "confidence_score" in result
            
            # Property: Confidence score is always valid
            assert 0.0 <= result["confidence_score"] <= 1.0
            
            # Property: Violations is always a list
            assert isinstance(result["violations"], list)
            
            # Property: If non-compliant, violations should be present
            if not result["compliant"]:
                assert len(result["violations"]) > 0

except ImportError:
    # Hypothesis not available - skip property-based tests
    class TestPropertyBasedPatterns:
        """Property-based testing requires hypothesis package."""
        
        def test_hypothesis_not_available(self):
            """Placeholder test when hypothesis is not installed."""
            pytest.skip("Hypothesis package not available for property-based testing")


# =============================================================================
# 5. Performance Testing Patterns
# =============================================================================

class TestPerformancePatterns:
    """
    Demonstrates performance testing patterns for AI agent systems.
    
    These patterns establish baselines and detect performance regressions.
    """
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_agent_response_time(self):
        """Test agent response time stays within acceptable limits."""
        import time
        
        mock_client = Mock()
        mock_client.get_next_response = lambda: {
            "compliance_status": "COMPLIANT",
            "confidence_score": 0.9,
            "violations": [],
            "recommendations": []
        }
        
        agent = MockContentAnalysisAgent({
            "client": mock_client,
            "model": "gpt-4"
        })
        
        input_data = ContentAnalysisInputSchema(
            content="Test content for performance measurement",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        start_time = time.time()
        result = await agent.aprocess(input_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert reasonable response time (adjust based on requirements)
        assert execution_time < 5.0, f"Agent took too long: {execution_time:.2f}s"
        assert isinstance(result, ContentAnalysisOutputSchema)
    
    @pytest.mark.performance
    def test_tool_throughput(self):
        """Test tool can handle multiple requests efficiently."""
        import time
        
        tool = MockComplianceCheckTool({
            "jurisdiction": "ON",
            "rule_set": "law_society_ontario"
        })
        
        test_inputs = [
            {"content": f"Test content {i}", "content_type": "marketing_copy"}
            for i in range(10)
        ]
        
        start_time = time.time()
        results = [tool.run(input_data) for input_data in test_inputs]
        end_time = time.time()
        
        total_time = end_time - start_time
        throughput = len(test_inputs) / total_time
        
        # Assert reasonable throughput
        assert throughput > 5.0, f"Tool throughput too low: {throughput:.2f} requests/second"
        assert len(results) == len(test_inputs)
        assert all(isinstance(result, dict) for result in results)


# =============================================================================
# 6. Integration Testing Patterns
# =============================================================================

class TestIntegrationPatterns:
    """
    Demonstrates integration testing patterns for agent-tool interactions.
    
    These patterns test complete workflows and component interactions.
    """
    
    @pytest.mark.asyncio
    async def test_agent_tool_integration(self):
        """Test agent successfully using a tool."""
        # Setup mock tool
        compliance_tool = MockComplianceCheckTool({
            "jurisdiction": "ON",
            "rule_set": "law_society_ontario"
        })
        
        # Setup mock agent with tool access
        mock_client = Mock()
        mock_client.get_next_response = lambda: {
            "compliance_status": "NON_COMPLIANT",
            "confidence_score": 0.85,
            "violations": [{"rule_id": "LSO_7.04", "description": "Guarantee language"}],
            "recommendations": ["Remove guarantee language"]
        }
        
        agent = MockContentAnalysisAgent({
            "client": mock_client,
            "model": "gpt-4",
            "tools": [compliance_tool]
        })
        
        input_data = ContentAnalysisInputSchema(
            content="We guarantee the best legal outcomes",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        result = await agent.aprocess(input_data)
        
        # Test integration success
        assert isinstance(result, ContentAnalysisOutputSchema)
        assert result.compliance_status == "NON_COMPLIANT"
        assert len(result.violations) > 0
        
        # Verify tool was called (if agent uses tools)
        if hasattr(agent, 'tools') and agent.tools:
            assert len(compliance_tool.call_history) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_end_to_end(self):
        """Test complete user workflow from input to output."""
        # This would test a complete user workflow
        # For now, we'll test a simplified version
        
        input_data = ContentAnalysisInputSchema(
            content="Professional legal services with experienced attorneys",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        # Step 1: Content analysis
        mock_client = Mock()
        mock_client.get_next_response = lambda: {
            "compliance_status": "COMPLIANT",
            "confidence_score": 0.95,
            "violations": [],
            "recommendations": []
        }
        
        agent = MockContentAnalysisAgent({
            "client": mock_client,
            "model": "gpt-4"
        })
        
        analysis_result = await agent.aprocess(input_data)
        
        # Step 2: Verify workflow completion
        assert analysis_result.compliance_status == "COMPLIANT"
        assert analysis_result.confidence_score > 0.9
        assert len(analysis_result.violations) == 0
        
        # Step 3: Verify agent state
        assert len(agent.call_history) == 1


if __name__ == "__main__":
    # Run the examples as a test suite
    pytest.main([__file__, "-v"])
