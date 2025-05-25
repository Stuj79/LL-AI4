import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import datetime

# Add parent directory to path to import the new modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# These will be imported once implemented
from tools.content_discovery import scan_website_content, extract_metadata, detect_content_language, classify_content_format
from tools.content_analysis import analyze_content_quality, check_content_freshness, analyze_topic_distribution, identify_compliance_issues

class TestContentDiscoveryTools(unittest.TestCase):
    """Tests for the content discovery tools."""
    
    def test_scan_website_content(self):
        # Mock URL to scan
        test_url = "https://example-law-firm.com"
        
        # Since we can't actually scan a website in a test, we'll mock the result
        with patch('tools.content_discovery.requests.get') as mock_get:
            # Set up mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html>
            <body>
                <article>
                    <h1>Corporate Law Services</h1>
                    <p>Our expertise in corporate law...</p>
                </article>
                <article>
                    <h1>Family Law Practice</h1>
                    <p>We handle family law matters...</p>
                </article>
            </body>
            </html>
            """
            mock_get.return_value = mock_response
            
            # Call the function
            result = scan_website_content(test_url, depth=1)
            
            # Assert the results
            self.assertIsInstance(result, list)
            self.assertGreaterEqual(len(result), 2)  # Should find at least 2 content pieces
            self.assertIn("url", result[0])
            self.assertIn("title", result[0])
    
    def test_extract_metadata(self):
        # Mock URL to extract metadata from
        test_url = "https://example-law-firm.com/corporate-law"
        
        # Mock the HTTP response
        with patch('tools.content_discovery.requests.get') as mock_get:
            # Set up mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html>
            <head>
                <title>Corporate Law Services | Example Law Firm</title>
                <meta name="description" content="Expert corporate law services for businesses in Canada">
                <meta name="keywords" content="corporate law, business law, Canada, legal services">
                <meta name="author" content="John Smith">
                <meta property="article:published_time" content="2023-01-15">
            </head>
            <body>
                <article>
                    <h1>Corporate Law Services</h1>
                    <p>Our expertise in corporate law...</p>
                </article>
            </body>
            </html>
            """
            mock_get.return_value = mock_response
            
            # Call the function
            result = extract_metadata(test_url)
            
            # Assert the results
            self.assertIsInstance(result, dict)
            self.assertIn("title", result)
            self.assertIn("description", result)
            self.assertIn("author", result)
            self.assertIn("publish_date", result)
            self.assertEqual(result["title"], "Corporate Law Services | Example Law Firm")
    
    def test_detect_content_language(self):
        # Test English content
        english_text = "This is a sample text about corporate law in Canada. It discusses various legal aspects of business operations."
        self.assertEqual(detect_content_language(english_text), "English")
        
        # Test French content
        french_text = "Ceci est un exemple de texte sur le droit des sociétés au Canada. Il traite de divers aspects juridiques des opérations commerciales."
        self.assertEqual(detect_content_language(french_text), "French")
        
        # Test bilingual content
        bilingual_text = "This section outlines corporate regulations. Cette section décrit les règlements corporatifs."
        result = detect_content_language(bilingual_text)
        self.assertTrue(result in ["English", "French", "Bilingual"])
    
    def test_classify_content_format(self):
        # Test blog post URL and content
        blog_url = "https://example-law-firm.com/blog/corporate-governance"
        blog_content = """
        <article class="blog-post">
            <h1>Corporate Governance Best Practices</h1>
            <div class="post-meta">Posted on January 15, 2023 by John Smith</div>
            <div class="post-content">
                <p>In this blog post, we discuss corporate governance best practices...</p>
                <p>Many companies struggle with implementing effective governance...</p>
            </div>
        </article>
        """
        self.assertEqual(classify_content_format(blog_url, blog_content), "Blog post")
        
        # Test practice area page URL and content
        practice_url = "https://example-law-firm.com/practice-areas/family-law"
        practice_content = """
        <div class="practice-area">
            <h1>Family Law</h1>
            <div class="service-description">
                <p>Our family law services include divorce, child custody, and support matters.</p>
                <ul>
                    <li>Divorce proceedings</li>
                    <li>Child custody agreements</li>
                </ul>
            </div>
        </div>
        """
        self.assertEqual(classify_content_format(practice_url, practice_content), "Practice page")
        
        # Test video page URL and content
        video_url = "https://example-law-firm.com/videos/real-estate-law-explained"
        video_content = """
        <div class="video-content">
            <h1>Real Estate Law Explained</h1>
            <div class="video-player">
                <iframe src="https://www.youtube.com/embed/12345"></iframe>
            </div>
            <div class="video-description">
                <p>This video explains the basics of real estate law in Canada.</p>
            </div>
        </div>
        """
        self.assertEqual(classify_content_format(video_url, video_content), "Video")


class TestContentAnalysisTools(unittest.TestCase):
    """Tests for the content analysis tools."""
    
    def test_analyze_content_quality(self):
        # High quality content
        high_quality = """
        Corporate Governance in Canada: A Comprehensive Guide
        
        This detailed guide provides businesses with critical insights into corporate governance requirements
        under Canadian law. We examine board composition requirements, shareholder rights, disclosure obligations,
        and compliance mechanisms that every corporation must implement.
        
        Our analysis incorporates recent regulatory changes and case law that impacts how corporations should
        structure their governance frameworks. Examples and practical guidance are provided throughout.
        """
        
        high_result = analyze_content_quality(high_quality)
        
        # High quality content should have a score of at least 4.0
        # If this fails, it may be due to the weighting algorithm in analyze_content_quality
        self.assertTrue(high_result["quality_score"] >= 4.0, 
                        f"Expected high quality score >= 4.0, got {high_result['quality_score']}")
        
        # Low quality content
        low_quality = """
        Corp governance info
        
        Boards need to meet. Shareholders have rights. Companies must follow rules.
        """
        
        low_result = analyze_content_quality(low_quality)
        # Low quality content should have a score below 3.0
        self.assertTrue(low_result["quality_score"] < 3.0,
                       f"Expected low quality score < 3.0, got {low_result['quality_score']}")
    
    def test_check_content_freshness(self):
        # Current content
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(check_content_freshness(current_date)["status"], "Up-to-date")
        
        # Recent content (3 months old)
        three_months_ago = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        self.assertEqual(check_content_freshness(three_months_ago)["status"], "Up-to-date")
        
        # Older content (1 year old)
        one_year_ago = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        # If this test fails, check the age threshold in check_content_freshness
        # Content exactly 365 days old should be classified as "Needs reviewing"
        one_year_result = check_content_freshness(one_year_ago)
        self.assertEqual(one_year_result["status"], "Needs reviewing",
                        f"Expected status for 1-year old content to be 'Needs reviewing', got '{one_year_result['status']}'")
        
        # Very old content (3 years old)
        three_years_ago = (datetime.datetime.now() - datetime.timedelta(days=3*365)).strftime("%Y-%m-%d")
        self.assertEqual(check_content_freshness(three_years_ago)["status"], "Outdated")
    
    def test_analyze_topic_distribution(self):
        # Sample content inventory
        inventory = [
            {
                "title": "Corporate Governance Guide",
                "practice_area": ["Corporate Law"],
                "topics": ["corporate governance", "board responsibilities", "shareholder meetings"]
            },
            {
                "title": "Shareholder Rights Overview",
                "practice_area": ["Corporate Law"],
                "topics": ["shareholder rights", "voting", "dividends", "corporate governance"]
            },
            {
                "title": "Family Law Services",
                "practice_area": ["Family Law"],
                "topics": ["divorce", "child custody", "support payments"]
            },
            {
                "title": "Real Estate Transactions",
                "practice_area": ["Real Estate"],
                "topics": ["property purchases", "title searches", "closing procedures"]
            }
        ]
        
        result = analyze_topic_distribution(inventory)
        
        # Assert the results
        self.assertIsInstance(result, dict)
        self.assertIn("practice_area_distribution", result)
        self.assertIn("topic_frequency", result)
        self.assertEqual(result["practice_area_distribution"]["Corporate Law"], 2)
        self.assertEqual(result["topic_frequency"]["corporate governance"], 2)
    
    def test_identify_compliance_issues(self):
        # Sample content with compliance issues
        content_with_issues = """
        Our lawyers are the best specialists in corporate law in Ontario.
        We guarantee successful outcomes in all litigation cases we handle.
        Our 100% success rate proves we are the most expert lawyers in Canada.
        """
        
        # Sample rules
        rules = {
            "prohibited_terms": ["specialist", "expert", "guarantee", "best", "most", "100%"],
            "restricted_claims": ["guarantee successful outcomes", "success rate"]
        }
        
        result = identify_compliance_issues(content_with_issues, rules)
        
        # Assert the results
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)  # Should find at least 3 issues
        self.assertIn("severity", result[0])
        self.assertIn("issue", result[0])
        self.assertIn("suggestion", result[0])


if __name__ == "__main__":
    unittest.main()
