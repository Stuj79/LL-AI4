from typing import Dict, List, Optional, Tuple, Set, Any
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from data import get_taxonomy
from data.legal_taxonomy import LegalCategory

class LegalTaxonomyMapper:
    """Maps content to the Canadian legal taxonomy."""
    
    def __init__(self):
        self.taxonomy = get_taxonomy()
        
    def get_parent_categories(self) -> List[Dict[str, Any]]:
        """Get all parent categories in a serializable format."""
        return [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description[:100] + "..." if len(category.description) > 100 else category.description
            }
            for category in self.taxonomy.get_all_parent_categories()
        ]
        
    def get_subcategories(self, parent_id: int) -> List[Dict[str, Any]]:
        """Get all subcategories for a parent category in a serializable format."""
        subcategories = self.taxonomy.get_subcategories(parent_id)
        return [
            {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id,
                "description": category.description[:100] + "..." if len(category.description) > 100 else category.description
            }
            for category in subcategories
        ]
        
    def extract_content_keywords(self, content: str) -> Set[str]:
        """Extract keywords from content text."""
        # Similar to extract_keywords in taxonomy_enricher.py
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            
        stop_words = set(stopwords.words('english'))
        word_tokens = word_tokenize(content.lower())
        keywords = [word for word in word_tokens if word.isalnum() and word not in stop_words]
        
        # Find phrases
        phrases = []
        for i in range(len(word_tokens) - 1):
            if word_tokens[i].isalnum() and word_tokens[i+1].isalnum():
                phrases.append(f"{word_tokens[i]} {word_tokens[i+1]}")
        
        for i in range(len(word_tokens) - 2):
            if (word_tokens[i].isalnum() and word_tokens[i+1].isalnum() and 
                word_tokens[i+2].isalnum()):
                phrases.append(f"{word_tokens[i]} {word_tokens[i+1]} {word_tokens[i+2]}")
        
        return set(keywords + phrases)
        
    def calculate_keyword_match_score(self, content_keywords: Set[str], 
                                     category: LegalCategory) -> float:
        """Calculate a score based on keyword matches."""
        if not category.keywords:
            return 0.0
            
        matches = content_keywords.intersection(category.keywords)
        return len(matches) / len(category.keywords) if category.keywords else 0.0
        
    def map_to_taxonomy(self, content: str) -> Dict[str, Any]:
        """Map content to the legal taxonomy."""
        content_keywords = self.extract_content_keywords(content)
        
        # Score each parent category
        parent_scores = []
        for parent in self.taxonomy.get_all_parent_categories():
            score = self.calculate_keyword_match_score(content_keywords, parent)
            parent_scores.append((parent, score))
        
        # Sort by score in descending order
        parent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top 3 parent categories
        top_parents = []
        for parent, score in parent_scores[:3]:
            if score > 0.1:  # Minimum threshold
                parent_result = {
                    "id": parent.id,
                    "name": parent.name,
                    "score": score,
                    "subcategories": []
                }
                
                # Score subcategories for this parent
                subcategories = self.taxonomy.get_subcategories(parent.id)
                subcategory_scores = []
                
                for sub in subcategories:
                    sub_score = self.calculate_keyword_match_score(content_keywords, sub)
                    if sub_score > 0.1:  # Minimum threshold
                        subcategory_scores.append({
                            "id": sub.id,
                            "name": sub.name,
                            "score": sub_score
                        })
                
                # Sort subcategories by score
                subcategory_scores.sort(key=lambda x: x["score"], reverse=True)
                parent_result["subcategories"] = subcategory_scores[:5]  # Top 5 subcategories
                
                top_parents.append(parent_result)
        
        return {
            "parent_categories": top_parents,
            "raw_content_length": len(content)
        }
