import asyncio
import json
from agents.content import ContentInventoryAgent

# Import the fixed functions from streamlit_app.py
from streamlit_app import categorize_content_item, evaluate_content_quality

async def test_streamlit_functions():
    """
    Test the fixed categorize_content_item and evaluate_content_quality functions
    from streamlit_app.py to verify they correctly handle both dictionary and string inputs.
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
