"""
UCKN Issue Detection Rules Molecule

Implements a rule-based engine for identifying potential issues
based on project configuration, dependencies, and common patterns.
"""

import logging
from typing import Any

from ..atoms.tech_stack_detector import TechStackDetector


class IssueDetectionRules:
    """
    Applies a set of predefined rules to detect potential issues in a project.
    """

    def __init__(self, tech_stack_detector: TechStackDetector):
        self.tech_stack_detector = tech_stack_detector
        self._logger = logging.getLogger(__name__)

    def _detect_dependency_conflicts(
        self, project_stack: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Rule: Detect potential dependency conflicts.
        (Placeholder for more sophisticated logic)
        """
        issues = []
        if "Python" in project_stack.get(
            "languages", []
        ) and "pip" in project_stack.get("package_managers", []):
            # This is a simplified example. Real detection would involve parsing requirements.txt/pyproject.toml
            # and checking for known incompatible packages or version ranges.
            self._logger.info("Checking for Python dependency conflicts (rule-based).")
            # Example: if a project uses an old Python version with a new library
            # For demonstration, let's assume a rule: if Python is detected, and no specific lock file,
            # there's a *potential* for conflict.
            if not any(
                pm in ["poetry", "pixi"]
                for pm in project_stack.get("package_managers", [])
            ):
                issues.append(
                    {
                        "type": "dependency_conflict",
                        "description": "Potential dependency conflicts due to lack of strict dependency locking (e.g., poetry.lock, pixi.lock).",
                        "severity": "medium",
                        "confidence": 0.7,
                        "preventive_measure": "Implement a dependency locking mechanism (e.g., Poetry, Pipenv, or strict requirements.txt with hashes).",
                    }
                )
        if "JavaScript" in project_stack.get(
            "languages", []
        ) and "npm" in project_stack.get("package_managers", []):
            self._logger.info(
                "Checking for JavaScript dependency conflicts (rule-based)."
            )
            # Similar logic for package.json/package-lock.json
            if not (
                project_stack.get("project_path")
                and (project_stack["project_path"] / "package-lock.json").exists()
            ):
                issues.append(
                    {
                        "type": "dependency_conflict",
                        "description": "Potential JavaScript dependency conflicts due to missing 'package-lock.json' or 'yarn.lock'.",
                        "severity": "medium",
                        "confidence": 0.7,
                        "preventive_measure": "Ensure 'package-lock.json' or 'yarn.lock' is committed to version control to guarantee consistent installations.",
                    }
                )
        return issues

    def _detect_build_failures(
        self, project_stack: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Rule: Detect potential build failures based on tech stack and common misconfigurations.
        (Placeholder for more sophisticated logic)
        """
        issues = []
        if "Python" in project_stack.get("languages", []):
            self._logger.info("Checking for Python build failure risks (rule-based).")
            # Example: Missing Dockerfile for a Python project intended for containerization
            if "Dockerfile" not in project_stack.get(
                "files", []
            ):  # Assuming tech_stack_detector could list files
                issues.append(
                    {
                        "type": "build_failure_risk",
                        "description": "No Dockerfile detected in a Python project, which might indicate a missing containerization strategy for deployment.",
                        "severity": "low",
                        "confidence": 0.6,
                        "preventive_measure": "Consider adding a Dockerfile for consistent build and deployment environments.",
                    }
                )
        if "JavaScript" in project_stack.get("languages", []):
            self._logger.info(
                "Checking for JavaScript build failure risks (rule-based)."
            )
            # Example: Missing build script in package.json for a frontend project
            # This would require parsing package.json, which is beyond current TechStackDetector scope.
            # For now, a generic rule.
            issues.append(
                {
                    "type": "build_failure_risk",
                    "description": "Ensure 'build' scripts are properly configured in 'package.json' for production builds.",
                    "severity": "low",
                    "confidence": 0.5,
                    "preventive_measure": "Verify 'scripts' section in 'package.json' includes a robust 'build' command.",
                }
            )
        return issues

    def _detect_test_flakiness(
        self, project_stack: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Rule: Detect potential test flakiness indicators.
        (Placeholder for more sophisticated logic)
        """
        issues = []
        if "pytest" in project_stack.get("testing", []):
            self._logger.info("Checking for Pytest flakiness indicators (rule-based).")
            # Example: Presence of certain patterns in test files (e.g., reliance on global state, sleep calls)
            # This would require code analysis, which is not in scope for this molecule yet.
            issues.append(
                {
                    "type": "test_flakiness_risk",
                    "description": "Potential for test flakiness. Review tests for reliance on external state, timing issues, or non-deterministic behavior.",
                    "severity": "medium",
                    "confidence": 0.6,
                    "preventive_measure": "Implement test isolation, use mocking/patching, and avoid `time.sleep()` in tests. Consider a flakiness detection tool.",
                }
            )
        return issues

    def _detect_performance_bottlenecks(
        self, project_stack: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Rule: Detect potential performance bottlenecks based on tech stack.
        (Placeholder for more sophisticated logic)
        """
        issues = []
        if "Python" in project_stack.get("languages", []):
            self._logger.info("Checking for Python performance risks (rule-based).")
            issues.append(
                {
                    "type": "performance_bottleneck_risk",
                    "description": "Consider using asynchronous programming (asyncio) or optimizing database queries for I/O-bound Python applications.",
                    "severity": "low",
                    "confidence": 0.5,
                    "preventive_measure": "Profile your application to identify hotspots. Optimize database interactions and consider caching strategies.",
                }
            )
        if "JavaScript" in project_stack.get("languages", []):
            self._logger.info("Checking for JavaScript performance risks (rule-based).")
            issues.append(
                {
                    "type": "performance_bottleneck_risk",
                    "description": "Large bundle sizes or unoptimized image assets can lead to slow loading times in web applications.",
                    "severity": "medium",
                    "confidence": 0.6,
                    "preventive_measure": "Implement code splitting, lazy loading, and image optimization techniques. Use Lighthouse or similar tools for auditing.",
                }
            )
        return issues

    def _detect_security_vulnerabilities(
        self, project_stack: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Rule: Detect potential security vulnerabilities based on tech stack and common practices.
        (Placeholder for more sophisticated logic)
        """
        issues = []
        if "Python" in project_stack.get("languages", []):
            self._logger.info("Checking for Python security risks (rule-based).")
            issues.append(
                {
                    "type": "security_vulnerability_risk",
                    "description": "Ensure all dependencies are up-to-date to mitigate known vulnerabilities. Use tools like Bandit or Snyk.",
                    "severity": "high",
                    "confidence": 0.7,
                    "preventive_measure": "Regularly audit dependencies for known CVEs. Implement secure coding practices (e.g., input validation, proper error handling).",
                }
            )
        if "JavaScript" in project_stack.get("languages", []):
            self._logger.info("Checking for JavaScript security risks (rule-based).")
            issues.append(
                {
                    "type": "security_vulnerability_risk",
                    "description": "Client-side JavaScript applications are susceptible to XSS and CSRF. Server-side Node.js apps need protection against injection attacks.",
                    "severity": "high",
                    "confidence": 0.7,
                    "preventive_measure": "Sanitize all user inputs. Use Content Security Policy (CSP). Implement proper authentication and authorization. Keep Node.js dependencies updated.",
                }
            )
        return issues

    def analyze_project_for_rules(self, project_path: str) -> list[dict[str, Any]]:
        """
        Analyzes a project using rule-based detection.

        Args:
            project_path: The path to the project directory.

        Returns:
            A list of dictionaries, each representing a detected issue.
        """
        self._logger.info(f"Starting rule-based analysis for project: {project_path}")
        project_stack = self.tech_stack_detector.analyze_project(project_path)
        project_stack[
            "project_path"
        ] = project_path  # Add path for potential file checks

        detected_issues = []

        # Apply various rule sets
        detected_issues.extend(self._detect_dependency_conflicts(project_stack))
        detected_issues.extend(self._detect_build_failures(project_stack))
        detected_issues.extend(self._detect_test_flakiness(project_stack))
        detected_issues.extend(self._detect_performance_bottlenecks(project_stack))
        detected_issues.extend(self._detect_security_vulnerabilities(project_stack))

        self._logger.info(
            f"Rule-based analysis complete. Found {len(detected_issues)} potential issues."
        )
        return detected_issues
