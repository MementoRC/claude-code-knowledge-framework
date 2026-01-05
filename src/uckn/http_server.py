#!/usr/bin/env python3
"""
HTTP entry point for UCKN MCP Server (Universal Code Knowledge Navigator).

Provides HTTP transport with:
- POST /mcp for JSON-RPC 2.0 MCP requests
- GET /mcp for SSE streaming notifications
- GET /health for health checks
- REST API for pattern/search queries

Usage:
    pixi run http-server
    pixi run http-server --port 4004 --api-key secret
    python src/uckn/http_server.py --help
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports - must be done before any uckn imports
_src_path = Path(__file__).parent.parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Imports after path setup (noqa for ruff E402)
from uckn.transport.http_server import HTTPUCKNServer  # noqa: E402
from uckn.transport.security import SecurityConfig  # noqa: E402


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the HTTP server."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="UCKN HTTP Server (Universal Code Knowledge Navigator)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start server with defaults (localhost:4004):
    pixi run http-server

  Start with custom port:
    pixi run http-server --port 5000

  Start with API key authentication:
    pixi run http-server --api-key mysecretkey

  Start with specific project root:
    pixi run http-server --project-root /path/to/project

Environment Variables:
  UCKN_API_KEY: API key for authentication
  UCKN_PROJECT_ROOT: Default project root path
  UCKN_DATABASE_URL: PostgreSQL connection string (for knowledge storage)
        """,
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1, localhost only for security)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4004,
        help="Port to bind to (default: 4004)",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root path (default: current directory or UCKN_PROJECT_ROOT)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("UCKN_API_KEY"),
        help="API key for authentication (optional, or use UCKN_API_KEY env var)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow network connections (DANGEROUS - only use in trusted networks)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the HTTP server."""
    args = parse_args()

    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Security warning if network access enabled
    if args.allow_network:
        logger.warning(
            "Network access enabled! This exposes the server to all network interfaces. "
            "Only use this in trusted networks."
        )

    # Determine project root
    project_root = (
        args.project_root or os.environ.get("UCKN_PROJECT_ROOT") or os.getcwd()
    )

    # Build security config
    security_config = SecurityConfig(
        localhost_only=not args.allow_network,
        require_api_key=bool(args.api_key),
        api_key=args.api_key,
    )

    # Create and run server
    server = HTTPUCKNServer(
        host=args.host if args.allow_network else "127.0.0.1",
        port=args.port,
        project_root=project_root,
        security_config=security_config,
    )

    logger.info("Starting UCKN HTTP Server (Universal Code Knowledge Navigator)")
    logger.info(f"  Host: {server.host}")
    logger.info(f"  Port: {server.port}")
    logger.info(f"  Project Root: {server.project_root}")
    logger.info(f"  API Key: {'enabled' if args.api_key else 'disabled'}")
    logger.info(
        f"  Network Access: {'enabled' if args.allow_network else 'localhost only'}"
    )
    logger.info("")
    logger.info("Endpoints:")
    logger.info(
        f"  POST http://{server.host}:{server.port}/mcp - MCP JSON-RPC requests"
    )
    logger.info(f"  GET  http://{server.host}:{server.port}/mcp - SSE notifications")
    logger.info(f"  GET  http://{server.host}:{server.port}/health - Health check")
    logger.info(
        f"  GET  http://{server.host}:{server.port}/api/search - Pattern search API"
    )
    logger.info(
        f"  GET  http://{server.host}:{server.port}/api/project-dna - Project DNA API"
    )
    logger.info("")

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
