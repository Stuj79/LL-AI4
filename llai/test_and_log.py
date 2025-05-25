import asyncio
import json
import os
from test_streamlit_functions_mock import test_streamlit_functions

async def run_test_and_log():
    """Run the test and log output to a file"""
    # Redirect stdout to a file
    import sys
    original_stdout = sys.stdout
    
    log_file_path = os.path.join(os.path.dirname(__file__), "test_results.log")
    
    with open(log_file_path, 'w') as log_file:
        # Redirect stdout to our log file
        sys.stdout = log_file
        
        # Run the test
        await test_streamlit_functions()
    
    # Restore stdout
    sys.stdout = original_stdout
    
    # Print a message indicating where the log file is
    print(f"Test completed. Results logged to: {log_file_path}")
    
    # Also print a summary
    with open(log_file_path, 'r') as log_file:
        content = log_file.read()
        print("\nTest Summary:\n")
        print(content)

if __name__ == "__main__":
    asyncio.run(run_test_and_log())
