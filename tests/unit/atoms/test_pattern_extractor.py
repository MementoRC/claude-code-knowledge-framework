"""
Tests for PatternExtractor atom
"""

import unittest
from unittest.mock import MagicMock
from pathlib import Path

from src.uckn.core.atoms.pattern_extractor import PatternExtractor
from src.uckn.core.atoms.tech_stack_detector import TechStackDetector


class TestPatternExtractor(unittest.TestCase):
    """Test cases for PatternExtractor"""

    def setUp(self):
        self.mock_tech_detector = MagicMock(spec=TechStackDetector)
        self.mock_tech_detector.analyze_project.return_value = {
            "languages": ["Python"],
            "package_managers": ["pip"],
            "frameworks": [],
            "testing": ["pytest"],
            "ci_cd": ["GitHub Actions"]
        }
        self.extractor = PatternExtractor(self.mock_tech_detector)

    def test_initialization(self):
        """Test PatternExtractor initialization"""
        self.assertIsInstance(self.extractor, PatternExtractor)
        self.assertEqual(self.extractor.tech_stack_detector, self.mock_tech_detector)

    def test_extract_from_git_changes_empty_diff(self):
        """Test extract_from_git_changes with empty diff"""
        result = self.extractor.extract_from_git_changes("", "/test/repo")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_extract_from_ci_changes_file_not_found(self):
        """Test extract_from_ci_changes with non-existent file"""
        result = self.extractor.extract_from_ci_changes("/nonexistent/file.yml", "/test/repo")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_extract_from_config_changes_file_not_found(self):
        """Test extract_from_config_changes with non-existent file"""
        result = self.extractor.extract_from_config_changes("/nonexistent/config.json", "/test/repo")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_extract_from_documentation_file_not_found(self):
        """Test extract_from_documentation with non-existent file"""
        result = self.extractor.extract_from_documentation("/nonexistent/readme.md", "/test/repo")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_generate_pattern_metadata_basic(self):
        """Test generate_pattern_metadata with basic string content"""
        pattern_content = "fix: resolve issue with authentication"
        metadata = self.extractor.generate_pattern_metadata(pattern_content, "/test/repo")
        
        self.assertIsInstance(metadata, dict)
        self.assertIn("pattern_type", metadata)
        self.assertIn("tech_stack", metadata)
        self.assertIn("timestamp", metadata)

    def test_calculate_success_metrics_basic(self):
        """Test calculate_success_metrics with basic data"""
        pattern_data = {
            "content": "some pattern content",
            "metadata": {
                "id": "test-pattern-1",
                "success_metrics": {
                    "success_rate": 0.0,
                    "usage_count": 0,
                    "last_calculated": None
                }
            }
        }
        usage_data = {
            "successful_applications": 2,
            "total_applications": 3
        }
        result = self.extractor.calculate_success_metrics(pattern_data, usage_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("metadata", result)
        self.assertIn("success_metrics", result["metadata"])
        self.assertAlmostEqual(result["metadata"]["success_metrics"]["success_rate"], 2/3, places=2)


if __name__ == "__main__":
    unittest.main()