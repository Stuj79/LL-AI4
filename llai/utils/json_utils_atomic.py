"""
Atomic Agents aligned JSON utilities for the Legal AI Marketing Assistant.

This module provides functions for parsing, extracting, and manipulating JSON data
using BaseIOSchema models and the new structured error handling patterns.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Union, List, Type, TypeVar
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import ValidationError
from .exceptions_atomic import (
    create_error_context,
    handle_json_parsing_error,
    handle_validation_error,
    AtomicJSONParsingError,
    AtomicSchemaValidationError
)

logger = logging.getLogger(__name__)

# Type variable for BaseIOSchema subclasses
T = TypeVar('T', bound=BaseIOSchema)

def parse_json_response_atomic(
    response_text: str, 
    schema_class: Type[T],
    context_operation: str = "JSON parsing"
) -> T:
    """
    Parse JSON response using BaseIOSchema validation with structured error handling.
    
    Args:
        response_text: The text to parse as JSON
        schema_class: The BaseIOSchema class to validate against
        context_operation: Description of the operation for error context
        
    Returns:
        Validated instance of the schema class
        
    Raises:
        AtomicJSONParsingError: If JSON parsing fails
        AtomicSchemaValidationError: If schema validation fails
    """
    context = create_error_context(
        operation=context_operation,
        component="json_utils_atomic",
        schema_class=schema_class.__name__
    )
    
    try:
        # First parse as JSON
        parsed_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error in {context_operation}: {str(e)}")
        raise handle_json_parsing_error(e, response_text, context)
    
    try:
        # Then validate with schema
        return schema_class.model_validate(parsed_data)
    except ValidationError as e:
        logger.warning(f"Schema validation error in {context_operation}: {str(e)}")
        raise handle_validation_error(e, schema_class.__name__, parsed_data, context)

def parse_json_response_atomic_safe(
    response_text: str, 
    schema_class: Type[T],
    context_operation: str = "JSON parsing"
) -> Union[T, Dict[str, Any]]:
    """
    Safe version that returns error dict instead of raising exceptions.
    
    Args:
        response_text: The text to parse as JSON
        schema_class: The BaseIOSchema class to validate against
        context_operation: Description of the operation for error context
        
    Returns:
        Validated instance of the schema class or error dictionary
    """
    try:
        return parse_json_response_atomic(response_text, schema_class, context_operation)
    except (AtomicJSONParsingError, AtomicSchemaValidationError) as e:
        return e.to_dict()

def extract_json_from_text_atomic(
    text: str,
    schema_class: Optional[Type[T]] = None,
    context_operation: str = "JSON extraction"
) -> Union[T, Dict[str, Any], None]:
    """
    Extract and validate JSON object from text that might contain other content.
    
    Args:
        text: The text that may contain a JSON object
        schema_class: Optional BaseIOSchema class to validate against
        context_operation: Description of the operation for error context
        
    Returns:
        Validated schema instance, raw dict, or None if no valid JSON found
        
    Raises:
        AtomicSchemaValidationError: If schema validation fails (when schema_class provided)
    """
    context = create_error_context(
        operation=context_operation,
        component="json_utils_atomic",
        schema_class=schema_class.__name__ if schema_class else "None"
    )
    
    # Try to find text that looks like JSON (between curly braces)
    json_patterns = [
        r'\{.*\}',  # Basic JSON object
        r'\[.*\]',  # JSON array
    ]
    
    for pattern in json_patterns:
        json_match = re.search(pattern, text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            try:
                parsed_data = json.loads(json_text)
                
                # If schema class provided, validate
                if schema_class:
                    try:
                        return schema_class.model_validate(parsed_data)
                    except ValidationError as e:
                        logger.warning(f"Schema validation failed during extraction: {str(e)}")
                        raise handle_validation_error(e, schema_class.__name__, parsed_data, context)
                else:
                    return parsed_data
                    
            except json.JSONDecodeError:
                continue  # Try next pattern
    
    # Try more aggressive extraction for potential JSON objects
    potential_jsons = re.findall(r'(\{[^{}]*\})', text)
    for potential_json in potential_jsons:
        try:
            parsed_data = json.loads(potential_json)
            
            if schema_class:
                try:
                    return schema_class.model_validate(parsed_data)
                except ValidationError:
                    continue  # Try next potential JSON
            else:
                return parsed_data
                
        except json.JSONDecodeError:
            continue
    
    return None

def safe_get_atomic(data: Union[BaseIOSchema, Dict[str, Any]], key_path: str, default: Any = None) -> Any:
    """
    Safely get a value from a BaseIOSchema instance or dictionary using dot-notation path.
    
    Args:
        data: The BaseIOSchema instance or dictionary to extract data from
        key_path: A dot-notation path (e.g., "user.profile.name")
        default: The default value to return if the path is not found
        
    Returns:
        The value at the specified path, or the default value if not found
    """
    keys = key_path.split('.')
    
    # Convert BaseIOSchema to dict if needed
    if isinstance(data, BaseIOSchema):
        result = data.model_dump()
    else:
        result = data
    
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    
    return result

def format_for_prompt_atomic(data: Union[BaseIOSchema, Dict[str, Any], List, Any]) -> str:
    """
    Format data as JSON string suitable for inclusion in prompts.
    
    Args:
        data: The data to format (BaseIOSchema, dictionary, list, or other JSON-serializable value)
        
    Returns:
        A formatted JSON string with consistent indentation
    """
    if isinstance(data, BaseIOSchema):
        return data.model_dump_json(indent=2)
    elif isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, default=str)
    else:
        return str(data)

def merge_schema_results(results: List[T], schema_class: Type[T]) -> T:
    """
    Merge multiple BaseIOSchema instances into a single instance.
    
    Args:
        results: A list of BaseIOSchema instances to merge
        schema_class: The schema class for the result
        
    Returns:
        A merged instance of the schema class
        
    Raises:
        AtomicSchemaValidationError: If the merged data fails validation
    """
    if not results:
        return schema_class()
    
    # Convert all instances to dictionaries
    merged_data = {}
    
    for result in results:
        result_dict = result.model_dump()
        for key, value in result_dict.items():
            # If the key already exists and both values are dictionaries, merge them
            if key in merged_data and isinstance(merged_data[key], dict) and isinstance(value, dict):
                merged_data[key].update(value)
            # If the key already exists and both values are lists, combine them
            elif key in merged_data and isinstance(merged_data[key], list) and isinstance(value, list):
                merged_data[key].extend(value)
            # Otherwise, overwrite or add the key
            else:
                merged_data[key] = value
    
    # Validate the merged data
    context = create_error_context(
        operation="schema merging",
        component="json_utils_atomic",
        schema_class=schema_class.__name__
    )
    
    try:
        return schema_class.model_validate(merged_data)
    except ValidationError as e:
        raise handle_validation_error(e, schema_class.__name__, merged_data, context)

def process_agent_response_atomic(
    response_text: str,
    schema_class: Type[T],
    context_operation: str = "agent response processing"
) -> Union[T, Dict[str, Any]]:
    """
    Process agent response text expected to contain JSON, with comprehensive error handling.
    
    This function attempts multiple strategies:
    1. Direct JSON parsing and validation
    2. JSON extraction from mixed text
    3. Structured error reporting on failure
    
    Args:
        response_text: The raw text content from the agent response
        schema_class: The BaseIOSchema class to validate against
        context_operation: Description of the operation for error context
        
    Returns:
        Validated schema instance or structured error dictionary
    """
    context = create_error_context(
        operation=context_operation,
        component="json_utils_atomic",
        schema_class=schema_class.__name__
    )
    
    # Strategy 1: Direct parsing and validation
    try:
        return parse_json_response_atomic(response_text, schema_class, context_operation)
    except AtomicJSONParsingError:
        logger.info(f"Direct JSON parsing failed in {context_operation}, trying extraction")
    except AtomicSchemaValidationError as e:
        logger.error(f"Schema validation failed in {context_operation}: {e}")
        return e.to_dict()
    
    # Strategy 2: JSON extraction from mixed text
    try:
        extracted = extract_json_from_text_atomic(response_text, schema_class, context_operation)
        if extracted:
            logger.info(f"Successfully extracted and validated JSON in {context_operation}")
            return extracted
    except AtomicSchemaValidationError as e:
        logger.error(f"Schema validation failed during extraction in {context_operation}: {e}")
        return e.to_dict()
    
    # Strategy 3: Return structured error
    logger.error(f"Failed to parse or extract valid JSON in {context_operation}")
    error = handle_json_parsing_error(
        json.JSONDecodeError("No valid JSON found", response_text, 0),
        response_text,
        context
    )
    return error.to_dict()

def validate_json_string(json_string: str, schema_class: Type[T]) -> bool:
    """
    Validate if a JSON string conforms to a BaseIOSchema without parsing.
    
    Args:
        json_string: The JSON string to validate
        schema_class: The BaseIOSchema class to validate against
        
    Returns:
        True if valid, False otherwise
    """
    try:
        parse_json_response_atomic(json_string, schema_class, "validation check")
        return True
    except (AtomicJSONParsingError, AtomicSchemaValidationError):
        return False

def create_error_response_schema(error: Exception, context_operation: str) -> Dict[str, Any]:
    """
    Create a standardized error response schema from any exception.
    
    Args:
        error: The exception that occurred
        context_operation: Description of the operation that failed
        
    Returns:
        Standardized error response dictionary
    """
    from .exceptions_atomic import extract_user_message, is_atomic_error
    
    if is_atomic_error(error):
        return error.to_dict()
    else:
        # Create a basic error response for non-atomic errors
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": {
                "operation": context_operation,
                "component": "json_utils_atomic"
            },
            "user_message": extract_user_message(error),
            "recoverable": True
        }
