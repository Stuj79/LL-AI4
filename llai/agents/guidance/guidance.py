from legion import agent
import logging
import os
import glob
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
HELP_RESOURCES_DIR = Path("llai/templates/help_resources")

# Helper functions moved outside the class
def get_help_resources_info():
    """Get metadata about available help resources for inclusion in prompts."""
    resources_info = []
    
    try:
        # Get all markdown files in help_resources directory and subdirectories
        md_files = glob.glob(str(HELP_RESOURCES_DIR / "**/*.md"), recursive=True)
        
        for md_file in md_files:
            rel_path = os.path.relpath(md_file, start=str(HELP_RESOURCES_DIR))
            resource_key = rel_path.replace("\\", "/").replace(".md", "")
            
            # Read first 200 characters to extract title
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read(200)
            
            # Extract title from first line (assuming it starts with #)
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines and lines[0].startswith('#') else resource_key
            
            resources_info.append({
                "path": resource_key,
                "title": title
            })
    
    except Exception as e:
        logger.error(f"Error getting help resources: {str(e)}")
    
    return resources_info

def get_help_content(resource_path):
    """Get the content of a specific help resource."""
    try:
        # Convert resource_path to file path
        file_path = HELP_RESOURCES_DIR / f"{resource_path}.md"
        
        # Read content from file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    except Exception as e:
        logger.error(f"Error getting help content for {resource_path}: {str(e)}")
        return f"Error: Could not retrieve content for {resource_path}"

@agent(model="openai:gpt-4o-mini", temperature=0.3)
class GuidanceAgent:
    """You are a helpful assistant for the Legal AI Marketing Assistant application.
    You provide context-aware help by finding relevant information in the help resources.
    
    Help resources are located in llai/templates/help_resources/ with these categories:
    - faqs/: Frequently asked questions on general, legal, and technical topics
    - troubleshooting/: Guides for resolving common issues
    - workflows/: Step-by-step guides for different application phases
    
    When helping users, first understand their question, then look for the most relevant 
    help resource that addresses their needs. You should also consider the current context 
    of the application (which phase they're in) when providing help.
    
    If you don't have a direct answer from the help resources, provide general guidance
    based on your knowledge of legal marketing and software applications.
    """
    # No helper methods here - they've been moved outside the class
