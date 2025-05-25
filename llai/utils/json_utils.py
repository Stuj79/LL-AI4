"""
JSON utilities for the Legal AI Marketing Assistant.

This module provides functions for parsing, extracting, and manipulating JSON data
with standardized error handling and validation.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Union, List
# Assuming error_utils is in the same parent directory or PYTHONPATH is set correctly
from .error_utils import handle_json_error

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse JSON response with standardized error handling.
    
    Args:
        response_text: The text to parse as JSON
        
    Returns:
        Parsed JSON as a dictionary, or an error dictionary if parsing fails
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback for non-JSON responses
        return {
            "error": "Could not parse JSON response",
            "raw_response": response_text
        }


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that might contain other content.
    
    Attempts to find a JSON object in the provided text, even if the JSON
    is surrounded by other text content.
    
    Args:
        text: The text that may contain a JSON object
        
    Returns:
        The extracted JSON object as a dictionary, or None if no valid JSON was found
    """
    # Try to find text that looks like JSON (between curly braces)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # If the first match fails, try a more aggressive approach
            pass
    
    # Try to find anything that might be JSON
    potential_jsons = re.findall(r'(\{.*?\})', text, re.DOTALL)
    for potential_json in potential_jsons:
        try:
            return json.loads(potential_json)
        except json.JSONDecodeError:
            continue
    
    return None


def safe_get(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get a value from a nested dictionary using a dot-notation path.
    
    Args:
        data: The dictionary to extract data from
        key_path: A dot-notation path (e.g., "user.profile.name")
        default: The default value to return if the path is not found
        
    Returns:
        The value at the specified path, or the default value if not found
    """
    keys = key_path.split('.')
    result = data
    
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    
    return result


def format_for_prompt(data: Union[Dict[str, Any], List, Any]) -> str:
    """
    Format data as JSON string suitable for inclusion in prompts.
    
    Args:
        data: The data to format (dictionary, list, or other JSON-serializable value)
        
    Returns:
        A formatted JSON string with consistent indentation
    """
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2)
    else:
        return str(data)


def merge_json_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple JSON result dictionaries into a single dictionary.
    
    Args:
        results: A list of dictionaries to merge
        
    Returns:
        A merged dictionary containing all keys from the input dictionaries
    """
    merged = {}
    
    for result in results:
        for key, value in result.items():
            # If the key already exists and both values are dictionaries, merge them
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            # If the key already exists and both values are lists, combine them
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key].extend(value)
            # Otherwise, overwrite or add the key
            else:
                merged[key] = value
    
    return merged


def process_agent_response_json(response_text: str, context: str = "JSON processing") -> Union[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Process agent response text expected to contain JSON, with standardized error handling.

    Attempts to parse the entire text as JSON. If that fails, tries to extract
    JSON embedded within the text. Returns a standardized error dictionary on failure.

    Args:
        response_text: The raw text content from the agent response.
        context: Description of the context for error messages.

    Returns:
        Parsed JSON as a dictionary or list, or a standardized error dictionary if parsing fails.
    """
    try:
        # First, try parsing the whole response directly (using the existing util)
        # Note: parse_json_response already handles basic JSONDecodeError and returns an error dict.
        # We might want to refine this based on how parse_json_response behaves.
        # Let's assume parse_json_response raises JSONDecodeError on failure for this wrapper.
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Direct JSON decode failed in {context}: {str(e)}. Trying extraction.")
        # If direct parsing fails, try extracting JSON from potentially mixed text
        extracted_json = extract_json_from_text(response_text)
        if extracted_json:
            logger.info(f"Successfully extracted JSON in {context} after initial parse failed.")
            # Ensure extracted JSON is returned in the expected format (dict or list)
            if isinstance(extracted_json, (dict, list)):
                 return extracted_json
            else:
                 # This case might occur if extract_json_from_text finds something unexpected
                 return handle_json_error(json.JSONDecodeError("Extracted content is not valid JSON", response_text, 0), response_text, context + " (extraction)")

        # If extraction also fails, return a standardized error using handle_json_error
        logger.error(f"Failed to parse or extract JSON in {context}.")
        return handle_json_error(e, response_text, context)
