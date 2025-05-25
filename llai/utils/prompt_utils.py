"""
Prompt utilities for the Legal AI Marketing Assistant.

This module provides template management and formatting functions for creating
standardized prompts to be used with AI agents.
"""

import json
from typing import Dict, Any, List, Optional, Union
from utils.json_utils import format_for_prompt

# Template definitions for common prompt patterns
TEMPLATES = {
    "content_inventory": """
Analyze this content inventory to identify practice areas with insufficient coverage.
Compare against the firm's practice areas to find gaps.

CONTENT INVENTORY:
{content_inventory}

FIRM PRACTICE AREAS:
{practice_areas}

Format the result as a JSON object with:
1. "covered_areas": list of practice areas with content
2. "gap_areas": list of practice areas with no or insufficient content
3. "coverage_metrics": dictionary with count of content items per practice area
""",

    "content_classification": """
Classify the following content into appropriate legal practice areas.

CONTENT:
{content}

Provide your classification as a JSON object with:
1. "primary_area": primary practice area
2. "secondary_areas": list of related practice areas 
3. "keywords": list of key legal terms identified
4. "confidence": confidence score (0.0-1.0)
""",

    "content_quality_analysis": """
Analyze the quality of the following legal marketing content.

CONTENT:
{content}

Provide your analysis as a JSON object with:
1. "quality_score": overall quality score (1-10)
2. "strengths": list of content strengths
3. "weaknesses": list of content weaknesses
4. "improvement_suggestions": list of specific improvement suggestions
5. "target_audience_alignment": assessment of how well the content aligns with the target audience (1-10)
""",

    "stakeholder_analysis": """
Analyze the following stakeholder input to identify key insights and preferences.

STAKEHOLDER INPUT:
{stakeholder_input}

STAKEHOLDER ROLE:
{stakeholder_role}

Provide your analysis as a JSON object with:
1. "key_insights": list of important insights from the stakeholder
2. "preferences": content and marketing preferences identified
3. "pain_points": challenges or issues mentioned by the stakeholder
4. "opportunities": potential opportunities based on the stakeholder input
5. "content_recommendations": specific content recommendations based on the analysis
""",

    "marketing_strategy": """
Develop a marketing strategy based on the following information.

FIRM PROFILE:
{firm_profile}

TARGET AUDIENCE:
{target_audience}

COMPETITIVE LANDSCAPE:
{competitive_landscape}

CONTENT INVENTORY:
{content_inventory}

Provide your strategy as a JSON object with:
1. "target_segments": list of primary target segments with descriptions
2. "key_messages": key messages for each target segment
3. "content_plan": recommended content types and topics
4. "distribution_channels": recommended channels for content distribution
5. "success_metrics": metrics to track for measuring success
"""
}


def format_content_prompt(data: Dict[str, Any], template_name: str) -> str:
    """
    Format prompt using a standardized template.
    
    Args:
        data: Dictionary containing values for template variables
        template_name: Name of the template to use
        
    Returns:
        A formatted prompt string
    
    Raises:
        ValueError: If the template name is unknown
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    template = TEMPLATES[template_name]
    
    # Format data for JSON insertion in templates
    formatted_data = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            formatted_data[key] = format_for_prompt(value)
        else:
            formatted_data[key] = value
    
    return template.format(**formatted_data)


def create_custom_prompt(
    sections: Dict[str, str],
    instructions: str,
    output_format: Dict[str, str],
    examples: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a custom prompt with standardized structure.
    
    Args:
        sections: Dictionary mapping section names to content
        instructions: Specific instructions for the task
        output_format: Dictionary mapping output field names to descriptions
        examples: Optional list of example inputs and outputs
        
    Returns:
        A formatted custom prompt string
    """
    prompt_parts = []
    
    # Add sections
    for section_name, content in sections.items():
        prompt_parts.append(f"{section_name.upper()}:")
        prompt_parts.append(content)
        prompt_parts.append("")
    
    # Add instructions
    prompt_parts.append("INSTRUCTIONS:")
    prompt_parts.append(instructions)
    prompt_parts.append("")
    
    # Add output format
    prompt_parts.append("OUTPUT FORMAT:")
    prompt_parts.append("Provide your response as a JSON object with the following fields:")
    for i, (field, description) in enumerate(output_format.items(), 1):
        prompt_parts.append(f"{i}. \"{field}\": {description}")
    prompt_parts.append("")
    
    # Add examples if provided
    if examples:
        prompt_parts.append("EXAMPLES:")
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"Example {i}:")
            if "input" in example:
                prompt_parts.append("Input:")
                prompt_parts.append(format_for_prompt(example["input"]))
            if "output" in example:
                prompt_parts.append("Output:")
                prompt_parts.append(format_for_prompt(example["output"]))
            prompt_parts.append("")
    
    return "\n".join(prompt_parts)


def combine_templates(
    template_names: List[str], 
    data: Dict[str, Any],
    additional_instructions: Optional[str] = None
) -> str:
    """
    Combine multiple templates into a single prompt.
    
    Args:
        template_names: List of template names to combine
        data: Dictionary containing values for template variables
        additional_instructions: Optional additional instructions to append
        
    Returns:
        A combined prompt string
        
    Raises:
        ValueError: If any template name is unknown
    """
    prompt_parts = []
    
    for template_name in template_names:
        if template_name not in TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = TEMPLATES[template_name]
        # Extract just the template content without format placeholders
        # This is a simplified approach and might need adjustment for complex templates
        current_template = template
        for key in data.keys():
            placeholder = "{" + key + "}"
            if placeholder in current_template:
                # Replace with empty string for now - we'll format at the end
                current_template = current_template.replace(placeholder, "{{" + key + "}}")
        
        prompt_parts.append(current_template)
    
    if additional_instructions:
        prompt_parts.append("\nADDITIONAL INSTRUCTIONS:")
        prompt_parts.append(additional_instructions)
    
    combined_template = "\n\n".join(prompt_parts)
    
    # Now format with the actual data
    formatted_data = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            formatted_data[key] = format_for_prompt(value)
        else:
            formatted_data[key] = value
    
    return combined_template.format(**formatted_data)


def add_template(name: str, template: str) -> None:
    """
    Add a new template to the template collection.
    
    Args:
        name: Name for the new template
        template: Template string
        
    Raises:
        ValueError: If the template name already exists
    """
    if name in TEMPLATES:
        raise ValueError(f"Template '{name}' already exists. Use update_template to modify it.")
    
    TEMPLATES[name] = template


def update_template(name: str, template: str) -> None:
    """
    Update an existing template.
    
    Args:
        name: Name of the template to update
        template: New template string
        
    Raises:
        ValueError: If the template name does not exist
    """
    if name not in TEMPLATES:
        raise ValueError(f"Template '{name}' does not exist. Use add_template to create it.")
    
    TEMPLATES[name] = template


def get_template(name: str) -> str:
    """
    Get a template by name.
    
    Args:
        name: Name of the template to retrieve
        
    Returns:
        The template string
        
    Raises:
        ValueError: If the template name does not exist
    """
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}")
    
    return TEMPLATES[name]


def list_templates() -> List[str]:
    """
    List all available template names.
    
    Returns:
        A list of template names
    """
    return list(TEMPLATES.keys())
