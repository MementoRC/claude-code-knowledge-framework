"""
UCKN Pattern Extractor Atom
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Assuming TechStackDetector is in the same 'atoms' directory or accessible via relative import
from src.uckn.core.atoms.tech_stack_detector import TechStackDetector

logger = logging.getLogger(__name__)


class PatternExtractor:
    """
    Extracts knowledge patterns from various sources within a project,
    such as Git changes, CI/CD configurations, general configuration files,
    and documentation.
    """

    def __init__(self, tech_stack_detector: TechStackDetector):
        """
        Initializes the PatternExtractor with a TechStackDetector instance.

        Args:
            tech_stack_detector: An instance of TechStackDetector to analyze
                                 the technology stack of projects.
        """
        if not isinstance(tech_stack_detector, TechStackDetector):
            raise TypeError(
                "tech_stack_detector must be an instance of TechStackDetector"
            )
        self.tech_stack_detector = tech_stack_detector
        logger.info("PatternExtractor initialized with TechStackDetector.")

    def _read_file_content(self, file_path: str) -> str | None:
        """Helper to safely read file content."""
        try:
            path = Path(file_path)
            if not path.is_file():
                logger.warning(f"File not found: {file_path}")
                return None
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

    def generate_pattern_metadata(
        self,
        pattern_content: str,
        project_path: str,
        source_file: str | None = None,
        pattern_type: str = "unknown",
    ) -> dict[str, Any]:
        """
        Generates metadata for an extracted pattern, including technology stack.

        Args:
            pattern_content: The actual content of the extracted pattern (e.g., code snippet, config).
            project_path: The root path of the project where the pattern was found.
            source_file: The specific file path from which the pattern was extracted (optional).
            pattern_type: The type of pattern (e.g., "git_change", "ci_config", "documentation").

        Returns:
            A dictionary containing the pattern's metadata.
        """
        metadata = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "source_file": source_file,
            "pattern_type": pattern_type,
            "content_hash": hash(
                pattern_content
            ),  # Simple hash for content identification
            "tech_stack": {},
            "success_metrics": {
                "success_rate": 0.0,
                "usage_count": 0,
                "last_calculated": None,
            },
        }
        try:
            # Analyze the project's tech stack to associate with the pattern
            project_stack = self.tech_stack_detector.analyze_project(project_path)
            metadata["tech_stack"] = project_stack
        except Exception as e:
            logger.error(f"Error analyzing tech stack for project {project_path}: {e}")
            metadata["tech_stack"] = {"error": str(e), "confidence": None}

        logger.debug(
            f"Generated metadata for pattern (type: {pattern_type}, id: {metadata['id']})"
        )
        return metadata

    def extract_from_git_changes(
        self, diff_content: str, project_path: str
    ) -> list[dict[str, Any]]:
        """
        Extracts patterns from Git commit diff content.
        This is a simplified parser focusing on added lines.

        Args:
            diff_content: The raw string content of a Git diff.
            project_path: The root path of the project.

        Returns:
            A list of dictionaries, each representing an extracted pattern.
        """
        patterns: list[dict[str, Any]] = []
        current_file = None
        current_block: list[str] = []

        try:
            for line in diff_content.splitlines():
                if line.startswith("--- a/"):
                    current_file = line[6:].strip()
                elif line.startswith("+++ b/"):
                    # This is the new file path, use it for context
                    current_file = line[6:].strip()
                elif line.startswith("+") and not line.startswith("+++"):
                    # Consider added lines as potential pattern content
                    current_block.append(line[1:])  # Remove '+'
                elif current_block and not line.startswith(
                    ("+", "-", " ", "diff", "index", "---", "+++")
                ):
                    # If a block was being built and we hit a non-diff line, finalize the block
                    pattern_content = "\n".join(current_block).strip()
                    if pattern_content:
                        metadata = self.generate_pattern_metadata(
                            pattern_content,
                            project_path,
                            source_file=current_file,
                            pattern_type="git_change",
                        )
                        patterns.append(
                            {"content": pattern_content, "metadata": metadata}
                        )
                    current_block = []

            # Add any remaining block at the end of the diff
            if current_block:
                pattern_content = "\n".join(current_block).strip()
                if pattern_content:
                    metadata = self.generate_pattern_metadata(
                        pattern_content,
                        project_path,
                        source_file=current_file,
                        pattern_type="git_change",
                    )
                    patterns.append({"content": pattern_content, "metadata": metadata})

            logger.info(f"Extracted {len(patterns)} patterns from Git changes.")
        except Exception as e:
            logger.error(f"Error extracting patterns from Git changes: {e}")
        return patterns

    def extract_from_ci_changes(
        self, ci_file_path: str, project_path: str
    ) -> list[dict[str, Any]]:
        """
        Extracts patterns from CI/CD workflow configuration files (e.g., YAML).
        This is a basic implementation that extracts the entire file content as a pattern.
        More advanced parsing would identify specific jobs, steps, or commands.

        Args:
            ci_file_path: The path to the CI/CD configuration file.
            project_path: The root path of the project.

        Returns:
            A list of dictionaries, each representing an extracted pattern.
        """
        patterns: list[dict[str, Any]] = []
        content = self._read_file_content(ci_file_path)
        if content:
            try:
                # For simplicity, treat the entire file as one pattern.
                # In a real scenario, you might parse YAML to extract individual jobs/steps.
                metadata = self.generate_pattern_metadata(
                    content,
                    project_path,
                    source_file=ci_file_path,
                    pattern_type="ci_config",
                )
                patterns.append({"content": content, "metadata": metadata})
                logger.info(f"Extracted 1 pattern from CI/CD file: {ci_file_path}")
            except Exception as e:
                logger.error(f"Error processing CI/CD file {ci_file_path}: {e}")
        return patterns

    def extract_from_config_changes(
        self, config_file_path: str, project_path: str
    ) -> list[dict[str, Any]]:
        """
        Extracts patterns from general configuration files (e.g., .ini, .json, .toml).
        Similar to CI/CD, this extracts the entire file content as a pattern.

        Args:
            config_file_path: The path to the configuration file.
            project_path: The root path of the project.

        Returns:
            A list of dictionaries, each representing an extracted pattern.
        """
        patterns: list[dict[str, Any]] = []
        content = self._read_file_content(config_file_path)
        if content:
            try:
                metadata = self.generate_pattern_metadata(
                    content,
                    project_path,
                    source_file=config_file_path,
                    pattern_type="config_file",
                )
                patterns.append({"content": content, "metadata": metadata})
                logger.info(f"Extracted 1 pattern from config file: {config_file_path}")
            except Exception as e:
                logger.error(f"Error processing config file {config_file_path}: {e}")
        return patterns

    def extract_from_documentation(
        self, doc_file_path: str, project_path: str
    ) -> list[dict[str, Any]]:
        """
        Extracts patterns from documentation files (e.g., Markdown, reStructuredText).
        This extracts code blocks or specific sections from documentation.

        Args:
            doc_file_path: The path to the documentation file.
            project_path: The root path of the project.

        Returns:
            A list of dictionaries, each representing an extracted pattern.
        """
        patterns: list[dict[str, Any]] = []
        content = self._read_file_content(doc_file_path)
        if content:
            try:
                # Simple markdown code block extraction
                # This can be expanded to parse specific sections, examples, etc.
                code_blocks = []
                in_code_block = False
                current_block: list[str] = []
                for line in content.splitlines():
                    if line.strip().startswith("```"):
                        if in_code_block:
                            code_blocks.append("\n".join(current_block).strip())
                            current_block = []
                        in_code_block = not in_code_block
                    elif in_code_block:
                        current_block.append(line)

                if (
                    not code_blocks and content.strip()
                ):  # If no code blocks, consider entire doc as a pattern
                    code_blocks.append(content.strip())

                for block_content in code_blocks:
                    if block_content:
                        metadata = self.generate_pattern_metadata(
                            block_content,
                            project_path,
                            source_file=doc_file_path,
                            pattern_type="documentation",
                        )
                        patterns.append(
                            {"content": block_content, "metadata": metadata}
                        )
                logger.info(
                    f"Extracted {len(patterns)} patterns from documentation file: {doc_file_path}"
                )
            except Exception as e:
                logger.error(
                    f"Error processing documentation file {doc_file_path}: {e}"
                )
        return patterns

    def calculate_success_metrics(
        self, pattern_data: dict[str, Any], usage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculates and updates success metrics for a given pattern.

        Args:
            pattern_data: The dictionary representing the pattern (must contain 'metadata' key).
            usage_data: A dictionary containing data relevant for metrics calculation,
                        e.g., {"successful_applications": 5, "total_applications": 10}.

        Returns:
            The updated pattern_data dictionary with 'success_metrics' updated.
        """
        if (
            "metadata" not in pattern_data
            or "success_metrics" not in pattern_data["metadata"]
        ):
            logger.warning(
                "Pattern data missing 'metadata' or 'success_metrics' key. Cannot calculate metrics."
            )
            return pattern_data

        metrics = pattern_data["metadata"]["success_metrics"]

        successful_apps = usage_data.get("successful_applications", 0)
        total_apps = usage_data.get("total_applications", 0)

        if total_apps > 0:
            metrics["success_rate"] = successful_apps / total_apps
        else:
            metrics["success_rate"] = 0.0  # No applications yet

        metrics["usage_count"] = total_apps
        metrics["last_calculated"] = datetime.now().isoformat()

        pattern_data["metadata"]["success_metrics"] = metrics
        logger.debug(
            f"Calculated success metrics for pattern ID: {pattern_data['metadata'].get('id', 'N/A')}"
        )
        return pattern_data
