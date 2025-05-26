"""
Atomic Agents Framework Hello World Example
This demonstrates basic agent creation and tool usage in Atomic Agents.
"""

import instructor
import openai
import asyncio
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from pydantic import Field
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define input/output schemas
class GreetingInput(BaseIOSchema):
    """Input schema for greeting functionality."""
    name: str = Field(..., description="The name of the person to greet")

class GreetingOutput(BaseIOSchema):
    """Output schema for greeting results."""
    message: str = Field(..., description="The greeting message")

class CalculationInput(BaseIOSchema):
    """Input schema for calculation functionality."""
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")

class CalculationOutput(BaseIOSchema):
    """Output schema for calculation results."""
    result: int = Field(..., description="The sum of the two numbers")
    operation: str = Field(..., description="Description of the operation performed")

class AgentInput(BaseIOSchema):
    """Input schema for the agent."""
    chat_message: str = Field(..., description="The user's message to the agent")

class AgentOutput(BaseIOSchema):
    """Output schema for the agent."""
    chat_message: str = Field(..., description="The agent's response")
    tools_used: List[str] = Field(default_factory=list, description="List of tools used in the response")

# Define tools
class GreetingTool(BaseTool):
    """Tool for greeting users."""
    input_schema = GreetingInput
    output_schema = GreetingOutput
    
    def run(self, params: GreetingInput) -> GreetingOutput:
        """Greet a user by name with a friendly message."""
        message = f"Hello, {params.name}! Welcome to the Atomic Agents framework demonstration."
        return GreetingOutput(message=message)

class CalculatorTool(BaseTool):
    """Tool for performing calculations."""
    input_schema = CalculationInput
    output_schema = CalculationOutput
    
    def run(self, params: CalculationInput) -> CalculationOutput:
        """Calculate the sum of two numbers."""
        result = params.a + params.b
        operation = f"Added {params.a} and {params.b}"
        return CalculationOutput(result=result, operation=operation)

# Define the agent
class HelloWorldAgent(BaseAgent):
    """A simple agent that demonstrates basic Atomic Agents framework capabilities."""
    
    def __init__(self, config: BaseAgentConfig):
        super().__init__(config)
        
        # Register tools
        self.register_tool("greeting", GreetingTool(BaseToolConfig()))
        self.register_tool("calculator", CalculatorTool(BaseToolConfig()))

async def main():
    """Demonstrate the Atomic Agents Hello World agent."""
    print("=== Atomic Agents Framework Hello World Demo ===")
    print()
    
    # Initialize memory
    memory = AgentMemory(max_messages=10)
    
    # Set up client
    client = instructor.from_openai(openai.OpenAI())
    
    # Create system prompt generator
    system_prompt_generator = SystemPromptGenerator(
        background=[
            "You are a helpful demonstration agent for the Atomic Agents framework.",
            "You have access to greeting and calculation tools.",
            "Use the tools when appropriate to fulfill user requests."
        ],
        steps=[
            "Understand the user's request",
            "Determine if any tools are needed",
            "Use the appropriate tools if necessary",
            "Provide a helpful response"
        ],
        output_instructions=[
            "Be friendly and helpful",
            "Explain what tools you used if any",
            "Provide clear and concise responses"
        ]
    )
    
    # Create agent configuration
    config = BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
        system_prompt_generator=system_prompt_generator,
        input_schema=AgentInput,
        output_schema=AgentOutput,
        temperature=0.2
    )
    
    # Create agent
    agent = HelloWorldAgent(config)
    
    # Test greeting functionality
    print("Testing greeting functionality...")
    response1 = agent.run(AgentInput(chat_message="Please greet a user named 'Alice'"))
    print(f"Agent Response: {response1.chat_message}")
    print(f"Tools Used: {response1.tools_used}")
    print()
    
    # Test calculation functionality
    print("Testing calculation functionality...")
    response2 = agent.run(AgentInput(chat_message="Please calculate the sum of 15 and 27"))
    print(f"Agent Response: {response2.chat_message}")
    print(f"Tools Used: {response2.tools_used}")
    print()
    
    # Test conversational capability
    print("Testing conversational capability...")
    response3 = agent.run(AgentInput(chat_message="What tools do you have available?"))
    print(f"Agent Response: {response3.chat_message}")
    print(f"Tools Used: {response3.tools_used}")

if __name__ == "__main__":
    asyncio.run(main())
