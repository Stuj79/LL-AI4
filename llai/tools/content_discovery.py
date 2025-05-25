import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional, Annotated
import datetime
import logging
from urllib.parse import urljoin
from pydantic import Field
from legion import tool

logger = logging.getLogger(__name__)

@tool
def scan_website_content(
    url: Annotated[str, Field(description="The URL of the website to scan")],
    depth: Annotated[int, Field(description="How many levels of links to follow")] = 2
) -> List[Dict[str, Any]]:
    """
    Scan a website to discover and catalog content pages.
    
    Args:
        url: The URL of the website to scan
        depth: How many levels of links to follow (default: 2)
        
    Returns:
        A list of content items with metadata
    """
    try:
        logger.info(f"Scanning website: {url} with depth {depth}")
        
        # Initial request to the main URL
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize content list
        content_items = []
        
        # Find all articles or main content sections
        content_sections = soup.find_all(['article', 'section', 'div'], class_=re.compile(r'(content|post|article|blog)'))
        
        # If no content sections found with specific classes, look for potential content containers
        if not content_sections:
            content_sections = soup.find_all(['article', 'section', 'div'], id=re.compile(r'(content|post|article|blog|main)'))
        
        # If still nothing found, try to find headings with potential content
        if not content_sections:
            headings = soup.find_all(['h1', 'h2', 'h3'])
            for heading in headings:
                parent = heading.find_parent(['div', 'section', 'article'])
                if parent and parent not in content_sections:
                    content_sections.append(parent)
        
        # Process each content section
        for section in content_sections:
            item = {}
            
            # Extract title
            title_tag = section.find(['h1', 'h2', 'h3'])
            item['title'] = title_tag.text.strip() if title_tag else "Untitled Content"
            
            # Try to find a link to the full content
            link = section.find('a')
            item['url'] = urljoin(url, link['href']) if link and 'href' in link.attrs else url
            
            # Try to extract publish date
            date_tag = section.find(text=re.compile(r'(posted|published|date|on)\s+', re.I)) or section.find(class_=re.compile(r'(date|time|posted|published)', re.I))
            item['publish_date'] = date_tag.text.strip() if date_tag else "Unknown"
            
            # Try to detect content type
            if 'blog' in url.lower() or section.find(class_=re.compile(r'blog', re.I)):
                item['type'] = "Blog post"
            elif 'practice' in url.lower() or section.find(text=re.compile(r'practice areas', re.I)):
                item['type'] = "Practice page"
            elif 'video' in url.lower() or section.find('iframe') or section.find('video'):
                item['type'] = "Video"
            else:
                item['type'] = "Article"
            
            # Add the content snippet
            content_p = section.find('p')
            item['snippet'] = content_p.text.strip() if content_p else ""
            
            content_items.append(item)
        
        # TODO: If depth > 1, follow links and continue scanning
        # This simplified version doesn't fully implement depth scanning
        
        return content_items
        
    except Exception as e:
        logger.error(f"Error scanning website {url}: {str(e)}")
        return [{"error": f"Failed to scan website: {str(e)}", "url": url}]

@tool
def extract_metadata(
    content_url: Annotated[str, Field(description="The URL of the content page to analyze")]
) -> Dict[str, Any]:
    """
    Extract metadata from a content page.
    
    Args:
        content_url: The URL of the content page
        
    Returns:
        A dictionary of metadata fields
    """
    try:
        logger.info(f"Extracting metadata from: {content_url}")
        
        # Request the page
        response = requests.get(content_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        metadata['title'] = title_tag.text.strip() if title_tag else "Untitled"
        
        # Extract description
        description_tag = soup.find('meta', attrs={'name': 'description'})
        metadata['description'] = description_tag['content'] if description_tag and 'content' in description_tag.attrs else ""
        
        # Extract keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        metadata['keywords'] = keywords_tag['content'] if keywords_tag and 'content' in keywords_tag.attrs else ""
        
        # Extract author
        author_tag = soup.find('meta', attrs={'name': 'author'})
        metadata['author'] = author_tag['content'] if author_tag and 'content' in author_tag.attrs else ""
        
        # Extract publish date
        publish_date_tag = soup.find('meta', attrs={'property': 'article:published_time'}) or soup.find('meta', attrs={'name': 'publication_date'})
        
        if publish_date_tag and 'content' in publish_date_tag.attrs:
            metadata['publish_date'] = publish_date_tag['content']
        else:
            # Look for date in the content
            date_tag = soup.find(class_=re.compile(r'(date|time|posted|published)', re.I))
            metadata['publish_date'] = date_tag.text.strip() if date_tag else ""
        
        # Extract content type
        if 'blog' in content_url.lower() or soup.find(class_=re.compile(r'blog', re.I)):
            metadata['content_type'] = "Blog post"
        elif 'practice' in content_url.lower() or soup.find(text=re.compile(r'practice areas', re.I)):
            metadata['content_type'] = "Practice page"
        elif 'video' in content_url.lower() or soup.find('iframe') or soup.find('video'):
            metadata['content_type'] = "Video"
        else:
            metadata['content_type'] = "Article"
        
        # Extract main content text
        content_section = soup.find(['article', 'section', 'div'], class_=re.compile(r'(content|post|article)', re.I))
        if content_section:
            # Get all paragraphs
            paragraphs = content_section.find_all('p')
            full_text = ' '.join([p.text.strip() for p in paragraphs])
            metadata['content_snippet'] = full_text[:300] + '...' if len(full_text) > 300 else full_text
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata from {content_url}: {str(e)}")
        return {"error": f"Failed to extract metadata: {str(e)}", "url": content_url}

@tool
def detect_content_language(
    text: Annotated[str, Field(description="The text to analyze for language detection")]
) -> str:
    """
    Detect the language of content text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Language identified ("English", "French", or "Bilingual")
    """
    # Basic implementation checking for characteristic patterns
    # For a real implementation, use a library like langdetect or langid
    
    # Simple word lists for basic detection
    english_words = ['the', 'and', 'of', 'to', 'in', 'is', 'that', 'for', 'it', 'with', 'as', 'on', 'be', 'this', 'law']
    french_words = ['le', 'la', 'les', 'des', 'et', 'en', 'que', 'qui', 'dans', 'est', 'pour', 'un', 'une', 'au', 'droit']
    
    # Normalize text for comparison
    text_lower = text.lower()
    
    # Count occurrences
    english_count = sum(1 for word in english_words if f' {word} ' in f' {text_lower} ')
    french_count = sum(1 for word in french_words if f' {word} ' in f' {text_lower} ')
    
    # Determine language based on counts
    if english_count > 0 and french_count > 0:
        # If both languages are detected
        if english_count > french_count * 3:  # Significantly more English
            return "English"
        elif french_count > english_count * 3:  # Significantly more French
            return "French"
        else:
            return "Bilingual"
    elif english_count > 0:
        return "English"
    elif french_count > 0:
        return "French"
    else:
        # Default to English if no clear indicators
        return "English"

@tool
def classify_content_format(
    url: Annotated[str, Field(description="The URL of the content")],
    content: Annotated[str, Field(description="The HTML content to analyze")]
) -> str:
    """
    Classify the format of content (article, blog post, video, etc.).
    
    Args:
        url: The URL of the content
        content: The HTML content to analyze
        
    Returns:
        Content format classification
    """
    # Convert to lowercase for case-insensitive matching
    url_lower = url.lower()
    content_lower = content.lower()
    
    # Create a BeautifulSoup object for better HTML parsing
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check for video content
    if 'video' in url_lower or soup.find('iframe') or soup.find('video'):
        return "Video"
    
    # Check for podcast content
    if 'podcast' in url_lower or 'audio' in url_lower or soup.find('audio'):
        return "Podcast"
    
    # Check for blog posts
    if 'blog' in url_lower or soup.find(class_=re.compile(r'blog', re.I)) or soup.find(text=re.compile(r'posted on|posted by', re.I)):
        return "Blog post"
    
    # Check for practice area pages
    if 'practice' in url_lower or soup.find(text=re.compile(r'practice areas', re.I)) or soup.find(class_=re.compile(r'practice-area', re.I)):
        return "Practice page"
    
    # Check for newsletters
    if 'newsletter' in url_lower or soup.find(class_=re.compile(r'newsletter', re.I)):
        return "Newsletter"
    
    # Check for guides or whitepapers
    if 'guide' in url_lower or 'whitepaper' in url_lower or 'ebook' in url_lower:
        return "Guide"
    
    # Check for infographics
    if 'infographic' in url_lower or soup.find('img', class_=re.compile(r'infographic', re.I)):
        return "Infographic"
    
    # Check for case studies
    if 'case-study' in url_lower or 'case-studies' in url_lower or soup.find(text=re.compile(r'case study', re.I)):
        return "Case Study"
    
    # Check for FAQ pages
    if 'faq' in url_lower or soup.find('dt') or soup.find(text=re.compile(r'frequently asked', re.I)):
        return "FAQ"
    
    # Default to article for general content
    return "Article"
