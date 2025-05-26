"""
Legion Framework Hello World Example
This demonstrates basic agent creation and tool usage in Legion.
"""

from legion import agent, tool
from typing import Annotated
from pydantic import Field
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@agent(model="openai:gpt-4o-mini", temperature=0.2)
class HelloWorldAgent:
    """A simple agent that demonstrates basic Legion framework capabilities."""
    
    @tool
    def greet_user(
        self,
        name: Annotated[str, Field(description="The name of the person to greet")]
    ) -> str:
        """Greet a user by name with a friendly message."""
        return f"Hello, {name}! Welcome to the Legion framework demonstration."
    
    @tool
    def calculate_sum(
        self,
        a: Annotated[int, Field(description="First number")],
        b: Annotated[int, Field(description="Second number")]
    ) -> int:
        """Calculate the sum of two numbers."""
        return a + b

async def main():
    """Demonstrate the Legion Hello World agent."""
    agent = HelloWorldAgent()
    
    print("=== Legion Framework Hello World Demo ===")
    print()
    
    # Test greeting functionality
    print("Testing greeting functionality...")
    response1 = await agent.aprocess("Please greet a user named 'Alice'")
    print(f"Agent Response: {response1}")
    print()
    
    # Test calculation functionality
    print("Testing calculation functionality...")
    response2 = await agent.aprocess("Please calculate the sum of 15 and 27")
    print(f"Agent Response: {response2}")
    print()
    
    # Test conversational capability
    print("Testing conversational capability...")
    response3 = await agent.aprocess("What tools do you have available?")
    print(f"Agent Response: {response3}")

if __name__ == "__main__":
    asyncio.run(main())
