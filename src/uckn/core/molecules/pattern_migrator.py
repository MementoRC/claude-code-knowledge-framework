"""
UCKN Pattern Migrator Molecule
Handles migration, validation, and reporting for legacy and modern pattern/error solution files.
"""

import json
import logging
import os
import traceback
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any, Optional

from ...storage.chromadb_connector import ChromaDBConnector
from ...storage.unified_database import UnifiedDatabase
from ..atoms.semantic_search import SemanticSearch
from .error_solution_manager import ErrorSolutionManager
from .pattern_manager import PatternManager


class MigrationReport:
    """
    Collects and prints results of migration/validation/reporting.
    """

    def __init__(self):
        self.migrated: list[dict[str, Any]] = []
        self.validated: list[dict[str, Any]] = []
        self.failed: list[dict[str, Any]] = []
        self.skipped: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_migrated(self, file_path, obj_type, obj_id):
        self.migrated.append({"file": str(file_path), "type": obj_type, "id": obj_id})

    def add_validated(self, file_path, obj_type, obj_id):
        self.validated.append({"file": str(file_path), "type": obj_type, "id": obj_id})

    def add_failed(self, file_path, reason, exc=None):
        self.failed.append({"file": str(file_path), "reason": reason, "exception": exc})

    def add_skipped(self, file_path, reason):
        self.skipped.append({"file": str(file_path), "reason": reason})

    def add_error(self, file_path, reason, exc=None):
        self.errors.append({"file": str(file_path), "reason": reason, "exception": exc})

    def finish(self):
        self.end_time = datetime.now()

    def print_report(self, console=None):
        self.finish()
        duration = (
            (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        )
        summary = (
            f"[Migration Report]\n"
            f"Start: {self.start_time}\n"
            f"End:   {self.end_time}\n"
            f"Duration: {duration:.2f}s\n"
            f"Migrated: {len(self.migrated)}\n"
            f"Validated: {len(self.validated)}\n"
            f"Skipped: {len(self.skipped)}\n"
            f"Failed: {len(self.failed)}\n"
            f"Errors: {len(self.errors)}\n"
        )
        if console:
            console.print(summary)
        else:
            print(summary)
        if self.migrated:
            (console.print if console else print)("\n[Migrated]")
            for m in self.migrated:
                (console.print if console else print)(
                    f"  {m['file']} ({m['type']}:{m['id']})"
                )
        if self.validated:
            (console.print if console else print)("\n[Validated]")
            for v in self.validated:
                (console.print if console else print)(
                    f"  {v['file']} ({v['type']}:{v['id']})"
                )
        if self.skipped:
            (console.print if console else print)("\n[Skipped]")
            for s in self.skipped:
                (console.print if console else print)(f"  {s['file']}: {s['reason']}")
        if self.failed:
            (console.print if console else print)("\n[Failed]")
            for f in self.failed:
                (console.print if console else print)(f"  {f['file']}: {f['reason']}")
                if f.get("exception"):
                    (console.print if console else print)(
                        f"    Exception: {f['exception']}"
                    )
        if self.errors:
            (console.print if console else print)("\n[Errors]")
            for e in self.errors:
                (console.print if console else print)(f"  {e['file']}: {e['reason']}")
                if e.get("exception"):
                    (console.print if console else print)(
                        f"    Exception: {e['exception']}"
                    )


class PatternMigrator:
    """
    Migrates, validates, and reports on legacy and modern pattern/error solution files.
    """

    def __init__(
        self,
        source_dir: str | Path,
        target_dir: str | Optional[Path] = None,
        dry_run: bool = False,
        validate_only: bool = False,
        report_only: bool = False,
        logger: Optional[Logger] = None,
        console=None,
    ):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir) if target_dir else None
        self.dry_run = dry_run
        self.validate_only = validate_only
        self.report_only = report_only
        self.logger = logger or logging.getLogger(__name__)
        self.console = console

        # Setup database and semantic search only if not report_only
        self.chroma_connector = None
        self.unified_db = None
        self.semantic_search = None
        self.pattern_manager = None
        self.error_solution_manager = None

        if not self.report_only:
            self.chroma_connector = ChromaDBConnector(
                db_path=str(self.target_dir or ".uckn/knowledge/chroma_db")
            )
            self.unified_db = UnifiedDatabase(
                pg_db_url="postgresql://user:pass@localhost/test_db",
                chroma_db_path=str(self.target_dir or ".uckn/knowledge/chroma_db")
            )
            self.semantic_search = SemanticSearch()
            self.pattern_manager = PatternManager(
                unified_db=self.unified_db,
                semantic_search=self.semantic_search,
            )
            self.error_solution_manager = ErrorSolutionManager(
                chroma_connector=self.chroma_connector,
                semantic_search=self.semantic_search,
            )

    def migrate(self) -> MigrationReport:
        """
        Full migration: scan, validate, embed, and store patterns and error solutions.
        """
        report = MigrationReport()
        files = self._scan_json_files(self.source_dir)
        for file_path in files:
            try:
                data = self._load_json(file_path)
                if not data:
                    report.add_failed(file_path, "Empty or invalid JSON")
                    continue

                # Determine type: pattern or error solution
                obj_type, obj_list = self._detect_type_and_extract(data, file_path)
                if not obj_type or not obj_list:
                    report.add_skipped(file_path, "Unrecognized or empty file format")
                    continue

                for obj in obj_list:
                    # Validate structure
                    valid, reason = self._validate_object(obj, obj_type)
                    if not valid:
                        report.add_failed(file_path, f"Validation failed: {reason}")
                        continue

                    # Generate embedding
                    if (
                        not self.semantic_search
                        or not self.semantic_search.is_available()
                    ):
                        report.add_failed(file_path, "Semantic search unavailable")
                        continue
                    embedding = self.semantic_search.encode(obj.get("document", ""))
                    if embedding is None:
                        report.add_failed(file_path, "Embedding generation failed")
                        continue

                    # Store in ChromaDB (unless dry_run)
                    if not self.dry_run:
                        if obj_type == "code_patterns":
                            pattern_id = self.pattern_manager.add_pattern(obj)
                            if pattern_id:
                                report.add_migrated(file_path, obj_type, pattern_id)
                            else:
                                report.add_failed(
                                    file_path, "Failed to add pattern to ChromaDB"
                                )
                        elif obj_type == "error_solutions":
                            solution_id = (
                                self.error_solution_manager.add_error_solution(obj)
                            )
                            if solution_id:
                                report.add_migrated(file_path, obj_type, solution_id)
                            else:
                                report.add_failed(
                                    file_path,
                                    "Failed to add error solution to ChromaDB",
                                )
                    else:
                        # Dry run: just report as migrated
                        obj_id = (
                            obj.get("pattern_id") or obj.get("solution_id") or "unknown"
                        )
                        report.add_migrated(file_path, obj_type, obj_id)
            except Exception as e:
                tb = traceback.format_exc()
                report.add_error(file_path, f"Exception during migration: {e}", exc=tb)
                if self.logger:
                    self.logger.error(f"Migration error for {file_path}: {e}\n{tb}")
        report.finish()
        return report

    def validate(self) -> MigrationReport:
        """
        Validation only: scan and validate files, but do not migrate or embed.
        """
        report = MigrationReport()
        files = self._scan_json_files(self.source_dir)
        for file_path in files:
            try:
                data = self._load_json(file_path)
                if not data:
                    report.add_failed(file_path, "Empty or invalid JSON")
                    continue

                obj_type, obj_list = self._detect_type_and_extract(data, file_path)
                if not obj_type or not obj_list:
                    report.add_skipped(file_path, "Unrecognized or empty file format")
                    continue

                for obj in obj_list:
                    valid, reason = self._validate_object(obj, obj_type)
                    if valid:
                        obj_id = (
                            obj.get("pattern_id") or obj.get("solution_id") or "unknown"
                        )
                        report.add_validated(file_path, obj_type, obj_id)
                    else:
                        report.add_failed(file_path, f"Validation failed: {reason}")
            except Exception as e:
                tb = traceback.format_exc()
                report.add_error(file_path, f"Exception during validation: {e}", exc=tb)
                if self.logger:
                    self.logger.error(f"Validation error for {file_path}: {e}\n{tb}")
        report.finish()
        return report

    def report_only_mode(self) -> MigrationReport:
        """
        Scan and report on files, but do not validate or migrate.
        """
        report = MigrationReport()
        files = self._scan_json_files(self.source_dir)
        for file_path in files:
            try:
                data = self._load_json(file_path)
                if not data:
                    report.add_skipped(file_path, "Empty or invalid JSON")
                    continue
                obj_type, obj_list = self._detect_type_and_extract(data, file_path)
                if not obj_type or not obj_list:
                    report.add_skipped(file_path, "Unrecognized or empty file format")
                    continue
                for obj in obj_list:
                    obj_id = (
                        obj.get("pattern_id") or obj.get("solution_id") or "unknown"
                    )
                    report.add_validated(file_path, obj_type, obj_id)
            except Exception as e:
                tb = traceback.format_exc()
                report.add_error(
                    file_path, f"Exception during report scan: {e}", exc=tb
                )
                if self.logger:
                    self.logger.error(f"Report scan error for {file_path}: {e}\n{tb}")
        report.finish()
        return report

    def _scan_json_files(self, directory: Path) -> list[Path]:
        """
        Recursively scan for .json files in the directory.
        """
        files = []
        for root, _, filenames in os.walk(directory):
            for fname in filenames:
                if fname.lower().endswith(".json"):
                    files.append(Path(root) / fname)
        return files

    def _load_json(self, file_path: Path) -> Optional[Any]:
        """
        Load JSON file, return None if invalid.
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to load JSON from {file_path}: {e}")
            return None

    def _detect_type_and_extract(
        self, data: Any, file_path: Path
    ) -> (Optional[str], list[dict[str, Any]] | None):
        """
        Detect if the file contains code_patterns or error_solutions, and extract as a list.
        Supports legacy and modern formats.
        """
        # Legacy Claude session format: {"sessions": [...]}
        if isinstance(data, dict) and "sessions" in data:
            # Each session is a pattern
            patterns = []
            for session in data["sessions"]:
                doc = (
                    session.get("document")
                    or session.get("text")
                    or session.get("content")
                )
                metadata = session.get("metadata", {})
                # Try to extract pattern_id or generate one
                pattern_id = (
                    metadata.get("pattern_id")
                    or session.get("id")
                    or session.get("session_id")
                )
                if not pattern_id:
                    pattern_id = f"legacy-{os.path.basename(file_path)}-{len(patterns)}"
                # Compose pattern object
                pattern_obj = {
                    "pattern_id": pattern_id,
                    "document": doc,
                    "metadata": metadata,
                }
                patterns.append(pattern_obj)
            return "code_patterns", patterns if patterns else None

        # Modern pattern file: either a dict or a list of dicts
        if isinstance(data, dict):
            # Single pattern or error solution
            if "pattern_id" in data or "technology_stack" in data:
                return "code_patterns", [data]
            if "solution_id" in data or "error_category" in data:
                return "error_solutions", [data]
            # Maybe a dict with a list under a key
            if "patterns" in data and isinstance(data["patterns"], list):
                return "code_patterns", data["patterns"]
            if "error_solutions" in data and isinstance(data["error_solutions"], list):
                return "error_solutions", data["error_solutions"]
        elif isinstance(data, list):
            # List of patterns or error solutions
            if data and isinstance(data[0], dict):
                if "pattern_id" in data[0] or "technology_stack" in data[0]:
                    return "code_patterns", data
                if "solution_id" in data[0] or "error_category" in data[0]:
                    return "error_solutions", data
        return None, None

    def _validate_object(self, obj: dict[str, Any], obj_type: str) -> (bool, str):
        """
        Validate object structure and required metadata.
        """
        if obj_type == "code_patterns":
            # Required: document, metadata, pattern_id, technology_stack, pattern_type, success_rate, created_at, updated_at
            if not obj.get("document"):
                return False, "Missing 'document'"
            metadata = obj.get("metadata", {})
            required = [
                "pattern_id",
                "technology_stack",
                "pattern_type",
                "success_rate",
                "created_at",
                "updated_at",
            ]
            for key in required:
                if key not in metadata and key != "pattern_id":
                    return False, f"Missing metadata key '{key}'"
            # pattern_id can be at top level or in metadata
            if not (obj.get("pattern_id") or metadata.get("pattern_id")):
                return False, "Missing 'pattern_id'"
            return True, ""
        elif obj_type == "error_solutions":
            # Required: document, metadata, solution_id, error_category, resolution_steps, avg_resolution_time, created_at, updated_at
            if not obj.get("document"):
                return False, "Missing 'document'"
            metadata = obj.get("metadata", {})
            required = [
                "solution_id",
                "error_category",
                "resolution_steps",
                "avg_resolution_time",
                "created_at",
                "updated_at",
            ]
            for key in required:
                if key not in metadata and key != "solution_id":
                    return False, f"Missing metadata key '{key}'"
            if not (obj.get("solution_id") or metadata.get("solution_id")):
                return False, "Missing 'solution_id'"
            return True, ""
        else:
            return False, f"Unknown object type '{obj_type}'"
