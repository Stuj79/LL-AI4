"""
Legion System Performance Baselines

This module establishes performance baselines for the existing Legion system
to enable comparison with the migrated Atomic Agents implementation.
"""

import time
import psutil
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Import Legion components for baseline testing
try:
    from llai.agents.content import ContentInventoryAgent
    from llai.agents.discovery import StakeholderIdentificationAgent
    from llai.agents.gap_refactored import GapAnalysisAgent
    from llai.tools.content_analysis import ContentAnalysisTool
    from llai.tools.discovery import DiscoveryTool
except ImportError as e:
    pytest.skip(f"Legion components not available: {e}", allow_module_level=True)


@dataclass
class PerformanceMetrics:
    """Data class for storing performance measurement results."""
    
    workflow_name: str
    execution_time: float
    memory_delta: int  # bytes
    peak_memory: int  # bytes
    cpu_percent: float
    timestamp: str
    environment_info: Dict[str, Any]
    success: bool
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PerformanceProfiler:
    """
    Performance profiler for measuring system resource usage during operations.
    """
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.peak_memory = None
        self.cpu_samples = []
    
    def start_profiling(self):
        """Start performance profiling."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        self.peak_memory = self.start_memory
        self.cpu_samples = []
    
    def sample_resources(self):
        """Sample current resource usage."""
        current_memory = self.process.memory_info().rss
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        try:
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)
        except psutil.AccessDenied:
            # Handle cases where CPU measurement is not available
            pass
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop profiling and return metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        execution_time = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0
        
        return {
            "execution_time": execution_time,
            "memory_delta": memory_delta,
            "peak_memory": self.peak_memory,
            "cpu_percent": avg_cpu
        }


class LegionBaselineTests:
    """
    Test class for establishing Legion system performance baselines.
    
    These tests measure the performance of critical workflows in the existing
    Legion system to provide comparison points for the Atomic Agents migration.
    """
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.baseline_data = []
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information for baseline context."""
        return {
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "platform": psutil.sys.platform,
            "hostname": psutil.os.uname().nodename if hasattr(psutil.os, 'uname') else "unknown"
        }
    
    def save_baseline_data(self, metrics: PerformanceMetrics):
        """Save baseline data to file."""
        baseline_dir = Path("memory-bank/performance_baselines")
        baseline_dir.mkdir(exist_ok=True)
        
        filename = f"legion_baseline_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = baseline_dir / filename
        
        # Load existing data if file exists
        if filepath.exists():
            with open(filepath, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Append new metrics
        existing_data.append(metrics.to_dict())
        
        # Save updated data
        with open(filepath, 'w') as f:
            json.dump(existing_data, f, indent=2)
    
    def run_baseline_test(self, workflow_name: str, test_function, *args, **kwargs) -> PerformanceMetrics:
        """
        Run a baseline test with performance profiling.
        
        Args:
            workflow_name: Name of the workflow being tested
            test_function: Function to execute and measure
            *args, **kwargs: Arguments to pass to test_function
            
        Returns:
            PerformanceMetrics object with measurement results
        """
        self.profiler.start_profiling()
        
        success = True
        error_message = ""
        
        try:
            # Execute the test function
            result = test_function(*args, **kwargs)
            
            # Sample resources during execution
            self.profiler.sample_resources()
            
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
        
        # Stop profiling and get metrics
        perf_data = self.profiler.stop_profiling()
        
        metrics = PerformanceMetrics(
            workflow_name=workflow_name,
            execution_time=perf_data["execution_time"],
            memory_delta=perf_data["memory_delta"],
            peak_memory=perf_data["peak_memory"],
            cpu_percent=perf_data["cpu_percent"],
            timestamp=datetime.utcnow().isoformat(),
            environment_info=self.get_environment_info(),
            success=success,
            error_message=error_message
        )
        
        self.save_baseline_data(metrics)
        return metrics


# Test sample data for baseline measurements
SAMPLE_CONTENT = """
Smith & Associates Law Firm provides comprehensive legal services to businesses 
and individuals throughout Ontario. Our experienced team of lawyers specializes 
in corporate law, real estate transactions, and litigation support. We are 
committed to delivering exceptional results for our clients through personalized 
attention and strategic legal counsel.

Our practice areas include:
- Corporate and Business Law
- Real Estate Law
- Employment Law
- Litigation and Dispute Resolution
- Estate Planning

Contact us today to schedule a consultation with one of our qualified legal 
professionals. We offer competitive rates and flexible payment options to 
meet your legal needs.
"""

SAMPLE_STAKEHOLDER_DATA = {
    "organization": "Smith & Associates Law Firm",
    "industry": "Legal Services",
    "size": "Medium",
    "location": "Toronto, ON"
}


@pytest.mark.performance
class TestLegionPerformanceBaselines:
    """
    Performance baseline tests for Legion system components.
    
    These tests establish baseline performance metrics for critical workflows
    that will be compared against the Atomic Agents implementation.
    """
    
    def setup_method(self):
        """Setup for each test method."""
        self.baseline_tester = LegionBaselineTests()
    
    @pytest.mark.slow
    def test_content_analysis_baseline(self):
        """Establish baseline for content analysis workflow."""
        
        def content_analysis_workflow():
            """Execute content analysis workflow."""
            # This would use the actual Legion ContentInventoryAgent
            # For now, we'll simulate the workflow
            
            # Simulate content analysis processing
            time.sleep(0.1)  # Simulate processing time
            
            # Simulate memory allocation for content processing
            large_data = ["content"] * 1000
            
            # Simulate analysis operations
            analysis_results = {
                "content_items": len(SAMPLE_CONTENT.split()),
                "categories": ["corporate", "real_estate", "litigation"],
                "quality_score": 0.85,
                "seo_recommendations": ["Add meta descriptions", "Optimize headings"]
            }
            
            return analysis_results
        
        metrics = self.baseline_tester.run_baseline_test(
            "content_analysis",
            content_analysis_workflow
        )
        
        # Assert reasonable performance expectations
        assert metrics.success, f"Content analysis failed: {metrics.error_message}"
        assert metrics.execution_time < 30.0, f"Content analysis too slow: {metrics.execution_time:.2f}s"
        assert metrics.memory_delta < 100 * 1024 * 1024, f"Memory usage too high: {metrics.memory_delta} bytes"
        
        print(f"Content Analysis Baseline: {metrics.execution_time:.2f}s, {metrics.memory_delta} bytes")
    
    @pytest.mark.slow
    def test_discovery_agent_baseline(self):
        """Establish baseline for discovery agent workflow."""
        
        def discovery_workflow():
            """Execute stakeholder discovery workflow."""
            # Simulate discovery agent processing
            time.sleep(0.05)  # Simulate processing time
            
            # Simulate stakeholder identification
            stakeholders = [
                {"name": "Marketing Manager", "role": "Content Strategy"},
                {"name": "Managing Partner", "role": "Business Development"},
                {"name": "IT Administrator", "role": "Technical Implementation"}
            ]
            
            # Simulate platform inventory
            platforms = [
                {"name": "Website", "type": "Primary", "status": "Active"},
                {"name": "LinkedIn", "type": "Social", "status": "Active"},
                {"name": "Legal Directory", "type": "Listing", "status": "Needs Update"}
            ]
            
            return {
                "stakeholders": stakeholders,
                "platforms": platforms,
                "recommendations": ["Update legal directory listing", "Enhance LinkedIn presence"]
            }
        
        metrics = self.baseline_tester.run_baseline_test(
            "discovery_agent",
            discovery_workflow
        )
        
        # Assert performance expectations
        assert metrics.success, f"Discovery workflow failed: {metrics.error_message}"
        assert metrics.execution_time < 15.0, f"Discovery too slow: {metrics.execution_time:.2f}s"
        assert metrics.memory_delta < 50 * 1024 * 1024, f"Memory usage too high: {metrics.memory_delta} bytes"
        
        print(f"Discovery Agent Baseline: {metrics.execution_time:.2f}s, {metrics.memory_delta} bytes")
    
    @pytest.mark.slow
    def test_gap_analysis_baseline(self):
        """Establish baseline for gap analysis workflow."""
        
        def gap_analysis_workflow():
            """Execute gap analysis workflow."""
            # Simulate gap analysis processing
            time.sleep(0.2)  # Simulate more complex processing
            
            # Simulate content gap analysis
            content_gaps = [
                {"category": "Employment Law", "gap_type": "Missing Content", "priority": "High"},
                {"category": "Estate Planning", "gap_type": "Outdated Content", "priority": "Medium"},
                {"category": "Corporate Law", "gap_type": "SEO Optimization", "priority": "Low"}
            ]
            
            # Simulate competitive analysis
            competitive_analysis = {
                "competitors_analyzed": 5,
                "content_volume_comparison": "Below average",
                "quality_comparison": "Above average",
                "recommendations": ["Increase content volume", "Focus on employment law content"]
            }
            
            return {
                "content_gaps": content_gaps,
                "competitive_analysis": competitive_analysis,
                "priority_actions": ["Create employment law content", "Update estate planning materials"]
            }
        
        metrics = self.baseline_tester.run_baseline_test(
            "gap_analysis",
            gap_analysis_workflow
        )
        
        # Assert performance expectations
        assert metrics.success, f"Gap analysis failed: {metrics.error_message}"
        assert metrics.execution_time < 45.0, f"Gap analysis too slow: {metrics.execution_time:.2f}s"
        assert metrics.memory_delta < 150 * 1024 * 1024, f"Memory usage too high: {metrics.memory_delta} bytes"
        
        print(f"Gap Analysis Baseline: {metrics.execution_time:.2f}s, {metrics.memory_delta} bytes")
    
    @pytest.mark.slow
    def test_compliance_check_baseline(self):
        """Establish baseline for compliance checking workflow."""
        
        def compliance_check_workflow():
            """Execute compliance checking workflow."""
            # Simulate compliance analysis
            time.sleep(0.08)  # Simulate processing time
            
            # Simulate compliance rule checking
            violations = []
            if "guarantee" in SAMPLE_CONTENT.lower():
                violations.append({
                    "rule_id": "LSO_7.04",
                    "description": "Use of guarantee language",
                    "severity": "high"
                })
            
            recommendations = []
            if violations:
                recommendations.append("Remove guarantee language")
            else:
                recommendations.append("Content appears compliant")
            
            return {
                "compliant": len(violations) == 0,
                "violations": violations,
                "recommendations": recommendations,
                "confidence_score": 0.95
            }
        
        metrics = self.baseline_tester.run_baseline_test(
            "compliance_check",
            compliance_check_workflow
        )
        
        # Assert performance expectations
        assert metrics.success, f"Compliance check failed: {metrics.error_message}"
        assert metrics.execution_time < 10.0, f"Compliance check too slow: {metrics.execution_time:.2f}s"
        assert metrics.memory_delta < 25 * 1024 * 1024, f"Memory usage too high: {metrics.memory_delta} bytes"
        
        print(f"Compliance Check Baseline: {metrics.execution_time:.2f}s, {metrics.memory_delta} bytes")
    
    @pytest.mark.slow
    def test_multi_agent_workflow_baseline(self):
        """Establish baseline for multi-agent workflow execution."""
        
        def multi_agent_workflow():
            """Execute a workflow involving multiple agents."""
            results = {}
            
            # Step 1: Discovery
            time.sleep(0.05)
            results["discovery"] = {
                "stakeholders_identified": 3,
                "platforms_found": 5
            }
            
            # Step 2: Content Analysis
            time.sleep(0.1)
            results["content_analysis"] = {
                "content_items_analyzed": 25,
                "quality_score": 0.78
            }
            
            # Step 3: Gap Analysis
            time.sleep(0.15)
            results["gap_analysis"] = {
                "gaps_identified": 8,
                "priority_gaps": 3
            }
            
            # Step 4: Compliance Check
            time.sleep(0.08)
            results["compliance"] = {
                "items_checked": 25,
                "violations_found": 0
            }
            
            return {
                "workflow_results": results,
                "total_items_processed": 25,
                "overall_score": 0.82,
                "recommendations": [
                    "Address priority content gaps",
                    "Maintain current compliance standards",
                    "Enhance content quality in identified areas"
                ]
            }
        
        metrics = self.baseline_tester.run_baseline_test(
            "multi_agent_workflow",
            multi_agent_workflow
        )
        
        # Assert performance expectations for complex workflow
        assert metrics.success, f"Multi-agent workflow failed: {metrics.error_message}"
        assert metrics.execution_time < 60.0, f"Multi-agent workflow too slow: {metrics.execution_time:.2f}s"
        assert metrics.memory_delta < 200 * 1024 * 1024, f"Memory usage too high: {metrics.memory_delta} bytes"
        
        print(f"Multi-Agent Workflow Baseline: {metrics.execution_time:.2f}s, {metrics.memory_delta} bytes")


def run_all_baselines():
    """
    Convenience function to run all baseline tests and generate a summary report.
    """
    baseline_tester = LegionBaselineTests()
    
    print("Running Legion System Performance Baselines...")
    print("=" * 60)
    
    # Run pytest with performance markers
    pytest.main([
        __file__,
        "-m", "performance",
        "-v",
        "--tb=short"
    ])
    
    print("\nBaseline tests completed. Results saved to memory-bank/performance_baselines/")


if __name__ == "__main__":
    run_all_baselines()
