"""
Tech stack detection test fixtures for UCKN.

Provides:
- Comprehensive tech stack test scenarios
- Project structure generation utilities
- File type detection test data
- Dependency file samples for various ecosystems
"""

import pytest
import tempfile
import os
import shutil

@pytest.fixture
def tech_stack_scenarios():
    """
    Returns a list of tech stack detection scenarios.
    """
    return [
        {
            "project_type": "python",
            "files": ["main.py", "requirements.txt", "setup.py"],
            "expected_stack": ["python"]
        },
        {
            "project_type": "nodejs",
            "files": ["index.js", "package.json"],
            "expected_stack": ["nodejs", "javascript"]
        },
        {
            "project_type": "java",
            "files": ["Main.java", "pom.xml"],
            "expected_stack": ["java", "maven"]
        },
        {
            "project_type": "dotnet",
            "files": ["Program.cs", "project.csproj"],
            "expected_stack": ["dotnet", "csharp"]
        }
    ]

@pytest.fixture
def project_structure_generator():
    """
    Utility to generate a project directory structure for tech stack detection.
    """
    temp_dirs = []

    def generator(files):
        temp_dir = tempfile.mkdtemp()
        temp_dirs.append(temp_dir)
        for fname in files:
            fpath = os.path.join(temp_dir, fname)
            with open(fpath, "w") as f:
                f.write("# test file")
        return temp_dir

    yield generator

    # Cleanup all created temp dirs
    for d in temp_dirs:
        shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def dependency_file_samples():
    """
    Returns sample dependency files for various ecosystems.
    """
    return {
        "requirements.txt": "pytest\nrequests\nsentence-transformers\n",
        "package.json": '{ "dependencies": { "express": "^4.17.1" } }',
        "pom.xml": "<project><dependencies></dependencies></project>",
        "project.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\"></Project>"
    }
