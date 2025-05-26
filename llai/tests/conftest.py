"""
Pytest configuration and fixtures for LL-AI testing infrastructure.

This module provides global fixtures and configuration for the test suite,
including mock LLM providers, test data, and common setup/teardown operations.
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Import our mock providers
from llai.tests.mocks.mock_llm_providers import (
    MockOpenAIClient,
    MockAnthropicClient,
    MockLLMProviderFactory,
    create_mock_openai_client,
    create_mock_anthropic_client,
    create_compliance_mock_client
)

# Import project components
try:
    from llai.models.agent_models_atomic import (
        ContentAnalysisInputSchema,
        ContentAnalysisOutputSchema
    )
    from llai.utils.exceptions_atomic import (
        AgentExecutionError,
        ToolExecutionError,
        ValidationError as CustomValidationError
    )
    from llai.config.settings import get_config
except ImportError:
    # Handle cases where components aren't available yet
    ContentAnalysisInputSchema = None
    ContentAnalysisOutputSchema = None
    AgentExecutionError = Exception
    ToolExecutionError = Exception
    CustomValidationError = Exception
    get_config = None


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "compatibility: mark test as compatibility test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test file location
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "compatibility" in str(item.fspath):
            item.add_marker(pytest.mark.compatibility)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# =============================================================================
# Event Loop Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Mock LLM Provider Fixtures
# =============================================================================

@pytest.fixture
def mock_openai_client():
    """Provide a basic mock OpenAI client."""
    return create_mock_openai_client()


@pytest.fixture
def mock_anthropic_client():
    """Provide a basic mock Anthropic client."""
    return create_mock_anthropic_client()


@pytest.fixture
def compliance_mock_client():
    """Provide a mock client configured for compliance testing."""
    return create_compliance_mock_client()


@pytest.fixture
def mock_openai_with_responses():
    """Provide a mock OpenAI client factory for custom responses."""
    def _create_client(responses: List[Dict] = None, patterns: Dict = None):
        return MockLLMProviderFactory.create_openai_mock(
            responses=responses,
            patterns=patterns
        )
    return _create_client


@pytest.fixture
def mock_anthropic_with_responses():
    """Provide a mock Anthropic client factory for custom responses."""
    def _create_client(responses: List[Dict] = None, patterns: Dict = None):
        return MockLLMProviderFactory.create_anthropic_mock(
            responses=responses,
            patterns=patterns
        )
    return _create_client


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_legal_content():
    """Provide sample legal marketing content for testing."""
    return {
        "compliant_content": """
        Smith & Associates Law Firm provides comprehensive legal services to businesses 
        and individuals throughout Ontario. Our experienced team of lawyers specializes 
        in corporate law, real estate transactions, and litigation support. We are 
        committed to delivering exceptional results for our clients through personalized 
        attention and strategic legal counsel.
        """,
        "non_compliant_content": """
        We guarantee the best legal results in the city! Our lawyers never lose a case 
        and we promise 100% success for all our clients. Choose us for guaranteed 
        victory in your legal matters.
        """,
        "borderline_content": """
        Our law firm has achieved excellent results for many clients over the years. 
        We strive to provide the highest quality legal representation and work 
        diligently to achieve favorable outcomes. Past results do not guarantee 
        future performance.
        """
    }


@pytest.fixture
def sample_content_analysis_input():
    """Provide sample input data for content analysis testing."""
    if ContentAnalysisInputSchema is None:
        return {
            "content": "Sample legal content for analysis",
            "analysis_type": "compliance",
            "jurisdiction": "ON",
            "priority": "medium"
        }
    
    return ContentAnalysisInputSchema(
        content="Sample legal content for analysis",
        analysis_type="compliance",
        jurisdiction="ON",
        priority="medium"
    )


@pytest.fixture
def sample_content_analysis_output():
    """Provide sample output data for content analysis testing."""
    return {
        "compliance_status": "COMPLIANT",
        "confidence_score": 0.95,
        "violations": [],
        "recommendations": [],
        "analysis_summary": "Content appears to comply with legal marketing regulations."
    }


@pytest.fixture
def sample_stakeholder_data():
    """Provide sample stakeholder data for discovery testing."""
    return {
        "organization": "Smith & Associates Law Firm",
        "industry": "Legal Services",
        "size": "Medium",
        "location": "Toronto, ON",
        "practice_areas": ["Corporate Law", "Real Estate", "Litigation"],
        "target_audience": ["Small Businesses", "Individual Clients"],
        "current_marketing": ["Website", "LinkedIn", "Legal Directory"]
    }


@pytest.fixture
def sample_gap_analysis_data():
    """Provide sample gap analysis data for testing."""
    return {
        "content_gaps": [
            {
                "category": "Employment Law",
                "gap_type": "Missing Content",
                "priority": "High",
                "description": "No content found for employment law services"
            },
            {
                "category": "Estate Planning",
                "gap_type": "Outdated Content",
                "priority": "Medium",
                "description": "Estate planning content is over 2 years old"
            }
        ],
        "competitive_analysis": {
            "competitors_analyzed": 5,
            "content_volume_comparison": "Below average",
            "quality_comparison": "Above average"
        },
        "recommendations": [
            "Create comprehensive employment law content",
            "Update estate planning materials",
            "Increase overall content volume"
        ]
    }


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def test_config():
    """Provide test configuration settings."""
    return {
        "llm_provider": "openai",
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 30,
        "retry_attempts": 3,
        "log_level": "DEBUG",
        "enable_mock_responses": True
    }


@pytest.fixture
def mock_environment_variables():
    """Provide mock environment variables for testing."""
    mock_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "test",
        "MOCK_LLM_RESPONSES": "true"
    }
    
    with patch.dict(os.environ, mock_env):
        yield mock_env


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture
def temp_directory():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_data_directory():
    """Provide path to test data directory."""
    test_dir = Path(__file__).parent / "fixtures" / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def performance_baseline_directory():
    """Provide path to performance baseline directory."""
    baseline_dir = Path("memory-bank/performance_baselines")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    return baseline_dir


# =============================================================================
# Agent and Tool Fixtures
# =============================================================================

@pytest.fixture
def mock_agent_config(mock_openai_client):
    """Provide mock agent configuration."""
    return {
        "client": mock_openai_client,
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.7,
        "memory": {},
        "tools": []
    }


@pytest.fixture
def mock_tool_config():
    """Provide mock tool configuration."""
    return {
        "jurisdiction": "ON",
        "rule_set": "law_society_ontario",
        "timeout": 30,
        "retry_attempts": 3
    }


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_thresholds():
    """Provide performance threshold values for testing."""
    return {
        "max_response_time": 30.0,  # seconds
        "max_memory_delta": 100 * 1024 * 1024,  # 100MB
        "min_throughput": 5.0,  # requests per second
        "max_cpu_percent": 80.0  # percentage
    }


@pytest.fixture
def baseline_metrics():
    """Provide baseline performance metrics for comparison."""
    return {
        "content_analysis": {
            "execution_time": 2.5,
            "memory_delta": 50 * 1024 * 1024,
            "cpu_percent": 25.0
        },
        "discovery_agent": {
            "execution_time": 1.2,
            "memory_delta": 25 * 1024 * 1024,
            "cpu_percent": 15.0
        },
        "gap_analysis": {
            "execution_time": 5.8,
            "memory_delta": 75 * 1024 * 1024,
            "cpu_percent": 35.0
        }
    }


# =============================================================================
# Error Simulation Fixtures
# =============================================================================

@pytest.fixture
def api_error_scenarios():
    """Provide common API error scenarios for testing."""
    return {
        "rate_limit": {
            "error_type": "RATE_LIMIT_ERROR",
            "message": "Rate limit exceeded. Please try again later.",
            "status_code": 429
        },
        "api_error": {
            "error_type": "API_ERROR",
            "message": "Internal server error",
            "status_code": 500
        },
        "timeout": {
            "error_type": "TIMEOUT_ERROR",
            "message": "Request timed out",
            "status_code": 408
        },
        "invalid_key": {
            "error_type": "AUTHENTICATION_ERROR",
            "message": "Invalid API key",
            "status_code": 401
        }
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Automatically clean up test artifacts after each test."""
    yield
    
    # Clean up any temporary files or state
    # This runs after each test
    pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment at the beginning of the test session."""
    # Ensure test directories exist
    test_dirs = [
        "memory-bank/performance_baselines",
        "llai/tests/fixtures/test_data"
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Session cleanup if needed
    pass


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def assert_performance():
    """Provide utility function for performance assertions."""
    def _assert_performance(actual_time: float, baseline_time: float, tolerance: float = 0.5):
        """
        Assert that actual performance is within tolerance of baseline.
        
        Args:
            actual_time: Actual execution time
            baseline_time: Baseline execution time
            tolerance: Tolerance factor (0.5 = 50% slower is acceptable)
        """
        max_acceptable_time = baseline_time * (1 + tolerance)
        assert actual_time <= max_acceptable_time, (
            f"Performance regression detected: {actual_time:.2f}s > {max_acceptable_time:.2f}s "
            f"(baseline: {baseline_time:.2f}s, tolerance: {tolerance*100}%)"
        )
    
    return _assert_performance


@pytest.fixture
def assert_schema_compliance():
    """Provide utility function for schema compliance assertions."""
    def _assert_schema_compliance(data: Dict, schema_class):
        """
        Assert that data complies with the given schema.
        
        Args:
            data: Data to validate
            schema_class: Schema class to validate against
        """
        if schema_class is None:
            # Skip validation if schema class not available
            return True
        
        try:
            validated = schema_class(**data)
            return True
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    return _assert_schema_compliance


# =============================================================================
# Parametrized Fixtures
# =============================================================================

@pytest.fixture(params=["openai", "anthropic"])
def llm_provider_type(request):
    """Parametrized fixture for testing with different LLM providers."""
    return request.param


@pytest.fixture(params=["ON", "BC", "AB", "QC"])
def canadian_jurisdiction(request):
    """Parametrized fixture for testing with different Canadian jurisdictions."""
    return request.param


@pytest.fixture(params=["compliance", "quality", "seo", "readability"])
def analysis_type(request):
    """Parametrized fixture for testing with different analysis types."""
    return request.param
