"""
HTTP Server for UCKN MCP (Universal Code Knowledge Navigator).

Provides:
- POST /mcp: JSON-RPC 2.0 MCP requests with MCP-Session-Id header
- GET /mcp: SSE stream for server-to-client notifications
- GET /health: Health check endpoint
- GET /api/patterns: REST API for pattern queries
- GET /api/search: REST API for knowledge search
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from uckn.transport.mcp_session_manager import MCPSessionManager
from uckn.transport.security import (
    LocalhostOnlyMiddleware,
    SecurityConfig,
    get_origin_validation_middleware,
    validate_api_key,
)

logger = logging.getLogger(__name__)


class DataclassJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and common non-serializable types."""

    def default(self, obj: Any) -> Any:
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        if hasattr(obj, "model_dump"):  # Pydantic v2
            return obj.model_dump()
        if hasattr(obj, "dict"):  # Pydantic v1
            return obj.dict()
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class NotificationManager:
    """Manages server-to-client notifications via SSE."""

    def __init__(self) -> None:
        self._subscribers: dict[str, asyncio.Queue[dict[str, Any]]] = {}

    async def subscribe(
        self, mcp_session_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to notifications for an MCP session."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[mcp_session_id] = queue

        try:
            while True:
                notification = await queue.get()
                yield notification
        finally:
            if mcp_session_id in self._subscribers:
                del self._subscribers[mcp_session_id]

    async def notify(
        self, mcp_session_id: str, event_type: str, data: dict[str, Any]
    ) -> None:
        """Send notification to a specific MCP session."""
        if mcp_session_id in self._subscribers:
            await self._subscribers[mcp_session_id].put(
                {
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast notification to all connected sessions."""
        notification = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        for queue in self._subscribers.values():
            await queue.put(notification)

    def get_subscriber_count(self) -> int:
        """Get count of active subscribers."""
        return len(self._subscribers)


class HTTPUCKNServer:
    """HTTP server for UCKN MCP with cross-session knowledge sharing."""

    MCP_PROTOCOL_VERSION = "2024-11-05"
    DEFAULT_PORT = 4004

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4004,
        project_root: str | None = None,
        security_config: SecurityConfig | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.project_root = project_root or os.getcwd()
        self.security_config = security_config or SecurityConfig()

        self.mcp_session_manager: MCPSessionManager | None = None
        self.notification_manager: NotificationManager | None = None
        self.tools_instance: Any = None

    def _initialize_tools(self) -> None:
        """Initialize UCKN tools."""
        try:
            from uckn.mcp.tools import UniversalKnowledgeTools

            self.tools_instance = UniversalKnowledgeTools(
                project_root=self.project_root
            )
            logger.info("UCKN tools initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize UCKN tools: {e}")
            self.tools_instance = None

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan manager."""
        logger.info(f"Starting UCKN HTTP server on {self.host}:{self.port}")
        logger.info(f"Project root: {self.project_root}")

        # Initialize components
        self._initialize_tools()
        self.mcp_session_manager = MCPSessionManager()
        self.notification_manager = NotificationManager()

        app.state.tools = self.tools_instance
        app.state.mcp_session_manager = self.mcp_session_manager
        app.state.notification_manager = self.notification_manager
        app.state.project_root = self.project_root

        logger.info("UCKN HTTP server ready")

        yield

        logger.info("Shutting down UCKN HTTP server")

    def create_app(self) -> FastAPI:
        """Create the FastAPI application with MCP endpoints."""
        app = FastAPI(
            title="UCKN MCP Server",
            description="HTTP transport for Universal Code Knowledge Navigator MCP",
            version="1.0.0",
            lifespan=self.lifespan,
        )

        if self.security_config.localhost_only:
            app.add_middleware(LocalhostOnlyMiddleware)

        app.add_middleware(
            get_origin_validation_middleware(self.security_config.allowed_origins)
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.security_config.allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["MCP-Session-Id", "MCP-Protocol-Version"],
        )

        self._add_mcp_endpoints(app)
        self._add_health_endpoint(app)
        self._add_api_endpoints(app)

        return app

    def _add_mcp_endpoints(self, app: FastAPI) -> None:
        """Add MCP protocol endpoints."""

        @app.post("/mcp")
        async def handle_mcp_post(
            request: Request,
            mcp_session_id: str | None = Header(None, alias="MCP-Session-Id"),
            x_api_key: str | None = Header(None, alias="X-API-Key"),
        ) -> JSONResponse:
            """Handle MCP JSON-RPC 2.0 requests."""
            if self.security_config.require_api_key and self.security_config.api_key:
                validate_api_key(x_api_key, self.security_config.api_key)

            try:
                body = await request.json()
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    },
                )

            method = body.get("method")
            params = body.get("params", {})
            req_id = body.get("id")

            mcp_manager = request.app.state.mcp_session_manager

            if method == "initialize":
                new_session_id = await mcp_manager.create_mcp_session(
                    client_info=params.get("clientInfo")
                )
                response = JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": self.MCP_PROTOCOL_VERSION,
                            "capabilities": {
                                "resources": {"subscribe": True, "listChanged": True},
                                "tools": {"listChanged": True},
                                "prompts": {"listChanged": True},
                            },
                            "serverInfo": {
                                "name": "uckn-knowledge",
                                "version": "1.0.0",
                            },
                        },
                    }
                )
                response.headers["MCP-Session-Id"] = new_session_id
                response.headers["MCP-Protocol-Version"] = self.MCP_PROTOCOL_VERSION
                return response

            if not mcp_session_id:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32600, "message": "Missing MCP-Session-Id"},
                    },
                )

            if not await mcp_manager.validate_session(mcp_session_id):
                return JSONResponse(
                    status_code=401,
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32600, "message": "Invalid MCP-Session-Id"},
                    },
                )

            await mcp_manager.update_activity(mcp_session_id)

            try:
                result = await self._handle_mcp_method(
                    method, params, mcp_session_id, request
                )
                return JSONResponse(
                    content={"jsonrpc": "2.0", "id": req_id, "result": result}
                )
            except Exception as e:
                logger.exception(f"Error handling MCP method {method}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32603, "message": str(e)},
                    },
                )

        @app.get("/mcp")
        async def handle_mcp_sse(
            request: Request,
            mcp_session_id: str | None = Header(None, alias="MCP-Session-Id"),
        ) -> StreamingResponse:
            """Server-Sent Events stream for notifications."""
            if not mcp_session_id:
                raise HTTPException(status_code=400, detail="Missing MCP-Session-Id")

            mcp_manager = request.app.state.mcp_session_manager
            notification_manager = request.app.state.notification_manager

            if not await mcp_manager.validate_session(mcp_session_id):
                raise HTTPException(status_code=401, detail="Invalid MCP-Session-Id")

            async def event_generator() -> AsyncGenerator[str, None]:
                try:
                    async for notification in notification_manager.subscribe(
                        mcp_session_id
                    ):
                        event_id = str(uuid.uuid4())[:8]
                        data = json.dumps(notification)
                        yield f"id: {event_id}\ndata: {data}\n\n"
                except asyncio.CancelledError:
                    pass

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

    async def _handle_mcp_method(
        self, method: str, params: dict[str, Any], mcp_session_id: str, request: Request
    ) -> dict[str, Any]:
        """Handle individual MCP methods."""
        if method == "resources/templates/list":
            return {
                "resourceTemplates": [
                    {
                        "uriTemplate": "patterns://type/{type}",
                        "name": "patterns",
                        "description": "Patterns by type",
                    },
                    {
                        "uriTemplate": "search://query/{query}",
                        "name": "search",
                        "description": "Search knowledge base",
                    },
                ]
            }

        if method == "resources/list":
            return {"resources": []}

        if method == "resources/read":
            return await self._handle_resource_read(params, request)

        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "search_patterns",
                        "description": "Search for knowledge patterns",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                                "pattern_type": {
                                    "type": "string",
                                    "enum": [
                                        "all",
                                        "setup",
                                        "bugfix",
                                        "optimization",
                                        "best_practice",
                                    ],
                                },
                                "limit": {"type": "integer", "default": 10},
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "get_project_dna",
                        "description": "Analyze project technology stack",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "project_path": {
                                    "type": "string",
                                    "description": "Path to project",
                                },
                            },
                        },
                    },
                    {
                        "name": "recommend_setup",
                        "description": "Get setup recommendations",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "project_path": {"type": "string"},
                                "limit": {"type": "integer", "default": 5},
                            },
                        },
                    },
                    {
                        "name": "predict_issues",
                        "description": "Predict potential issues",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "project_path": {"type": "string"},
                                "limit": {"type": "integer", "default": 5},
                            },
                        },
                    },
                    {
                        "name": "contribute_pattern",
                        "description": "Contribute a new pattern",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pattern_title": {"type": "string"},
                                "pattern_description": {"type": "string"},
                                "pattern_type": {"type": "string"},
                                "technologies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": [
                                "pattern_title",
                                "pattern_description",
                                "pattern_type",
                            ],
                        },
                    },
                    {
                        "name": "validate_solution",
                        "description": "Validate a proposed solution",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "solution_description": {"type": "string"},
                                "problem_context": {"type": "string"},
                            },
                            "required": ["solution_description", "problem_context"],
                        },
                    },
                ]
            }

        if method == "tools/call":
            return await self._handle_tool_call(params, mcp_session_id, request)

        if method == "notifications/initialized":
            return {}

        if method == "prompts/list":
            return {"prompts": []}

        if method == "prompts/get":
            return {"prompt": None}

        raise ValueError(f"Unknown method: {method}")

    async def _handle_resource_read(
        self, params: dict[str, Any], request: Request
    ) -> dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri", "")
        tools = request.app.state.tools

        if uri.startswith("patterns://type/"):
            pattern_type = uri.replace("patterns://type/", "")
            if tools:
                result = await tools.search_patterns("", pattern_type, 50, None)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(result, cls=DataclassJSONEncoder),
                        }
                    ]
                }
            return {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": "{}"}]
            }

        if uri.startswith("search://query/"):
            query = uri.replace("search://query/", "")
            if tools:
                result = await tools.search_patterns(query, "all", 20, None)
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(result, cls=DataclassJSONEncoder),
                        }
                    ]
                }
            return {
                "contents": [{"uri": uri, "mimeType": "application/json", "text": "{}"}]
            }

        return {"contents": []}

    async def _handle_tool_call(
        self, params: dict[str, Any], mcp_session_id: str, request: Request
    ) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        tools = request.app.state.tools

        if not tools:
            result = {"error": "UCKN tools not initialized"}
            return {"content": [{"type": "text", "text": json.dumps(result)}]}

        try:
            if tool_name == "search_patterns":
                tool_result = await tools.search_patterns(
                    query=arguments.get("query", ""),
                    pattern_type=arguments.get("pattern_type", "all"),
                    limit=arguments.get("limit", 10),
                    project_path=arguments.get("project_path"),
                )
            elif tool_name == "get_project_dna":
                tool_result = await tools.get_project_dna(
                    project_path=arguments.get("project_path"),
                )
            elif tool_name == "recommend_setup":
                tool_result = await tools.recommend_setup(
                    project_path=arguments.get("project_path"),
                    limit=arguments.get("limit", 5),
                )
            elif tool_name == "predict_issues":
                tool_result = await tools.predict_issues(
                    project_path=arguments.get("project_path"),
                    limit=arguments.get("limit", 5),
                )
            elif tool_name == "contribute_pattern":
                tool_result = await tools.contribute_pattern(
                    pattern_title=arguments.get("pattern_title", ""),
                    pattern_description=arguments.get("pattern_description", ""),
                    pattern_type=arguments.get("pattern_type", ""),
                    pattern_code=arguments.get("pattern_code", ""),
                    technologies=arguments.get("technologies"),
                    project_path=arguments.get("project_path"),
                )
            elif tool_name == "validate_solution":
                tool_result = await tools.validate_solution(
                    solution_description=arguments.get("solution_description", ""),
                    problem_context=arguments.get("problem_context", ""),
                    project_path=arguments.get("project_path"),
                )
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}

            result = {"tool": tool_name, "status": "success", "result": tool_result}

        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            result = {"tool": tool_name, "status": "error", "error": str(e)}

        return {
            "content": [
                {"type": "text", "text": json.dumps(result, cls=DataclassJSONEncoder)}
            ]
        }

    def _add_health_endpoint(self, app: FastAPI) -> None:
        """Add health check endpoint."""

        @app.get("/health")
        async def health_check(request: Request) -> dict[str, Any]:
            mcp_manager = request.app.state.mcp_session_manager
            notif_manager = request.app.state.notification_manager
            tools = request.app.state.tools
            return {
                "status": "healthy",
                "server": "uckn-knowledge",
                "version": "1.0.0",
                "mcp_protocol_version": self.MCP_PROTOCOL_VERSION,
                "tools_available": tools is not None,
                "active_mcp_sessions": mcp_manager.get_active_session_count()
                if mcp_manager
                else 0,
                "sse_subscribers": notif_manager.get_subscriber_count()
                if notif_manager
                else 0,
                "project_root": request.app.state.project_root,
                "timestamp": datetime.now().isoformat(),
            }

    def _add_api_endpoints(self, app: FastAPI) -> None:
        """Add REST endpoints for direct API access."""

        @app.get("/api/search")
        async def api_search(
            request: Request,
            query: str,
            pattern_type: str = "all",
            limit: int = 10,
            x_api_key: str | None = Header(None, alias="X-API-Key"),
        ) -> dict[str, Any]:
            """Search patterns via REST API."""
            if self.security_config.require_api_key and self.security_config.api_key:
                validate_api_key(x_api_key, self.security_config.api_key)

            tools = request.app.state.tools
            if not tools:
                raise HTTPException(status_code=503, detail="Tools not available")

            result = await tools.search_patterns(query, pattern_type, limit, None)
            return {"query": query, "pattern_type": pattern_type, "result": result}

        @app.get("/api/project-dna")
        async def api_project_dna(
            request: Request,
            project_path: str | None = None,
            x_api_key: str | None = Header(None, alias="X-API-Key"),
        ) -> dict[str, Any]:
            """Get project DNA via REST API."""
            if self.security_config.require_api_key and self.security_config.api_key:
                validate_api_key(x_api_key, self.security_config.api_key)

            tools = request.app.state.tools
            if not tools:
                raise HTTPException(status_code=503, detail="Tools not available")

            result = await tools.get_project_dna(project_path)
            return {
                "project_path": project_path or request.app.state.project_root,
                "result": result,
            }

    async def run(self) -> None:
        """Run the HTTP server."""
        app = self.create_app()
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True,
        )
        server = uvicorn.Server(config)
        await server.serve()
