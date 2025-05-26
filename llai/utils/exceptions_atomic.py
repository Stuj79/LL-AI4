"""
Atomic Agents aligned exception handling for the Legal AI Marketing Assistant.

This module provides structured exception classes that leverage BaseIOSchema for
consistent error reporting and integrate with Pydantic ValidationError and
instructor error handling patterns.
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Type, Union
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field, ValidationError
import json

logger = logging.getLogger(__name__)

# --- Base Exception Schema ---

class ErrorContext(BaseIOSchema):
    """Schema for error context information."""
    operation: str = Field(..., description="The operation that was being performed")
    component: str = Field(..., description="The component where the error occurred")
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="Additional context information")

class AppBaseException(BaseIOSchema):
    """Base exception schema for structured error reporting."""
    error_type: str = Field(..., description="Type of error that occurred")
    message: str = Field(..., description="Human-readable error message")
    context: ErrorContext = Field(..., description="Context where the error occurred")
    timestamp: str = Field(..., description="ISO timestamp when the error occurred")
    severity: str = Field("error", description="Error severity level (debug, info, warning, error, critical)")
    recoverable: bool = Field(True, description="Whether the error is recoverable")
    user_message: Optional[str] = Field(None, description="User-friendly error message")

# --- Specific Exception Schemas ---

class LLMResponseError(AppBaseException):
    """Schema for LLM response related errors."""
    error_type: str = Field("LLMResponseError", description="Type of error")
    provider: str = Field(..., description="LLM provider that generated the error")
    model: str = Field(..., description="Model that was being used")
    raw_response: Optional[str] = Field(None, description="Raw response from the LLM")
    token_count: Optional[int] = Field(None, description="Number of tokens in the response")

class ToolExecutionError(AppBaseException):
    """Schema for tool execution errors."""
    error_type: str = Field("ToolExecutionError", description="Type of error")
    tool_name: str = Field(..., description="Name of the tool that failed")
    tool_input: Dict[str, Any] = Field(..., description="Input that was provided to the tool")
    execution_time: Optional[float] = Field(None, description="Time taken before failure (seconds)")

class ConfigurationError(AppBaseException):
    """Schema for configuration related errors."""
    error_type: str = Field("ConfigurationError", description="Type of error")
    config_key: str = Field(..., description="Configuration key that caused the error")
    expected_type: str = Field(..., description="Expected type for the configuration value")
    actual_value: Any = Field(..., description="Actual value that was provided")

class SchemaValidationError(AppBaseException):
    """Schema for Pydantic validation errors."""
    error_type: str = Field("SchemaValidationError", description="Type of error")
    schema_name: str = Field(..., description="Name of the schema that failed validation")
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation error details")
    raw_data: Dict[str, Any] = Field(..., description="Raw data that failed validation")

class JSONParsingError(AppBaseException):
    """Schema for JSON parsing errors."""
    error_type: str = Field("JSONParsingError", description="Type of error")
    raw_response: str = Field(..., description="Raw text that failed to parse as JSON")
    parse_position: Optional[int] = Field(None, description="Character position where parsing failed")
    expected_format: str = Field("JSON", description="Expected data format")

class APIError(AppBaseException):
    """Schema for API related errors."""
    error_type: str = Field("APIError", description="Type of error")
    status_code: int = Field(..., description="HTTP status code")
    endpoint: str = Field(..., description="API endpoint that was called")
    request_method: str = Field(..., description="HTTP method used")
    response_body: Optional[str] = Field(None, description="Response body from the API")

# --- Exception Classes ---

class AtomicException(Exception):
    """Base exception class that wraps structured error schemas."""
    
    def __init__(self, error_schema: AppBaseException):
        self.error_schema = error_schema
        super().__init__(error_schema.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary."""
        return self.error_schema.model_dump()
    
    def to_json(self) -> str:
        """Convert the exception to a JSON string."""
        return self.error_schema.model_dump_json(indent=2)

class AtomicLLMResponseError(AtomicException):
    """Exception for LLM response errors."""
    pass

class AtomicToolExecutionError(AtomicException):
    """Exception for tool execution errors."""
    pass

class AtomicConfigurationError(AtomicException):
    """Exception for configuration errors."""
    pass

class AtomicSchemaValidationError(AtomicException):
    """Exception for schema validation errors."""
    pass

class AtomicJSONParsingError(AtomicException):
    """Exception for JSON parsing errors."""
    pass

class AtomicAPIError(AtomicException):
    """Exception for API errors."""
    pass

# --- Error Handler Functions ---

def create_error_context(operation: str, component: str, **kwargs) -> ErrorContext:
    """Create an error context object."""
    return ErrorContext(
        operation=operation,
        component=component,
        additional_info=kwargs
    )

def handle_validation_error(
    error: ValidationError,
    schema_name: str,
    raw_data: Dict[str, Any],
    context: ErrorContext
) -> AtomicSchemaValidationError:
    """Handle Pydantic validation errors with structured reporting."""
    from datetime import datetime
    
    # Extract validation error details
    validation_errors = []
    for err in error.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
            "input": err.get("input")
        })
    
    error_schema = SchemaValidationError(
        message=f"Schema validation failed for {schema_name}: {str(error)}",
        context=context,
        timestamp=datetime.now().isoformat(),
        schema_name=schema_name,
        validation_errors=validation_errors,
        raw_data=raw_data,
        user_message=f"The provided data does not match the expected format for {schema_name}"
    )
    
    logger.error(f"Schema validation error: {error_schema.message}")
    return AtomicSchemaValidationError(error_schema)

def handle_llm_response_error(
    error: Exception,
    provider: str,
    model: str,
    context: ErrorContext,
    raw_response: Optional[str] = None
) -> AtomicLLMResponseError:
    """Handle LLM response errors with structured reporting."""
    from datetime import datetime
    
    error_schema = LLMResponseError(
        message=f"LLM response error from {provider}/{model}: {str(error)}",
        context=context,
        timestamp=datetime.now().isoformat(),
        provider=provider,
        model=model,
        raw_response=raw_response,
        user_message="There was an issue processing the AI response. Please try again."
    )
    
    logger.error(f"LLM response error: {error_schema.message}")
    return AtomicLLMResponseError(error_schema)

def handle_tool_execution_error(
    error: Exception,
    tool_name: str,
    tool_input: Dict[str, Any],
    context: ErrorContext,
    execution_time: Optional[float] = None
) -> AtomicToolExecutionError:
    """Handle tool execution errors with structured reporting."""
    from datetime import datetime
    
    error_schema = ToolExecutionError(
        message=f"Tool execution failed for {tool_name}: {str(error)}",
        context=context,
        timestamp=datetime.now().isoformat(),
        tool_name=tool_name,
        tool_input=tool_input,
        execution_time=execution_time,
        user_message=f"There was an issue executing the {tool_name} operation. Please try again."
    )
    
    logger.error(f"Tool execution error: {error_schema.message}")
    return AtomicToolExecutionError(error_schema)

def handle_json_parsing_error(
    error: json.JSONDecodeError,
    raw_response: str,
    context: ErrorContext
) -> AtomicJSONParsingError:
    """Handle JSON parsing errors with structured reporting."""
    from datetime import datetime
    
    error_schema = JSONParsingError(
        message=f"JSON parsing failed: {str(error)}",
        context=context,
        timestamp=datetime.now().isoformat(),
        raw_response=raw_response,
        parse_position=error.pos if hasattr(error, 'pos') else None,
        user_message="There was an issue processing the response data. Please try again."
    )
    
    logger.error(f"JSON parsing error: {error_schema.message}")
    return AtomicJSONParsingError(error_schema)

def handle_configuration_error(
    config_key: str,
    expected_type: str,
    actual_value: Any,
    context: ErrorContext
) -> AtomicConfigurationError:
    """Handle configuration errors with structured reporting."""
    from datetime import datetime
    
    error_schema = ConfigurationError(
        message=f"Configuration error for {config_key}: expected {expected_type}, got {type(actual_value).__name__}",
        context=context,
        timestamp=datetime.now().isoformat(),
        config_key=config_key,
        expected_type=expected_type,
        actual_value=actual_value,
        user_message="There is a configuration issue. Please check your settings."
    )
    
    logger.error(f"Configuration error: {error_schema.message}")
    return AtomicConfigurationError(error_schema)

def handle_api_error(
    status_code: int,
    endpoint: str,
    method: str,
    context: ErrorContext,
    response_body: Optional[str] = None
) -> AtomicAPIError:
    """Handle API errors with structured reporting."""
    from datetime import datetime
    
    error_schema = APIError(
        message=f"API error {status_code} for {method} {endpoint}",
        context=context,
        timestamp=datetime.now().isoformat(),
        status_code=status_code,
        endpoint=endpoint,
        request_method=method,
        response_body=response_body,
        user_message="There was an issue connecting to the service. Please try again later."
    )
    
    logger.error(f"API error: {error_schema.message}")
    return AtomicAPIError(error_schema)

# --- Utility Functions ---

def is_atomic_error(obj: Any) -> bool:
    """Check if an object is an atomic error."""
    return isinstance(obj, AtomicException)

def extract_user_message(error: Union[AtomicException, Exception]) -> str:
    """Extract a user-friendly message from any error."""
    if isinstance(error, AtomicException):
        return error.error_schema.user_message or error.error_schema.message
    else:
        return f"An unexpected error occurred: {str(error)}"

def log_error_with_context(error: AtomicException, include_traceback: bool = False) -> None:
    """Log an atomic error with full context."""
    error_dict = error.to_dict()
    logger.error(f"Atomic Error: {error_dict}")
    
    if include_traceback:
        logger.error(traceback.format_exc())
