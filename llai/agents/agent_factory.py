"""
Agent Factory for Legal Marketing Agents.

This module provides the factory pattern implementation for consistent instantiation
of legal marketing agents with proper dependency injection and configuration management.
"""

from typing import Dict, Any, Optional, Type, Union
import logging
from abc import ABC, abstractmethod

from atomic_agents.agents.base_agent import BaseAgent
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field

from llai.agents.legal_marketing_base_agent import (
    LegalMarketingBaseAgent,
    LegalMarketingAgentConfig,
    DisclaimerProvider,
    AdvertisingRuleProvider,
    EthicalGuidelineProvider
)
from llai.agents.context_providers import (
    FileBasedDisclaimerProvider,
    FileBasedAdvertisingRuleProvider,
    FileBasedEthicalGuidelineProvider,
    MockDisclaimerProvider,
    MockAdvertisingRuleProvider,
    MockEthicalGuidelineProvider,
    DisclaimerProviderConfig,
    AdvertisingRuleProviderConfig,
    EthicalGuidelineProviderConfig
)
from llai.config.settings import AppConfig
from llai.utils.exceptions_atomic import AgentFactoryError
from llai.utils.logging_setup import get_logger

logger = get_logger(__name__)


# --- Factory Configuration ---

class LegalAgentFactoryConfig(BaseIOSchema):
    """Configuration for the legal agent factory."""
    use_mock_providers: bool = Field(False, description="Whether to use mock providers for testing")
    disclaimer_provider_config: Optional[DisclaimerProviderConfig] = Field(None, description="Configuration for disclaimer provider")
    advertising_rule_provider_config: Optional[AdvertisingRuleProviderConfig] = Field(None, description="Configuration for advertising rule provider")
    ethical_guideline_provider_config: Optional[EthicalGuidelineProviderConfig] = Field(None, description="Configuration for ethical guideline provider")
    default_jurisdiction: str = Field("ON", description="Default jurisdiction for agents")
    enable_audit_logging: bool = Field(True, description="Whether to enable audit logging by default")


# --- LLM Client Manager Interface ---

class LLMClientManager(ABC):
    """Abstract interface for LLM client management."""
    
    @abstractmethod
    def get_client(self, model_name: str) -> Any:
        """Get an LLM client for the specified model."""
        pass
    
    @abstractmethod
    def get_default_client(self) -> Any:
        """Get the default LLM client."""
        pass


class MockLLMClientManager(LLMClientManager):
    """Mock LLM client manager for testing."""
    
    def __init__(self):
        self.clients = {}
    
    def get_client(self, model_name: str) -> Any:
        """Get a mock client for the specified model."""
        if model_name not in self.clients:
            # Return a mock client object
            self.clients[model_name] = type('MockClient', (), {
                'model': model_name,
                'generate': lambda self, prompt: f"Mock response for: {prompt[:50]}..."
            })()
        return self.clients[model_name]
    
    def get_default_client(self) -> Any:
        """Get the default mock client."""
        return self.get_client("gpt-4o-mini")


# --- Legal Agent Factory ---

class LegalAgentFactory:
    """
    Factory class for creating legal marketing agents with proper dependency injection.
    
    This factory handles:
    - LLM client selection and injection
    - Context provider instantiation and configuration
    - Agent-specific configuration validation
    - Dependency management and error handling
    """
    
    def __init__(
        self,
        global_config: AppConfig,
        llm_client_manager: LLMClientManager,
        factory_config: Optional[LegalAgentFactoryConfig] = None
    ):
        """
        Initialize the legal agent factory.
        
        Args:
            global_config: Global application configuration
            llm_client_manager: Manager for LLM clients
            factory_config: Factory-specific configuration
        """
        self.global_config = global_config
        self.llm_client_manager = llm_client_manager
        self.factory_config = factory_config or LegalAgentFactoryConfig()
        
        # Initialize context providers
        self._disclaimer_provider: Optional[DisclaimerProvider] = None
        self._advertising_rule_provider: Optional[AdvertisingRuleProvider] = None
        self._ethical_guideline_provider: Optional[EthicalGuidelineProvider] = None
        
        # Registry of available agent types
        self._agent_registry: Dict[str, Type[LegalMarketingBaseAgent]] = {}
        
        logger.info("Legal agent factory initialized")
    
    def register_agent_type(self, agent_name: str, agent_class: Type[LegalMarketingBaseAgent]) -> None:
        """
        Register an agent type with the factory.
        
        Args:
            agent_name: Name to register the agent under
            agent_class: Agent class to register
        """
        self._agent_registry[agent_name] = agent_class
        logger.info(f"Registered agent type: {agent_name}")
    
    def create_agent(
        self,
        agent_type: str,
        agent_config: Optional[LegalMarketingAgentConfig] = None,
        **kwargs
    ) -> LegalMarketingBaseAgent:
        """
        Create an agent of the specified type with proper configuration and dependencies.
        
        Args:
            agent_type: Type of agent to create
            agent_config: Agent-specific configuration
            **kwargs: Additional arguments for agent creation
            
        Returns:
            Configured agent instance
            
        Raises:
            AgentFactoryError: If agent creation fails
        """
        try:
            logger.info(f"Creating agent of type: {agent_type}")
            
            # Validate agent type
            if agent_type not in self._agent_registry:
                raise AgentFactoryError(
                    error_type="UNKNOWN_AGENT_TYPE",
                    message=f"Unknown agent type: {agent_type}",
                    context={"agent_type": agent_type, "available_types": list(self._agent_registry.keys())}
                )
            
            # Get agent class
            agent_class = self._agent_registry[agent_type]
            
            # Setup configuration
            config = self._setup_agent_config(agent_type, agent_config)
            
            # Setup context providers
            disclaimer_provider = self._get_disclaimer_provider()
            advertising_rule_provider = self._get_advertising_rule_provider()
            ethical_guideline_provider = self._get_ethical_guideline_provider()
            
            # Create agent instance
            agent = agent_class(
                config=config,
                disclaimer_provider=disclaimer_provider,
                advertising_rule_provider=advertising_rule_provider,
                ethical_guideline_provider=ethical_guideline_provider,
                **kwargs
            )
            
            logger.info(f"Successfully created agent: {agent_type}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type}: {str(e)}")
            raise AgentFactoryError(
                error_type="AGENT_CREATION_FAILED",
                message=f"Failed to create agent of type {agent_type}",
                context={
                    "agent_type": agent_type,
                    "error": str(e),
                    "config": agent_config.model_dump() if agent_config else None
                }
            )
    
    def _setup_agent_config(
        self,
        agent_type: str,
        agent_config: Optional[LegalMarketingAgentConfig]
    ) -> LegalMarketingAgentConfig:
        """
        Setup and validate agent configuration.
        
        Args:
            agent_type: Type of agent being created
            agent_config: Provided agent configuration
            
        Returns:
            Validated and configured agent config
        """
        if agent_config is None:
            # Create default configuration
            agent_config = LegalMarketingAgentConfig(
                client=self.llm_client_manager.get_default_client(),
                model="gpt-4o-mini"
            )
        
        # Apply factory defaults if not specified
        if agent_config.default_jurisdiction is None:
            agent_config.default_jurisdiction = self.factory_config.default_jurisdiction
        
        if not hasattr(agent_config, 'audit_logging_level') or agent_config.audit_logging_level is None:
            agent_config.audit_logging_level = "standard" if self.factory_config.enable_audit_logging else "minimal"
        
        # Ensure LLM client is set
        if not hasattr(agent_config, 'client') or agent_config.client is None:
            agent_config.client = self.llm_client_manager.get_default_client()
        
        # Validate configuration
        self._validate_agent_config(agent_type, agent_config)
        
        return agent_config
    
    def _validate_agent_config(self, agent_type: str, config: LegalMarketingAgentConfig) -> None:
        """
        Validate agent configuration.
        
        Args:
            agent_type: Type of agent being created
            config: Configuration to validate
            
        Raises:
            AgentFactoryError: If configuration is invalid
        """
        # Basic validation
        if not config.default_jurisdiction:
            raise AgentFactoryError(
                error_type="INVALID_CONFIGURATION",
                message="Default jurisdiction must be specified",
                context={"agent_type": agent_type}
            )
        
        if config.compliance_threshold < 0.0 or config.compliance_threshold > 1.0:
            raise AgentFactoryError(
                error_type="INVALID_CONFIGURATION",
                message="Compliance threshold must be between 0.0 and 1.0",
                context={"agent_type": agent_type, "threshold": config.compliance_threshold}
            )
        
        # Agent-specific validation can be added here
        logger.debug(f"Configuration validated for agent type: {agent_type}")
    
    def _get_disclaimer_provider(self) -> Optional[DisclaimerProvider]:
        """Get or create disclaimer provider."""
        if self._disclaimer_provider is None:
            if self.factory_config.use_mock_providers:
                self._disclaimer_provider = MockDisclaimerProvider()
                logger.info("Using mock disclaimer provider")
            elif self.factory_config.disclaimer_provider_config:
                self._disclaimer_provider = FileBasedDisclaimerProvider(
                    self.factory_config.disclaimer_provider_config
                )
                logger.info("Using file-based disclaimer provider")
            else:
                logger.warning("No disclaimer provider configured")
        
        return self._disclaimer_provider
    
    def _get_advertising_rule_provider(self) -> Optional[AdvertisingRuleProvider]:
        """Get or create advertising rule provider."""
        if self._advertising_rule_provider is None:
            if self.factory_config.use_mock_providers:
                self._advertising_rule_provider = MockAdvertisingRuleProvider()
                logger.info("Using mock advertising rule provider")
            elif self.factory_config.advertising_rule_provider_config:
                self._advertising_rule_provider = FileBasedAdvertisingRuleProvider(
                    self.factory_config.advertising_rule_provider_config
                )
                logger.info("Using file-based advertising rule provider")
            else:
                logger.warning("No advertising rule provider configured")
        
        return self._advertising_rule_provider
    
    def _get_ethical_guideline_provider(self) -> Optional[EthicalGuidelineProvider]:
        """Get or create ethical guideline provider."""
        if self._ethical_guideline_provider is None:
            if self.factory_config.use_mock_providers:
                self._ethical_guideline_provider = MockEthicalGuidelineProvider()
                logger.info("Using mock ethical guideline provider")
            elif self.factory_config.ethical_guideline_provider_config:
                self._ethical_guideline_provider = FileBasedEthicalGuidelineProvider(
                    self.factory_config.ethical_guideline_provider_config
                )
                logger.info("Using file-based ethical guideline provider")
            else:
                logger.warning("No ethical guideline provider configured")
        
        return self._ethical_guideline_provider
    
    def get_available_agent_types(self) -> List[str]:
        """
        Get list of available agent types.
        
        Returns:
            List of registered agent type names
        """
        return list(self._agent_registry.keys())
    
    def validate_dependencies(self) -> Dict[str, bool]:
        """
        Validate that all required dependencies are available.
        
        Returns:
            Dictionary mapping dependency names to availability status
        """
        dependencies = {
            "llm_client_manager": self.llm_client_manager is not None,
            "global_config": self.global_config is not None,
            "disclaimer_provider": self._get_disclaimer_provider() is not None,
            "advertising_rule_provider": self._get_advertising_rule_provider() is not None,
            "ethical_guideline_provider": self._get_ethical_guideline_provider() is not None
        }
        
        logger.info(f"Dependency validation: {dependencies}")
        return dependencies
    
    def create_test_agent(
        self,
        agent_type: str,
        **config_overrides
    ) -> LegalMarketingBaseAgent:
        """
        Create an agent configured for testing with mock providers.
        
        Args:
            agent_type: Type of agent to create
            **config_overrides: Configuration overrides for testing
            
        Returns:
            Agent configured for testing
        """
        # Create test configuration
        test_config = LegalMarketingAgentConfig(
            client=self.llm_client_manager.get_default_client(),
            model="gpt-4o-mini",
            default_jurisdiction="ON",
            enable_strict_compliance_checks=False,
            audit_logging_level="minimal",
            **config_overrides
        )
        
        # Temporarily use mock providers
        original_use_mock = self.factory_config.use_mock_providers
        self.factory_config.use_mock_providers = True
        
        try:
            agent = self.create_agent(agent_type, test_config)
            return agent
        finally:
            # Restore original setting
            self.factory_config.use_mock_providers = original_use_mock


# --- Factory Builder ---

def create_legal_agent_factory(
    global_config: AppConfig,
    use_mock_providers: bool = False,
    **factory_config_kwargs
) -> LegalAgentFactory:
    """
    Create a configured legal agent factory.
    
    Args:
        global_config: Global application configuration
        use_mock_providers: Whether to use mock providers
        **factory_config_kwargs: Additional factory configuration
        
    Returns:
        Configured legal agent factory
    """
    # Create LLM client manager
    llm_client_manager = MockLLMClientManager()  # In production, this would be a real implementation
    
    # Create factory configuration
    factory_config = LegalAgentFactoryConfig(
        use_mock_providers=use_mock_providers,
        **factory_config_kwargs
    )
    
    # Create factory
    factory = LegalAgentFactory(
        global_config=global_config,
        llm_client_manager=llm_client_manager,
        factory_config=factory_config
    )
    
    logger.info("Legal agent factory created and configured")
    return factory
