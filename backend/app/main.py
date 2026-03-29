"""FastAPI application entry point."""
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.api import programs, targets, approvals, plugins, flows, coverage, intel, credentials, credential_engine, mixed_mode, custom_headers, reporting, findings, jobs, slack, hypotheses, learning
from app.api import program_parser, app_settings, verify

try:
    from app.services.grpc_credential_server import serve as serve_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("gRPC credential server not available - protobuf dependencies missing")

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


grpc_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global grpc_task
    logger.info("Starting Bug Bounty Automator API")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if GRPC_AVAILABLE:
        grpc_task = asyncio.create_task(serve_grpc(50051))
        logger.info("Started gRPC credential server on port 50051")
    
    yield
    
    logger.info("Shutting down Bug Bounty Automator API")
    if grpc_task:
        grpc_task.cancel()
        try:
            await grpc_task
        except asyncio.CancelledError:
            pass
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
app.include_router(credentials.router, prefix="/api")
app.include_router(credential_engine.router, prefix="/api")
app.include_router(mixed_mode.router, prefix="/api")
app.include_router(custom_headers.router, prefix="/api")
app.include_router(reporting.router, prefix="/api")
app.include_router(program_parser.router, prefix="/api")
app.include_router(findings.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(slack.router, prefix="/api")
app.include_router(app_settings.router, prefix="/api")
app.include_router(verify.router, prefix="/api")
app.include_router(hypotheses.router, prefix="/api")
app.include_router(learning.router, prefix="/api")


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
            "program_parse": "/api/programs/parse",
            "targets": "/api/targets",
            "approvals": "/api/approvals",
            "plugins": "/api/plugins",
            "flows": "/api/flows",
            "coverage": "/api/coverage",
            "intel": "/api/intel",
            "credentials": "/api/credentials",
        },
    }
