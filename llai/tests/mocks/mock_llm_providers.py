"""
Mock LLM Providers for Testing

This module provides mock implementations of LLM clients (OpenAI, Anthropic)
that can be used for deterministic testing of Atomic Agents without making
actual API calls.
"""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Callable
from unittest.mock import Mock


class MockLLMProviderBase(ABC):
    """
    Base class for mock LLM providers.
    
    Provides common functionality for queuing responses, pattern matching,
    and error simulation across different LLM provider implementations.
    """
    
    def __init__(self):
        self.response_queue: List[Union[Dict, str, Exception]] = []
        self.call_history: List[Dict] = []
        self.response_patterns: Dict[str, Union[Dict, str, Exception]] = {}
        self.default_response: Optional[Union[Dict, str]] = None
        self.call_count = 0
        
    def set_response(self, response: Union[Dict, str]):
        """
        Set a single response for the next call.
        
        Args:
            response: Response data (dict) or content string
        """
        if isinstance(response, str):
            response = {"content": response}
        self.response_queue.append(response)
    
    def set_responses(self, responses: List[Union[Dict, str]]):
        """
        Set multiple responses to be returned in sequence.
        
        Args:
            responses: List of response data or content strings
        """
        for response in responses:
            self.set_response(response)
    
    def set_response_pattern(self, pattern: str, response: Union[Dict, str, Exception]):
        """
        Set response based on input pattern matching.
        
        Args:
            pattern: Regex pattern to match against input content
            response: Response to return when pattern matches
        """
        self.response_patterns[pattern] = response
    
    def set_error(self, error_type: str, message: str):
        """
        Set an error to be raised on the next call.
        
        Args:
            error_type: Type of error (e.g., "API_ERROR", "RATE_LIMIT")
            message: Error message
        """
        error = Exception(f"{error_type}: {message}")
        self.response_queue.append(error)
    
    def set_default_response(self, response: Union[Dict, str]):
        """
        Set a default response when no queued responses or patterns match.
        
        Args:
            response: Default response data
        """
        if isinstance(response, str):
            response = {"content": response}
        self.default_response = response
    
    def clear_responses(self):
        """Clear all queued responses and patterns."""
        self.response_queue.clear()
        self.response_patterns.clear()
        self.default_response = None
    
    def get_call_history(self) -> List[Dict]:
        """Get history of all calls made to this mock provider."""
        return self.call_history.copy()
    
    def get_call_count(self) -> int:
        """Get total number of calls made to this provider."""
        return self.call_count
    
    def _find_pattern_match(self, content: str) -> Optional[Union[Dict, str, Exception]]:
        """
        Find a response pattern that matches the given content.
        
        Args:
            content: Content to match against patterns
            
        Returns:
            Matching response or None if no pattern matches
        """
        for pattern, response in self.response_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                return response
        return None
    
    def _get_next_response(self, input_content: str = "") -> Union[Dict, str]:
        """
        Get the next response based on queue, patterns, or default.
        
        Args:
            input_content: Input content for pattern matching
            
        Returns:
            Response data
            
        Raises:
            Exception: If an error was queued
        """
        # Check for pattern-based responses first
        if input_content:
            pattern_response = self._find_pattern_match(input_content)
            if pattern_response is not None:
                if isinstance(pattern_response, Exception):
                    raise pattern_response
                return pattern_response
        
        # Use queued response
        if self.response_queue:
            response = self.response_queue.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        
        # Use default response
        if self.default_response:
            return self.default_response
        
        # Fallback response
        return {"content": "Mock response"}
    
    @abstractmethod
    def create_completion(self, **kwargs) -> Dict:
        """Create a completion response. Must be implemented by subclasses."""
        pass


class MockOpenAIClient(MockLLMProviderBase):
    """
    Mock OpenAI client for testing.
    
    Mimics the OpenAI API interface used by Atomic Agents,
    including chat completions and streaming responses.
    """
    
    def __init__(self):
        super().__init__()
        self.chat = self
        self.completions = self
        self.model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.7
    
    def create(self, **kwargs) -> Dict:
        """
        Mock the chat.completions.create method.
        
        Args:
            **kwargs: OpenAI API parameters (messages, model, etc.)
            
        Returns:
            OpenAI-formatted response
        """
        self.call_count += 1
        
        # Extract parameters
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self.model)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        
        # Record the call
        self.call_history.append({
            "method": "chat.completions.create",
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "timestamp": datetime.utcnow(),
            "call_number": self.call_count
        })
        
        # Extract user content for pattern matching
        user_content = ""
        if messages:
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_content = message.get("content", "")
                    break
        
        # Get response
        try:
            response_data = self._get_next_response(user_content)
            return self._format_openai_response(response_data, model)
        except Exception as e:
            # Simulate OpenAI API error format
            raise self._create_openai_error(str(e))
    
    def _format_openai_response(self, content: Union[Dict, str], model: str) -> Dict:
        """
        Format response in OpenAI API format.
        
        Args:
            content: Response content
            model: Model name used
            
        Returns:
            OpenAI-formatted response
        """
        if isinstance(content, dict):
            # If content is already structured, serialize it
            message_content = json.dumps(content, indent=2)
        else:
            message_content = str(content)
        
        return {
            "id": f"chatcmpl-mock-{self.call_count}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message_content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": len(message_content.split()),
                "total_tokens": 100 + len(message_content.split())
            }
        }
    
    def _create_openai_error(self, message: str) -> Exception:
        """
        Create an OpenAI-style error.
        
        Args:
            message: Error message
            
        Returns:
            Exception formatted like OpenAI errors
        """
        # Create a mock OpenAI error
        error = Exception(message)
        error.response = Mock()
        error.response.status_code = 429 if "rate limit" in message.lower() else 500
        return error


class MockAnthropicClient(MockLLMProviderBase):
    """
    Mock Anthropic client for testing.
    
    Mimics the Anthropic API interface used by Atomic Agents.
    """
    
    def __init__(self):
        super().__init__()
        self.messages = self
        self.model = "claude-3-sonnet-20240229"
        self.max_tokens = 2000
    
    def create(self, **kwargs) -> Dict:
        """
        Mock the messages.create method.
        
        Args:
            **kwargs: Anthropic API parameters
            
        Returns:
            Anthropic-formatted response
        """
        self.call_count += 1
        
        # Extract parameters
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self.model)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        system = kwargs.get("system", "")
        
        # Record the call
        self.call_history.append({
            "method": "messages.create",
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "system": system,
            "timestamp": datetime.utcnow(),
            "call_number": self.call_count
        })
        
        # Extract user content for pattern matching
        user_content = ""
        if messages:
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_content = message.get("content", "")
                    break
        
        # Get response
        try:
            response_data = self._get_next_response(user_content)
            return self._format_anthropic_response(response_data, model)
        except Exception as e:
            # Simulate Anthropic API error
            raise self._create_anthropic_error(str(e))
    
    def _format_anthropic_response(self, content: Union[Dict, str], model: str) -> Dict:
        """
        Format response in Anthropic API format.
        
        Args:
            content: Response content
            model: Model name used
            
        Returns:
            Anthropic-formatted response
        """
        if isinstance(content, dict):
            message_content = json.dumps(content, indent=2)
        else:
            message_content = str(content)
        
        return {
            "id": f"msg_mock_{self.call_count}",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": message_content
                }
            ],
            "model": model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": 100,
                "output_tokens": len(message_content.split())
            }
        }
    
    def _create_anthropic_error(self, message: str) -> Exception:
        """
        Create an Anthropic-style error.
        
        Args:
            message: Error message
            
        Returns:
            Exception formatted like Anthropic errors
        """
        error = Exception(message)
        error.status_code = 429 if "rate limit" in message.lower() else 500
        return error


class MockStreamingResponse:
    """
    Mock streaming response for testing streaming LLM interactions.
    """
    
    def __init__(self, content: str, chunk_size: int = 10):
        self.content = content
        self.chunk_size = chunk_size
        self.position = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.position >= len(self.content):
            raise StopIteration
        
        chunk = self.content[self.position:self.position + self.chunk_size]
        self.position += self.chunk_size
        
        return {
            "choices": [{
                "delta": {
                    "content": chunk
                }
            }]
        }


class MockLLMProviderFactory:
    """
    Factory for creating mock LLM providers with common configurations.
    """
    
    @staticmethod
    def create_openai_mock(
        default_response: Optional[Union[Dict, str]] = None,
        responses: Optional[List[Union[Dict, str]]] = None,
        patterns: Optional[Dict[str, Union[Dict, str]]] = None
    ) -> MockOpenAIClient:
        """
        Create a configured OpenAI mock client.
        
        Args:
            default_response: Default response when no other response is available
            responses: List of responses to queue
            patterns: Pattern-based responses
            
        Returns:
            Configured MockOpenAIClient
        """
        client = MockOpenAIClient()
        
        if default_response:
            client.set_default_response(default_response)
        
        if responses:
            client.set_responses(responses)
        
        if patterns:
            for pattern, response in patterns.items():
                client.set_response_pattern(pattern, response)
        
        return client
    
    @staticmethod
    def create_anthropic_mock(
        default_response: Optional[Union[Dict, str]] = None,
        responses: Optional[List[Union[Dict, str]]] = None,
        patterns: Optional[Dict[str, Union[Dict, str]]] = None
    ) -> MockAnthropicClient:
        """
        Create a configured Anthropic mock client.
        
        Args:
            default_response: Default response when no other response is available
            responses: List of responses to queue
            patterns: Pattern-based responses
            
        Returns:
            Configured MockAnthropicClient
        """
        client = MockAnthropicClient()
        
        if default_response:
            client.set_default_response(default_response)
        
        if responses:
            client.set_responses(responses)
        
        if patterns:
            for pattern, response in patterns.items():
                client.set_response_pattern(pattern, response)
        
        return client
    
    @staticmethod
    def create_compliance_mock() -> MockOpenAIClient:
        """
        Create a mock client configured for compliance testing scenarios.
        
        Returns:
            MockOpenAIClient with compliance-specific patterns
        """
        patterns = {
            r"guarantee": {
                "compliance_status": "NON_COMPLIANT",
                "confidence_score": 0.95,
                "violations": [{
                    "rule_id": "LSO_7.04",
                    "description": "Use of guarantee language prohibited",
                    "severity": "high"
                }],
                "recommendations": ["Remove guarantee language"]
            },
            r"best lawyer": {
                "compliance_status": "NON_COMPLIANT",
                "confidence_score": 0.90,
                "violations": [{
                    "rule_id": "LSO_7.02",
                    "description": "Superlative claims require substantiation",
                    "severity": "medium"
                }],
                "recommendations": ["Substantiate superlative claims"]
            }
        }
        
        default_response = {
            "compliance_status": "COMPLIANT",
            "confidence_score": 0.85,
            "violations": [],
            "recommendations": []
        }
        
        return MockLLMProviderFactory.create_openai_mock(
            default_response=default_response,
            patterns=patterns
        )


# Convenience functions for common testing scenarios
def create_mock_openai_client(**kwargs) -> MockOpenAIClient:
    """Create a basic OpenAI mock client."""
    return MockLLMProviderFactory.create_openai_mock(**kwargs)


def create_mock_anthropic_client(**kwargs) -> MockAnthropicClient:
    """Create a basic Anthropic mock client."""
    return MockLLMProviderFactory.create_anthropic_mock(**kwargs)


def create_compliance_mock_client() -> MockOpenAIClient:
    """Create a mock client configured for compliance testing."""
    return MockLLMProviderFactory.create_compliance_mock()
