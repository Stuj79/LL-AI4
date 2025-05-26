"""
Tests for Week 3 utilities: error handling, JSON utilities, and logging infrastructure.
This validates that the new Atomic Agents aligned utilities work correctly.
"""

import pytest
import json
import logging
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

# Import the utilities we're testing
from llai.utils.exceptions_atomic import (
    ErrorContext,
    AppBaseException,
    LLMResponseError,
    ToolExecutionError,
    ConfigurationError,
    SchemaValidationError,
    JSONParsingError,
    APIError,
    AtomicException,
    AtomicLLMResponseError,
    AtomicToolExecutionError,
    AtomicConfigurationError,
    AtomicSchemaValidationError,
    AtomicJSONParsingError,
    AtomicAPIError,
    create_error_context,
    handle_validation_error,
    handle_llm_response_error,
    handle_tool_execution_error,
    handle_json_parsing_error,
    handle_configuration_error,
    handle_api_error,
    is_atomic_error,
    extract_user_message
)

from llai.utils.json_utils_atomic import (
    parse_json_response_atomic,
    parse_json_response_atomic_safe,
    extract_json_from_text_atomic,
    safe_get_atomic,
    format_for_prompt_atomic,
    merge_schema_results,
    process_agent_response_atomic,
    validate_json_string,
    create_error_response_schema
)

from llai.utils.logging_setup import (
    setup_logging,
    get_logger,
    setup_module_logger,
    create_context_logger,
    log_function_entry,
    log_function_exit,
    log_performance,
    logged_function
)

# Import test schemas
from llai.models.agent_responses_atomic import CatalogContentItem, CatalogContentResponse
from llai.config.settings import LoggingConfig

class TestErrorHandling:
    """Test suite for atomic error handling."""
    
    def test_error_context_creation(self):
        """Test ErrorContext creation and validation."""
        context = create_error_context(
            operation="test_operation",
            component="test_component",
            extra_info="test_value"
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.additional_info["extra_info"] == "test_value"
    
    def test_app_base_exception_schema(self):
        """Test AppBaseException schema validation."""
        from datetime import datetime
        
        context = create_error_context("test", "test")
        
        error_schema = AppBaseException(
            error_type="TestError",
            message="Test error message",
            context=context,
            timestamp=datetime.now().isoformat(),
            severity="error",
            recoverable=True,
            user_message="User-friendly message"
        )
        
        assert error_schema.error_type == "TestError"
        assert error_schema.message == "Test error message"
        assert error_schema.severity == "error"
        assert error_schema.recoverable == True
        assert error_schema.user_message == "User-friendly message"
    
    def test_llm_response_error_schema(self):
        """Test LLMResponseError schema."""
        from datetime import datetime
        
        context = create_error_context("llm_call", "agent")
        
        error_schema = LLMResponseError(
            message="LLM failed to respond",
            context=context,
            timestamp=datetime.now().isoformat(),
            provider="openai",
            model="gpt-4",
            raw_response="Invalid response",
            token_count=150
        )
        
        assert error_schema.error_type == "LLMResponseError"
        assert error_schema.provider == "openai"
        assert error_schema.model == "gpt-4"
        assert error_schema.token_count == 150
    
    def test_atomic_exception_wrapper(self):
        """Test AtomicException wrapper functionality."""
        from datetime import datetime
        
        context = create_error_context("test", "test")
        error_schema = AppBaseException(
            error_type="TestError",
            message="Test message",
            context=context,
            timestamp=datetime.now().isoformat()
        )
        
        exception = AtomicException(error_schema)
        
        assert str(exception) == "Test message"
        assert exception.error_schema.error_type == "TestError"
        
        # Test serialization
        error_dict = exception.to_dict()
        assert error_dict["error_type"] == "TestError"
        assert error_dict["message"] == "Test message"
        
        error_json = exception.to_json()
        assert isinstance(error_json, str)
        parsed = json.loads(error_json)
        assert parsed["error_type"] == "TestError"
    
    def test_handle_validation_error(self):
        """Test Pydantic validation error handling."""
        # Create invalid data for CatalogContentItem
        invalid_data = {"title": 123}  # title should be string or None
        
        try:
            CatalogContentItem.model_validate(invalid_data)
        except ValidationError as e:
            context = create_error_context("validation", "test")
            atomic_error = handle_validation_error(e, "CatalogContentItem", invalid_data, context)
            
            assert isinstance(atomic_error, AtomicSchemaValidationError)
            assert atomic_error.error_schema.schema_name == "CatalogContentItem"
            assert len(atomic_error.error_schema.validation_errors) > 0
            assert atomic_error.error_schema.raw_data == invalid_data
    
    def test_handle_llm_response_error(self):
        """Test LLM response error handling."""
        original_error = Exception("Connection timeout")
        context = create_error_context("llm_call", "agent")
        
        atomic_error = handle_llm_response_error(
            original_error, "openai", "gpt-4", context, "partial response"
        )
        
        assert isinstance(atomic_error, AtomicLLMResponseError)
        assert atomic_error.error_schema.provider == "openai"
        assert atomic_error.error_schema.model == "gpt-4"
        assert atomic_error.error_schema.raw_response == "partial response"
        assert "Connection timeout" in atomic_error.error_schema.message
    
    def test_handle_tool_execution_error(self):
        """Test tool execution error handling."""
        original_error = Exception("Tool failed")
        context = create_error_context("tool_execution", "agent")
        tool_input = {"param1": "value1"}
        
        atomic_error = handle_tool_execution_error(
            original_error, "test_tool", tool_input, context, 2.5
        )
        
        assert isinstance(atomic_error, AtomicToolExecutionError)
        assert atomic_error.error_schema.tool_name == "test_tool"
        assert atomic_error.error_schema.tool_input == tool_input
        assert atomic_error.error_schema.execution_time == 2.5
    
    def test_handle_json_parsing_error(self):
        """Test JSON parsing error handling."""
        json_error = json.JSONDecodeError("Invalid JSON", "bad json", 5)
        context = create_error_context("json_parsing", "utils")
        
        atomic_error = handle_json_parsing_error(json_error, "bad json", context)
        
        assert isinstance(atomic_error, AtomicJSONParsingError)
        assert atomic_error.error_schema.raw_response == "bad json"
        assert atomic_error.error_schema.parse_position == 5
    
    def test_is_atomic_error(self):
        """Test atomic error detection."""
        from datetime import datetime
        
        context = create_error_context("test", "test")
        error_schema = AppBaseException(
            error_type="TestError",
            message="Test",
            context=context,
            timestamp=datetime.now().isoformat()
        )
        
        atomic_error = AtomicException(error_schema)
        regular_error = Exception("Regular error")
        
        assert is_atomic_error(atomic_error) == True
        assert is_atomic_error(regular_error) == False
    
    def test_extract_user_message(self):
        """Test user message extraction."""
        from datetime import datetime
        
        context = create_error_context("test", "test")
        error_schema = AppBaseException(
            error_type="TestError",
            message="Technical message",
            context=context,
            timestamp=datetime.now().isoformat(),
            user_message="User-friendly message"
        )
        
        atomic_error = AtomicException(error_schema)
        regular_error = Exception("Regular error")
        
        assert extract_user_message(atomic_error) == "User-friendly message"
        assert "Regular error" in extract_user_message(regular_error)

class TestJSONUtilities:
    """Test suite for atomic JSON utilities."""
    
    def test_parse_json_response_atomic_success(self):
        """Test successful JSON parsing with schema validation."""
        json_data = {
            "title": "Test Article",
            "type": "article",
            "platform": "website"
        }
        json_string = json.dumps(json_data)
        
        result = parse_json_response_atomic(json_string, CatalogContentItem)
        
        assert isinstance(result, CatalogContentItem)
        assert result.title == "Test Article"
        assert result.type == "article"
        assert result.platform == "website"
    
    def test_parse_json_response_atomic_json_error(self):
        """Test JSON parsing error handling."""
        invalid_json = "{ invalid json"
        
        with pytest.raises(AtomicJSONParsingError):
            parse_json_response_atomic(invalid_json, CatalogContentItem)
    
    def test_parse_json_response_atomic_validation_error(self):
        """Test schema validation error handling."""
        # Valid JSON but invalid for schema
        json_data = {"title": 123}  # title should be string or None
        json_string = json.dumps(json_data)
        
        with pytest.raises(AtomicSchemaValidationError):
            parse_json_response_atomic(json_string, CatalogContentItem)
    
    def test_parse_json_response_atomic_safe(self):
        """Test safe parsing that returns error dict instead of raising."""
        invalid_json = "{ invalid json"
        
        result = parse_json_response_atomic_safe(invalid_json, CatalogContentItem)
        
        assert isinstance(result, dict)
        assert result["error_type"] == "JSONParsingError"
        assert "raw_response" in result
    
    def test_extract_json_from_text_atomic(self):
        """Test JSON extraction from mixed text."""
        mixed_text = 'Here is some text {"title": "Extracted", "type": "article"} and more text'
        
        result = extract_json_from_text_atomic(mixed_text, CatalogContentItem)
        
        assert isinstance(result, CatalogContentItem)
        assert result.title == "Extracted"
        assert result.type == "article"
    
    def test_extract_json_from_text_atomic_no_schema(self):
        """Test JSON extraction without schema validation."""
        mixed_text = 'Text {"key": "value"} more text'
        
        result = extract_json_from_text_atomic(mixed_text)
        
        assert isinstance(result, dict)
        assert result["key"] == "value"
    
    def test_extract_json_from_text_atomic_no_json(self):
        """Test extraction when no JSON is found."""
        text_only = "This is just plain text with no JSON"
        
        result = extract_json_from_text_atomic(text_only, CatalogContentItem)
        
        assert result is None
    
    def test_safe_get_atomic(self):
        """Test safe value extraction from BaseIOSchema and dict."""
        item = CatalogContentItem(
            title="Test",
            metadata={"author": "John", "nested": {"deep": "value"}}
        )
        
        # Test with BaseIOSchema
        assert safe_get_atomic(item, "title") == "Test"
        assert safe_get_atomic(item, "metadata.author") == "John"
        assert safe_get_atomic(item, "metadata.nested.deep") == "value"
        assert safe_get_atomic(item, "nonexistent", "default") == "default"
        
        # Test with dict
        data = {"user": {"profile": {"name": "Jane"}}}
        assert safe_get_atomic(data, "user.profile.name") == "Jane"
        assert safe_get_atomic(data, "user.missing", "default") == "default"
    
    def test_format_for_prompt_atomic(self):
        """Test formatting data for prompts."""
        item = CatalogContentItem(title="Test", type="article")
        
        # Test with BaseIOSchema
        result = format_for_prompt_atomic(item)
        assert isinstance(result, str)
        assert "Test" in result
        assert "article" in result
        
        # Test with dict
        data = {"key": "value"}
        result = format_for_prompt_atomic(data)
        assert isinstance(result, str)
        assert "key" in result
        
        # Test with other types
        result = format_for_prompt_atomic("simple string")
        assert result == "simple string"
    
    def test_merge_schema_results(self):
        """Test merging multiple schema instances."""
        item1 = CatalogContentItem(title="Item 1", type="article")
        item2 = CatalogContentItem(title="Item 2", platform="website")
        
        # Note: This test assumes the merge logic works with the last value
        # The actual behavior depends on the schema structure
        merged = merge_schema_results([item1, item2], CatalogContentItem)
        
        assert isinstance(merged, CatalogContentItem)
        # The merge should contain data from both items
    
    def test_process_agent_response_atomic_success(self):
        """Test successful agent response processing."""
        json_data = {"title": "Test", "type": "article"}
        json_string = json.dumps(json_data)
        
        result = process_agent_response_atomic(json_string, CatalogContentItem)
        
        assert isinstance(result, CatalogContentItem)
        assert result.title == "Test"
    
    def test_process_agent_response_atomic_extraction(self):
        """Test agent response processing with extraction fallback."""
        mixed_response = 'Analysis: {"title": "Extracted", "type": "article"} End.'
        
        result = process_agent_response_atomic(mixed_response, CatalogContentItem)
        
        assert isinstance(result, CatalogContentItem)
        assert result.title == "Extracted"
    
    def test_process_agent_response_atomic_failure(self):
        """Test agent response processing failure."""
        invalid_response = "No JSON here at all"
        
        result = process_agent_response_atomic(invalid_response, CatalogContentItem)
        
        assert isinstance(result, dict)
        assert result["error_type"] == "JSONParsingError"
    
    def test_validate_json_string(self):
        """Test JSON string validation."""
        valid_json = json.dumps({"title": "Test", "type": "article"})
        invalid_json = "{ invalid"
        
        assert validate_json_string(valid_json, CatalogContentItem) == True
        assert validate_json_string(invalid_json, CatalogContentItem) == False
    
    def test_create_error_response_schema(self):
        """Test error response schema creation."""
        from datetime import datetime
        
        context = create_error_context("test", "test")
        error_schema = AppBaseException(
            error_type="TestError",
            message="Test",
            context=context,
            timestamp=datetime.now().isoformat()
        )
        atomic_error = AtomicException(error_schema)
        regular_error = Exception("Regular error")
        
        # Test with atomic error
        result1 = create_error_response_schema(atomic_error, "test_operation")
        assert result1["error_type"] == "TestError"
        
        # Test with regular error
        result2 = create_error_response_schema(regular_error, "test_operation")
        assert result2["error_type"] == "Exception"
        assert result2["message"] == "Regular error"

class TestLoggingSetup:
    """Test suite for logging infrastructure."""
    
    def test_logging_config_integration(self):
        """Test logging setup with LoggingConfig."""
        config = LoggingConfig(
            level="DEBUG",
            enable_rich_logging=False,
            file_path=None
        )
        
        # Test setup doesn't raise errors
        setup_logging(config)
        
        # Test logger creation
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_setup_module_logger(self):
        """Test module-specific logger setup."""
        logger = setup_module_logger("test_module", "WARNING")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
        assert logger.level == logging.WARNING
    
    def test_create_context_logger(self):
        """Test context logger creation."""
        base_logger = get_logger("base")
        context_logger = create_context_logger("test_context", base_logger)
        
        # Context logger should be a LoggerAdapter
        assert hasattr(context_logger, 'process')
        
        # Test message processing
        msg, kwargs = context_logger.process("test message", {})
        assert "[test_context]" in msg
        assert "test message" in msg
    
    @patch('llai.utils.logging_setup.get_logger')
    def test_log_function_entry_exit(self, mock_get_logger):
        """Test function entry and exit logging."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Test entry logging
        log_function_entry("test_function", {"arg1": "value1"})
        mock_logger.debug.assert_called_with("Entering test_function with args: {'arg1': 'value1'}")
        
        # Test exit logging
        log_function_exit("test_function", "result")
        mock_logger.debug.assert_called_with("Exiting test_function with result type: str")
    
    @patch('llai.utils.logging_setup.get_logger')
    def test_log_performance(self, mock_get_logger):
        """Test performance logging."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        log_performance("test_operation", 1.234)
        mock_logger.info.assert_called_with("Performance: test_operation took 1.234 seconds")
    
    def test_logged_function_decorator(self):
        """Test the logged function decorator."""
        mock_logger = MagicMock()
        
        @logged_function(mock_logger)
        def test_function(x, y=None):
            return x + (y or 0)
        
        result = test_function(5, y=3)
        
        assert result == 8
        # Verify logging calls were made
        assert mock_logger.debug.call_count >= 2  # Entry and exit

if __name__ == "__main__":
    # Run basic tests
    test_error = TestErrorHandling()
    test_error.test_error_context_creation()
    test_error.test_app_base_exception_schema()
    test_error.test_atomic_exception_wrapper()
    
    test_json = TestJSONUtilities()
    test_json.test_parse_json_response_atomic_success()
    test_json.test_safe_get_atomic()
    test_json.test_format_for_prompt_atomic()
    
    test_logging = TestLoggingSetup()
    test_logging.test_logging_config_integration()
    test_logging.test_setup_module_logger()
    
    print("All basic tests passed!")
