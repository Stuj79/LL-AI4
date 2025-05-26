"""
Legal Marketing Base Agent for Atomic Agents migration.

This module provides the foundational base agent class for all legal marketing agents,
extending Atomic Agents BaseAgent with legal marketing domain-specific features including
disclaimer management, compliance checking, and confidentiality handling.
"""

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field, ConfigDict
from typing import Dict, List, Any, Optional, Union, ClassVar
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from llai.utils.exceptions_atomic import (
    LegalMarketingAgentError,
    ComplianceValidationError,
    DisclaimerInjectionError
)
from llai.utils.logging_setup import get_logger

logger = get_logger(__name__)


# --- Legal Marketing Domain Schemas ---

class Disclaimer(BaseIOSchema):
    """Schema for legal disclaimer information."""
    id: str = Field(..., description="Unique identifier for the disclaimer")
    text: str = Field(..., description="The disclaimer text content")
    jurisdiction: str = Field(..., description="Jurisdiction where this disclaimer applies (e.g., 'ON', 'BC', 'AB')")
    content_type: str = Field(..., description="Type of content this disclaimer applies to (e.g., 'marketing', 'legal_advice', 'general')")
    mandatory: bool = Field(True, description="Whether this disclaimer is mandatory for the specified context")
    position: str = Field("footer", description="Where the disclaimer should be positioned ('header', 'footer', 'inline')")

class AdvertisingRule(BaseIOSchema):
    """Schema for legal advertising rule information."""
    rule_id: str = Field(..., description="Unique identifier for the advertising rule")
    jurisdiction: str = Field(..., description="Jurisdiction where this rule applies")
    rule_text: str = Field(..., description="The text of the advertising rule")
    category: str = Field(..., description="Category of the rule (e.g., 'solicitation', 'testimonials', 'guarantees')")
    severity: str = Field(..., description="Severity level if violated ('low', 'medium', 'high', 'critical')")
    enforcement_body: str = Field(..., description="Body that enforces this rule (e.g., 'Law Society of Ontario')")

class EthicalGuideline(BaseIOSchema):
    """Schema for ethical guideline information."""
    guideline_id: str = Field(..., description="Unique identifier for the ethical guideline")
    title: str = Field(..., description="Title of the ethical guideline")
    description: str = Field(..., description="Detailed description of the guideline")
    task_type: str = Field(..., description="Type of task this guideline applies to")
    compliance_level: str = Field(..., description="Required compliance level ('recommended', 'required', 'mandatory')")
    reference: str = Field(..., description="Reference to source document or rule")

class ComplianceStatus(BaseIOSchema):
    """Schema for compliance validation results."""
    is_compliant: bool = Field(..., description="Whether the content/action is compliant")
    compliance_score: float = Field(..., ge=0.0, le=1.0, description="Compliance score between 0 and 1")
    violations: List[str] = Field(default_factory=list, description="List of compliance violations found")
    recommendations: List[str] = Field(default_factory=list, description="List of recommendations for improvement")
    applied_rules: List[str] = Field(default_factory=list, description="List of rule IDs that were applied")
    review_required: bool = Field(False, description="Whether human review is required")

class AuditLogEntry(BaseIOSchema):
    """Schema for audit log entries."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the audit entry")
    agent_type: str = Field(..., description="Type of agent that generated this entry")
    operation: str = Field(..., description="Operation that was performed")
    input_summary: str = Field(..., description="Summary of the input data")
    output_summary: str = Field(..., description="Summary of the output data")
    compliance_status: Optional[ComplianceStatus] = Field(None, description="Compliance status if applicable")
    disclaimers_applied: List[str] = Field(default_factory=list, description="List of disclaimer IDs that were applied")
    user_id: Optional[str] = Field(None, description="User ID if applicable")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


# --- Configuration Schemas ---

class LegalMarketingAgentConfig(BaseAgentConfig):
    """Configuration schema for legal marketing agents."""
    default_jurisdiction: Optional[str] = Field(None, description="Default jurisdiction for compliance rules (e.g., 'ON', 'BC', 'AB')")
    disclaimer_profile_id: Optional[str] = Field(None, description="ID for disclaimer set to use")
    enable_strict_compliance_checks: bool = Field(True, description="Enable strict compliance validation")
    audit_logging_level: str = Field("standard", description="Level of audit logging detail ('minimal', 'standard', 'detailed')")
    confidentiality_handling_mode: str = Field("strict", description="PII processing approach ('strict', 'moderate', 'permissive')")
    human_review_required: bool = Field(False, description="Whether content needs human validation before publication")
    max_disclaimer_length: int = Field(500, description="Maximum length for disclaimer text")
    compliance_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum compliance score threshold")


# --- Context Provider Interfaces ---

class DisclaimerProvider(ABC):
    """Abstract base class for disclaimer providers."""
    
    @abstractmethod
    async def get_disclaimers(self, jurisdiction: str, content_type: str) -> List[Disclaimer]:
        """Get applicable disclaimers for the given context."""
        pass

class AdvertisingRuleProvider(ABC):
    """Abstract base class for advertising rule providers."""
    
    @abstractmethod
    async def get_rules(self, jurisdiction: str, marketing_channel: str) -> List[AdvertisingRule]:
        """Get applicable advertising rules for the given context."""
        pass

class EthicalGuidelineProvider(ABC):
    """Abstract base class for ethical guideline providers."""
    
    @abstractmethod
    async def get_guidelines(self, task_type: str) -> List[EthicalGuideline]:
        """Get applicable ethical guidelines for the given task type."""
        pass


# --- Legal Marketing Base Agent ---

class LegalMarketingBaseAgent(BaseAgent):
    """
    Base agent class for all legal marketing agents.
    
    Extends Atomic Agents BaseAgent with legal marketing domain-specific features
    including disclaimer management, compliance checking, and confidentiality handling.
    """
    
    def __init__(
        self,
        config: LegalMarketingAgentConfig,
        disclaimer_provider: Optional[DisclaimerProvider] = None,
        advertising_rule_provider: Optional[AdvertisingRuleProvider] = None,
        ethical_guideline_provider: Optional[EthicalGuidelineProvider] = None
    ):
        """
        Initialize the legal marketing base agent.
        
        Args:
            config: Configuration for the agent
            disclaimer_provider: Provider for disclaimer information
            advertising_rule_provider: Provider for advertising rules
            ethical_guideline_provider: Provider for ethical guidelines
        """
        super().__init__(config)
        self.legal_config = config
        self.disclaimer_provider = disclaimer_provider
        self.advertising_rule_provider = advertising_rule_provider
        self.ethical_guideline_provider = ethical_guideline_provider
        self._audit_log: List[AuditLogEntry] = []
    
    async def _inject_disclaimers(
        self, 
        response: BaseIOSchema, 
        content_type: str = "marketing"
    ) -> BaseIOSchema:
        """
        Inject appropriate disclaimers into the response.
        
        Args:
            response: The response to inject disclaimers into
            content_type: Type of content for disclaimer selection
            
        Returns:
            Response with disclaimers injected
            
        Raises:
            DisclaimerInjectionError: If disclaimer injection fails
        """
        try:
            if not self.disclaimer_provider or not self.legal_config.default_jurisdiction:
                logger.warning("No disclaimer provider or jurisdiction configured, skipping disclaimer injection")
                return response
            
            disclaimers = await self.disclaimer_provider.get_disclaimers(
                self.legal_config.default_jurisdiction,
                content_type
            )
            
            if not disclaimers:
                logger.info(f"No disclaimers found for jurisdiction {self.legal_config.default_jurisdiction} and content type {content_type}")
                return response
            
            # Apply disclaimers based on position
            disclaimer_texts = []
            disclaimer_ids = []
            
            for disclaimer in disclaimers:
                if disclaimer.mandatory or len(disclaimer.text) <= self.legal_config.max_disclaimer_length:
                    disclaimer_texts.append(disclaimer.text)
                    disclaimer_ids.append(disclaimer.id)
            
            if disclaimer_texts and hasattr(response, 'content'):
                # Inject disclaimers into content
                disclaimer_section = "\n\n--- Legal Disclaimers ---\n" + "\n\n".join(disclaimer_texts)
                response.content = response.content + disclaimer_section
                
                # Log disclaimer application
                await self._audit_log_operation(
                    operation="disclaimer_injection",
                    input_summary=f"Content type: {content_type}",
                    output_summary=f"Applied {len(disclaimer_ids)} disclaimers",
                    disclaimers_applied=disclaimer_ids
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to inject disclaimers: {str(e)}")
            raise DisclaimerInjectionError(
                error_type="DISCLAIMER_INJECTION_FAILED",
                message="Failed to inject disclaimers into response",
                context={
                    "content_type": content_type,
                    "jurisdiction": self.legal_config.default_jurisdiction,
                    "error": str(e)
                }
            )
    
    async def _validate_compliance(
        self, 
        content: str, 
        marketing_channel: str = "general"
    ) -> ComplianceStatus:
        """
        Validate content against legal marketing compliance rules.
        
        Args:
            content: Content to validate
            marketing_channel: Marketing channel for rule selection
            
        Returns:
            Compliance validation results
            
        Raises:
            ComplianceValidationError: If compliance validation fails
        """
        try:
            if not self.legal_config.enable_strict_compliance_checks:
                return ComplianceStatus(
                    is_compliant=True,
                    compliance_score=1.0,
                    violations=[],
                    recommendations=[],
                    applied_rules=[],
                    review_required=False
                )
            
            violations = []
            recommendations = []
            applied_rules = []
            
            # Get applicable rules
            if self.advertising_rule_provider and self.legal_config.default_jurisdiction:
                rules = await self.advertising_rule_provider.get_rules(
                    self.legal_config.default_jurisdiction,
                    marketing_channel
                )
                
                # Basic compliance checks
                content_lower = content.lower()
                
                for rule in rules:
                    applied_rules.append(rule.rule_id)
                    
                    # Check for common violations
                    if rule.category == "guarantees" and any(word in content_lower for word in ["guarantee", "guaranteed", "ensure"]):
                        violations.append(f"Potential guarantee violation: {rule.rule_text}")
                    
                    if rule.category == "solicitation" and any(word in content_lower for word in ["call now", "act fast", "limited time"]):
                        violations.append(f"Potential solicitation violation: {rule.rule_text}")
                    
                    if rule.category == "testimonials" and any(word in content_lower for word in ["testimonial", "review", "client says"]):
                        recommendations.append(f"Consider disclaimer for testimonials: {rule.rule_text}")
            
            # Calculate compliance score
            compliance_score = max(0.0, 1.0 - (len(violations) * 0.2))
            is_compliant = compliance_score >= self.legal_config.compliance_threshold
            review_required = not is_compliant or self.legal_config.human_review_required
            
            return ComplianceStatus(
                is_compliant=is_compliant,
                compliance_score=compliance_score,
                violations=violations,
                recommendations=recommendations,
                applied_rules=applied_rules,
                review_required=review_required
            )
            
        except Exception as e:
            logger.error(f"Failed to validate compliance: {str(e)}")
            raise ComplianceValidationError(
                error_type="COMPLIANCE_VALIDATION_FAILED",
                message="Failed to validate content compliance",
                context={
                    "marketing_channel": marketing_channel,
                    "jurisdiction": self.legal_config.default_jurisdiction,
                    "error": str(e)
                }
            )
    
    async def _handle_confidential_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle confidential data according to configured privacy settings.
        
        Args:
            data: Data that may contain confidential information
            
        Returns:
            Data with confidential information handled appropriately
        """
        if self.legal_config.confidentiality_handling_mode == "strict":
            # Remove or mask potential PII
            sensitive_keys = ["email", "phone", "address", "ssn", "client_name"]
            cleaned_data = {}
            
            for key, value in data.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    cleaned_data[key] = "[REDACTED]"
                else:
                    cleaned_data[key] = value
            
            return cleaned_data
        
        return data
    
    async def _audit_log_operation(
        self,
        operation: str,
        input_summary: str,
        output_summary: str,
        compliance_status: Optional[ComplianceStatus] = None,
        disclaimers_applied: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """
        Log an operation for audit purposes.
        
        Args:
            operation: Name of the operation performed
            input_summary: Summary of input data
            output_summary: Summary of output data
            compliance_status: Compliance validation results if applicable
            disclaimers_applied: List of disclaimer IDs applied
            user_id: User ID if applicable
            session_id: Session ID for tracking
        """
        if self.legal_config.audit_logging_level == "minimal":
            return
        
        audit_entry = AuditLogEntry(
            agent_type=self.__class__.__name__,
            operation=operation,
            input_summary=input_summary,
            output_summary=output_summary,
            compliance_status=compliance_status,
            disclaimers_applied=disclaimers_applied or [],
            user_id=user_id,
            session_id=session_id
        )
        
        self._audit_log.append(audit_entry)
        
        if self.legal_config.audit_logging_level == "detailed":
            logger.info(f"Audit log entry: {audit_entry.model_dump_json()}")
    
    async def _post_process_response(
        self, 
        response: BaseIOSchema,
        content_type: str = "marketing",
        marketing_channel: str = "general"
    ) -> BaseIOSchema:
        """
        Post-process response with legal marketing compliance features.
        
        Args:
            response: Response to post-process
            content_type: Type of content for compliance checking
            marketing_channel: Marketing channel for rule selection
            
        Returns:
            Post-processed response with compliance features applied
        """
        try:
            # Validate compliance if content is available
            compliance_status = None
            if hasattr(response, 'content') and response.content:
                compliance_status = await self._validate_compliance(
                    response.content, 
                    marketing_channel
                )
            
            # Inject disclaimers
            response = await self._inject_disclaimers(response, content_type)
            
            # Log the operation
            await self._audit_log_operation(
                operation="post_process_response",
                input_summary=f"Content type: {content_type}, Channel: {marketing_channel}",
                output_summary="Applied compliance features and disclaimers",
                compliance_status=compliance_status
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to post-process response: {str(e)}")
            raise LegalMarketingAgentError(
                error_type="POST_PROCESSING_FAILED",
                message="Failed to apply legal marketing compliance features",
                context={
                    "content_type": content_type,
                    "marketing_channel": marketing_channel,
                    "error": str(e)
                }
            )
    
    def get_audit_log(self) -> List[AuditLogEntry]:
        """
        Get the audit log for this agent instance.
        
        Returns:
            List of audit log entries
        """
        return self._audit_log.copy()
    
    def clear_audit_log(self) -> None:
        """Clear the audit log for this agent instance."""
        self._audit_log.clear()
