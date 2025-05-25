"""
Base agent classes for the Legal AI Marketing Assistant.

This module provides base agent classes with common functionality for all agents,
reducing code duplication and standardizing error handling, JSON processing,
and prompt construction.
"""

from legion import agent, tool
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, ConfigDict
import logging
import json
from utils.json_utils import parse_json_response, extract_json_from_text, format_for_prompt
from utils.error_utils import handle_agent_error, handle_json_error
from utils.prompt_utils import format_content_prompt
from typing import ClassVar

class AgentConfig(BaseModel):
    """Base configuration model for all agents."""
    # Step 2: Add the ClassVar[dict] annotation
    agent_config: ClassVar[dict] = ConfigDict(
        arbitrary_types_allowed=True,
        extra='ignore',
        validate_assignment=True,
        str_strip_whitespace=True,
        validate_default=True
    )

logger = logging.getLogger(__name__)


class BaseAgent(AgentConfig):
    """
    Base agent class with common functionality for all agents.
    
    This class provides standard methods for processing JSON responses,
    handling errors, and other common operations needed by multiple agent types.
    """
    
    async def _process_json_response(self, response, context: str = "JSON processing") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a response that should contain JSON with standardized error handling.
        
        Args:
            response: The agent response object
            context: Description of the context for error messages
            
        Returns:
            Parsed JSON as a dictionary or list, or an error dictionary if parsing fails
        """
        try:
            return parse_json_response(response.content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error in {context}: {str(e)}")
            # Try to extract JSON from text if it might be embedded in other content
            extracted_json = extract_json_from_text(response.content)
            if extracted_json:
                return extracted_json
            
            # If extraction fails, return error dictionary
            return handle_json_error(e, response.content, context)
    
    async def _handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """
        Standardized error handling for all agents.
        
        Args:
            error: The exception that occurred
            context: Description of the context where the error occurred
            
        Returns:
            A standardized error response dictionary
        """
        return handle_agent_error(error, context)


class ContentAgent(BaseAgent):
    """
    Base agent class for content-related operations.
    
    This class extends BaseAgent with functionality specific to content processing,
    such as content categorization, analysis, and inventory management.
    """
    
    async def _prepare_content_prompt(self, data: Dict[str, Any], template_name: str) -> str:
        """
        Prepare content prompt using standardized templates.
        
        Args:
            data: Dictionary containing values for template variables
            template_name: Name of the template to use
            
        Returns:
            A formatted prompt string
        """
        return format_content_prompt(data, template_name)
    
    async def _format_content_item(self, content_item: Dict[str, Any]) -> str:
        """
        Format a content item for inclusion in a prompt.
        
        Args:
            content_item: The content item to format
            
        Returns:
            Formatted content item as a string
        """
        return format_for_prompt(content_item)
    
    
class AnalysisAgent(BaseAgent):
    """
    Base agent class for analysis operations.
    
    This class extends BaseAgent with functionality specific to data analysis,
    such as SEO analysis, performance tracking, and competitive benchmarking.
    """
    
    async def _prepare_analysis_prompt(self, data: Dict[str, Any], template_name: str) -> str:
        """
        Prepare analysis prompt using standardized templates.
        
        Args:
            data: Dictionary containing values for template variables
            template_name: Name of the template to use
            
        Returns:
            A formatted prompt string
        """
        return format_content_prompt(data, template_name)
    
    async def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """
        Format metrics for inclusion in a prompt.
        
        Args:
            metrics: The metrics to format
            
        Returns:
            Formatted metrics as a string
        """
        return format_for_prompt(metrics)


class ResearchAgent(BaseAgent):
    """
    Base agent class for research operations.
    
    This class extends BaseAgent with functionality specific to research activities,
    such as discovering relevant legal content, analyzing stakeholder feedback,
    and identifying industry trends.
    """
    
    async def _prepare_research_prompt(self, data: Dict[str, Any], template_name: str) -> str:
        """
        Prepare research prompt using standardized templates.
        
        Args:
            data: Dictionary containing values for template variables
            template_name: Name of the template to use
            
        Returns:
            A formatted prompt string
        """
        return format_content_prompt(data, template_name)
