"""
UCKN Tech Stack Detector Atom
"""

from pathlib import Path
from typing import Dict, Any


class TechStackDetector:
    """Detect project technology stack"""

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze project for technology stack"""
        path = Path(project_path)

        stack = {
            "languages": [],
            "package_managers": [],
            "frameworks": [],
            "testing": [],
            "ci_cd": [],
        }

        # Detect Python
        if (path / "pyproject.toml").exists():
            stack["languages"].append("Python")
            stack["package_managers"].append("pip/poetry/pixi")

        if (path / "requirements.txt").exists():
            stack["package_managers"].append("pip")

        # Detect JavaScript/Node.js
        if (path / "package.json").exists():
            stack["languages"].append("JavaScript")
            stack["package_managers"].append("npm")

        # Detect testing frameworks
        if (path / "pytest.ini").exists() or "pytest" in str(path):
            stack["testing"].append("pytest")

        # Detect CI/CD
        if (path / ".github" / "workflows").exists():
            stack["ci_cd"].append("GitHub Actions")

        return stack
