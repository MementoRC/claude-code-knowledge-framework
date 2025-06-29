"""Rate Limiting Middleware for UCKN API"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Dict

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from ..dependencies import get_settings

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm"""
    
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        
        # In-memory storage for rate limiting
        # In production, this should use Redis or similar distributed cache
        self._request_counts: Dict[str, deque] = defaultdict(deque)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Rate limit configurations per endpoint type
        self.rate_limits = {
            'default': {
                'requests': self.settings.rate_limit_requests,
                'window': self.settings.rate_limit_window
            },
            'search': {
                'requests': 50,  # More restrictive for search endpoints
                'window': 60
            },
            'analysis': {
                'requests': 10,  # Very restrictive for analysis endpoints
                'window': 60
            },
            'upload': {
                'requests': 20,  # Moderate for upload endpoints
                'window': 60
            }
        }
        
        # Endpoint patterns and their rate limit types
        self.endpoint_patterns = {
            '/api/v1/patterns/search': 'search',
            '/api/v1/projects/analyze': 'analysis',
            '/api/v1/patterns/': 'upload',  # POST to patterns
            '/api/v1/projects/': 'upload',  # POST to projects
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process rate limiting for incoming requests"""
        
        # Skip rate limiting if disabled
        if not self.settings.rate_limit_enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path.startswith('/health'):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit configuration for this endpoint
        rate_limit_config = self._get_rate_limit_config(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(
            client_id, rate_limit_config
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_id} on {request.url.path}"
            )
            return self._rate_limit_response(remaining, reset_time)
        
        # Record request
        await self._record_request(client_id, rate_limit_config)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit_config['requests'])
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["X-RateLimit-Window"] = str(rate_limit_config['window'])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get user ID from authentication state
        if hasattr(request.state, 'user'):
            user_id = request.state.user.get('user_id')
            if user_id:
                return f"user:{user_id}"
        
        # Try to get API key
        if hasattr(request.state, 'api_key'):
            api_key = request.state.api_key
            if api_key:
                # Use a hash of the API key for privacy
                import hashlib
                return f"api:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # Fall back to IP address
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            request.client.host if request.client else "unknown"
        )
        
        return f"ip:{client_ip}"
    
    def _get_rate_limit_config(self, request: Request) -> Dict[str, int]:
        """Get rate limit configuration for the endpoint"""
        path = request.url.path
        method = request.method
        
        # Check for specific endpoint patterns
        for pattern, limit_type in self.endpoint_patterns.items():
            if pattern in path:
                # For POST requests to base endpoints, use upload limits
                if pattern.endswith('/') and method == 'POST':
                    return self.rate_limits[limit_type]
                elif not pattern.endswith('/'):
                    return self.rate_limits[limit_type]
        
        # Default rate limit
        return self.rate_limits['default']
    
    async def _check_rate_limit(self, client_id: str, config: Dict[str, int]) -> tuple:
        """Check if client has exceeded rate limit"""
        async with self._locks[client_id]:
            current_time = time.time()
            window_start = current_time - config['window']
            
            # Get request history for this client
            requests = self._request_counts[client_id]
            
            # Remove old requests outside the window
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check if under limit
            remaining = config['requests'] - len(requests)
            is_allowed = remaining > 0
            
            # Calculate reset time (when the oldest request will expire)
            reset_time = int(requests[0] + config['window']) if requests else int(current_time)
            
            return is_allowed, remaining, reset_time
    
    async def _record_request(self, client_id: str, config: Dict[str, int]):
        """Record a new request for the client"""
        async with self._locks[client_id]:
            current_time = time.time()
            self._request_counts[client_id].append(current_time)
    
    def _rate_limit_response(self, remaining: int, reset_time: int) -> Response:
        """Return rate limit exceeded response"""
        retry_after = max(0, reset_time - int(time.time()))
        
        response_body = {
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after_seconds": retry_after,
            "status_code": 429
        }
        
        return Response(
            content=str(response_body).replace("'", '"'),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={
                "Content-Type": "application/json",
                "Retry-After": str(retry_after),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time)
            }
        )
    
    async def cleanup_old_entries(self):
        """Periodic cleanup of old rate limit entries"""
        """This would be called by a background task in production"""
        current_time = time.time()
        max_window = max(config['window'] for config in self.rate_limits.values())
        cutoff_time = current_time - max_window * 2  # Keep some buffer
        
        for client_id in list(self._request_counts.keys()):
            async with self._locks[client_id]:
                requests = self._request_counts[client_id]
                
                # Remove old requests
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # Remove empty entries
                if not requests:
                    del self._request_counts[client_id]
                    del self._locks[client_id]


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int, limit: int, window: int):
        self.retry_after = retry_after
        self.limit = limit
        self.window = window
        super().__init__(f"Rate limit exceeded: {limit} requests per {window} seconds")
