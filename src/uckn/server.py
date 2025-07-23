"""
UCKN MCP Server Implementation
Provides Model Context Protocol server for UCKN knowledge framework
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ServerCapabilities,
    TextContent,
    Tool,
)
from pydantic import AnyUrl

from .core import KnowledgeManager, SemanticSearch

logger = logging.getLogger(__name__)

# Initialize UCKN components
knowledge_manager = KnowledgeManager()
semantic_search_engine = SemanticSearch()

app = Server("uckn-knowledge")


@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available knowledge resources"""
    logger.info("handle_list_resources called")
    return [
        Resource(
            uri=AnyUrl("uckn://knowledge/patterns"),
            name="Knowledge Patterns",
            description="Development patterns and solutions database",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("uckn://knowledge/tech-stack"),
            name="Technology Stack",
            description="Detected technology stack information",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("uckn://knowledge/errors"),
            name="Error Solutions",
            description="Common error patterns and solutions",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific knowledge resource"""
    uri_str = str(uri)

    if uri_str == "uckn://knowledge/patterns":
        # Return knowledge patterns
        patterns = await knowledge_manager.get_all_patterns()
        return f"Available patterns: {len(patterns)} found\n" + "\n".join([
            f"- {pattern.get('title', 'Unknown')}: {pattern.get('description', 'No description')}"
            for pattern in patterns
        ])

    elif uri_str == "uckn://knowledge/tech-stack":
        # Return technology stack detection
        tech_stack = await knowledge_manager.detect_tech_stack(".")
        return "Technology Stack:\n" + "\n".join([
            f"- {tech}: {version}"
            for tech, version in tech_stack.items()
        ])

    elif uri_str == "uckn://knowledge/errors":
        # Return error solutions
        errors = await knowledge_manager.get_error_solutions()
        return f"Error Solutions: {len(errors)} found\n" + "\n".join([
            f"- {error.get('pattern', 'Unknown error')}: {error.get('solution', 'No solution')}"
            for error in errors
        ])

    else:
        raise ValueError(f"Unknown resource: {uri_str}")


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available UCKN tools"""
    return [
        Tool(
            name="search_patterns",
            description="Search for development patterns and solutions",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for patterns"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_project",
            description="Analyze project structure and technology stack",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Project path to analyze",
                        "default": "."
                    }
                }
            }
        ),
        Tool(
            name="find_error_solution",
            description="Find solutions for specific error patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "Error message or pattern to search for solutions"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context about the error",
                        "default": ""
                    }
                },
                "required": ["error_message"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls"""

    if name == "search_patterns":
        query = arguments["query"]
        limit = arguments.get("limit", 10)

        # Perform semantic search
        results = await semantic_search_engine.search_async(query, limit=limit)

        response = f"Found {len(results)} patterns matching '{query}':\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. **{result.get('title', 'Unknown Pattern')}**\n"
            response += f"   Description: {result.get('description', 'No description available')}\n"
            response += f"   Relevance: {result.get('score', 'N/A')}\n\n"

        return [TextContent(type="text", text=response)]

    elif name == "analyze_project":
        path = arguments.get("path", ".")

        # Analyze project structure
        analysis = await knowledge_manager.analyze_project(path)

        response = f"Project Analysis for '{path}':\n\n"
        response += "**Technology Stack:**\n"
        for tech, version in analysis.get("tech_stack", {}).items():
            response += f"- {tech}: {version}\n"

        response += "\n**Project Structure:**\n"
        for component in analysis.get("structure", []):
            response += f"- {component}\n"

        response += "\n**Recommendations:**\n"
        for rec in analysis.get("recommendations", []):
            response += f"- {rec}\n"

        return [TextContent(type="text", text=response)]

    elif name == "find_error_solution":
        error_message = arguments["error_message"]
        context = arguments.get("context", "")

        # Search for error solutions
        solutions = await knowledge_manager.find_error_solutions(error_message, context)

        response = f"Solutions for error: '{error_message}'\n\n"
        if not solutions:
            response += "No specific solutions found in knowledge base.\n"
            response += "Consider checking documentation or community resources."
        else:
            for i, solution in enumerate(solutions, 1):
                response += f"{i}. **{solution.get('title', 'Solution')}**\n"
                response += f"   Problem: {solution.get('problem', 'N/A')}\n"
                response += f"   Solution: {solution.get('solution', 'N/A')}\n"
                response += f"   Steps: {solution.get('steps', 'N/A')}\n\n"

        return [TextContent(type="text", text=response)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main server entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting UCKN MCP Server...")
    logger.info("UCKN components ready (no async initialization required)")

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="uckn-knowledge",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    resources={"subscribe": True, "listChanged": True},
                    tools={"listChanged": True}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
