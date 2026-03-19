"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.api import programs, targets, approvals, plugins, flows, coverage, intel

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Bug Bounty Automator API")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    logger.info("Shutting down Bug Bounty Automator API")
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Semi-automated bug hunting platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(programs.router, prefix="/api")
app.include_router(targets.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(plugins.router, prefix="/api")
app.include_router(flows.router, prefix="/api")
app.include_router(coverage.router, prefix="/api")
app.include_router(intel.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api")
async def api_info():
    return {
        "version": "1.0",
        "endpoints": {
            "programs": "/api/programs",
            "targets": "/api/targets",
            "approvals": "/api/approvals",
            "plugins": "/api/plugins",
            "flows": "/api/flows",
            "coverage": "/api/coverage",
            "intel": "/api/intel",
        },
    }
