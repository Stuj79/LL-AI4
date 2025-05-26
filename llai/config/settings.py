"""
Centralized configuration models using BaseIOSchema for the Legal AI Marketing Assistant.
This replaces scattered configuration patterns with structured, validated settings.
"""

import os
from typing import Optional, Dict, Any, List
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMProviderConfig(BaseIOSchema):
    """Configuration for LLM providers and API settings."""
    openai_api_key: str = Field(..., description="OpenAI API key from environment")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key from environment")
    default_model: str = Field("gpt-4o-mini", description="Default LLM model to use")
    fallback_model: str = Field("gpt-3.5-turbo", description="Fallback model if default fails")
    max_retries: int = Field(3, ge=0, description="Maximum number of API call retries")
    timeout: int = Field(30, ge=1, description="API call timeout in seconds")
    
    @classmethod
    def from_env(cls) -> "LLMProviderConfig":
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_model=os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
            fallback_model=os.getenv("FALLBACK_LLM_MODEL", "gpt-3.5-turbo"),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        )

class AgentDefaultConfig(BaseIOSchema):
    """Default configuration settings for agents."""
    temperature: float = Field(0.3, ge=0.0, le=2.0, description="Default temperature for agent responses")
    max_tokens: Optional[int] = Field(None, description="Default maximum tokens for responses")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Default top_p sampling parameter")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Default frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Default presence penalty")

class ContentAgentConfig(AgentDefaultConfig):
    """Configuration specific to content-related agents."""
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="Lower temperature for more consistent content analysis")
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum quality score threshold")
    categorization_confidence: float = Field(0.8, ge=0.0, le=1.0, description="Minimum confidence for categorization")
    enable_auto_tagging: bool = Field(True, description="Whether to enable automatic content tagging")

class CreativeAgentConfig(AgentDefaultConfig):
    """Configuration specific to creative/generation agents."""
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Higher temperature for more creative output")
    max_tokens: Optional[int] = Field(2000, description="Higher token limit for creative content")
    enable_style_consistency: bool = Field(True, description="Whether to enforce brand voice consistency")

class AnalysisAgentConfig(AgentDefaultConfig):
    """Configuration specific to analysis agents."""
    temperature: float = Field(0.4, ge=0.0, le=2.0, description="Moderate temperature for balanced analysis")
    gap_threshold: int = Field(5, ge=1, description="Minimum number of items to not consider a gap")
    include_secondary_analysis: bool = Field(True, description="Whether to include secondary analysis metrics")
    confidence_level: str = Field("medium", description="Required confidence level for analysis results")

class LocalLLMConfig(BaseIOSchema):
    """Configuration for local LLM servers (e.g., LM Studio)."""
    base_url: str = Field("http://localhost:1234/v1", description="Base URL for local LLM server")
    model_name: str = Field("llama-3-groq-8b-tool-use", description="Local model name")
    api_key: Optional[str] = Field("lm-studio", description="API key for local server (if required)")
    enabled: bool = Field(False, description="Whether to use local LLM instead of cloud providers")
    fallback_to_cloud: bool = Field(True, description="Whether to fallback to cloud providers if local fails")

class DatabaseConfig(BaseIOSchema):
    """Configuration for database connections."""
    connection_string: Optional[str] = Field(None, description="Database connection string")
    max_connections: int = Field(10, ge=1, description="Maximum number of database connections")
    connection_timeout: int = Field(30, ge=1, description="Database connection timeout in seconds")
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database configuration from environment variables."""
        return cls(
            connection_string=os.getenv("DATABASE_URL"),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
            connection_timeout=int(os.getenv("DB_TIMEOUT", "30"))
        )

class LoggingConfig(BaseIOSchema):
    """Configuration for application logging."""
    level: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log message format")
    file_path: Optional[str] = Field(None, description="Path to log file (if file logging enabled)")
    max_file_size: int = Field(10485760, ge=1024, description="Maximum log file size in bytes (10MB default)")
    backup_count: int = Field(5, ge=0, description="Number of backup log files to keep")
    enable_rich_logging: bool = Field(True, description="Whether to use rich console logging")
    
    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create logging configuration from environment variables."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_file_size=int(os.getenv("LOG_MAX_SIZE", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            enable_rich_logging=os.getenv("ENABLE_RICH_LOGGING", "true").lower() == "true"
        )

class ApplicationConfig(BaseIOSchema):
    """Main application configuration that combines all other configs."""
    llm_provider: LLMProviderConfig = Field(..., description="LLM provider configuration")
    content_agents: ContentAgentConfig = Field(default_factory=ContentAgentConfig, description="Content agent configuration")
    creative_agents: CreativeAgentConfig = Field(default_factory=CreativeAgentConfig, description="Creative agent configuration")
    analysis_agents: AnalysisAgentConfig = Field(default_factory=AnalysisAgentConfig, description="Analysis agent configuration")
    local_llm: LocalLLMConfig = Field(default_factory=LocalLLMConfig, description="Local LLM configuration")
    database: DatabaseConfig = Field(..., description="Database configuration")
    logging: LoggingConfig = Field(..., description="Logging configuration")
    
    # Application-specific settings
    app_name: str = Field("Legal AI Marketing Assistant", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug_mode: bool = Field(False, description="Whether to run in debug mode")
    max_concurrent_agents: int = Field(5, ge=1, description="Maximum number of concurrent agent operations")
    
    @classmethod
    def from_env(cls) -> "ApplicationConfig":
        """Create complete application configuration from environment variables."""
        return cls(
            llm_provider=LLMProviderConfig.from_env(),
            database=DatabaseConfig.from_env(),
            logging=LoggingConfig.from_env(),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "5"))
        )

# Global configuration instance
_config: Optional[ApplicationConfig] = None

def get_config() -> ApplicationConfig:
    """Get the global application configuration instance."""
    global _config
    if _config is None:
        _config = ApplicationConfig.from_env()
    return _config

def reload_config() -> ApplicationConfig:
    """Reload configuration from environment variables."""
    global _config
    load_dotenv()  # Reload .env file
    _config = ApplicationConfig.from_env()
    return _config

def get_agent_config(agent_type: str) -> AgentDefaultConfig:
    """Get configuration for a specific agent type."""
    config = get_config()
    
    agent_configs = {
        "content": config.content_agents,
        "creative": config.creative_agents,
        "analysis": config.analysis_agents,
        "default": AgentDefaultConfig()
    }
    
    return agent_configs.get(agent_type, agent_configs["default"])
