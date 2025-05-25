# Import agents for external use
from .content import ContentInventoryAgent, ContentCategorizationAgent, ContentQualityAssessmentAgent
# from .content import ContentGapAnalysisAgent, ContentClassificationAgent
# from .hierarchical_classification import HierarchicalClassificationAgent
from .gap_refactored import PracticeAreaGapAgent, FormatGapAgent, MultilingualNeedsAgent, GapReportAssemblyAgent

__all__ = [
    "ContentInventoryAgent",
    # "ContentGapAnalysisAgent",
    # "ContentClassificationAgent",
    "ContentCategorizationAgent",
    "ContentQualityAssessmentAgent",
    # "HierarchicalClassificationAgent",
    "PracticeAreaGapAgent",
    "FormatGapAgent",
    "MultilingualNeedsAgent",
    "GapReportAssemblyAgent",
]


# For backward compatibility with main.py
# These classes don't actually exist yet but are referenced in main.py
class CopywriterAgent: pass
class ContentStrategistAgent: pass
class BrandVoiceAgent: pass
class SeoAnalystAgent: pass
class CompetitorBenchmarkAgent: pass
class PerformanceTrackerAgent: pass
class WebScraperAgent: pass
class LegalResearchAgent: pass
class AudienceAnalysisAgent: pass
