"""
Context Providers for Legal Marketing Agents.

This module provides concrete implementations of context providers that supply
legal marketing domain knowledge including disclaimers, advertising rules,
and ethical guidelines.
"""

from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
import logging

from llai.agents.legal_marketing_base_agent import (
    DisclaimerProvider,
    AdvertisingRuleProvider, 
    EthicalGuidelineProvider,
    Disclaimer,
    AdvertisingRule,
    EthicalGuideline
)
from llai.utils.logging_setup import get_logger
from llai.utils.exceptions_atomic import ContextProviderError
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field

logger = get_logger(__name__)


# --- Configuration Schemas ---

class DisclaimerProviderConfig(BaseIOSchema):
    """Configuration for disclaimer provider."""
    data_source_path: str = Field(..., description="Path to disclaimer data source")
    cache_ttl_seconds: int = Field(300, description="Cache time-to-live in seconds")
    default_disclaimers: List[str] = Field(default_factory=list, description="Default disclaimer IDs to always include")

class AdvertisingRuleProviderConfig(BaseIOSchema):
    """Configuration for advertising rule provider."""
    data_source_path: str = Field(..., description="Path to advertising rules data source")
    cache_ttl_seconds: int = Field(600, description="Cache time-to-live in seconds")
    strict_mode: bool = Field(True, description="Whether to apply strict rule interpretation")

class EthicalGuidelineProviderConfig(BaseIOSchema):
    """Configuration for ethical guideline provider."""
    data_source_path: str = Field(..., description="Path to ethical guidelines data source")
    cache_ttl_seconds: int = Field(600, description="Cache time-to-live in seconds")
    include_recommendations: bool = Field(True, description="Whether to include recommended guidelines")


# --- File-Based Disclaimer Provider ---

class FileBasedDisclaimerProvider(DisclaimerProvider):
    """
    File-based implementation of DisclaimerProvider.
    
    Loads disclaimer data from JSON files organized by jurisdiction and content type.
    """
    
    def __init__(self, config: DisclaimerProviderConfig):
        """
        Initialize the file-based disclaimer provider.
        
        Args:
            config: Configuration for the provider
        """
        self.config = config
        self._cache: Dict[str, List[Disclaimer]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Ensure data source path exists
        if not os.path.exists(config.data_source_path):
            logger.warning(f"Disclaimer data source path does not exist: {config.data_source_path}")
    
    async def get_disclaimers(self, jurisdiction: str, content_type: str) -> List[Disclaimer]:
        """
        Get applicable disclaimers for the given context.
        
        Args:
            jurisdiction: Jurisdiction code (e.g., 'ON', 'BC', 'AB')
            content_type: Type of content (e.g., 'marketing', 'legal_advice', 'general')
            
        Returns:
            List of applicable disclaimers
            
        Raises:
            ContextProviderError: If disclaimer loading fails
        """
        try:
            cache_key = f"{jurisdiction}_{content_type}"
            
            # Check cache validity
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]
            
            disclaimers = await self._load_disclaimers(jurisdiction, content_type)
            
            # Update cache
            self._cache[cache_key] = disclaimers
            self._cache_timestamps[cache_key] = self._get_current_timestamp()
            
            return disclaimers
            
        except Exception as e:
            logger.error(f"Failed to get disclaimers for {jurisdiction}/{content_type}: {str(e)}")
            raise ContextProviderError(
                error_type="DISCLAIMER_LOADING_FAILED",
                message="Failed to load disclaimers",
                context={
                    "jurisdiction": jurisdiction,
                    "content_type": content_type,
                    "error": str(e)
                }
            )
    
    async def _load_disclaimers(self, jurisdiction: str, content_type: str) -> List[Disclaimer]:
        """Load disclaimers from file system."""
        disclaimers = []
        
        # Try to load jurisdiction-specific disclaimers
        jurisdiction_file = Path(self.config.data_source_path) / f"{jurisdiction.lower()}_disclaimers.json"
        if jurisdiction_file.exists():
            disclaimers.extend(await self._load_disclaimers_from_file(jurisdiction_file, content_type))
        
        # Load general disclaimers
        general_file = Path(self.config.data_source_path) / "general_disclaimers.json"
        if general_file.exists():
            disclaimers.extend(await self._load_disclaimers_from_file(general_file, content_type))
        
        # Add default disclaimers if configured
        if self.config.default_disclaimers:
            for disclaimer_id in self.config.default_disclaimers:
                default_disclaimer = Disclaimer(
                    id=disclaimer_id,
                    text=f"Default disclaimer: {disclaimer_id}",
                    jurisdiction=jurisdiction,
                    content_type=content_type,
                    mandatory=True,
                    position="footer"
                )
                disclaimers.append(default_disclaimer)
        
        return disclaimers
    
    async def _load_disclaimers_from_file(self, file_path: Path, content_type: str) -> List[Disclaimer]:
        """Load disclaimers from a specific JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            disclaimers = []
            for item in data.get('disclaimers', []):
                # Filter by content type if specified
                if 'content_types' in item and content_type not in item['content_types']:
                    continue
                
                disclaimer = Disclaimer(
                    id=item['id'],
                    text=item['text'],
                    jurisdiction=item.get('jurisdiction', 'general'),
                    content_type=content_type,
                    mandatory=item.get('mandatory', True),
                    position=item.get('position', 'footer')
                )
                disclaimers.append(disclaimer)
            
            return disclaimers
            
        except Exception as e:
            logger.error(f"Failed to load disclaimers from {file_path}: {str(e)}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        age = self._get_current_timestamp() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl_seconds
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# --- File-Based Advertising Rule Provider ---

class FileBasedAdvertisingRuleProvider(AdvertisingRuleProvider):
    """
    File-based implementation of AdvertisingRuleProvider.
    
    Loads advertising rules from JSON files organized by jurisdiction and marketing channel.
    """
    
    def __init__(self, config: AdvertisingRuleProviderConfig):
        """
        Initialize the file-based advertising rule provider.
        
        Args:
            config: Configuration for the provider
        """
        self.config = config
        self._cache: Dict[str, List[AdvertisingRule]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Ensure data source path exists
        if not os.path.exists(config.data_source_path):
            logger.warning(f"Advertising rules data source path does not exist: {config.data_source_path}")
    
    async def get_rules(self, jurisdiction: str, marketing_channel: str) -> List[AdvertisingRule]:
        """
        Get applicable advertising rules for the given context.
        
        Args:
            jurisdiction: Jurisdiction code (e.g., 'ON', 'BC', 'AB')
            marketing_channel: Marketing channel (e.g., 'website', 'social_media', 'email')
            
        Returns:
            List of applicable advertising rules
            
        Raises:
            ContextProviderError: If rule loading fails
        """
        try:
            cache_key = f"{jurisdiction}_{marketing_channel}"
            
            # Check cache validity
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]
            
            rules = await self._load_rules(jurisdiction, marketing_channel)
            
            # Update cache
            self._cache[cache_key] = rules
            self._cache_timestamps[cache_key] = self._get_current_timestamp()
            
            return rules
            
        except Exception as e:
            logger.error(f"Failed to get advertising rules for {jurisdiction}/{marketing_channel}: {str(e)}")
            raise ContextProviderError(
                error_type="ADVERTISING_RULES_LOADING_FAILED",
                message="Failed to load advertising rules",
                context={
                    "jurisdiction": jurisdiction,
                    "marketing_channel": marketing_channel,
                    "error": str(e)
                }
            )
    
    async def _load_rules(self, jurisdiction: str, marketing_channel: str) -> List[AdvertisingRule]:
        """Load advertising rules from file system."""
        rules = []
        
        # Try to load jurisdiction-specific rules
        jurisdiction_file = Path(self.config.data_source_path) / f"{jurisdiction.lower()}_advertising_rules.json"
        if jurisdiction_file.exists():
            rules.extend(await self._load_rules_from_file(jurisdiction_file, marketing_channel))
        
        # Load general rules
        general_file = Path(self.config.data_source_path) / "general_advertising_rules.json"
        if general_file.exists():
            rules.extend(await self._load_rules_from_file(general_file, marketing_channel))
        
        return rules
    
    async def _load_rules_from_file(self, file_path: Path, marketing_channel: str) -> List[AdvertisingRule]:
        """Load advertising rules from a specific JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rules = []
            for item in data.get('rules', []):
                # Filter by marketing channel if specified
                if 'channels' in item and marketing_channel not in item['channels']:
                    continue
                
                rule = AdvertisingRule(
                    rule_id=item['rule_id'],
                    jurisdiction=item.get('jurisdiction', 'general'),
                    rule_text=item['rule_text'],
                    category=item.get('category', 'general'),
                    severity=item.get('severity', 'medium'),
                    enforcement_body=item.get('enforcement_body', 'Unknown')
                )
                rules.append(rule)
            
            return rules
            
        except Exception as e:
            logger.error(f"Failed to load advertising rules from {file_path}: {str(e)}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        age = self._get_current_timestamp() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl_seconds
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# --- File-Based Ethical Guideline Provider ---

class FileBasedEthicalGuidelineProvider(EthicalGuidelineProvider):
    """
    File-based implementation of EthicalGuidelineProvider.
    
    Loads ethical guidelines from JSON files organized by task type.
    """
    
    def __init__(self, config: EthicalGuidelineProviderConfig):
        """
        Initialize the file-based ethical guideline provider.
        
        Args:
            config: Configuration for the provider
        """
        self.config = config
        self._cache: Dict[str, List[EthicalGuideline]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Ensure data source path exists
        if not os.path.exists(config.data_source_path):
            logger.warning(f"Ethical guidelines data source path does not exist: {config.data_source_path}")
    
    async def get_guidelines(self, task_type: str) -> List[EthicalGuideline]:
        """
        Get applicable ethical guidelines for the given task type.
        
        Args:
            task_type: Type of task (e.g., 'content_generation', 'client_communication', 'marketing')
            
        Returns:
            List of applicable ethical guidelines
            
        Raises:
            ContextProviderError: If guideline loading fails
        """
        try:
            cache_key = task_type
            
            # Check cache validity
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]
            
            guidelines = await self._load_guidelines(task_type)
            
            # Update cache
            self._cache[cache_key] = guidelines
            self._cache_timestamps[cache_key] = self._get_current_timestamp()
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Failed to get ethical guidelines for {task_type}: {str(e)}")
            raise ContextProviderError(
                error_type="ETHICAL_GUIDELINES_LOADING_FAILED",
                message="Failed to load ethical guidelines",
                context={
                    "task_type": task_type,
                    "error": str(e)
                }
            )
    
    async def _load_guidelines(self, task_type: str) -> List[EthicalGuideline]:
        """Load ethical guidelines from file system."""
        guidelines = []
        
        # Try to load task-specific guidelines
        task_file = Path(self.config.data_source_path) / f"{task_type}_guidelines.json"
        if task_file.exists():
            guidelines.extend(await self._load_guidelines_from_file(task_file))
        
        # Load general guidelines
        general_file = Path(self.config.data_source_path) / "general_guidelines.json"
        if general_file.exists():
            guidelines.extend(await self._load_guidelines_from_file(general_file))
        
        return guidelines
    
    async def _load_guidelines_from_file(self, file_path: Path) -> List[EthicalGuideline]:
        """Load ethical guidelines from a specific JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            guidelines = []
            for item in data.get('guidelines', []):
                # Filter by compliance level if not including recommendations
                if not self.config.include_recommendations and item.get('compliance_level') == 'recommended':
                    continue
                
                guideline = EthicalGuideline(
                    guideline_id=item['guideline_id'],
                    title=item['title'],
                    description=item['description'],
                    task_type=item.get('task_type', 'general'),
                    compliance_level=item.get('compliance_level', 'recommended'),
                    reference=item.get('reference', 'Internal guidelines')
                )
                guidelines.append(guideline)
            
            return guidelines
            
        except Exception as e:
            logger.error(f"Failed to load ethical guidelines from {file_path}: {str(e)}")
            return []
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        age = self._get_current_timestamp() - self._cache_timestamps[cache_key]
        return age < self.config.cache_ttl_seconds
    
    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# --- Mock Providers for Testing ---

class MockDisclaimerProvider(DisclaimerProvider):
    """Mock disclaimer provider for testing purposes."""
    
    def __init__(self):
        self.disclaimers = {
            "ON_marketing": [
                Disclaimer(
                    id="on_attorney_advertising",
                    text="Attorney Advertising. Prior results do not guarantee a similar outcome.",
                    jurisdiction="ON",
                    content_type="marketing",
                    mandatory=True,
                    position="footer"
                )
            ],
            "BC_marketing": [
                Disclaimer(
                    id="bc_legal_services",
                    text="This communication is from a law firm and may constitute attorney advertising.",
                    jurisdiction="BC",
                    content_type="marketing",
                    mandatory=True,
                    position="footer"
                )
            ]
        }
    
    async def get_disclaimers(self, jurisdiction: str, content_type: str) -> List[Disclaimer]:
        """Get mock disclaimers."""
        key = f"{jurisdiction}_{content_type}"
        return self.disclaimers.get(key, [])


class MockAdvertisingRuleProvider(AdvertisingRuleProvider):
    """Mock advertising rule provider for testing purposes."""
    
    def __init__(self):
        self.rules = {
            "ON_general": [
                AdvertisingRule(
                    rule_id="on_guarantee_prohibition",
                    jurisdiction="ON",
                    rule_text="Lawyers must not guarantee outcomes in legal matters",
                    category="guarantees",
                    severity="high",
                    enforcement_body="Law Society of Ontario"
                )
            ],
            "BC_general": [
                AdvertisingRule(
                    rule_id="bc_solicitation_rules",
                    jurisdiction="BC",
                    rule_text="Lawyers must not engage in aggressive solicitation",
                    category="solicitation",
                    severity="medium",
                    enforcement_body="Law Society of British Columbia"
                )
            ]
        }
    
    async def get_rules(self, jurisdiction: str, marketing_channel: str) -> List[AdvertisingRule]:
        """Get mock advertising rules."""
        key = f"{jurisdiction}_{marketing_channel}"
        return self.rules.get(key, [])


class MockEthicalGuidelineProvider(EthicalGuidelineProvider):
    """Mock ethical guideline provider for testing purposes."""
    
    def __init__(self):
        self.guidelines = {
            "content_generation": [
                EthicalGuideline(
                    guideline_id="content_accuracy",
                    title="Ensure Content Accuracy",
                    description="All legal content must be accurate and up-to-date",
                    task_type="content_generation",
                    compliance_level="mandatory",
                    reference="Professional Conduct Rules 3.1"
                )
            ],
            "client_communication": [
                EthicalGuideline(
                    guideline_id="confidentiality_protection",
                    title="Protect Client Confidentiality",
                    description="Client information must be protected at all times",
                    task_type="client_communication",
                    compliance_level="mandatory",
                    reference="Professional Conduct Rules 1.6"
                )
            ]
        }
    
    async def get_guidelines(self, task_type: str) -> List[EthicalGuideline]:
        """Get mock ethical guidelines."""
        return self.guidelines.get(task_type, [])
