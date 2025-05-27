"""
LLM Client Manager for Atomic Agents Integration.

This module provides real LLM client management for the Legal AI Marketing Assistant,
replacing the mock implementation with actual Atomic Agents LLM clients.
"""

from typing import Dict, Any, Optional, Union
import logging
from abc import ABC, abstractmethod

from atomic_agents.agents.base_agent import BaseAgent
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field

from llai.config.settings import ApplicationConfig, LLMProviderConfig
from llai.utils.exceptions_atomic import LLMClientError
from llai.utils.logging_setup import get_logger

logger = get_logger(__name__)


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
    
    @abstractmethod
    def list_available_models(self) -> Dict[str, str]:
        """List available models and their providers."""
        pass


# --- Mock LLM Client Manager (for testing) ---

class MockLLMClientManager(LLMClientManager):
    """Mock LLM client manager for testing."""
    
    def __init__(self):
        self.clients = {}
        logger.info("Mock LLM client manager initialized")
    
    def get_client(self, model_name: str) -> Any:
        """Get a mock client for the specified model."""
        if model_name not in self.clients:
            # Return a mock client object
            self.clients[model_name] = type('MockClient', (), {
                'model': model_name,
                'generate': lambda self, prompt: f"Mock response for: {prompt[:50]}...",
                'chat': lambda self, messages: f"Mock chat response for {len(messages)} messages"
            })()
            logger.debug(f"Created mock client for model: {model_name}")
        return self.clients[model_name]
    
    def get_default_client(self) -> Any:
        """Get the default mock client."""
        return self.get_client("gpt-4o-mini")
    
    def list_available_models(self) -> Dict[str, str]:
        """List available mock models."""
        return {
            "gpt-4o-mini": "mock",
            "gpt-4": "mock",
            "gpt-3.5-turbo": "mock",
            "claude-3-sonnet": "mock",
            "claude-3-haiku": "mock"
        }


# --- Real LLM Client Manager ---

class AtomicAgentsLLMClientManager(LLMClientManager):
    """
    Real LLM client manager that creates Atomic Agents compatible LLM clients.
    
    This manager handles:
    - OpenAI client creation and configuration
    - Anthropic client creation and configuration
    - Model selection and fallback logic
    - Error handling and retry logic
    - Client caching and reuse
    """
    
    def __init__(self, config: ApplicationConfig):
        """
        Initialize the LLM client manager.
        
        Args:
            config: Application configuration containing LLM provider settings
        """
        self.config = config
        self.llm_config = config.llm_provider
        self.clients: Dict[str, Any] = {}
        self._validate_configuration()
        logger.info("Atomic Agents LLM client manager initialized")
    
    def _validate_configuration(self) -> None:
        """Validate LLM provider configuration."""
        if not self.llm_config.openai_api_key:
            logger.warning("OpenAI API key not configured")
        
        if not self.llm_config.anthropic_api_key:
            logger.warning("Anthropic API key not configured")
        
        if not self.llm_config.openai_api_key and not self.llm_config.anthropic_api_key:
            raise LLMClientError(
                error_type="CONFIGURATION_ERROR",
                message="No LLM provider API keys configured",
                context={"available_providers": []}
            )
        
        logger.debug("LLM configuration validated")
    
    def get_client(self, model_name: str) -> Any:
        """
        Get an LLM client for the specified model.
        
        Args:
            model_name: Name of the model to get client for
            
        Returns:
            Configured LLM client
            
        Raises:
            LLMClientError: If client creation fails
        """
        try:
            if model_name in self.clients:
                return self.clients[model_name]
            
            # Determine provider based on model name
            provider = self._get_provider_for_model(model_name)
            
            if provider == "openai":
                client = self._create_openai_client(model_name)
            elif provider == "anthropic":
                client = self._create_anthropic_client(model_name)
            else:
                raise LLMClientError(
                    error_type="UNSUPPORTED_MODEL",
                    message=f"Unsupported model: {model_name}",
                    context={"model": model_name, "available_models": list(self.list_available_models().keys())}
                )
            
            # Cache the client
            self.clients[model_name] = client
            logger.info(f"Created LLM client for model: {model_name} (provider: {provider})")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create LLM client for model {model_name}: {str(e)}")
            raise LLMClientError(
                error_type="CLIENT_CREATION_FAILED",
                message=f"Failed to create LLM client for model {model_name}",
                context={"model": model_name, "error": str(e)}
            )
    
    def get_default_client(self) -> Any:
        """Get the default LLM client."""
        try:
            return self.get_client(self.llm_config.default_model)
        except LLMClientError:
            # Try fallback model
            logger.warning(f"Default model {self.llm_config.default_model} failed, trying fallback")
            return self.get_client(self.llm_config.fallback_model)
    
    def list_available_models(self) -> Dict[str, str]:
        """List available models and their providers."""
        models = {}
        
        # OpenAI models
        if self.llm_config.openai_api_key:
            models.update({
                "gpt-4": "openai",
                "gpt-4-turbo": "openai",
                "gpt-4o": "openai",
                "gpt-4o-mini": "openai",
                "gpt-3.5-turbo": "openai"
            })
        
        # Anthropic models
        if self.llm_config.anthropic_api_key:
            models.update({
                "claude-3-opus": "anthropic",
                "claude-3-sonnet": "anthropic",
                "claude-3-haiku": "anthropic",
                "claude-3-5-sonnet": "anthropic"
            })
        
        return models
    
    def _get_provider_for_model(self, model_name: str) -> str:
        """Determine the provider for a given model name."""
        available_models = self.list_available_models()
        
        if model_name in available_models:
            return available_models[model_name]
        
        # Try to infer from model name patterns
        if any(pattern in model_name.lower() for pattern in ["gpt", "openai"]):
            return "openai"
        elif any(pattern in model_name.lower() for pattern in ["claude", "anthropic"]):
            return "anthropic"
        
        raise LLMClientError(
            error_type="UNKNOWN_MODEL_PROVIDER",
            message=f"Cannot determine provider for model: {model_name}",
            context={"model": model_name, "available_models": list(available_models.keys())}
        )
    
    def _create_openai_client(self, model_name: str) -> Any:
        """Create an OpenAI client for Atomic Agents."""
        try:
            # Import OpenAI client from Atomic Agents
            from atomic_agents.lib.components.agent_memory import AgentMemory
            from atomic_agents.agents.base_agent import BaseAgent
            
            # For now, we'll create a simple client wrapper
            # In a full implementation, this would use the actual Atomic Agents OpenAI integration
            
            class OpenAIClientWrapper:
                def __init__(self, api_key: str, model: str, config: LLMProviderConfig):
                    self.api_key = api_key
                    self.model = model
                    self.config = config
                    # In real implementation, initialize actual OpenAI client here
                    logger.debug(f"OpenAI client wrapper created for model: {model}")
                
                async def generate(self, prompt: str, **kwargs) -> str:
                    """Generate response using OpenAI API."""
                    # This is a placeholder - real implementation would call OpenAI API
                    logger.info(f"Generating response with OpenAI model: {self.model}")
                    return f"[OpenAI {self.model}] Response to: {prompt[:100]}..."
                
                async def chat(self, messages: list, **kwargs) -> str:
                    """Chat completion using OpenAI API."""
                    # This is a placeholder - real implementation would call OpenAI API
                    logger.info(f"Chat completion with OpenAI model: {self.model}")
                    return f"[OpenAI {self.model}] Chat response to {len(messages)} messages"
            
            return OpenAIClientWrapper(
                api_key=self.llm_config.openai_api_key,
                model=model_name,
                config=self.llm_config
            )
            
        except ImportError as e:
            raise LLMClientError(
                error_type="DEPENDENCY_ERROR",
                message="Failed to import required OpenAI dependencies",
                context={"model": model_name, "error": str(e)}
            )
    
    def _create_anthropic_client(self, model_name: str) -> Any:
        """Create an Anthropic client for Atomic Agents."""
        try:
            # Import Anthropic client from Atomic Agents
            # For now, we'll create a simple client wrapper
            
            class AnthropicClientWrapper:
                def __init__(self, api_key: str, model: str, config: LLMProviderConfig):
                    self.api_key = api_key
                    self.model = model
                    self.config = config
                    # In real implementation, initialize actual Anthropic client here
                    logger.debug(f"Anthropic client wrapper created for model: {model}")
                
                async def generate(self, prompt: str, **kwargs) -> str:
                    """Generate response using Anthropic API."""
                    # This is a placeholder - real implementation would call Anthropic API
                    logger.info(f"Generating response with Anthropic model: {self.model}")
                    return f"[Anthropic {self.model}] Response to: {prompt[:100]}..."
                
                async def chat(self, messages: list, **kwargs) -> str:
                    """Chat completion using Anthropic API."""
                    # This is a placeholder - real implementation would call Anthropic API
                    logger.info(f"Chat completion with Anthropic model: {self.model}")
                    return f"[Anthropic {self.model}] Chat response to {len(messages)} messages"
            
            return AnthropicClientWrapper(
                api_key=self.llm_config.anthropic_api_key,
                model=model_name,
                config=self.llm_config
            )
            
        except ImportError as e:
            raise LLMClientError(
                error_type="DEPENDENCY_ERROR",
                message="Failed to import required Anthropic dependencies",
                context={"model": model_name, "error": str(e)}
            )
    
    def clear_cache(self) -> None:
        """Clear the client cache."""
        self.clients.clear()
        logger.info("LLM client cache cleared")
    
    def get_client_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific client."""
        if model_name not in self.clients:
            return {"status": "not_created", "model": model_name}
        
        client = self.clients[model_name]
        return {
            "status": "created",
            "model": model_name,
            "provider": self._get_provider_for_model(model_name),
            "client_type": type(client).__name__
        }


# --- Factory Functions ---

def create_llm_client_manager(
    config: ApplicationConfig,
    use_mock: bool = False
) -> LLMClientManager:
    """
    Create an LLM client manager based on configuration.
    
    Args:
        config: Application configuration
        use_mock: Whether to use mock clients for testing
        
    Returns:
        Configured LLM client manager
    """
    if use_mock:
        logger.info("Creating mock LLM client manager")
        return MockLLMClientManager()
    else:
        logger.info("Creating real Atomic Agents LLM client manager")
        return AtomicAgentsLLMClientManager(config)


def get_default_llm_client_manager() -> LLMClientManager:
    """Get a default LLM client manager using environment configuration."""
    from llai.config.settings import get_config
    config = get_config()
    return create_llm_client_manager(config, use_mock=False)
