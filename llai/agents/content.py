from legion import agent, tool
from typing import List, Dict
from pydantic import BaseModel, Field
import json

class QualityScore(BaseModel):
    clarity: float = Field(..., ge=0.0, le=1.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    tone: float = Field(..., ge=0.0, le=1.0)
    overall: float = Field(..., ge=0.0, le=1.0)
    feedback: List[str]

class ContentCategorization(BaseModel):
    id: str
    ai_categories: List[str]
    ai_sub_categories: List[str]

@agent(model="openai:gpt-4o-mini", temperature=0.2)
class ContentInventoryAgent:
    """
    You are a content inventory specialist. Given a source
    (CMS endpoint, file path), RETURN A JSON ARRAY:
    [
      { "id": str, "title": str, "author": str, "date": str, "tags": [str] },
      …
    ]
    """
    @tool
    def fetch_content_metadata(self, source: str) -> List[Dict]:
        """List raw content records from the CMS or filesystem."""
        ...

    @tool
    def normalize_content_entries(self, raw: List[Dict]) -> List[Dict]:
        """Clean and standardize metadata fields."""
        ...

@agent(model="openai:gpt-4o-mini", temperature=0.2)
class ContentCategorizationAgent:
    """
    You are a legal content categorization expert. Given one content item
    and a legal practice area taxonomy, categorize the content according to the
    legal taxonomy.
     
    RESPOND WITH A RAW JSON OBJECT matching this schema exactly 
    (no extra prose or markdown):
    {
      "id": str,
      "ai_categories": [str],
      "ai_sub_categories": [str]
    }
    The ai_categories and ai_sub_categories should be the best-fitting
    categories and subcategories from the taxonomy provided.
    """
    @tool
    def parse_categorized_content(self, raw_json: str) -> ContentCategorization:
        """Parse and validate the LLM’s JSON output into a ContentCategorization."""
        data = json.loads(raw_json)
        return ContentCategorization.model_validate(data)
        

@agent(model="openai:gpt-4o-mini", temperature=0.2)
class ContentQualityAssessmentAgent:
    """
    You are an expert content reviewer. Given a content item JSON
    (with fields id, title, body), rate clarity, accuracy, tone,
    and overall. Provide actionable feedback.

    RESPOND WITH A RAW JSON OBJECT matching:
    {
      "clarity": float,
      "accuracy": float,
      "tone": float,
      "overall": float,
      "feedback": [str]
    }
    """
    @tool
    def parse_quality_score(self, raw_json: str) -> QualityScore:
        """Parse and validate the LLM’s JSON output into a QualityScore."""
        ...
