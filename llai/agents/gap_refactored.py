from legion import agent, tool
from typing import List, Dict
from pydantic import BaseModel, Field
import json

class PracticeAreaGaps(BaseModel):
    gaps: List[str]

class FormatGaps(BaseModel):
    gaps: List[str]

# @agent(model="openai:gpt-4o-mini", temperature=0.2)
LM_STUDIO_URL = "http://localhost:1234/v1" # Replace with your actual LM Studio server URL
MODEL = "openai:llama-3-groq-8b-tool-use" # Replace with your actual model name

@agent(
    model=MODEL, 
    temperature=0.5,
    # --- Key Configuration ---
    base_url=LM_STUDIO_URL,
    # api_key="lm-studio" # Or None, or omit if LM Studio server doesn't require one
    # -------------------------
)
class PracticeAreaGapAgent:
    """
    You are a gap analyst for practice areas. Given existing
    content topics and a list of required practice areas,
    RESPOND WITH A RAW JSON ARRAY OF MISSING AREAS:
    [ "practice area1", "practice area2", … ]
    """
    @tool
    def identify_topic_gaps(
        self,
        covered: List[str],
        required: List[str]
    ) -> List[str]:
        print(f"Covered practice areas: {type(covered)}")  # Debugging line to check existing topics
        print(f"Required practice areas: {type(required)}")  # Debugging line to check required topics
        """Return which practice areas are not covered by existing topics."""
        gaps = [item for item in required if item not in covered]
        return gaps

    @tool
    def parse_practice_area_gaps(self, raw_json: str) -> PracticeAreaGaps:
        """Parse and validate the LLM’s JSON output into a PracticeAreaGaps."""
        print(f"Raw JSON: {raw_json}")  # Debugging line to check the raw JSON input
        data = json.loads(raw_json)
        print(f"Parsed JSON: {data}")  # Debugging line to check the parsed data
        # return PracticeAreaGaps.model_validate(data)

@agent(
    model=MODEL, 
    temperature=0.5,
    # --- Key Configuration ---
    base_url=LM_STUDIO_URL,
    # api_key="lm-studio" # Or None, or omit if LM Studio server doesn't require one
    # -------------------------
)
class FormatGapAgent:
    """
    You are a format gap detector. Given a list of formats covered
    and a list of possible formats,
    RESPOND WITH A RAW JSON ARRAY OF MISSING AREAS:
    [ "format1", "format2", … ]
    """
   
    @tool
    def identify_format_gaps(
        self,
        covered: List[str],
        possible: List[str]
    ) -> List[str]:
        print(f"Covered formats: {type(covered)}")  # Debugging line to check existing topics
        print(f"Possible formats: {type(possible)}")  # Debugging line to check required topics
        """Return which possible formats are not covered."""
        gaps = [item for item in possible if item not in covered]
        return gaps
    
    @tool
    def parse_format_gaps(self, raw_json: str) -> FormatGaps:
        """Parse and validate the LLM’s JSON output into a FormatAreaGaps."""
        print(f"Raw JSON: {raw_json}")  # Debugging line to check the raw JSON input
        data = json.loads(raw_json)
        print(f"Parsed JSON: {data}")  # Debugging line to check the parsed data
        # return FormatGaps.model_validate(data)

@agent(
    model=MODEL, 
    temperature=0.5,
    # --- Key Configuration ---
    base_url=LM_STUDIO_URL,
    # api_key="lm-studio" # Or None, or omit if LM Studio server doesn't require one
    # -------------------------
)
class MultilingualNeedsAgent:
    """
    You are a language coverage assessor. Given content items
    annotated with locale codes and a list of target locales,
    RESPOND WITH A JSON ARRAY:
    [
      { "locale": str, "missing_count": int },
      …
    ]
    """
    @tool
    def analyze_language_coverage(
        self,
        items: List[Dict],
        locales: List[str]
    ) -> List[Dict]:
        """Count how many items are missing per target locale."""
        ...

@agent(
    model=MODEL, 
    temperature=0.7,
    # --- Key Configuration ---
    base_url=LM_STUDIO_URL,
    # api_key="lm-studio" # Or None, or omit if LM Studio server doesn't require one
    # -------------------------
)
class GapReportAssemblyAgent:
    """
    You are a report assembler. Given two inputs:
    - practice_gaps: List[str]
    - format_gaps: List[Dict]

    RESPOND WITH an analysis report, critiquing the gaps
    and suggesting next steps.
    """
    # @tool
    # def assemble_gap_report(
    #     self,
    #     practice_gaps: List[str],
    #     format_gaps: List[Dict],
    #     # language_gaps: List[Dict]
    # ) -> Dict:
    #     """Merge the three gap‑lists into one structured report."""
    #     return {
    #         "practice_area_gaps": practice_gaps,
    #         "format_gaps": format_gaps,
    #         # "language_gaps": language_gaps
    #     }
