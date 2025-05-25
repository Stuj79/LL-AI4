from legion import tool
from pydantic import Field
from typing import Annotated
import requests
from bs4 import BeautifulSoup

@tool
def fetch_webpage(
    url: Annotated[str, Field(description="URL of the webpage to scrape")]
) -> str:
    """Fetch the HTML content from a given URL."""
    # Implementation using requests or similar library
    import requests
    response = requests.get(url)
    return response.text[:20]

@tool
def extract_text_from_html(
    html: Annotated[str, Field(description="HTML content to extract text from")],
    selector: Annotated[str, Field(description="CSS selector to target specific elements")] = "body"
) -> str:
    """Extract text content from HTML using CSS selectors."""
    # Implementation using BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.select(selector)
    return "\n".join([elem.get_text(strip=True) for elem in elements][:100])