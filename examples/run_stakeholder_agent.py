#!/usr/bin/env python3
"""
Example script demonstrating how to run the StakeholderIdentificationAgent.

This script shows how to:
1. Load application configuration (including LLM API keys from .env)
2. Create the LegalAgentFactory with real LLM integration
3. Register and instantiate the StakeholderIdentificationAgent
4. Execute stakeholder identification with sample data
5. Display the structured results

Prerequisites:
- Copy llai/.env.example to llai/.env
- Add your OpenAI API key: OPENAI_API_KEY=your_key_here
- Optionally add Anthropic API key: ANTHROPIC_API_KEY=your_key_here

Usage:
    python examples/run_stakeholder_agent.py
"""
import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
import asyncio
import json
from typing import Dict, Any

from llai.agents.stakeholder_identification_agent_atomic import (
    StakeholderIdentificationAgent,
    StakeholderIdentificationAgentConfig,
    StakeholderIdentificationInputSchema
)
from llai.agents.agent_factory import create_legal_agent_factory
from llai.config.settings import get_config
from llai.utils.logging_setup import get_logger

# Initialize logger
logger = get_logger(__name__)


def print_section(title: str, content: Any = None) -> None:
    """Print a formatted section with title and optional content."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    if content is not None:
        if isinstance(content, (dict, list)):
            print(json.dumps(content, indent=2))
        else:
            print(content)


async def main():
    """Main function demonstrating StakeholderIdentificationAgent usage."""
    
    print_section("Legal AI Marketing Assistant - Stakeholder Identification Demo")
    
    try:
        # Step 1: Load application configuration
        print_section("Step 1: Loading Configuration")
        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"  - App Name: {config.app_name}")
        print(f"  - Version: {config.version}")
        print(f"  - Default LLM Model: {config.llm_provider.default_model}")
        print(f"  - OpenAI API Key: {'✓ Set' if config.llm_provider.openai_api_key else '✗ Not set'}")
        print(f"  - Anthropic API Key: {'✓ Set' if config.llm_provider.anthropic_api_key else '✗ Not set'}")
        
        # Step 2: Create the Legal Agent Factory
        print_section("Step 2: Creating Legal Agent Factory")
        factory = create_legal_agent_factory(
            global_config=config,
            use_mock_providers=True,  # Use mock context providers for simplicity
            use_mock_llm=False       # Try to use real LLM (will fallback to mock if no API keys)
        )
        print(f"✓ Legal Agent Factory created")
        
        # Step 3: Register the StakeholderIdentificationAgent
        print_section("Step 3: Registering Agent Type")
        factory.register_agent_type("stakeholder_identification", StakeholderIdentificationAgent)
        print(f"✓ StakeholderIdentificationAgent registered")
        print(f"  Available agent types: {factory.get_available_agent_types()}")
        
        # Step 4: Create the agent instance (factory will handle configuration)
        print_section("Step 4: Creating Agent Instance")
        # Get LLM client first to pass to config
        llm_client = factory.llm_client_manager.get_default_client()
        
        # Create agent configuration with proper client
        agent_config = StakeholderIdentificationAgentConfig(
            client=llm_client,
            model=config.llm_provider.default_model,
            default_jurisdiction="ON",
            include_external_stakeholders=True,
            stakeholder_detail_level="detailed",
            max_stakeholders_per_category=15,
            include_communication_plan=True,
            compliance_threshold=0.8,
            enable_strict_compliance_checks=True
        )
        
        print(f"✓ Agent configuration created")
        print(f"  - Model: {agent_config.model}")
        print(f"  - Jurisdiction: {agent_config.default_jurisdiction}")
        print(f"  - Include External Stakeholders: {agent_config.include_external_stakeholders}")
        print(f"  - Detail Level: {agent_config.stakeholder_detail_level}")
        
        # Create agent instance using factory
        agent = factory.create_agent(
            agent_type="stakeholder_identification",
            agent_config=agent_config
        )
        print(f"✓ StakeholderIdentificationAgent created successfully")
        print(f"  - Agent Type: {type(agent).__name__}")
        print(f"  - LLM Client Type: {type(llm_client).__name__}")
        
        # Step 6: Prepare sample input data
        print_section("Step 6: Preparing Sample Input Data")
        sample_input = StakeholderIdentificationInputSchema(
            company_structure="""
            Our law firm has the following structure:
            - Managing Partner (Sarah Johnson) - oversees all operations
            - Marketing Director (Mike Chen) - leads marketing initiatives
            - Content Manager (Lisa Rodriguez) - manages content creation and SEO
            - Legal Compliance Officer (David Kim) - ensures regulatory compliance
            - IT Manager (Alex Thompson) - handles technology and digital platforms
            - Business Development Manager (Emma Wilson) - client acquisition and relationships
            - Administrative Assistant (Tom Brown) - supports marketing operations
            
            We also work with external vendors:
            - SEO Agency (Digital Legal Solutions) - technical SEO and optimization
            - Graphic Designer (Creative Law Designs) - visual content creation
            - Web Developer (LawTech Solutions) - website maintenance and updates
            """,
            organization_size="medium",
            industry_focus="Personal injury, family law, and estate planning",
            current_marketing_team="Small in-house team with external vendor support",
            project_scope="Comprehensive digital marketing strategy overhaul including website redesign, content strategy, and social media presence"
        )
        
        print(f"✓ Sample input data prepared")
        print(f"  - Organization Size: {sample_input.organization_size}")
        print(f"  - Industry Focus: {sample_input.industry_focus}")
        print(f"  - Project Scope: {sample_input.project_scope[:100]}...")
        
        # Step 7: Execute stakeholder identification
        print_section("Step 7: Executing Stakeholder Identification")
        print("🔄 Processing stakeholder identification...")
        
        result = await agent.identify_stakeholders(sample_input)
        
        print(f"✓ Stakeholder identification completed successfully!")
        print(f"  - Total Stakeholders: {result.total_stakeholders}")
        print(f"  - Internal Stakeholders: {len(result.internal_stakeholders)}")
        print(f"  - External Stakeholders: {len(result.external_stakeholders)}")
        print(f"  - Decision Makers: {len(result.decision_makers)}")
        
        # Step 8: Display detailed results
        print_section("Step 8: Detailed Results")
        
        # Internal Stakeholders
        print("\n📋 INTERNAL STAKEHOLDERS:")
        for i, stakeholder in enumerate(result.internal_stakeholders, 1):
            print(f"\n  {i}. {stakeholder.name}")
            print(f"     Role: {stakeholder.role}")
            print(f"     Influence Level: {stakeholder.influence_level}")
            print(f"     Involvement Type: {stakeholder.involvement_type}")
            print(f"     Responsibilities: {', '.join(stakeholder.responsibilities)}")
        
        # External Stakeholders
        if result.external_stakeholders:
            print("\n🌐 EXTERNAL STAKEHOLDERS:")
            for i, stakeholder in enumerate(result.external_stakeholders, 1):
                print(f"\n  {i}. {stakeholder.name}")
                print(f"     Role: {stakeholder.role}")
                print(f"     Influence Level: {stakeholder.influence_level}")
                print(f"     Involvement Type: {stakeholder.involvement_type}")
                print(f"     Responsibilities: {', '.join(stakeholder.responsibilities)}")
        
        # Stakeholder Matrix
        print("\n📊 STAKEHOLDER MATRIX:")
        for category, stakeholders in result.stakeholder_matrix.items():
            print(f"  {category.title()}: {', '.join(stakeholders)}")
        
        # Communication Plan
        print("\n📞 COMMUNICATION PLAN:")
        for i, plan_item in enumerate(result.communication_plan, 1):
            print(f"  {i}. {plan_item}")
        
        # Decision Makers
        print(f"\n👥 KEY DECISION MAKERS: {', '.join(result.decision_makers)}")
        
        # Analysis Summary
        print(f"\n📝 ANALYSIS SUMMARY:")
        print(f"  {result.analysis_summary}")
        
        # Step 9: Validate dependencies
        print_section("Step 9: Factory Dependency Validation")
        dependencies = factory.validate_dependencies()
        for dep_name, is_available in dependencies.items():
            status = "✓" if is_available else "✗"
            print(f"  {status} {dep_name}: {'Available' if is_available else 'Not Available'}")
        
        print_section("Demo Completed Successfully! 🎉")
        print("The StakeholderIdentificationAgent is working correctly.")
        print("\nNext steps:")
        print("1. Review the stakeholder analysis results above")
        print("2. Try modifying the sample input data to test different scenarios")
        print("3. Add your LLM API keys to llai/.env for real LLM responses")
        print("4. Explore other agent capabilities like platform inventory compilation")
        
    except Exception as e:
        print_section("❌ Error Occurred")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        
        print("\n🔧 Troubleshooting Tips:")
        print("1. Ensure you're running from the project root directory")
        print("2. Check that all dependencies are installed")
        print("3. Verify the llai/.env file exists with API keys (optional)")
        print("4. Check the logs for more detailed error information")


if __name__ == "__main__":
    """Run the stakeholder identification demo."""
    print("Starting Legal AI Marketing Assistant Demo...")
    asyncio.run(main())
