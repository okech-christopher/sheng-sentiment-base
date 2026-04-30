"""Middleware for Sheng-Native API.

This module provides request logging, timing, and performance monitoring
to ensure <100ms latency targets are met.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and timing."""
    
    def __init__(self, app, latency_threshold: float = 100.0):
        """Initialize middleware.
        
        Args:
            app: FastAPI application
            latency_threshold: Latency threshold in ms for warnings
        """
        super().__init__(app)
        self.latency_threshold = latency_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging and timing.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with timing headers
        """
        start_time = time.time()
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate timing
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Add timing headers
        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))
        
        # Log completion
        if duration_ms > self.latency_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.latency_threshold}ms)"
            )
        else:
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"in {duration_ms:.2f}ms"
            )
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and alerts."""
    
    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.request_count = 0
        self.total_time = 0.0
        self.error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance tracking.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with performance metrics
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Update metrics
            end_time = time.time()
            duration = end_time - start_time
            self.request_count += 1
            self.total_time += duration
            
            # Add performance headers
            avg_time = self.total_time / self.request_count
            response.headers["X-Avg-Response-Time-Ms"] = str(round(avg_time * 1000, 2))
            response.headers["X-Request-Count"] = str(self.request_count)
            
            return response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Request error: {request.method} {request.url.path} - {str(e)}")
            
            # Return error response with metrics
            error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "metrics": {
                        "request_count": self.request_count,
                        "error_rate": round(error_rate, 4),
                        "avg_response_time_ms": round((self.total_time / self.request_count) * 1000, 2) if self.request_count > 0 else 0
                    }
                }
            )
    
    def get_metrics(self) -> dict:
        """Get current performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        avg_time = self.total_time / self.request_count if self.request_count > 0 else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        
        return {
            "request_count": self.request_count,
            "total_time_seconds": round(self.total_time, 3),
            "avg_response_time_ms": round(avg_time * 1000, 2),
            "error_count": self.error_count,
            "error_rate": round(error_rate, 4)
        }
