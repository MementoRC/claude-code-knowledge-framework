"""Logging Middleware for UCKN API"""

import json
import logging
import time
import uuid
from typing import Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive logging middleware for API requests and responses"""

    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses

        # Configure structured logging
        self.audit_logger = logging.getLogger("uckn.audit")
        self.audit_logger.setLevel(logging.INFO)

        # Sensitive headers to exclude from logs
        self.sensitive_headers = {
            "authorization",
            "x-api-key",
            "x-api-token",
            "cookie",
            "set-cookie",
        }

        # Endpoints to exclude from detailed logging
        self.exclude_endpoints = {
            "/health/ping",
            "/health/status",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request/response logging"""

        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request ID to request state
        request.state.request_id = request_id

        # Skip detailed logging for excluded endpoints
        should_log_details = request.url.path not in self.exclude_endpoints

        # Log request
        if self.log_requests and should_log_details:
            await self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Add request ID and processing time to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"

            # Log response
            if self.log_responses and should_log_details:
                await self._log_response(request, response, request_id, processing_time)

            # Log summary for all requests
            await self._log_request_summary(
                request, response, request_id, processing_time
            )

            return response

        except Exception as e:
            # Log error
            processing_time = time.time() - start_time
            await self._log_error(request, e, request_id, processing_time)
            raise

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details"""
        try:
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "unknown")

            # Get user information if available
            user_info = self._get_user_info(request)

            # Prepare request data
            request_data = {
                "event_type": "request",
                "request_id": request_id,
                "timestamp": time.time(),
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._filter_headers(dict(request.headers)),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_info": user_info,
            }

            # Add request body for POST/PUT requests (with size limit)
            if request.method in ("POST", "PUT", "PATCH"):
                body = await self._get_request_body(request)
                if body:
                    request_data["body_size"] = len(body)
                    if len(body) < 10000:  # Log body only if smaller than 10KB
                        request_data["body"] = body

            self.audit_logger.info(json.dumps(request_data))

        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        processing_time: float,
    ):
        """Log response details"""
        try:
            # Get response body (with size limit)
            response_body = None
            if hasattr(response, "body"):
                body_size = len(response.body)
                if body_size < 10000:  # Log body only if smaller than 10KB
                    response_body = response.body.decode("utf-8", errors="ignore")

            response_data = {
                "event_type": "response",
                "request_id": request_id,
                "timestamp": time.time(),
                "status_code": response.status_code,
                "headers": self._filter_headers(dict(response.headers)),
                "processing_time_ms": round(processing_time * 1000, 2),
                "body_size": len(response.body) if hasattr(response, "body") else 0,
            }

            if response_body:
                response_data["body"] = response_body

            self.audit_logger.info(json.dumps(response_data))

        except Exception as e:
            logger.error(f"Error logging response: {e}")

    async def _log_request_summary(
        self,
        request: Request,
        response: Response,
        request_id: str,
        processing_time: float,
    ):
        """Log request summary for all requests"""
        try:
            user_info = self._get_user_info(request)

            summary_data = {
                "event_type": "request_summary",
                "request_id": request_id,
                "timestamp": time.time(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "client_ip": self._get_client_ip(request),
                "user_id": user_info.get("user_id") if user_info else None,
                "success": 200 <= response.status_code < 400,
            }

            # Log level based on status code
            if response.status_code >= 500:
                logger.error(json.dumps(summary_data))
            elif response.status_code >= 400:
                logger.warning(json.dumps(summary_data))
            else:
                logger.info(json.dumps(summary_data))

        except Exception as e:
            logger.error(f"Error logging request summary: {e}")

    async def _log_error(
        self,
        request: Request,
        error: Exception,
        request_id: str,
        processing_time: float,
    ):
        """Log error details"""
        try:
            user_info = self._get_user_info(request)

            error_data = {
                "event_type": "error",
                "request_id": request_id,
                "timestamp": time.time(),
                "method": request.method,
                "path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "processing_time_ms": round(processing_time * 1000, 2),
                "client_ip": self._get_client_ip(request),
                "user_id": user_info.get("user_id") if user_info else None,
            }

            # Add stack trace for internal errors
            if not isinstance(error, ValueError | TypeError):
                import traceback

                error_data["stack_trace"] = traceback.format_exc()

            logger.error(json.dumps(error_data))

        except Exception as e:
            logger.error(f"Error logging error: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_info(self, request: Request) -> dict[str, Any] | None:
        """Get user information from request state"""
        if hasattr(request.state, "user"):
            user = request.state.user
            return {
                "user_id": user.get("user_id"),
                "username": user.get("username"),
                "roles": user.get("roles", []),
            }
        return None

    def _filter_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Filter out sensitive headers from logs"""
        filtered = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                filtered[key] = "[REDACTED]"
            else:
                filtered[key] = value
        return filtered

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Get request body as string"""
        try:
            # Check if body has already been read
            if hasattr(request, "_body"):
                return request._body.decode("utf-8", errors="ignore")

            # For JSON content type, try to get body
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body = await request.body()
                if body:
                    return body.decode("utf-8", errors="ignore")

            return None

        except Exception as e:
            logger.debug(f"Could not read request body: {e}")
            return None
