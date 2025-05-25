"""
Tests for refactored agent implementations.

This module provides tests to verify that refactored agents using the base agent
classes maintain the same functionality as the original implementations.
"""

import asyncio
import json
import os
import sys
import unittest
from typing import Dict, Any, List

# Add parent directory to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import original agent implementations
from agents.content import ContentInventoryAgent as OriginalContentInventoryAgent
from agents.analysis import SeoAnalystAgent as OriginalSeoAnalystAgent

# Import refactored agent implementations
from llai.agents.content import ContentInventoryAgent as RefactoredContentInventoryAgent
from agents.analysis_refactored import SeoAnalystAgent as RefactoredSeoAnalystAgent


class TestRefactoredAgents(unittest.TestCase):
    """Tests to verify that refactored agents maintain original functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create instances of original and refactored agents
        self.original_content_agent = OriginalContentInventoryAgent()
        self.refactored_content_agent = RefactoredContentInventoryAgent()
        
        self.original_seo_agent = OriginalSeoAnalystAgent()
        self.refactored_seo_agent = RefactoredSeoAnalystAgent()
        
        # Sample test data
        self.sample_content_data = """
        Our firm has published several content pieces recently:
        1. "Estate Planning for Small Business Owners" - A blog post published on our website in March 2025
        2. "Understanding Canadian Corporate Tax" - A whitepaper published in January 2025
        3. "Family Law Basics: Divorce in Canada" - A video published on YouTube in February 2025
        4. "5 Tips for Intellectual Property Protection" - An infographic shared on LinkedIn last week
        """
        
        self.sample_content_item = {
            "title": "Estate Planning for Small Business Owners",
            "type": "Blog Post",
            "platform": "Website",
            "publication_date": "March 2025",
            "description": "A guide for small business owners on estate planning considerations."
        }
        
        self.sample_seo_content = """
        # Estate Planning for Small Business Owners
        
        Estate planning is a crucial process for small business owners. Without proper planning,
        your business may face significant challenges in the event of your disability or death.
        
        ## Why Estate Planning Matters for Business Owners
        
        As a small business owner, your business is likely your most valuable asset. Proper
        estate planning helps ensure that your business can continue operating smoothly,
        regardless of what happens to you.
        
        ## Key Estate Planning Documents
        
        1. Will
        2. Power of Attorney
        3. Shareholders' Agreement
        4. Succession Plan
        
        ## Tax Considerations
        
        Estate planning can help minimize tax liabilities when transferring business assets.
        """

    async def test_content_catalog(self):
        """Test that the refactored content cataloging maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_content_agent.catalog_content(self.sample_content_data)
        refactored_result = await self.refactored_content_agent.catalog_content(self.sample_content_data)
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, list))
        self.assertTrue(isinstance(refactored_result, list))
        
        # Verify both results contain the expected content items
        self.assertEqual(len(original_result), len(refactored_result))
        
        # Print results for manual comparison (during development)
        print("\nOriginal content catalog result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored content catalog result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_content_categorization(self):
        """Test that the refactored content categorization maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_content_agent.categorize_content(self.sample_content_item)
        refactored_result = await self.refactored_content_agent.categorize_content(self.sample_content_item)
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, dict))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Verify both results contain the expected fields
        original_keys = set(original_result.keys())
        refactored_keys = set(refactored_result.keys())
        
        # The refactored implementation should have at least the same fields as the original
        self.assertTrue(original_keys.issubset(refactored_keys))
        
        # Print results for manual comparison (during development)
        print("\nOriginal content categorization result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored content categorization result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_seo_analysis(self):
        """Test that the refactored SEO analysis maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_seo_agent.analyze_seo(self.sample_seo_content)
        refactored_result = await self.refactored_seo_agent.analyze_seo(self.sample_seo_content)
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, (dict, str)))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Print results for manual comparison (during development)
        print("\nOriginal SEO analysis result:")
        print(original_result)
        print("\nRefactored SEO analysis result:")
        print(json.dumps(refactored_result, indent=2))


def run_async_test(test_method):
    """Helper to run async test methods."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_method())


if __name__ == "__main__":
    # Run the tests
    test = TestRefactoredAgents()
    test.setUp()
    
    print("Testing refactored agent implementations...")
    
    print("\n--- Test: Content Catalog ---")
    run_async_test(test.test_content_catalog)
    
    print("\n--- Test: Content Categorization ---")
    run_async_test(test.test_content_categorization)
    
    print("\n--- Test: SEO Analysis ---")
    run_async_test(test.test_seo_analysis)
    
    print("\nTests completed!")
