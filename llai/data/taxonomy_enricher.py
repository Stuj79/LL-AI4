import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download('punkt_tab')
import re
from collections import Counter
from typing import List, Set, Dict

from .legal_taxonomy import LegalCategory, LegalTaxonomy

def extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text."""
    # Ensure NLTK resources are available
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')
    
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text.lower())
    keywords = [word for word in word_tokens if word.isalnum() and word not in stop_words]
    
    # Find legal phrases (2-3 word combinations)
    phrases = []
    for i in range(len(word_tokens) - 1):
        if word_tokens[i].isalnum() and word_tokens[i+1].isalnum():
            phrases.append(f"{word_tokens[i]} {word_tokens[i+1]}")
    
    for i in range(len(word_tokens) - 2):
        if (word_tokens[i].isalnum() and word_tokens[i+1].isalnum() and 
            word_tokens[i+2].isalnum()):
            phrases.append(f"{word_tokens[i]} {word_tokens[i+1]} {word_tokens[i+2]}")
    
    # Combine words and phrases
    all_keywords = set(keywords + phrases)
    
    # Filter for relevance - remove overly common terms
    return all_keywords

def enrich_taxonomy(taxonomy: LegalTaxonomy) -> LegalTaxonomy:
    """Add keywords and semantic features to the taxonomy."""
    for category_id, category in taxonomy.categories.items():
        # Extract keywords from description
        if category.description:
            category.keywords.update(extract_keywords(category.description))
        
        # Add the category name and variations as keywords
        name_words = category.name.lower().split()
        category.keywords.add(category.name.lower())
        for i in range(len(name_words)):
            if name_words[i] not in stopwords.words('english'):
                category.keywords.add(name_words[i])
    
    return taxonomy
