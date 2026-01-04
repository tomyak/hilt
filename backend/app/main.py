from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, openai, websocket

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Human-in-the-Loop LLM Proxy - Provides human oversight for LLM requests"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
