from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.core.rate_limit import limiter
from app.api.v1 import auth, openai, websocket

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Human-in-the-Loop LLM Proxy - Provides human oversight for LLM requests"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with restricted methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Middleware to limit request body size"""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": f"Request body too large. Maximum size is {settings.MAX_REQUEST_SIZE} bytes"}
        )
    return await call_next(request)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(openai.router, prefix="/v1", tags=["OpenAI Compatible"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.request_manager import request_manager
    from app.services.websocket_manager import websocket_manager

    stats = request_manager.get_stats()
    stats["active_connections"] = websocket_manager.get_connection_count()
    stats["status"] = "healthy"

    return stats


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"Request timeout: {settings.REQUEST_TIMEOUT_SECONDS} seconds")
    print(f"CORS origins: {settings.cors_origins_list}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("Shutting down HILT backend")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": "Human-in-the-Loop LLM Proxy",
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth/login",
            "openai": "/v1/chat/completions",
            "websocket": "/ws?token=<jwt_token>"
        }
    }
