from legion import agent, tool
# from legion.agents import TaskAgent
# from legion.types import AgentResponse, Message
from typing import List, Dict, Any, Optional, Annotated
from pydantic import Field
import logging

logger = logging.getLogger(__name__)

@agent(model="openai:gpt-4o-mini", temperature=0.7)
class CopywriterAgent:
    """Agent to generate marketing copy for legal services."""

    @tool
    def create_copy(
        self,
        topic: Annotated[str, Field(description="Topic to create marketing copy for")],
        tone: Annotated[str, Field(description="Tone of the copy (e.g., 'professional', 'casual', 'authoritative')")] = "professional"
    ) -> str:
        """Generate marketing copy for legal services on a specific topic with the desired tone."""
        # Create a simple copy draft.
        return f"Marketing copy for {topic} with a {tone} tone."
    
@agent(model="openai:gpt-4o-mini", temperature=0.6)
class ContentStrategistAgent:
    """Agent to develop content strategies and plans."""

    @tool
    def plan_strategy(
        self,
        project: Annotated[str, Field(description="Project or campaign to develop a content strategy for")],
        steps: Annotated[int, Field(description="Number of steps to include in the strategy")] = 3
    ) -> str:
        """Develop a content strategy plan with specified number of steps."""
        # Provide a basic strategy plan.
        strategy_steps = "\n".join([f"Step {i+1}: Define objective" for i in range(steps)])
        return f"Content strategy for {project}:\n{strategy_steps}"

@agent(model="openai:gpt-4o-mini", temperature=0.5)
class BrandVoiceAgent:
    """Agent to check and enforce brand voice consistency."""

    @tool
    def validate_voice(
        self,
        content: Annotated[str, Field(description="Content to validate for brand voice consistency")],
        brand_voice: Annotated[str, Field(description="Brand voice guidelines or style to validate against")]
    ) -> str:
        """Check content for consistency with a specified brand voice and provide validation results."""
        # Simulate validation by echoing the check.
        return f"Content validated against the brand voice: {brand_voice}"
