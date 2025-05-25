"""
Error handling utilities for the Legal AI Marketing Assistant.

This module provides standardized error handling functions and error response
structures to ensure consistent error management throughout the application.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Type, Union
import json

# Configure logger
logger = logging.getLogger(__name__)


def handle_agent_error(
    error: Exception, context: str, include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Handle agent errors with standardized error response.
    
    Args:
        error: The exception that was raised
        context: Description of the context where the error occurred
        include_traceback: Whether to include the full traceback in the response
        
    Returns:
        A standardized error response dictionary
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Log the error
    logger.error(f"Error in {context}: {error_type} - {error_message}")
    if include_traceback:
        logger.error(traceback.format_exc())
    
    # Create standardized error response
    error_response = {
        "error": True,
        "error_type": error_type,
        "error_message": error_message,
        "context": context,
        "status": "failed"
    }
    
    if include_traceback:
        error_response["traceback"] = traceback.format_exc()
    
    return error_response


def handle_json_error(
    error: json.JSONDecodeError, raw_content: str, context: str
) -> Dict[str, Any]:
    """
    Handle JSON parsing errors with standardized error response.
    
    Args:
        error: The JSONDecodeError that was raised
        raw_content: The raw content that failed to parse
        context: Description of the context where the error occurred
        
    Returns:
        A standardized error response dictionary
    """
    # Log the error
    logger.error(f"JSON parsing error in {context}: {str(error)}")
    
    # Create standardized error response
    error_response = {
        "error": True,
        "error_type": "JSONDecodeError",
        "error_message": str(error),
        "context": context,
        "status": "failed",
        "raw_response": raw_content
    }
    
    return error_response


def handle_api_error(
    status_code: int, error_message: str, context: str
) -> Dict[str, Any]:
    """
    Handle API errors with standardized error response.
    
    Args:
        status_code: The HTTP status code
        error_message: The error message from the API
        context: Description of the context where the error occurred
        
    Returns:
        A standardized error response dictionary
    """
    # Log the error
    logger.error(f"API error in {context}: {status_code} - {error_message}")
    
    # Create standardized error response
    error_response = {
        "error": True,
        "error_type": "APIError",
        "status_code": status_code,
        "error_message": error_message,
        "context": context,
        "status": "failed"
    }
    
    return error_response


def handle_validation_error(
    error_message: str, invalid_fields: Dict[str, str], context: str
) -> Dict[str, Any]:
    """
    Handle data validation errors with standardized error response.
    
    Args:
        error_message: The general error message
        invalid_fields: Dictionary mapping field names to validation errors
        context: Description of the context where the error occurred
        
    Returns:
        A standardized error response dictionary
    """
    # Log the error
    logger.error(f"Validation error in {context}: {error_message}")
    for field, msg in invalid_fields.items():
        logger.error(f"  - {field}: {msg}")
    
    # Create standardized error response
    error_response = {
        "error": True,
        "error_type": "ValidationError",
        "error_message": error_message,
        "invalid_fields": invalid_fields,
        "context": context,
        "status": "failed"
    }
    
    return error_response


def is_error_response(response: Dict[str, Any]) -> bool:
    """
    Check if a response dictionary is an error response.
    
    Args:
        response: The response dictionary to check
        
    Returns:
        True if the response is an error response, False otherwise
    """
    return (
        isinstance(response, dict) and
        response.get("error") is True and
        "error_message" in response
    )


def format_exception_for_user(
    error: Exception, context: str, user_friendly_message: Optional[str] = None
) -> str:
    """
    Format an exception into a user-friendly message.
    
    Args:
        error: The exception that was raised
        context: Description of the context where the error occurred
        user_friendly_message: Optional custom message to show the user
        
    Returns:
        A user-friendly error message string
    """
    if user_friendly_message:
        return user_friendly_message
    
    error_type = type(error).__name__
    
    # Default user-friendly messages based on error type
    if error_type == "JSONDecodeError":
        return f"There was an issue processing the response data. Please try again."
    elif error_type == "ConnectionError":
        return f"There was a connection issue while {context}. Please check your internet connection and try again."
    elif error_type == "TimeoutError":
        return f"The operation timed out while {context}. Please try again later."
    else:
        return f"An unexpected error occurred while {context}. Please try again or contact support if the issue persists."
