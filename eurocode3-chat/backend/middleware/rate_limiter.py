"""
Rate Limiting Middleware for FastAPI.
Implements token bucket algorithm with Redis-like in-memory storage.
"""
import time
from typing import Dict, Optional, Callable, Any
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting."""
    tokens: float
    last_update: float
    max_tokens: int
    refill_rate: float  # tokens per second

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        now = time.time()

        # Refill tokens based on time elapsed
        time_passed = now - self.last_update
        self.tokens = min(
            self.max_tokens,
            self.tokens + time_passed * self.refill_rate
        )
        self.last_update = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def time_until_available(self) -> float:
        """Calculate seconds until a token is available."""
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.refill_rate


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.
    Thread-safe for async operations.
    """

    def __init__(
        self,
        requests_per_minute: int = 30,
        requests_per_hour: int = 500,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size

        # Separate buckets for different time windows
        self._minute_buckets: Dict[str, RateLimitBucket] = {}
        self._hour_buckets: Dict[str, RateLimitBucket] = {}
        self._lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get real IP from headers (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        return request.client.host if request.client else "unknown"

    async def is_allowed(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limits.
        Returns (allowed, info_dict).
        """
        client_id = self._get_client_id(request)

        async with self._lock:
            # Initialize buckets if needed
            if client_id not in self._minute_buckets:
                self._minute_buckets[client_id] = RateLimitBucket(
                    tokens=self.burst_size,
                    last_update=time.time(),
                    max_tokens=self.burst_size,
                    refill_rate=self.requests_per_minute / 60
                )

            if client_id not in self._hour_buckets:
                self._hour_buckets[client_id] = RateLimitBucket(
                    tokens=self.requests_per_hour,
                    last_update=time.time(),
                    max_tokens=self.requests_per_hour,
                    refill_rate=self.requests_per_hour / 3600
                )

            minute_bucket = self._minute_buckets[client_id]
            hour_bucket = self._hour_buckets[client_id]

            # Check both rate limits
            minute_ok = minute_bucket.consume(1)
            hour_ok = hour_bucket.consume(1) if minute_ok else False

            info = {
                "client_id": client_id,
                "minute_remaining": int(minute_bucket.tokens),
                "hour_remaining": int(hour_bucket.tokens),
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour,
            }

            if not minute_ok:
                info["retry_after"] = minute_bucket.time_until_available()
                info["exceeded"] = "minute"
            elif not hour_ok:
                info["retry_after"] = hour_bucket.time_until_available()
                info["exceeded"] = "hour"

            return (minute_ok and hour_ok), info

    async def cleanup_old_buckets(self):
        """Remove stale bucket entries."""
        async with self._lock:
            now = time.time()
            stale_threshold = 3600  # 1 hour

            for buckets in [self._minute_buckets, self._hour_buckets]:
                stale_keys = [
                    k for k, v in buckets.items()
                    if now - v.last_update > stale_threshold
                ]
                for key in stale_keys:
                    del buckets[key]

    def get_rate_limit_headers(self, info: Dict[str, Any]) -> Dict[str, str]:
        """Generate rate limit headers for response."""
        headers = {
            "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
            "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
            "X-RateLimit-Remaining-Minute": str(info.get("minute_remaining", 0)),
            "X-RateLimit-Remaining-Hour": str(info.get("hour_remaining", 0)),
        }

        if "retry_after" in info:
            headers["Retry-After"] = str(int(info["retry_after"]) + 1)

        return headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/"]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through rate limiter."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(request)
        headers = self.rate_limiter.get_rate_limit_headers(info)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Please wait {int(info.get('retry_after', 60))} seconds.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": info.get("retry_after", 60)
                },
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


def rate_limit(
    requests_per_minute: int = 10,
    requests_per_hour: int = 100
):
    """
    Decorator for endpoint-specific rate limiting.
    Use for fine-grained control on specific endpoints.
    """
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour
    )

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            allowed, info = await limiter.is_allowed(request)

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Retry after {int(info.get('retry_after', 60))} seconds.",
                    headers=limiter.get_rate_limit_headers(info)
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
