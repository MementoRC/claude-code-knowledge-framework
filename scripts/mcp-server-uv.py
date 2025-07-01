#!/usr/bin/env python3
"""
UV-optimized UCKN MCP Server Entry Point

This script provides a UV-friendly entry point for the UCKN MCP server
that handles dependency management automatically.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path for development
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Also add the project root to handle different import scenarios
sys.path.insert(0, str(project_root))

# Set default environment variables if not provided
os.environ.setdefault("UCKN_KNOWLEDGE_DIR", str(Path.cwd() / ".uckn" / "knowledge"))
os.environ.setdefault("UCKN_LOG_LEVEL", "INFO")

# Import and run the MCP server
try:
    import asyncio
    from uckn.mcp.universal_knowledge_server import main
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    print(f"Error importing UCKN MCP server: {e}", file=sys.stderr)
    print("Make sure you're running this with: uv run scripts/mcp-server-uv.py", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error starting UCKN MCP server: {e}", file=sys.stderr)
    sys.exit(1)