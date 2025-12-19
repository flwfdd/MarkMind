"""MarkMind Backend - Main Application Entry Point"""

from contextlib import asynccontextmanager

from app.api import chat, graph, ingest
from app.database import db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting MarkMind Backend...")
    db.connect()
    print("Database connected")
    yield
    # Shutdown
    print("Shutting down...")
    db.disconnect()


app = FastAPI(
    title="MarkMind Backend",
    description="Local knowledge base system with Graph RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(graph.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "MarkMind Backend is running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    try:
        db.connect()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {"status": "ok", "database": db_status}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="debug",
    )
