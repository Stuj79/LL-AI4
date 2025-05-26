"""
Stakeholder Identification Agent - Atomic Agents Implementation.

This module provides the Atomic Agents implementation of the StakeholderIdentificationAgent,
migrated from the Legion framework with enhanced legal marketing compliance features.
"""

from typing import Dict, List, Any, Optional
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
import logging

from llai.agents.legal_marketing_base_agent import (
    LegalMarketingBaseAgent,
    LegalMarketingAgentConfig
)
from llai.utils.logging_setup import get_logger
from llai.utils.exceptions_atomic import StakeholderIdentificationError

logger = get_logger(__name__)


# --- Input/Output Schemas ---

class StakeholderIdentificationInputSchema(BaseIOSchema):
    """Input schema for stakeholder identification."""
    company_structure: str = Field(
        ..., 
        description="Text describing company structure, departments, or team makeup"
    )
    organization_size: Optional[str] = Field(
        None, 
        description="Size of the organization (e.g., 'small', 'medium', 'large', 'enterprise')"
    )
    industry_focus: Optional[str] = Field(
        None, 
        description="Primary industry or legal practice areas"
    )
    current_marketing_team: Optional[str] = Field(
        None, 
        description="Description of current marketing team structure if any"
    )
    project_scope: Optional[str] = Field(
        None, 
        description="Scope of the marketing project or initiative"
    )

class StakeholderInfo(BaseIOSchema):
    """Schema for individual stakeholder information."""
    name: str = Field(..., description="Name or title of the stakeholder")
    role: str = Field(..., description="Role or position of the stakeholder")
    contact_info: str = Field("", description="Contact information for the stakeholder")
    responsibilities: List[str] = Field(
        default_factory=list, 
        description="List of stakeholder responsibilities"
    )
    influence_level: str = Field(
        "medium", 
        description="Level of influence in decision making ('low', 'medium', 'high')"
    )
    involvement_type: str = Field(
        "collaborative", 
        description="Type of involvement ('decision_maker', 'collaborative', 'consultative', 'informational')"
    )

class StakeholderIdentificationOutputSchema(BaseIOSchema):
    """Output schema for stakeholder identification results."""
    internal_stakeholders: List[StakeholderInfo] = Field(
        default_factory=list, 
        description="List of internal stakeholders"
    )
    external_stakeholders: List[StakeholderInfo] = Field(
        default_factory=list, 
        description="List of external stakeholders"
    )
    stakeholder_matrix: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Matrix mapping stakeholder categories to stakeholder names"
    )
    communication_plan: List[str] = Field(
        default_factory=list, 
        description="Recommended communication strategies for different stakeholder groups"
    )
    decision_makers: List[str] = Field(
        default_factory=list, 
        description="List of key decision makers identified"
    )
    total_stakeholders: int = Field(0, description="Total number of stakeholders identified")
    analysis_summary: str = Field("", description="Summary of the stakeholder analysis")

class PlatformInventoryInputSchema(BaseIOSchema):
    """Input schema for platform inventory compilation."""
    platform_data: str = Field(
        ..., 
        description="Information about marketing platforms used"
    )
    access_requirements: Optional[str] = Field(
        None, 
        description="Specific access requirements or constraints"
    )
    integration_needs: Optional[str] = Field(
        None, 
        description="Integration requirements between platforms"
    )

class PlatformInfo(BaseIOSchema):
    """Schema for platform information."""
    name: str = Field(..., description="Name of the platform")
    platform_type: str = Field(..., description="Type of platform (e.g., 'website', 'social_media', 'email')")
    access_level: str = Field(..., description="Level of access available")
    url: Optional[str] = Field(None, description="URL or identifier for the platform")
    account: Optional[str] = Field(None, description="Account identifier")
    integration_status: str = Field("unknown", description="Integration status with other platforms")

class PlatformInventoryOutputSchema(BaseIOSchema):
    """Output schema for platform inventory results."""
    website_platforms: List[PlatformInfo] = Field(
        default_factory=list, 
        description="Website and content management platforms"
    )
    social_media_platforms: List[PlatformInfo] = Field(
        default_factory=list, 
        description="Social media platforms"
    )
    email_marketing_platforms: List[PlatformInfo] = Field(
        default_factory=list, 
        description="Email marketing platforms"
    )
    analytics_platforms: List[PlatformInfo] = Field(
        default_factory=list, 
        description="Analytics and tracking platforms"
    )
    other_platforms: List[PlatformInfo] = Field(
        default_factory=list, 
        description="Other marketing-related platforms"
    )
    platform_summary: Dict[str, int] = Field(
        default_factory=dict, 
        description="Summary count of platforms by type"
    )
    integration_opportunities: List[str] = Field(
        default_factory=list, 
        description="Identified integration opportunities"
    )
    access_gaps: List[str] = Field(
        default_factory=list, 
        description="Identified access gaps or limitations"
    )


# --- Agent Configuration ---

class StakeholderIdentificationAgentConfig(LegalMarketingAgentConfig):
    """Configuration specific to stakeholder identification agent."""
    include_external_stakeholders: bool = Field(
        True, 
        description="Whether to include external stakeholders in analysis"
    )
    stakeholder_detail_level: str = Field(
        "standard", 
        description="Level of detail for stakeholder analysis ('basic', 'standard', 'detailed')"
    )
    max_stakeholders_per_category: int = Field(
        20, 
        description="Maximum number of stakeholders to identify per category"
    )
    include_communication_plan: bool = Field(
        True, 
        description="Whether to include communication planning recommendations"
    )


# --- Stakeholder Identification Agent ---

class StakeholderIdentificationAgent(LegalMarketingBaseAgent):
    """
    Agent that identifies and categorizes stakeholders in a legal marketing team.
    
    This agent extends LegalMarketingBaseAgent with specific functionality for:
    - Identifying internal and external stakeholders
    - Categorizing stakeholders by role and influence
    - Creating stakeholder communication plans
    - Compiling platform inventories
    """
    
    def __init__(self, config: StakeholderIdentificationAgentConfig, **kwargs):
        """
        Initialize the stakeholder identification agent.
        
        Args:
            config: Agent-specific configuration
            **kwargs: Additional arguments passed to base agent
        """
        super().__init__(config, **kwargs)
        self.agent_config = config
        logger.info("StakeholderIdentificationAgent initialized")
    
    async def identify_stakeholders(
        self, 
        input_data: StakeholderIdentificationInputSchema
    ) -> StakeholderIdentificationOutputSchema:
        """
        Identify and categorize stakeholders based on company structure information.
        
        Args:
            input_data: Input data containing company structure information
            
        Returns:
            Structured stakeholder identification results
            
        Raises:
            StakeholderIdentificationError: If stakeholder identification fails
        """
        try:
            logger.info("Starting stakeholder identification process")
            
            # Log the operation for audit purposes
            await self._audit_log_operation(
                operation="identify_stakeholders",
                input_summary=f"Company structure analysis for {input_data.organization_size or 'unspecified'} organization",
                output_summary="Stakeholder identification in progress"
            )
            
            # Construct prompt for LLM
            prompt = await self._construct_stakeholder_prompt(input_data)
            
            # Process with LLM (this would be the actual LLM call in production)
            llm_response = await self._process_with_llm(prompt)
            
            # Parse and structure the response
            result = await self._parse_stakeholder_response(llm_response, input_data)
            
            # Apply legal marketing compliance features
            result = await self._post_process_response(
                result, 
                content_type="stakeholder_analysis",
                marketing_channel="internal_planning"
            )
            
            # Final audit log
            await self._audit_log_operation(
                operation="identify_stakeholders_completed",
                input_summary=f"Analyzed {input_data.organization_size or 'unspecified'} organization",
                output_summary=f"Identified {result.total_stakeholders} stakeholders across {len(result.internal_stakeholders) + len(result.external_stakeholders)} categories"
            )
            
            logger.info(f"Stakeholder identification completed: {result.total_stakeholders} stakeholders identified")
            return result
            
        except Exception as e:
            logger.error(f"Stakeholder identification failed: {str(e)}")
            raise StakeholderIdentificationError(
                error_type="STAKEHOLDER_IDENTIFICATION_FAILED",
                message="Failed to identify stakeholders",
                context={
                    "organization_size": input_data.organization_size,
                    "industry_focus": input_data.industry_focus,
                    "error": str(e)
                }
            )
    
    async def compile_platform_inventory(
        self, 
        input_data: PlatformInventoryInputSchema
    ) -> PlatformInventoryOutputSchema:
        """
        Compile an inventory of marketing platforms from provided data.
        
        Args:
            input_data: Input data containing platform information
            
        Returns:
            Structured platform inventory results
            
        Raises:
            StakeholderIdentificationError: If platform inventory compilation fails
        """
        try:
            logger.info("Starting platform inventory compilation")
            
            # Log the operation
            await self._audit_log_operation(
                operation="compile_platform_inventory",
                input_summary="Platform data analysis",
                output_summary="Platform inventory compilation in progress"
            )
            
            # Construct prompt for LLM
            prompt = await self._construct_platform_prompt(input_data)
            
            # Process with LLM
            llm_response = await self._process_with_llm(prompt)
            
            # Parse and structure the response
            result = await self._parse_platform_response(llm_response, input_data)
            
            # Apply compliance features
            result = await self._post_process_response(
                result,
                content_type="platform_inventory",
                marketing_channel="internal_planning"
            )
            
            # Final audit log
            total_platforms = sum(result.platform_summary.values()) if result.platform_summary else 0
            await self._audit_log_operation(
                operation="compile_platform_inventory_completed",
                input_summary="Platform data analyzed",
                output_summary=f"Compiled inventory of {total_platforms} platforms"
            )
            
            logger.info(f"Platform inventory compilation completed: {total_platforms} platforms catalogued")
            return result
            
        except Exception as e:
            logger.error(f"Platform inventory compilation failed: {str(e)}")
            raise StakeholderIdentificationError(
                error_type="PLATFORM_INVENTORY_FAILED",
                message="Failed to compile platform inventory",
                context={
                    "error": str(e)
                }
            )
    
    async def _construct_stakeholder_prompt(self, input_data: StakeholderIdentificationInputSchema) -> str:
        """Construct prompt for stakeholder identification."""
        prompt = f"""
        As a legal marketing consultant, analyze the following company structure and identify key stakeholders for a marketing initiative.

        Company Structure: {input_data.company_structure}
        Organization Size: {input_data.organization_size or 'Not specified'}
        Industry Focus: {input_data.industry_focus or 'General legal services'}
        Current Marketing Team: {input_data.current_marketing_team or 'Not specified'}
        Project Scope: {input_data.project_scope or 'General marketing improvement'}

        Please identify and categorize stakeholders into:
        1. Internal stakeholders (employees, partners, management)
        2. External stakeholders (clients, vendors, regulatory bodies)

        For each stakeholder, provide:
        - Name/Title
        - Role and responsibilities
        - Influence level (low/medium/high)
        - Involvement type (decision_maker/collaborative/consultative/informational)

        Also provide:
        - A stakeholder matrix organizing them by category
        - Communication plan recommendations
        - Key decision makers
        - Analysis summary

        Focus on stakeholders relevant to legal marketing compliance and effectiveness.
        """
        
        return prompt
    
    async def _construct_platform_prompt(self, input_data: PlatformInventoryInputSchema) -> str:
        """Construct prompt for platform inventory."""
        prompt = f"""
        As a legal marketing technology consultant, analyze the following platform information and create a comprehensive inventory.

        Platform Data: {input_data.platform_data}
        Access Requirements: {input_data.access_requirements or 'Not specified'}
        Integration Needs: {input_data.integration_needs or 'Not specified'}

        Please categorize platforms into:
        1. Website/Content Management platforms
        2. Social Media platforms
        3. Email Marketing platforms
        4. Analytics/Tracking platforms
        5. Other marketing-related platforms

        For each platform, provide:
        - Platform name
        - Platform type
        - Access level available
        - URL or identifier (if applicable)
        - Account information (if applicable)
        - Integration status

        Also provide:
        - Platform summary counts by type
        - Integration opportunities
        - Access gaps or limitations

        Consider legal marketing compliance requirements for each platform type.
        """
        
        return prompt
    
    async def _process_with_llm(self, prompt: str) -> str:
        """Process prompt with LLM (mock implementation for now)."""
        # In a real implementation, this would call the actual LLM
        # For now, return a mock response
        return f"Mock LLM response for prompt: {prompt[:100]}..."
    
    async def _parse_stakeholder_response(
        self, 
        llm_response: str, 
        input_data: StakeholderIdentificationInputSchema
    ) -> StakeholderIdentificationOutputSchema:
        """Parse LLM response into structured stakeholder data."""
        # Mock implementation - in production this would parse actual LLM response
        internal_stakeholders = [
            StakeholderInfo(
                name="Marketing Director",
                role="Leadership",
                responsibilities=["Strategy oversight", "Budget approval", "Team management"],
                influence_level="high",
                involvement_type="decision_maker"
            ),
            StakeholderInfo(
                name="Content Manager",
                role="Management",
                responsibilities=["Content calendar", "Quality assurance", "SEO optimization"],
                influence_level="medium",
                involvement_type="collaborative"
            ),
            StakeholderInfo(
                name="Legal Compliance Officer",
                role="Compliance",
                responsibilities=["Regulatory compliance", "Content review", "Risk assessment"],
                influence_level="high",
                involvement_type="consultative"
            )
        ]
        
        external_stakeholders = [
            StakeholderInfo(
                name="SEO Agency",
                role="Vendor",
                responsibilities=["Technical SEO", "Keyword research", "Performance reporting"],
                influence_level="medium",
                involvement_type="collaborative"
            ),
            StakeholderInfo(
                name="Law Society Representative",
                role="Regulatory",
                responsibilities=["Compliance guidance", "Rule interpretation"],
                influence_level="high",
                involvement_type="consultative"
            )
        ]
        
        return StakeholderIdentificationOutputSchema(
            internal_stakeholders=internal_stakeholders,
            external_stakeholders=external_stakeholders if self.agent_config.include_external_stakeholders else [],
            stakeholder_matrix={
                "leadership": ["Marketing Director", "Legal Compliance Officer"],
                "management": ["Content Manager"],
                "vendors": ["SEO Agency"],
                "regulatory": ["Law Society Representative"]
            },
            communication_plan=[
                "Weekly status meetings with leadership team",
                "Bi-weekly content review sessions with compliance officer",
                "Monthly vendor performance reviews",
                "Quarterly regulatory compliance check-ins"
            ],
            decision_makers=["Marketing Director", "Legal Compliance Officer"],
            total_stakeholders=len(internal_stakeholders) + (len(external_stakeholders) if self.agent_config.include_external_stakeholders else 0),
            analysis_summary=f"Identified {len(internal_stakeholders)} internal and {len(external_stakeholders) if self.agent_config.include_external_stakeholders else 0} external stakeholders for {input_data.organization_size or 'the'} organization's legal marketing initiative."
        )
    
    async def _parse_platform_response(
        self, 
        llm_response: str, 
        input_data: PlatformInventoryInputSchema
    ) -> PlatformInventoryOutputSchema:
        """Parse LLM response into structured platform data."""
        # Mock implementation - in production this would parse actual LLM response
        website_platforms = [
            PlatformInfo(
                name="Company Website",
                platform_type="website",
                access_level="Admin",
                url="https://example-law-firm.com",
                integration_status="integrated"
            )
        ]
        
        social_media_platforms = [
            PlatformInfo(
                name="LinkedIn",
                platform_type="social_media",
                access_level="Admin",
                url="linkedin.com/company/example-law-firm",
                integration_status="standalone"
            ),
            PlatformInfo(
                name="Twitter",
                platform_type="social_media",
                access_level="Editor",
                url="twitter.com/example_law_firm",
                integration_status="standalone"
            )
        ]
        
        email_platforms = [
            PlatformInfo(
                name="Mailchimp",
                platform_type="email_marketing",
                access_level="Admin",
                account="marketing@example-law-firm.com",
                integration_status="integrated"
            )
        ]
        
        analytics_platforms = [
            PlatformInfo(
                name="Google Analytics",
                platform_type="analytics",
                access_level="Admin",
                account="UA-12345678-1",
                integration_status="integrated"
            )
        ]
        
        return PlatformInventoryOutputSchema(
            website_platforms=website_platforms,
            social_media_platforms=social_media_platforms,
            email_marketing_platforms=email_platforms,
            analytics_platforms=analytics_platforms,
            other_platforms=[],
            platform_summary={
                "website": len(website_platforms),
                "social_media": len(social_media_platforms),
                "email_marketing": len(email_platforms),
                "analytics": len(analytics_platforms),
                "other": 0
            },
            integration_opportunities=[
                "Connect social media platforms to analytics for unified reporting",
                "Integrate email marketing with website for lead capture",
                "Set up cross-platform content syndication"
            ],
            access_gaps=[
                "Limited access to Twitter account (Editor level only)",
                "No access to advanced analytics features"
            ]
        )
