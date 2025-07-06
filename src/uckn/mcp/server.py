#!/usr/bin/env python3
"""
Entry point for the Universal Knowledge MCP Server
"""

import sys
import os

# Add the parent directory to the path so we can import from uckn
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from uckn.mcp.universal_knowledge_server import main

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
