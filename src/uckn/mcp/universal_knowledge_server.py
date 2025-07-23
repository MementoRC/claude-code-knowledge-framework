#!/usr/bin/env python3
"""
Universal Knowledge MCP Server

Provides MCP tools for local knowledge access and pattern management.
Implements the following tools:
- search_patterns: Search for knowledge patterns
- recommend_setup: Get setup recommendations
- predict_issues: Predict potential issues
- validate_solution: Validate proposed solutions
- contribute_pattern: Contribute new patterns
- get_project_dna: Analyze project technology stack
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolResult,
        TextContent,
        Tool,
    )
except ImportError as e:
    print(f"MCP library not available: {e}", file=sys.stderr)
    sys.exit(1)

# Import UCKN components
try:
    from uckn.core.atoms.multi_modal_embeddings import MultiModalEmbeddings
    from uckn.core.atoms.project_dna_fingerprinter import ProjectDNAFingerprinter
    from uckn.core.molecules.pattern_analytics import PatternAnalytics
    from uckn.core.molecules.pattern_manager import PatternManager
    from uckn.core.molecules.tech_stack_compatibility_matrix import (
        TechStackCompatibilityMatrix,
    )
    from uckn.core.organisms.knowledge_manager import KnowledgeManager
    from uckn.core.organisms.pattern_recommendation_engine import (
        PatternRecommendationEngine,
    )
    from uckn.core.semantic_search_enhanced import (
        EnhancedSemanticSearchEngine as SemanticSearchEngine,
    )
    from uckn.storage.chromadb_connector import ChromaDBConnector
    from uckn.storage.unified_database import UnifiedDatabase
except ImportError as e:
    print(f"UCKN components not available: {e}", file=sys.stderr)
    sys.exit(1)


class UniversalKnowledgeServer:
    """MCP Server for Universal Knowledge system"""

    def __init__(self, project_root: str | None = None):
        """Initialize the Universal Knowledge MCP server."""
        self.server = Server("universal-knowledge")
        self.project_root = project_root or os.getcwd()
        self.logger = logging.getLogger(__name__)

        # Initialize UCKN components
        self._initialize_components()

        # Register tools
        self._register_tools()

    def _initialize_components(self):
        """Initialize UCKN knowledge management components."""
        try:
            # Initialize storage layer
            db_path = os.path.join(self.project_root, ".uckn", "storage")
            self.chroma_connector = ChromaDBConnector(db_path=db_path)

            # Get PostgreSQL URL from environment
            pg_url = os.environ.get("UCKN_DATABASE_URL")
            if not pg_url:
                raise ValueError("UCKN_DATABASE_URL environment variable is required")

            chroma_path = os.path.join(self.project_root, ".uckn", "knowledge", "chroma_db")
            self.unified_db = UnifiedDatabase(pg_db_url=pg_url, chroma_db_path=chroma_path)

            # Initialize atoms
            self.dna_fingerprinter = ProjectDNAFingerprinter()
            self.embeddings = MultiModalEmbeddings()
            self.semantic_search = SemanticSearchEngine(
                embedding_atom=self.embeddings,
                chroma_connector=self.chroma_connector
            )

            # Initialize molecules
            self.pattern_manager = PatternManager(
                unified_db=self.unified_db,
                semantic_search=self.semantic_search
            )
            self.compatibility_matrix = TechStackCompatibilityMatrix(
                chroma_connector=self.chroma_connector
            )
            self.pattern_analytics = PatternAnalytics(
                chroma_connector=self.chroma_connector
            )

            # Initialize organisms
            self.recommendation_engine = PatternRecommendationEngine(
                dna_fingerprinter=self.dna_fingerprinter,
                semantic_search=self.semantic_search,
                compatibility_matrix=self.compatibility_matrix,
                pattern_analytics=self.pattern_analytics,
                pattern_manager=self.pattern_manager
            )

            knowledge_dir = os.path.join(self.project_root, ".uckn", "knowledge")
            self.knowledge_manager = KnowledgeManager(
                knowledge_dir=knowledge_dir,
                pg_db_url=pg_url
            )

            self.logger.info("UCKN components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize UCKN components: {e}")
            # Create mock components for graceful degradation
            self._create_mock_components()

    def _create_mock_components(self):
        """Create mock components for graceful degradation."""
        class MockComponent:
            def is_available(self): return False
            def __getattr__(self, name): return lambda *args, **kwargs: None

        self.chroma_connector = MockComponent()
        self.dna_fingerprinter = MockComponent()
        self.semantic_search = MockComponent()
        self.pattern_manager = MockComponent()
        self.compatibility_matrix = MockComponent()
        self.pattern_analytics = MockComponent()
        self.recommendation_engine = MockComponent()
        self.knowledge_manager = MockComponent()

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="search_patterns",
                    description="Search for knowledge patterns based on query and context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for patterns"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory (optional)",
                                "default": self.project_root
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            },
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of patterns to search for",
                                "enum": ["all", "setup", "bugfix", "optimization", "best_practice"]
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="recommend_setup",
                    description="Get setup recommendations for a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory",
                                "default": self.project_root
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of recommendations",
                                "default": 5
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="predict_issues",
                    description="Predict potential issues based on project characteristics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory",
                                "default": self.project_root
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of predictions",
                                "default": 5
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="validate_solution",
                    description="Validate a proposed solution against known patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "solution_description": {
                                "type": "string",
                                "description": "Description of the proposed solution"
                            },
                            "problem_context": {
                                "type": "string",
                                "description": "Context of the problem being solved"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory",
                                "default": self.project_root
                            }
                        },
                        "required": ["solution_description", "problem_context"]
                    }
                ),
                Tool(
                    name="contribute_pattern",
                    description="Contribute a new pattern to the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern_title": {
                                "type": "string",
                                "description": "Title of the pattern"
                            },
                            "pattern_description": {
                                "type": "string",
                                "description": "Detailed description of the pattern"
                            },
                            "pattern_code": {
                                "type": "string",
                                "description": "Code example or implementation"
                            },
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of pattern",
                                "enum": ["setup", "bugfix", "optimization", "best_practice", "architecture"]
                            },
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Related technologies/frameworks"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory",
                                "default": self.project_root
                            }
                        },
                        "required": ["pattern_title", "pattern_description", "pattern_type"]
                    }
                ),
                Tool(
                    name="get_project_dna",
                    description="Analyze project technology stack and generate DNA fingerprint",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory",
                                "default": self.project_root
                            }
                        },
                        "required": []
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "search_patterns":
                    return await self._search_patterns(**arguments)
                elif name == "recommend_setup":
                    return await self._recommend_setup(**arguments)
                elif name == "predict_issues":
                    return await self._predict_issues(**arguments)
                elif name == "validate_solution":
                    return await self._validate_solution(**arguments)
                elif name == "contribute_pattern":
                    return await self._contribute_pattern(**arguments)
                elif name == "get_project_dna":
                    return await self._get_project_dna(**arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    ).model_dump()
            except Exception as e:
                self.logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                ).model_dump()

    async def _search_patterns(
        self,
        query: str,
        project_path: str = None,
        limit: int = 10,
        pattern_type: str = "all"
    ) -> CallToolResult:
        """Search for knowledge patterns."""
        try:
            project_path = project_path or self.project_root

            # Perform semantic search
            if hasattr(self.semantic_search, 'search_by_text'):
                results = self.semantic_search.search_by_text(
                    query_text=query,
                    limit=limit
                )
            else:
                # Fallback to pattern manager search
                results = self.pattern_manager.search_patterns(
                    query=query,
                    limit=limit
                )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "pattern_id": result.get("id", "unknown"),
                    "content": result.get("document", ""),
                    "metadata": result.get("metadata", {}),
                    "similarity_score": result.get("similarity_score", 0.0)
                })

            response = {
                "query": query,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Search failed: {str(e)}")]
            ).model_dump()

    async def _recommend_setup(
        self,
        project_path: str = None,
        limit: int = 5
    ) -> CallToolResult:
        """Get setup recommendations."""
        try:
            project_path = project_path or self.project_root

            if hasattr(self.recommendation_engine, 'get_setup_recommendations'):
                recommendations = self.recommendation_engine.get_setup_recommendations(
                    project_path=project_path,
                    limit=limit
                )

                formatted_recommendations = []
                for rec in recommendations:
                    formatted_recommendations.append({
                        "pattern_id": rec.pattern_id,
                        "description": rec.description,
                        "confidence_score": rec.confidence_score,
                        "compatibility_score": rec.compatibility_score,
                        "success_rate": rec.success_rate
                    })

                response = {
                    "project_path": project_path,
                    "recommendations": formatted_recommendations,
                    "total_recommendations": len(formatted_recommendations)
                }
            else:
                response = {
                    "error": "Recommendation engine not available",
                    "project_path": project_path
                }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Setup recommendations failed: {str(e)}")]
            ).model_dump()

    async def _predict_issues(
        self,
        project_path: str = None,
        limit: int = 5
    ) -> CallToolResult:
        """Predict potential issues."""
        try:
            project_path = project_path or self.project_root

            if hasattr(self.recommendation_engine, 'get_proactive_recommendations'):
                predictions = self.recommendation_engine.get_proactive_recommendations(
                    project_path=project_path,
                    limit=limit
                )

                formatted_predictions = []
                for pred in predictions:
                    formatted_predictions.append({
                        "issue_type": pred.description,
                        "pattern_id": pred.pattern_id,
                        "prevention_strategy": pred.pattern_content,
                        "confidence_score": pred.confidence_score
                    })

                response = {
                    "project_path": project_path,
                    "potential_issues": formatted_predictions,
                    "total_predictions": len(formatted_predictions)
                }
            else:
                response = {
                    "error": "Issue prediction not available",
                    "project_path": project_path
                }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Issue prediction failed: {str(e)}")]
            ).model_dump()

    async def _validate_solution(
        self,
        solution_description: str,
        problem_context: str,
        project_path: str = None
    ) -> CallToolResult:
        """Validate a proposed solution."""
        try:
            project_path = project_path or self.project_root

            # Search for similar solutions
            if hasattr(self.semantic_search, 'search_by_text'):
                similar_solutions = self.semantic_search.search_by_text(
                    query_text=f"{problem_context} {solution_description}",
                    limit=5
                )

                validation_result = {
                    "solution_description": solution_description,
                    "problem_context": problem_context,
                    "validation_score": 0.0,
                    "similar_patterns": [],
                    "recommendations": []
                }

                if similar_solutions:
                    # Calculate validation score based on similarity to known good patterns
                    scores = [result.get("similarity_score", 0.0) for result in similar_solutions]
                    validation_result["validation_score"] = max(scores) if scores else 0.0

                    for solution in similar_solutions:
                        validation_result["similar_patterns"].append({
                            "pattern_id": solution.get("id", "unknown"),
                            "similarity_score": solution.get("similarity_score", 0.0),
                            "description": solution.get("document", "")[:200]
                        })

                    # Provide recommendations based on validation
                    if validation_result["validation_score"] > 0.8:
                        validation_result["recommendations"].append(
                            "Solution appears to follow established patterns"
                        )
                    elif validation_result["validation_score"] > 0.6:
                        validation_result["recommendations"].append(
                            "Solution is partially validated, consider reviewing similar patterns"
                        )
                    else:
                        validation_result["recommendations"].append(
                            "Consider alternative approaches based on similar patterns"
                        )
            else:
                validation_result = {
                    "error": "Solution validation not available"
                }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(validation_result, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Solution validation failed: {str(e)}")]
            ).model_dump()

    async def _contribute_pattern(
        self,
        pattern_title: str,
        pattern_description: str,
        pattern_type: str,
        pattern_code: str = "",
        technologies: list[str] = None,
        project_path: str = None
    ) -> CallToolResult:
        """Contribute a new pattern."""
        try:
            project_path = project_path or self.project_root
            technologies = technologies or []

            # Create pattern data with proper metadata matching ChromaDB schema
            pattern_data = {
                "document": f"{pattern_title}\n\n{pattern_description}\n\n{pattern_code}",
                "metadata": {
                    "title": pattern_title,
                    "description": pattern_description,
                    "pattern_type": pattern_type,
                    "technology_stack": ",".join(technologies) if technologies else "",  # Required: comma-separated string
                    "success_rate": 0.8,  # Required: default success rate for contributed patterns
                    "technologies": technologies,  # Keep for backward compatibility
                    "code": pattern_code,
                    "contributed_at": "manual_contribution"
                }
            }

            if hasattr(self.pattern_manager, 'add_pattern'):
                pattern_id = self.pattern_manager.add_pattern(pattern_data)

                if pattern_id:
                    response = {
                        "status": "success",
                        "pattern_id": pattern_id,
                        "message": "Pattern contributed successfully"
                    }
                else:
                    response = {
                        "status": "error",
                        "message": "Failed to add pattern to knowledge base"
                    }
            else:
                response = {
                    "status": "error",
                    "message": "Pattern contribution not available"
                }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Pattern contribution failed: {str(e)}")]
            ).model_dump()

    async def _get_project_dna(
        self,
        project_path: str = None
    ) -> CallToolResult:
        """Get project DNA fingerprint."""
        try:
            project_path = project_path or self.project_root

            if hasattr(self.dna_fingerprinter, 'generate_fingerprint'):
                fingerprint = self.dna_fingerprinter.generate_fingerprint(project_path)

                response = {
                    "project_path": project_path,
                    "dna_fingerprint": fingerprint,
                    "analysis_timestamp": "current"
                }
            else:
                response = {
                    "error": "DNA fingerprinting not available",
                    "project_path": project_path
                }

            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(response, indent=2))]
            ).model_dump()

        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"DNA analysis failed: {str(e)}")]
            ).model_dump()


async def main():
    """Run the Universal Knowledge MCP server."""

    # Set up session-specific logging in working directory
    import logging
    from datetime import datetime

    # Create log file in current working directory with timestamp
    log_filename = f"uckn-mcp-server-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_path = os.path.join(os.getcwd(), log_filename)

    # Configure logging to file only (avoid stderr)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_path, mode='w')],
        force=True  # Override any existing logging config
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("="*60)
        logger.info("UCKN MCP Server Starting")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Log file: {log_path}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Command line: {' '.join(sys.argv)}")

        # Log environment variables
        for key, value in os.environ.items():
            if 'UCKN' in key:
                logger.info(f"Environment: {key}={value}")

        # Get project root from command line or environment
        project_root = None
        if len(sys.argv) > 1:
            project_root = sys.argv[1]
            logger.info(f"Project root from command line: {project_root}")
        elif "PROJECT_ROOT" in os.environ:
            project_root = os.environ["PROJECT_ROOT"]
            logger.info(f"Project root from environment: {project_root}")
        else:
            logger.info("No project root specified, using current directory")

        logger.info("Initializing UCKN server...")
        # Initialize server
        server_instance = UniversalKnowledgeServer(project_root=project_root)
        logger.info("UCKN server initialized successfully")

        logger.info("Creating MCP server options...")
        # Run server using the same pattern as working MCP servers
        options = server_instance.server.create_initialization_options()
        logger.info(f"Server options: {options}")

        logger.info("Starting stdio server...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Stdio context established, starting server.run()")
            await server_instance.server.run(
                read_stream,
                write_stream,
                options,
                raise_exceptions=True
            )
            logger.info("Server run completed normally")

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")

        # Also log current working directory and environment for debugging
        logger.error(f"Working directory at error: {os.getcwd()}")
        logger.error(f"Python path: {sys.path}")
        raise
    finally:
        logger.info("UCKN MCP Server shutdown")
        logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
