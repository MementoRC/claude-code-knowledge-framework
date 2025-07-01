#!/usr/bin/env python3
"""
Setup script for UV-based UCKN integration in user projects.

This script helps users configure UCKN with UV in their own projects.
"""

import json
import os
import sys
from pathlib import Path
import shutil


def setup_uv_integration(project_path: str = "."):
    """Setup UV integration for UCKN in a user project."""
    
    project_path = Path(project_path).resolve()
    print(f"Setting up UCKN UV integration in: {project_path}")
    
    # 1. Create pyproject.toml if it doesn't exist
    pyproject_path = project_path / "pyproject.toml"
    if not pyproject_path.exists():
        print("Creating pyproject.toml...")
        pyproject_content = """[project]
name = "my-project"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
uckn = [
    "uckn-framework",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
        pyproject_path.write_text(pyproject_content)
    
    # 2. Create .mcp.json configuration
    mcp_config_path = project_path / ".mcp.json"
    uckn_framework_path = Path(__file__).parent.parent.resolve()
    
    mcp_config = {
        "mcpServers": {
            "uckn-knowledge": {
                "command": "uv",
                "args": [
                    "run",
                    "--project",
                    str(uckn_framework_path),
                    "scripts/mcp-server-uv.py"
                ],
                "env": {
                    "UCKN_KNOWLEDGE_DIR": "./.uckn/knowledge",
                    "UCKN_LOG_LEVEL": "INFO",
                    "UCKN_PROJECT_ROOT": str(project_path)
                }
            }
        }
    }
    
    print("Creating .mcp.json configuration...")
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)
    
    # 3. Create UCKN directory structure
    uckn_dir = project_path / ".uckn"
    uckn_dir.mkdir(exist_ok=True)
    (uckn_dir / "knowledge").mkdir(exist_ok=True)
    (uckn_dir / "config").mkdir(exist_ok=True)
    
    # 4. Create basic configuration
    config_file = uckn_dir / "config" / "uckn.toml"
    config_content = """[uckn]
project_name = "my-project"
knowledge_dir = ".uckn/knowledge"
log_level = "INFO"

[database]
type = "sqlite"  # or "postgresql" for production
path = ".uckn/knowledge/uckn.db"

[search]
enabled = true
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
"""
    config_file.write_text(config_content)
    
    # 5. Create usage examples
    examples_dir = uckn_dir / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    usage_example = examples_dir / "basic_usage.py"
    usage_content = '''"""
Basic UCKN usage example for UV integration.
"""

from uckn.core.organisms.knowledge_manager import KnowledgeManager

# Initialize UCKN
km = KnowledgeManager(project_root=".")

# Example: Search for patterns
patterns = km.search_patterns("FastAPI setup", limit=5)
print(f"Found {len(patterns)} patterns")

# Example: Get project recommendations
recommendations = km.get_recommendations()
print(f"Recommendations: {recommendations}")
'''
    usage_example.write_text(usage_content)
    
    print("✅ UCKN UV integration setup complete!")
    print(f"""
📁 Created structure:
   - {mcp_config_path.relative_to(project_path)}
   - {uckn_dir.relative_to(project_path)}/
   - {config_file.relative_to(project_path)}
   - {usage_example.relative_to(project_path)}

🚀 Next steps:
   1. Start Claude Code in this directory
   2. Try: "Can you search for setup patterns in my knowledge base?"
   3. Try: "What recommendations do you have for this project?"

📝 Configuration:
   - MCP server: {mcp_config['mcpServers']['uckn-knowledge']['command']} {' '.join(mcp_config['mcpServers']['uckn-knowledge']['args'])}
   - Knowledge dir: {mcp_config['mcpServers']['uckn-knowledge']['env']['UCKN_KNOWLEDGE_DIR']}
""")


if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    setup_uv_integration(project_path)