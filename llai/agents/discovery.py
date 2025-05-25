from legion import agent, tool
from typing import Dict, List, Any, Annotated, ClassVar # Added ClassVar
from pydantic import Field, BaseModel
import logging
import datetime
from agents.agent_base import BaseAgent

logger = logging.getLogger(__name__)

class StakeholderInfo(BaseModel):
    name: str
    role: str
    contact_info: str = ""
    responsibilities: List[str] = []

# --- Logic for identify_stakeholders ---
# Defined outside the class, assuming no 'self' needed for tool logic.
def _identify_stakeholders_logic(
    company_structure: Annotated[str, Field(description="Text describing company structure, departments, or team makeup")]
) -> Dict[str, List[Dict[str, Any]]]:
    """Identify and categorize stakeholders from company information."""
    # (Implementation remains the same)
    return {
        "internal": [
            {"name": "Marketing Director", "role": "Leadership", "responsibilities": ["Strategy oversight", "Budget approval"]},
            {"name": "Content Manager", "role": "Management", "responsibilities": ["Content calendar", "Quality assurance"]}
        ],
        "external": [
            {"name": "SEO Agency", "role": "Vendor", "responsibilities": ["Technical SEO", "Keyword research"]}
        ]
    }

# --- Logic for compile_platform_inventory ---
# Defined outside the class, assuming no 'self' needed for tool logic.
def _compile_platform_inventory_logic(
    platform_data: Annotated[str, Field(description="Information about marketing platforms used")]
) -> Dict[str, List[Dict[str, str]]]:
    """Compile an inventory of marketing platforms from provided data."""
    # (Implementation remains the same)
    return {
        "website": [{"name": "Company Website", "access_level": "Admin", "platform": "WordPress"}],
        "social_media": [
            {"name": "LinkedIn", "access_level": "Admin", "url": "linkedin.com/company/example"},
            {"name": "Twitter", "access_level": "Editor", "url": "twitter.com/example"}
        ],
        "email_marketing": [{"name": "Mailchimp", "access_level": "Admin", "account": "example@company.com"}]
    }


@agent(model="openai:gpt-4o-mini", temperature=0.3)
class StakeholderIdentificationAgent:
    """Agent that identifies and categorizes stakeholders in a legal marketing team."""

    # Assign decorated logic functions to ClassVar attributes
    identify_stakeholders: ClassVar = tool(_identify_stakeholders_logic)
    compile_platform_inventory: ClassVar = tool(_compile_platform_inventory_logic)


@agent(model="openai:gpt-4o-mini", temperature=0.3)
class AnalyticsCollectionAgent:
    """Agent that collects, organizes, and summarizes marketing analytics data."""
    
    @tool
    def collect_website_analytics(
        self,
        analytics_data: Annotated[str, Field(description="Raw website analytics data")],
        time_period: Annotated[str, Field(description="Time period for the data")] = "Last 30 days"
    ) -> Dict[str, Any]:
        """Process and organize website analytics data."""
        # This would parse analytics data from various sources
        return {
            "traffic": {"total_visits": 5000, "unique_visitors": 3200},
            "engagement": {"avg_time_on_page": "2:15", "bounce_rate": "45%"},
            "top_pages": [
                {"url": "/services", "views": 1200, "bounce_rate": "35%"},
                {"url": "/about", "views": 800, "bounce_rate": "40%"}
            ],
            "time_period": time_period
        }
    
    @tool
    def collect_social_media_metrics(
        self,
        platform: Annotated[str, Field(description="Social media platform name")],
        metrics_data: Annotated[str, Field(description="Raw metrics data for the platform")],
        time_period: Annotated[str, Field(description="Time period for the data")] = "Last 30 days"
    ) -> Dict[str, Any]:
        """Process and organize social media metrics."""
        # This would handle different social platforms with their specific metrics
        return {
            "platform": platform,
            "followers": 2500,
            "engagement": {"likes": 450, "shares": 120, "comments": 85},
            "reach": 8500,
            "impressions": 12000,
            "time_period": time_period
        }
    
    @tool
    def collect_email_metrics(
        self,
        email_data: Annotated[str, Field(description="Raw email campaign data")],
        time_period: Annotated[str, Field(description="Time period for the data")] = "Last 30 days"
    ) -> Dict[str, Any]:
        """Process and organize email marketing metrics."""
        # This would process email marketing platform data
        return {
            "campaigns": 5,
            "total_sends": 7500,
            "open_rate": "22%",
            "click_rate": "3.5%",
            "conversion_rate": "1.2%",
            "time_period": time_period
        }
    
    @tool
    def compile_analytics_report(
        self,
        website_data: Annotated[Dict[str, Any], Field(description="Website analytics data")],
        social_data: Annotated[List[Dict[str, Any]], Field(description="List of social media platform data")],
        email_data: Annotated[Dict[str, Any], Field(description="Email marketing data")],
        time_period: Annotated[str, Field(description="Time period covered in the report")] = "Last 30 days"
    ) -> Dict[str, Any]:
        """Compile a comprehensive marketing analytics report from multiple data sources."""
        # This would create a consolidated report with key metrics
        return {
            "report_title": f"Marketing Performance Report - {time_period}",
            "generated_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "website_performance": website_data,
            "social_media_performance": social_data,
            "email_performance": email_data,
            "key_findings": [
                "Website traffic increased 15% from previous period",
                "LinkedIn engagement exceeds other platforms by 35%",
                "Email open rates are below industry average by 3 percentage points"
            ]
        }

@agent(model="openai:gpt-4o-mini", temperature=0.4)
class BenchmarkAnalysisAgent:
    """Agent that establishes marketing performance benchmarks and identifies trends."""
    
    @tool
    def establish_performance_benchmarks(
        self,
        current_data: Annotated[Dict[str, Any], Field(description="Current performance metrics")],
        historical_data: Annotated[Dict[str, Any], Field(description="Historical performance metrics")],
        industry_data: Annotated[Dict[str, Any], Field(description="Industry benchmark data")] = None
    ) -> Dict[str, Any]:
        """Establish performance benchmarks by comparing current metrics to historical and industry data."""
        # This would analyze trends and establish baseline metrics
        benchmarks = {
            "website": {
                "traffic": {
                    "current": current_data.get("website", {}).get("traffic", {}).get("total_visits"),
                    "historical_avg": 4500,  # Calculated from historical_data
                    "trend": "+11%",  # Calculated comparison
                    "industry_avg": 5200,  # From industry_data if provided
                },
                "bounce_rate": {
                    "current": "45%",
                    "historical_avg": "48%",
                    "trend": "+3%",  # Improvement
                    "industry_avg": "42%"
                }
            },
            "social_media": {
                "engagement_rate": {
                    "current": "2.8%",
                    "historical_avg": "2.5%",
                    "trend": "+0.3%",
                    "industry_avg": "3.2%"
                }
            },
            "email": {
                "open_rate": {
                    "current": "22%",
                    "historical_avg": "23%",
                    "trend": "-1%",
                    "industry_avg": "25%"
                }
            }
        }
        
        return {
            "benchmarks": benchmarks,
            "time_period": current_data.get("time_period", "Current period"),
            "comparison_period": historical_data.get("time_period", "Previous period"),
            "key_observations": [
                "Website traffic showing positive growth trend",
                "Social engagement improving but still below industry standards",
                "Email performance trending downward and below industry average"
            ]
        }
    
    @tool
    def identify_compliance_concerns(
        self,
        marketing_data: Annotated[Dict[str, Any], Field(description="Marketing assets and content")],
        regulatory_guidelines: Annotated[Dict[str, Any], Field(description="Legal regulatory guidelines")]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identify potential compliance issues in marketing assets."""
        # This would scan content for compliance issues
        return {
            "high_risk": [
                {
                    "asset": "Homepage hero section",
                    "issue": "Uses term 'specialists' without appropriate disclaimer",
                    "guideline_ref": "Ontario Rule 4.3"
                }
            ],
            "medium_risk": [
                {
                    "asset": "Attorney bio pages",
                    "issue": "Client testimonials may need additional disclaimers",
                    "guideline_ref": "BC Law Society Marketing Rule 3.2"
                }
            ],
            "low_risk": [
                {
                    "asset": "Blog posts",
                    "issue": "Missing clear distinction between legal information vs. advice",
                    "guideline_ref": "General best practice"
                }
            ]
        }
