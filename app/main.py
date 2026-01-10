"""Main FastAPI Application"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chat, traces
from app.core.config import settings
from app.db.session import engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import app.models  # Register models

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(levelname)-8s - %(name)-20s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Application starting up...")
    logger.info(f"Log level: {logging.getLevelName(logging.getLogger().level)}")
    logger.info(f"API Key configured: {'✓' if settings.API_KEY else '✗'}")
    logger.info(f"Gemini API Key configured: {'✓' if settings.GEMINI_API_KEY else '✗'}")
    
    # Sync agent model config with .env
    from app.core.startup import sync_agent_model_config
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        await sync_agent_model_config(db)
    
    yield
    # Shutdown
    logger.info("👋 Application shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

from app.api.v1 import chat, traces, stream, analytics

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["chat"])
app.include_router(stream.router, prefix=settings.API_V1_PREFIX + "/chat", tags=["streaming"])
app.include_router(traces.router, prefix=settings.API_V1_PREFIX, tags=["traces"])
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX, tags=["analytics"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }



@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Detailed health check with actual DB connectivity test"""
    from sqlalchemy import text
    from datetime import datetime
    
    try:
        # Perform a simple query to verify DB connectivity
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        status = "unhealthy"
    
    return {
        "status": status,
        "database": db_status,
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }

