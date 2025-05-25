from legion import agent, tool
# from legion.agents import ToolAgent
# from legion.types import AgentResponse, Message
from typing import List, Dict, Any, Optional, Annotated
import logging
from tools.research import fetch_webpage, extract_text_from_html
from pydantic import Field

logger = logging.getLogger(__name__)

 
@agent(model="openai:gpt-4o-mini", temperature=0.3)
class LegalResearchAgent:
    """Agent to perform legal research and review compliance documents."""

    @tool
    def research(
        self, 
        query: Annotated[str, Field(description="Legal research query to investigate")]
    ) -> str:
        """Perform legal research based on a query."""
        # Simulate a research response.
        return f"Legal research findings for query: {query}"
    
    
@agent(model="openai:gpt-4o-mini", temperature=0.3)
class AudienceAnalysisAgent:
    """Agent to analyze audience data for legal marketing."""

    @tool
    def analyze(
        self, 
        audience_data: Annotated[str, Field(description="Audience data to analyze for legal marketing insights")]
    ) -> str:
        """Analyze audience data to extract marketing insights."""
        # Simulate analysis; later integrate actual data processing.
        return f"Analysis of audience data: {audience_data}"


@agent(
    model="openai:gpt-4o-mini",
    temperature=0.3,
    tools=[fetch_webpage, extract_text_from_html]  # Bind external tools
)
class WebScraperAgent:
    """An agent that scrapes web content and formats it for analysis.
    
    I can fetch web pages, extract specific content using CSS selectors,
    and format the results for better readability.
    """
    
    @tool
    def extract_structured_data(
        self,
        url: Annotated[str, Field(description="URL to scrape")],
        data_type: Annotated[str, Field(description="Type of data to extract (e.g., 'article', 'product')")] = "article"
    ) -> Dict[str, Any]:
        """Extract structured data from a webpage based on the data type."""
        # This would be implemented to extract different types of structured data
        # For example, for articles it might extract title, author, date, content
        # For products it might extract name, price, description, reviews
        pass
    
    @tool
    def format_scraped_content(
        self,
        content: Annotated[str, Field(description="Raw scraped content to format")],
        format_type: Annotated[str, Field(description="Format type (e.g., 'summary', 'bullet_points')")] = "summary"
    ) -> str:
        """Format scraped content into a more readable structure."""
        # Implementation to format content based on format_type
        if format_type == "summary":
            # Return a summarized version
            return f"Summary of content:\n{content[:500]}..."
        elif format_type == "bullet_points":
            # Convert paragraphs to bullet points
            paragraphs = content.split('\n\n')
            return "\n".join([f"• {p.strip()}" for p in paragraphs if p.strip()])
        return content
    
    @tool
    def clean_text(
        self,
        text: Annotated[str, Field(description="Text to clean")],
        remove_extra_whitespace: Annotated[bool, Field(description="Whether to remove extra whitespace")] = True,
        remove_urls: Annotated[bool, Field(description="Whether to remove URLs")] = False
    ) -> str:
        """Clean scraped text by removing unwanted elements."""
        # Implementation to clean text
        import re
        result = text
        
        if remove_extra_whitespace:
            result = re.sub(r'\s+', ' ', result).strip()
            
        if remove_urls:
            result = re.sub(r'https?://\S+', '', result)
            
        return result
    
    
# # Example WebScraperAgent Usage
# async def main():
#     # Create an instance of our agent
#     scraper = WebScraperAgent()

#     # Example 1: Basic scraping and formatting
#     response = await scraper.aprocess(
#         "Please scrape the content from https://example.com and format it as bullet points."
#     )
#     print("Example 1 Response:")
#     print(response.content)
#     print()

#     # Example 2: Targeted scraping with CSS selector
#     response = await scraper.aprocess(
#         "Extract the main article content from https://example.com/blog/article using the selector '.article-content'"
#     )
#     print("Example 2 Response:")
#     print(response.content)
#     print()

#     # Example 3: Complex operation with cleaning
#     response = await scraper.aprocess(
#         "Scrape https://example.com/about, extract the team information using '.team-members', clean the text by removing extra whitespace, and format it as a summary."
#     )
#     print("Example 3 Response:")
#     print(response.content)
