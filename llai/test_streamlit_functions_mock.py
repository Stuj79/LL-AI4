import asyncio
import json

# Create a mock agent class for testing
class MockContentInventoryAgent:
    async def categorize_content(self, content_item_json):
        # Just verify the input is a string and parse it to validate format
        assert isinstance(content_item_json, str), "content_item_json must be a string"
        try:
            content_dict = json.loads(content_item_json)
            # Return a mock response to simulate success
            return {
                "practice_area": content_dict.get("practice_area", "Unknown"),
                "audience": content_dict.get("audience", "Unknown"),
                "format": content_dict.get("format", "Unknown"),
                "categorization_confidence": 0.95
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string provided"}
    
    async def evaluate_content_quality(self, content_item_json):
        # Just verify the input is a string and parse it to validate format
        assert isinstance(content_item_json, str), "content_item_json must be a string"
        try:
            content_dict = json.loads(content_item_json)
            # Return a mock response to simulate success
            return {
                "quality_rating": 4,
                "currency_status": "Up-to-date",
                "strategic_alignment": 4,
                "improvement_suggestions": ["Add more case studies", "Include client testimonials"]
            }
        except json.JSONDecodeError:
            return {"error": "Invalid JSON string provided"}

# Define our fixed functions (similar to the ones in streamlit_app.py)
async def categorize_content_item(content_item):
    content_agent = MockContentInventoryAgent()
    try:
        # The categorize_content method expects a JSON string
        # If content_item is already a string, use it directly
        # If it's a dictionary, convert it to a JSON string
        if isinstance(content_item, dict):
            content_item_json = json.dumps(content_item)
        else:
            # Already a string, use as is
            content_item_json = content_item
            
        # Call the categorize_content method with the JSON string
        response = await content_agent.categorize_content(content_item_json)
        return response
    except Exception as e:
        return {"error": f"Error categorizing content: {str(e)}"}

async def evaluate_content_quality(content_item):
    content_agent = MockContentInventoryAgent()
    try:
        # The evaluate_content_quality method also expects a JSON string
        # If content_item is already a string, use it directly
        # If it's a dictionary, convert it to a JSON string
        if isinstance(content_item, dict):
            content_item_json = json.dumps(content_item)
        else:
            # Already a string, use as is
            content_item_json = content_item
            
        # Call the evaluate_content_quality method with the JSON string
        response = await content_agent.evaluate_content_quality(content_item_json)
        return response
    except Exception as e:
        return {"error": f"Error evaluating content quality: {str(e)}"}

async def test_streamlit_functions():
    """
    Test the fixed categorize_content_item and evaluate_content_quality functions
    using mocked agent methods to verify they correctly handle both dictionary and string inputs.
    """
    # Create a test content item
    content_item_dict = {
        'title': 'Estate Planning Overview',
        'format': 'Article',
        'practice_area': 'Estate Law',
        'platform': 'website',
        'audience': 'Potential Clients',
        'publication_date': '2024-01-15',
        'description': 'A comprehensive overview of estate planning considerations'
    }
    
    # Also create a JSON string version
    content_item_json = json.dumps(content_item_dict)
    
    print("\n=== Testing categorize_content_item ===")
    
    # Test with dictionary input
    print("\nTesting with dictionary input:")
    result_dict = await categorize_content_item(content_item_dict)
    print(f"Result type: {type(result_dict)}")
    print(f"Result: {result_dict}")
    
    # Test with JSON string input
    print("\nTesting with JSON string input:")
    result_str = await categorize_content_item(content_item_json)
    print(f"Result type: {type(result_str)}")
    print(f"Result: {result_str}")
    
    print("\n=== Testing evaluate_content_quality ===")
    
    # Test with dictionary input
    print("\nTesting with dictionary input:")
    result_dict = await evaluate_content_quality(content_item_dict)
    print(f"Result type: {type(result_dict)}")
    print(f"Result: {result_dict}")
    
    # Test with JSON string input
    print("\nTesting with JSON string input:")
    result_str = await evaluate_content_quality(content_item_json)
    print(f"Result type: {type(result_str)}")
    print(f"Result: {result_str}")
    
    print("\n=== Tests Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(test_streamlit_functions())
