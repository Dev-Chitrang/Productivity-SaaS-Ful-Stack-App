import time
import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.core.logger import logger

def setup_middlewares(app) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        logger.info("request_start method=%s path=%s client=%s", request.method, request.url.path, request.client.host if request.client else "unknown")
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(
            "request_complete method=%s path=%s status=%d duration=%.2fms",
            request.method, request.url.path, response.status_code, duration
        )
        return response

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response
        
