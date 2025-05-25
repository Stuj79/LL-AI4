"""
Tests for the refactored ContentGapAnalysisAgent.

This module verifies that the refactored ContentGapAnalysisAgent using the ContentAgent
base class maintains the same functionality as the original implementation.
"""

import asyncio
import json
import os
import sys
import unittest
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

# Import directly from the module files to avoid __init__.py imports that may cause dependency issues
import importlib.util
import sys

# Import ContentGapAnalysisAgent from content.py (still using dynamic for comparison)
content_spec = importlib.util.spec_from_file_location("content", os.path.join(os.path.dirname(__file__), "../agents/content.py"))
content_module = importlib.util.module_from_spec(content_spec)
sys.modules["content"] = content_module
content_spec.loader.exec_module(content_module)
OriginalContentGapAnalysisAgent = content_module.ContentGapAnalysisAgent

# Import agent_base.py for ContentAgent base class (still using dynamic)
agent_base_spec = importlib.util.spec_from_file_location("agent_base", os.path.join(os.path.dirname(__file__), "../agents/agent_base.py"))
agent_base_module = importlib.util.module_from_spec(agent_base_spec)
sys.modules["agent_base"] = agent_base_module
agent_base_spec.loader.exec_module(agent_base_module)

# Import utility modules using standard package imports
from llai.utils import json_utils, prompt_utils, error_utils

# Import ContentGapAnalysisAgent from content_refactored.py (still using dynamic for comparison)
# Assuming content_refactored.py exists and contains ContentGapAnalysisAgent
content_refactored_path = os.path.join(os.path.dirname(__file__), "../agents/content_refactored.py")
if os.path.exists(content_refactored_path):
    content_refactored_spec = importlib.util.spec_from_file_location("content_refactored", content_refactored_path)
    content_refactored_module = importlib.util.module_from_spec(content_refactored_spec)
    sys.modules["content_refactored"] = content_refactored_module
    content_refactored_spec.loader.exec_module(content_refactored_module)
    RefactoredContentGapAnalysisAgent = content_refactored_module.ContentGapAnalysisAgent
else:
    # Define a placeholder if the refactored file doesn't exist to avoid NameError
    class RefactoredContentGapAnalysisAgent: pass
    print("Warning: content_refactored.py not found. Using placeholder.")


class TestContentGapAnalysisAgent(unittest.TestCase):
    """Tests to verify that refactored ContentGapAnalysisAgent maintains original functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create instances of original and refactored agents
        self.original_agent = OriginalContentGapAnalysisAgent()
        self.refactored_agent = RefactoredContentGapAnalysisAgent()
        
        # Sample test data
        self.sample_content_inventory = [
            {
                "title": "Estate Planning for Small Business Owners",
                "type": "Blog Post",
                "platform": "Website",
                "publication_date": "March 2025",
                "practice_area": "Business Law",
                "description": "A guide for small business owners on estate planning considerations."
            },
            {
                "title": "Understanding Canadian Corporate Tax",
                "type": "Whitepaper",
                "platform": "Website",
                "publication_date": "January 2025",
                "practice_area": "Tax Law",
                "description": "Overview of corporate tax requirements in Canada."
            },
            {
                "title": "Family Law Basics: Divorce in Canada",
                "type": "Video",
                "platform": "YouTube",
                "publication_date": "February 2025",
                "practice_area": "Family Law",
                "description": "An overview of divorce procedures in Canada."
            }
        ]
        
        self.sample_practice_areas = [
            "Business Law",
            "Tax Law",
            "Family Law",
            "Criminal Law",
            "Intellectual Property Law"
        ]
        
        self.sample_client_demographics = {
            "language_distribution": {
                "English": 70,
                "French": 25,
                "Chinese": 5
            },
            "locations": {
                "Ontario": 60,
                "Quebec": 25,
                "British Columbia": 15
            }
        }
        
        # Prepare JSON inputs for original agent
        self.practice_areas_json = json.dumps({
            "content_inventory": self.sample_content_inventory,
            "firm_practice_areas": self.sample_practice_areas
        })
        
        self.format_gaps_json = json.dumps({
            "content_inventory": self.sample_content_inventory
        })
        
        self.multilingual_json = json.dumps({
            "content_inventory": self.sample_content_inventory,
            "client_demographics": self.sample_client_demographics
        })
        
        # Prepare mock gap analysis results for report generation test
        self.mock_practice_area_gaps = {
            "covered_areas": ["Business Law", "Tax Law", "Family Law"],
            "gap_areas": ["Criminal Law", "Intellectual Property Law"],
            "coverage_metrics": {
                "Business Law": 1,
                "Tax Law": 1,
                "Family Law": 1,
                "Criminal Law": 0,
                "Intellectual Property Law": 0
            }
        }
        
        self.mock_format_gaps = {
            "existing_formats": ["Blog Post", "Whitepaper", "Video"],
            "missing_formats": ["Podcast", "Webinar", "Guide", "Infographic", "Newsletter", "Case Study", "Testimonial", "FAQ Page"],
            "format_counts": {
                "Blog Post": 1,
                "Whitepaper": 1,
                "Video": 1
            }
        }
        
        self.mock_multilingual_gaps = {
            "language_distribution": {
                "English": 3,
                "French": 0,
                "Other": 0
            },
            "language_gaps": ["French"],
            "translation_priorities": [
                "Translate 'Family Law Basics' video to French",
                "Translate key Business Law content to French"
            ]
        }
        
        self.gap_report_json = json.dumps({
            "practice_area_gaps": self.mock_practice_area_gaps,
            "format_gaps": self.mock_format_gaps,
            "multilingual_gaps": self.mock_multilingual_gaps
        })

    async def test_identify_practice_area_gaps(self):
        """Test that the refactored practice area gap analysis maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_agent.identify_practice_area_gaps(self.practice_areas_json)
        refactored_result = await self.refactored_agent.identify_practice_area_gaps(
            self.sample_content_inventory, 
            self.sample_practice_areas
        )
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, dict))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Verify both results contain the expected fields
        expected_fields = ["covered_areas", "gap_areas", "coverage_metrics"]
        for field in expected_fields:
            self.assertIn(field, original_result)
            self.assertIn(field, refactored_result)
        
        # Verify covered_areas and gap_areas contain the expected content
        # We can't expect exact matches because of LLM non-determinism, but we can check for key elements
        self.assertIn("Business Law", original_result.get("covered_areas", []))
        self.assertIn("Business Law", refactored_result.get("covered_areas", []))
        
        self.assertIn("Criminal Law", original_result.get("gap_areas", []))
        self.assertIn("Criminal Law", refactored_result.get("gap_areas", []))
        
        # Print results for manual comparison
        print("\nOriginal practice area gaps result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored practice area gaps result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_identify_format_gaps(self):
        """Test that the refactored format gap analysis maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_agent.identify_format_gaps(self.format_gaps_json)
        refactored_result = await self.refactored_agent.identify_format_gaps(self.sample_content_inventory)
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, dict))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Verify both results contain the expected fields
        expected_fields = ["existing_formats", "missing_formats", "format_counts"]
        for field in expected_fields:
            self.assertIn(field, original_result)
            self.assertIn(field, refactored_result)
        
        # Verify existing_formats contains the expected content
        for format_type in ["Blog Post", "Whitepaper", "Video"]:
            self.assertIn(format_type, [f.strip() for f in original_result.get("existing_formats", [])])
            self.assertIn(format_type, [f.strip() for f in refactored_result.get("existing_formats", [])])
        
        # Print results for manual comparison
        print("\nOriginal format gaps result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored format gaps result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_evaluate_multilingual_needs(self):
        """Test that the refactored multilingual needs analysis maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_agent.evaluate_multilingual_needs(self.multilingual_json)
        refactored_result = await self.refactored_agent.evaluate_multilingual_needs(
            self.sample_content_inventory,
            self.sample_client_demographics
        )
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, dict))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Verify both results contain the expected fields
        expected_fields = ["language_distribution", "language_gaps", "translation_priorities"]
        for field in expected_fields:
            self.assertIn(field, original_result)
            self.assertIn(field, refactored_result)
        
        # Verify language_gaps contains French (since our demographics show 25% French speakers but no French content)
        self.assertIn("French", [lang.strip() for lang in original_result.get("language_gaps", [])])
        self.assertIn("French", [lang.strip() for lang in refactored_result.get("language_gaps", [])])
        
        # Print results for manual comparison
        print("\nOriginal multilingual needs result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored multilingual needs result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_generate_gap_analysis_report(self):
        """Test that the refactored gap analysis report generation maintains functionality."""
        # Get results from both implementations
        original_result = await self.original_agent.generate_gap_analysis_report(self.gap_report_json)
        refactored_result = await self.refactored_agent.generate_gap_analysis_report(
            self.mock_practice_area_gaps,
            self.mock_format_gaps,
            self.mock_multilingual_gaps
        )
        
        # Verify results have the expected structure
        self.assertTrue(isinstance(original_result, dict))
        self.assertTrue(isinstance(refactored_result, dict))
        
        # Verify both results contain the expected fields
        expected_fields = ["title", "practice_area_gaps", "format_gaps", "multilingual_gaps", "recommendations"]
        for field in expected_fields:
            self.assertIn(field, original_result)
            self.assertIn(field, refactored_result)
        
        # Verify title is as expected
        self.assertEqual(original_result.get("title"), "Content Gap Analysis Report")
        self.assertEqual(refactored_result.get("title"), "Content Gap Analysis Report")
        
        # Print results for manual comparison
        print("\nOriginal gap analysis report result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored gap analysis report result:")
        print(json.dumps(refactored_result, indent=2))
    
    async def test_error_handling(self):
        """Test that error handling is consistent between implementations."""
        # Prepare invalid input for original implementation
        invalid_json = "{{invalid json}}"
        
        # Get results from both implementations
        original_result = await self.original_agent.identify_practice_area_gaps(invalid_json)
        refactored_result = await self.refactored_agent.identify_practice_area_gaps(None, None)
        
        # Verify error results have the expected structure
        self.assertIn("error", original_result)
        self.assertIn("error", refactored_result)
        
        # Print results for manual comparison
        print("\nOriginal error result:")
        print(json.dumps(original_result, indent=2))
        print("\nRefactored error result:")
        print(json.dumps(refactored_result, indent=2))


def run_async_test(test_method):
    """Helper to run async test methods."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_method())


if __name__ == "__main__":
    # Run the tests
    test = TestContentGapAnalysisAgent()
    test.setUp()
    
    print("Testing ContentGapAnalysisAgent...")
    
    print("\n--- Test: Identify Practice Area Gaps ---")
    run_async_test(test.test_identify_practice_area_gaps)
    
    print("\n--- Test: Identify Format Gaps ---")
    run_async_test(test.test_identify_format_gaps)
    
    print("\n--- Test: Evaluate Multilingual Needs ---")
    run_async_test(test.test_evaluate_multilingual_needs)
    
    print("\n--- Test: Generate Gap Analysis Report ---")
    run_async_test(test.test_generate_gap_analysis_report)
    
    print("\n--- Test: Error Handling ---")
    run_async_test(test.test_error_handling)
    
    print("\nTests completed!")
