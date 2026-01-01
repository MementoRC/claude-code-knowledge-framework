"""
Test Pattern Migrator functionality
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch


from uckn.core.molecules.pattern_migrator import MigrationReport, PatternMigrator


class TestMigrationReport:
    """Test MigrationReport functionality"""

    def test_migration_report_initialization(self):
        """Test MigrationReport initializes correctly"""
        report = MigrationReport()
        assert len(report.migrated) == 0
        assert len(report.validated) == 0
        assert len(report.failed) == 0
        assert len(report.skipped) == 0
        assert len(report.errors) == 0
        assert report.start_time is not None
        assert report.end_time is None

    def test_migration_report_add_methods(self):
        """Test adding items to MigrationReport"""
        report = MigrationReport()

        report.add_migrated("/test/file.json", "code_patterns", "pattern-123")
        assert len(report.migrated) == 1
        assert report.migrated[0]["file"] == "/test/file.json"
        assert report.migrated[0]["type"] == "code_patterns"
        assert report.migrated[0]["id"] == "pattern-123"

        report.add_validated("/test/file2.json", "error_solutions", "solution-456")
        assert len(report.validated) == 1

        report.add_failed("/test/file3.json", "Invalid JSON")
        assert len(report.failed) == 1

        report.add_skipped("/test/file4.json", "Empty file")
        assert len(report.skipped) == 1

        report.add_error("/test/file5.json", "Exception occurred", "traceback")
        assert len(report.errors) == 1


class TestPatternMigrator:
    """Test PatternMigrator functionality"""

    def test_migrator_initialization_report_only(self):
        """Test PatternMigrator initializes correctly in report-only mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            migrator = PatternMigrator(
                source_dir=temp_dir, target_dir=None, report_only=True
            )
            assert migrator.source_dir == Path(temp_dir)
            assert migrator.report_only is True
            assert migrator.chroma_connector is None
            assert migrator.semantic_search is None

    @patch("uckn.core.molecules.pattern_migrator.ChromaDBConnector")
    @patch("uckn.core.molecules.pattern_migrator.SemanticSearch")
    @patch("uckn.core.molecules.pattern_migrator.PatternManager")
    @patch("uckn.core.molecules.pattern_migrator.ErrorSolutionManager")
    def test_migrator_initialization_full_mode(
        self,
        mock_error_manager,
        mock_pattern_manager,
        mock_semantic_search,
        mock_chroma,
    ):
        """Test PatternMigrator initializes correctly in full mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            migrator = PatternMigrator(
                source_dir=temp_dir, target_dir=temp_dir, report_only=False
            )
            assert migrator.source_dir == Path(temp_dir)
            assert migrator.report_only is False
            assert mock_chroma.called
            assert mock_semantic_search.called
            assert mock_pattern_manager.called
            assert mock_error_manager.called

    def test_scan_json_files(self):
        """Test scanning for JSON files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_dir = Path(temp_dir)
            (test_dir / "pattern1.json").write_text('{"test": true}')
            (test_dir / "pattern2.json").write_text('{"test": true}')
            (test_dir / "not_json.txt").write_text("not json")

            # Create subdirectory with JSON
            subdir = test_dir / "subdir"
            subdir.mkdir()
            (subdir / "pattern3.json").write_text('{"test": true}')

            migrator = PatternMigrator(source_dir=temp_dir, report_only=True)
            files = migrator._scan_json_files(test_dir)

            assert len(files) == 3
            json_files = [f.name for f in files]
            assert "pattern1.json" in json_files
            assert "pattern2.json" in json_files
            assert "pattern3.json" in json_files
            assert "not_json.txt" not in json_files

    def test_load_json_valid(self):
        """Test loading valid JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_data = {"pattern_id": "test-123", "document": "test content"}
            test_file.write_text(json.dumps(test_data))

            migrator = PatternMigrator(source_dir=temp_dir, report_only=True)
            data = migrator._load_json(test_file)

            assert data == test_data

    def test_load_json_invalid(self):
        """Test loading invalid JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.json"
            test_file.write_text("invalid json content {")

            migrator = PatternMigrator(source_dir=temp_dir, report_only=True)
            data = migrator._load_json(test_file)

            assert data is None

    def test_detect_type_legacy_sessions(self):
        """Test detecting legacy session format"""
        migrator = PatternMigrator(source_dir=".", report_only=True)

        legacy_data = {
            "sessions": [
                {
                    "session_id": "test-123",
                    "document": "test content",
                    "metadata": {"pattern_id": "pattern-123"},
                }
            ]
        }

        obj_type, obj_list = migrator._detect_type_and_extract(
            legacy_data, Path("test.json")
        )

        assert obj_type == "code_patterns"
        assert len(obj_list) == 1
        assert obj_list[0]["pattern_id"] == "pattern-123"
        assert obj_list[0]["document"] == "test content"

    def test_detect_type_modern_pattern(self):
        """Test detecting modern pattern format"""
        migrator = PatternMigrator(source_dir=".", report_only=True)

        pattern_data = {
            "pattern_id": "test-123",
            "document": "test content",
            "metadata": {"technology_stack": ["python"], "pattern_type": "setup"},
        }

        obj_type, obj_list = migrator._detect_type_and_extract(
            pattern_data, Path("test.json")
        )

        assert obj_type == "code_patterns"
        assert len(obj_list) == 1
        assert obj_list[0]["pattern_id"] == "test-123"

    def test_detect_type_error_solution(self):
        """Test detecting error solution format"""
        migrator = PatternMigrator(source_dir=".", report_only=True)

        error_data = {
            "solution_id": "error-123",
            "document": "error solution",
            "metadata": {"error_category": "import_error"},
        }

        obj_type, obj_list = migrator._detect_type_and_extract(
            error_data, Path("test.json")
        )

        assert obj_type == "error_solutions"
        assert len(obj_list) == 1
        assert obj_list[0]["solution_id"] == "error-123"

    def test_validate_object_code_pattern_valid(self):
        """Test validating valid code pattern object"""
        migrator = PatternMigrator(source_dir=".", report_only=True)

        pattern = {
            "pattern_id": "test-123",
            "document": "test content",
            "metadata": {
                "pattern_id": "test-123",
                "technology_stack": ["python"],
                "pattern_type": "setup",
                "success_rate": 0.9,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        }

        valid, reason = migrator._validate_object(pattern, "code_patterns")
        assert valid is True
        assert reason == ""

    def test_validate_object_code_pattern_missing_document(self):
        """Test validating code pattern with missing document"""
        migrator = PatternMigrator(source_dir=".", report_only=True)

        pattern = {"pattern_id": "test-123", "metadata": {}}

        valid, reason = migrator._validate_object(pattern, "code_patterns")
        assert valid is False
        assert "Missing 'document'" in reason

    def test_report_only_mode(self):
        """Test report-only mode functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test JSON file
            test_file = Path(temp_dir) / "pattern.json"
            test_data = {
                "pattern_id": "test-123",
                "document": "test content",
                "metadata": {"technology_stack": ["python"], "pattern_type": "setup"},
            }
            test_file.write_text(json.dumps(test_data))

            migrator = PatternMigrator(source_dir=temp_dir, report_only=True)
            report = migrator.report_only_mode()

            assert len(report.validated) == 1
            assert report.validated[0]["type"] == "code_patterns"
            assert report.validated[0]["id"] == "test-123"
            assert len(report.migrated) == 0
            assert len(report.failed) == 0
