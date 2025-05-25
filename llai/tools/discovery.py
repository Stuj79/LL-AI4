from legion import tool
from typing import Annotated, Dict, List, Any
from pydantic import Field
import json
import re

@tool
def extract_analytics_from_ga4(
    json_data: Annotated[str, Field(description="JSON data exported from Google Analytics 4")],
    metrics_of_interest: Annotated[List[str], Field(description="List of metrics to extract")] = ["sessions", "pageviews", "bounceRate"]
) -> Dict[str, Any]:
    """Extract and format analytics data from Google Analytics 4 JSON export."""
    # This would parse GA4 JSON format and extract relevant metrics
    try:
        data = json.loads(json_data)
        result = {}
        
        # Extract metrics of interest
        for metric in metrics_of_interest:
            if metric in data:
                result[metric] = data[metric]
        
        # Add dimension breakdowns if present
        if "dimensions" in data:
            result["dimensions"] = data["dimensions"]
            
        return result
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data provided"}
    except Exception as e:
        return {"error": str(e)}

@tool
def extract_analytics_from_social_media(
    platform: Annotated[str, Field(description="Social media platform name (e.g., 'LinkedIn', 'Twitter')")],
    csv_data: Annotated[str, Field(description="CSV data exported from the social media platform")]
) -> Dict[str, Any]:
    """Extract and format analytics data from social media CSV exports."""
    # This would parse CSV data from various social platforms
    lines = csv_data.strip().split("\n")
    headers = lines[0].split(",")
    
    result = {
        "platform": platform,
        "metrics": {},
        "posts": []
    }
    
    # For demonstration, extract some fake metrics
    result["metrics"]["followers"] = 2500
    result["metrics"]["engagement_rate"] = "2.8%"
    
    # Add sample post data
    if len(lines) > 1:
        for i in range(1, min(4, len(lines))):
            result["posts"].append({
                "date": "2024-03-01",
                "content": "Sample post content",
                "impressions": 1200,
                "engagement": 45
            })
    
    return result

@tool
def check_provincial_law_compliance(
    content: Annotated[str, Field(description="Marketing content to check for compliance")],
    province: Annotated[str, Field(description="Canadian province code (e.g., 'ON', 'BC')")] = "ON"
) -> Dict[str, Any]:
    """Check marketing content for compliance with provincial law society rules."""
    # This would scan content for compliance issues based on provincial rules
    
    # Define some basic rules per province
    province_rules = {
        "ON": [
            {"term": "specialist", "rule": "Cannot claim to be a specialist without certification"},
            {"term": "expert", "rule": "Avoid using 'expert' without substantiation"}
        ],
        "BC": [
            {"term": "guarantee", "rule": "Cannot guarantee specific legal outcomes"},
            {"term": "best lawyer", "rule": "Avoid comparative claims without substantiation"}
        ]
    }
    
    # Get rules for specified province, defaulting to Ontario
    rules = province_rules.get(province, province_rules["ON"])
    
    violations = []
    for rule in rules:
        if re.search(r'\b' + rule["term"] + r'\b', content, re.IGNORECASE):
            violations.append({
                "term": rule["term"],
                "rule": rule["rule"],
                "context": re.findall(r'.{0,30}\b' + rule["term"] + r'\b.{0,30}', content, re.IGNORECASE)
            })
    
    return {
        "province": province,
        "compliant": len(violations) == 0,
        "violations": violations
    }
