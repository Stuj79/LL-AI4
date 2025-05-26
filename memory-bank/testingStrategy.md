# Testing Strategy for Atomic Agents Migration

This document outlines the comprehensive testing strategy for the Legion to Atomic Agents migration project, establishing patterns, tools, and methodologies for reliable validation of migrated components.

## 1. Testing Philosophy for AI Agent Systems

### 1.1. Core Principles

**Non-Deterministic Response Handling:**
- Focus on testing output characteristics and properties rather than exact content matches
- Validate schema adherence and structural correctness
- Use mock providers for deterministic testing of agent logic
- Implement property-based testing for consistent behavior validation

**Comprehensive Coverage Strategy:**
- **Unit Tests:** Individual components in isolation (agents, tools, schemas)
- **Integration Tests:** Component interactions and workflows
- **Compatibility Tests:** Bridge adapters and data transformation accuracy
- **Performance Tests:** Baseline establishment and regression detection

**Migration-Specific Considerations:**
- Parallel testing of Legion and Atomic Agents implementations
- Functional parity validation between old and new systems
- Performance comparison against established baselines
- Bridge adapter reliability and data integrity verification

### 1.2. Testing Targets & Coverage Goals

| Test Type | Coverage Target | Focus Areas |
|-----------|----------------|-------------|
| Unit Tests | ≥85% | Schema validation, business logic, error handling |
| Integration Tests | ≥70% | Agent-tool interactions, workflow completion |
| Compatibility Tests | 100% | Bridge adapters, data transformation |
| Performance Tests | Baseline + Regression | Response time, memory usage, throughput |

## 2. Test Organization Structure

### 2.1. Directory Structure

```
llai/tests/
├── __init__.py
├── conftest.py                     # Global fixtures and configuration
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_agents/              # Agent unit tests
│   ├── test_tools/               # Tool unit tests
│   ├── test_schemas/             # Schema validation tests
│   └── test_utilities/           # Utility function tests
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_agent_workflows/     # End-to-end agent workflows
│   ├── test_tool_orchestration/  # Multi-tool interactions
│   └── test_memory_integration/  # Memory system integration
├── compatibility/                 # Migration-specific tests
│   ├── __init__.py
│   ├── test_bridge_adapters/     # Bridge adapter validation
│   ├── test_data_migration/      # Data transformation tests
│   └── test_functional_parity/   # Legion vs Atomic Agents comparison
├── performance/                   # Performance and baseline tests
│   ├── __init__.py
│   ├── legion_baselines.py       # Legacy system baselines
│   ├── atomic_benchmarks.py      # Atomic Agents performance tests
│   └── regression_tests.py       # Performance regression detection
├── mocks/                        # Mock implementations
│   ├── __init__.py
│   ├── mock_llm_providers.py     # Mock LLM clients
│   ├── mock_tools.py             # Mock tool implementations
│   └── mock_data.py              # Test data generators
├── fixtures/                     # Test fixtures and data
│   ├── __init__.py
│   ├── agent_fixtures.py         # Agent test fixtures
│   ├── tool_fixtures.py          # Tool test fixtures
│   └── data_fixtures.py          # Test data fixtures
└── atomic_patterns_examples.py   # Reference implementation examples
```

### 2.2. Test Categorization

**Unit Test Categories:**
- **Schema Tests:** BaseIOSchema validation, custom validators, serialization
- **Agent Logic Tests:** Business logic, state management, error handling
- **Tool Function Tests:** Input processing, output generation, error scenarios
- **Utility Tests:** Helper functions, data processing, configuration management

**Integration Test Categories:**
- **Agent-Tool Integration:** Agents successfully using tools
- **Workflow Tests:** Complete user workflows from input to output
- **Memory Integration:** Agent memory persistence and retrieval
- **Configuration Integration:** Environment-specific behavior validation

## 3. Testing Patterns for Atomic Agents Components

### 3.1. BaseIOSchema Testing Patterns

```python
import pytest
from pydantic import ValidationError
from llai.models.agent_models_atomic import ContentAnalysisInputSchema

class TestContentAnalysisInputSchema:
    """Test patterns for BaseIOSchema validation."""
    
    def test_valid_schema_creation(self):
        """Test successful schema creation with valid data."""
        valid_data = {
            "content": "Sample legal marketing content for analysis",
            "analysis_type": "compliance",
            "jurisdiction": "ON"
        }
        schema = ContentAnalysisInputSchema(**valid_data)
        assert schema.content == valid_data["content"]
        assert schema.analysis_type == valid_data["analysis_type"]
        assert schema.jurisdiction == valid_data["jurisdiction"]
    
    def test_schema_validation_errors(self):
        """Test schema validation with invalid data."""
        invalid_data = {
            "content": "",  # Too short
            "analysis_type": "invalid_type",
            "jurisdiction": "INVALID"
        }
        with pytest.raises(ValidationError) as exc_info:
            ContentAnalysisInputSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["field"] == "content" for error in errors)
    
    def test_schema_serialization(self):
        """Test schema serialization and deserialization."""
        original_data = {
            "content": "Test content",
            "analysis_type": "compliance",
            "jurisdiction": "ON"
        }
        schema = ContentAnalysisInputSchema(**original_data)
        
        # Test JSON serialization
        json_data = schema.model_dump()
        reconstructed = ContentAnalysisInputSchema(**json_data)
        
        assert reconstructed.content == schema.content
        assert reconstructed.analysis_type == schema.analysis_type
```

### 3.2. Agent Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock, Mock
from llai.agents.content_atomic import ContentAnalysisAgent
from llai.tests.mocks.mock_llm_providers import MockOpenAIClient

class TestContentAnalysisAgent:
    """Test patterns for Atomic Agents."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create agent with mock LLM provider."""
        config = BaseAgentConfig(
            client=MockOpenAIClient(),
            model="gpt-4",
            memory=AgentMemory()
        )
        return ContentAnalysisAgent(config)
    
    async def test_agent_successful_execution(self, mock_agent):
        """Test successful agent execution with valid input."""
        input_data = ContentAnalysisInputSchema(
            content="Sample legal content for analysis",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        # Configure mock to return valid response
        mock_agent.client.set_response({
            "compliance_status": "COMPLIANT",
            "confidence_score": 0.95,
            "violations": [],
            "recommendations": []
        })
        
        result = await mock_agent.aprocess(input_data)
        
        # Test output schema compliance
        assert isinstance(result, ContentAnalysisOutputSchema)
        assert result.compliance_status in ["COMPLIANT", "NON_COMPLIANT", "REQUIRES_REVIEW"]
        assert 0.0 <= result.confidence_score <= 1.0
        assert isinstance(result.violations, list)
    
    async def test_agent_error_handling(self, mock_agent):
        """Test agent error handling with invalid responses."""
        input_data = ContentAnalysisInputSchema(
            content="Test content",
            analysis_type="compliance",
            jurisdiction="ON"
        )
        
        # Configure mock to simulate API error
        mock_agent.client.set_error("API_ERROR", "Rate limit exceeded")
        
        with pytest.raises(AgentExecutionError) as exc_info:
            await mock_agent.aprocess(input_data)
        
        assert "Rate limit exceeded" in str(exc_info.value)
```

### 3.3. Tool Testing Patterns

```python
import pytest
from llai.tools.compliance_atomic import ComplianceCheckTool
from llai.models.tool_schemas_atomic import ComplianceCheckInputSchema

class TestComplianceCheckTool:
    """Test patterns for Atomic Tools."""
    
    @pytest.fixture
    def compliance_tool(self):
        """Create compliance check tool instance."""
        config = ComplianceToolConfig(
            jurisdiction="ON",
            rule_set="law_society_ontario"
        )
        return ComplianceCheckTool(config)
    
    def test_tool_successful_execution(self, compliance_tool):
        """Test successful tool execution."""
        input_data = ComplianceCheckInputSchema(
            content="Professional legal services provided by qualified lawyers",
            content_type="marketing_copy"
        )
        
        result = compliance_tool.run(input_data)
        
        assert isinstance(result, ComplianceCheckOutputSchema)
        assert hasattr(result, 'compliant')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'recommendations')
    
    def test_tool_validation_errors(self, compliance_tool):
        """Test tool input validation."""
        invalid_input = ComplianceCheckInputSchema(
            content="",  # Empty content should fail validation
            content_type="invalid_type"
        )
        
        with pytest.raises(ToolExecutionError):
            compliance_tool.run(invalid_input)
```

## 4. Non-Deterministic Response Testing Strategy

### 4.1. Property-Based Testing Approach

```python
from hypothesis import given, strategies as st
import pytest

class TestAgentResponseProperties:
    """Property-based tests for consistent agent behavior."""
    
    @given(
        content=st.text(min_size=50, max_size=1000),
        jurisdiction=st.sampled_from(['ON', 'BC', 'AB', 'QC'])
    )
    async def test_compliance_analysis_properties(self, content, jurisdiction):
        """Test that compliance analysis always has required properties."""
        agent = ComplianceAnalysisAgent(test_config)
        
        result = await agent.analyze_compliance(
            ComplianceInputSchema(content=content, jurisdiction=jurisdiction)
        )
        
        # Property: Result always has required fields
        assert hasattr(result, 'compliance_status')
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'violations')
        
        # Property: Confidence score is always valid
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Property: Compliance status is always valid
        assert result.compliance_status in ['COMPLIANT', 'NON_COMPLIANT', 'REQUIRES_REVIEW']
        
        # Property: If non-compliant, violations should be present
        if result.compliance_status == 'NON_COMPLIANT':
            assert len(result.violations) > 0
```

### 4.2. Output Characteristic Validation

```python
def test_agent_output_characteristics():
    """Test output characteristics rather than exact content."""
    result = await agent.process(input_data)
    
    # Test structural properties
    assert len(result.summary) >= 50  # Minimum summary length
    assert len(result.recommendations) <= 10  # Maximum recommendations
    
    # Test content properties
    assert any(keyword in result.summary.lower() for keyword in expected_keywords)
    assert result.confidence_score > 0.7  # Minimum confidence threshold
    
    # Test format properties
    assert result.created_at is not None
    assert isinstance(result.metadata, dict)
```

## 5. Mock LLM Provider Implementation

### 5.1. Mock Provider Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import json

class MockLLMProviderBase(ABC):
    """Base class for mock LLM providers."""
    
    def __init__(self):
        self.response_queue: List[Union[Dict, Exception]] = []
        self.call_history: List[Dict] = []
        self.response_patterns: Dict[str, Union[Dict, Exception]] = {}
    
    def set_response(self, response: Union[Dict, str]):
        """Set a single response for the next call."""
        if isinstance(response, str):
            response = {"content": response}
        self.response_queue.append(response)
    
    def set_response_pattern(self, pattern: str, response: Union[Dict, Exception]):
        """Set response based on input pattern matching."""
        self.response_patterns[pattern] = response
    
    def set_error(self, error_type: str, message: str):
        """Set an error to be raised on the next call."""
        error = Exception(f"{error_type}: {message}")
        self.response_queue.append(error)
    
    @abstractmethod
    def create_completion(self, **kwargs) -> Dict:
        """Create a completion response."""
        pass
```

### 5.2. OpenAI Mock Implementation

```python
class MockOpenAIClient(MockLLMProviderBase):
    """Mock OpenAI client for testing."""
    
    def __init__(self):
        super().__init__()
        self.chat = self
        self.completions = self
    
    def create(self, **kwargs) -> Dict:
        """Mock the chat.completions.create method."""
        # Record the call
        self.call_history.append({
            "method": "chat.completions.create",
            "kwargs": kwargs,
            "timestamp": datetime.utcnow()
        })
        
        # Check for pattern-based responses
        messages = kwargs.get("messages", [])
        if messages:
            user_content = messages[-1].get("content", "")
            for pattern, response in self.response_patterns.items():
                if pattern.lower() in user_content.lower():
                    if isinstance(response, Exception):
                        raise response
                    return self._format_openai_response(response)
        
        # Use queued response
        if self.response_queue:
            response = self.response_queue.pop(0)
            if isinstance(response, Exception):
                raise response
            return self._format_openai_response(response)
        
        # Default response
        return self._format_openai_response({"content": "Mock response"})
    
    def _format_openai_response(self, content: Dict) -> Dict:
        """Format response in OpenAI API format."""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps(content) if isinstance(content, dict) else content,
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
```

## 6. Performance Testing Strategy

### 6.1. Baseline Establishment

**Key Performance Indicators (KPIs):**
- End-to-end response time (wall clock)
- Peak memory usage during execution
- CPU utilization (average and peak)
- Throughput (requests per minute)

**Critical Workflows for Baseline Testing:**
1. Content Analysis Workflow (Legion)
2. Discovery Agent Execution (Legion)
3. Gap Analysis Report Generation (Legion)
4. Compliance Check Process (Legion)
5. Multi-agent Workflow Execution (Legion)

### 6.2. Performance Test Implementation

```python
import time
import psutil
import pytest
from memory_profiler import profile

class TestLegionPerformanceBaselines:
    """Establish performance baselines for Legion system."""
    
    @pytest.mark.performance
    def test_content_analysis_baseline(self):
        """Measure baseline performance for content analysis."""
        # Setup
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_time = time.time()
        
        # Execute Legion content analysis
        result = execute_legion_content_analysis(test_content)
        
        # Measure
        end_time = time.time()
        end_memory = process.memory_info().rss
        execution_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        # Record baseline
        baseline_data = {
            "workflow": "content_analysis",
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": get_environment_info()
        }
        
        save_baseline_data(baseline_data)
        
        # Assertions for regression detection
        assert execution_time < 30.0  # Maximum acceptable time
        assert memory_delta < 100 * 1024 * 1024  # Maximum 100MB increase
```

## 7. CI/CD Integration Considerations

### 7.1. Test Execution Strategy

**Fast Tests (Unit & Mock-based):**
- Run on every commit
- Complete in under 2 minutes
- Use mock LLM providers exclusively

**Integration Tests:**
- Run on pull requests
- May use real LLM providers with rate limiting
- Complete in under 10 minutes

**Performance Tests:**
- Run nightly or on release branches
- Establish and track performance trends
- Alert on significant regressions

### 7.2. Quality Gates

**Pre-commit Checks:**
- Code formatting (Black)
- Linting (Flake8)
- Type checking (MyPy)
- Fast unit tests

**Pull Request Checks:**
- Full test suite execution
- Coverage reporting
- Security scanning
- Performance regression checks

## 8. Testing Tools & Dependencies

### 8.1. Core Testing Framework
- **pytest** - Primary testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-benchmark** - Performance testing (if applicable)

### 8.2. Specialized Testing Tools
- **hypothesis** - Property-based testing
- **memory-profiler** - Memory usage profiling
- **psutil** - System resource monitoring
- **freezegun** - Time mocking for deterministic tests

### 8.3. Mock and Fixture Tools
- **unittest.mock** - Standard mocking library
- **responses** - HTTP request mocking (if needed)
- **factory_boy** - Test data generation (if applicable)

---

**Last Updated:** 2025-05-25  
**Version:** 1.0  
**Next Review:** After Week 4 completion
