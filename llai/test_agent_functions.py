import asyncio
from llai.agents.content import ContentInventoryAgent
import json

async def test_categorize_content():
    # Create a test content item
    content_item = {
        'title': 'Estate Planning Overview',
        'format': 'Article',
        'practice_area': 'Estate Law',
        'platform': 'website',
        'audience': 'Potential Clients',
        'publication_date': '2024-01-15',
        'description': 'A comprehensive overview of estate planning considerations'
    }
    
    # Convert to JSON string
    content_item_json = json.dumps(content_item)
    
    # Create agent instance
    agent = ContentInventoryAgent()
    
    # Test with JSON string
    print('\nTesting categorize_content with JSON string:')
    try:
        result = await agent.categorize_content(content_item_json)
        print('Success! Result:', result)
    except Exception as e:
        print(f'Error: {str(e)}')
    
    # Test evaluate_content_quality with JSON string
    print('\nTesting evaluate_content_quality with JSON string:')
    try:
        result = await agent.evaluate_content_quality(content_item_json)
        print('Success! Result:', result)
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_categorize_content())
