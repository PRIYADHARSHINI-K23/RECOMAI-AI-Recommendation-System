import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.database.session import init_db, check_db_connection, SessionLocal, engine
from app.database.seed_data import seed_database
from app.api import api_router
from app.ai.max_service import max_service
from app.mojo.bridge import mojo_bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("recomai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown lifespan hook."""
    logger.info("Initializing RECOMAI database schema...")
    try:
        init_db()
        # Seed initial dataset if database is empty
        with SessionLocal() as db:
            seed_database(db)
        logger.info("RECOMAI database ready.")
    except Exception as e:
        logger.error("Database initialization notice: %s", str(e))

    logger.info("RECOMAI Recommendation Engine initialized.")
    yield
    # Ensure all DB connections are closed on shutdown
    engine.dispose()
    logger.info("RECOMAI shutting down.")

app = FastAPI(
    title="RECOMAI - AI Recommendation System",
    description="Discover what fits you, powered by intelligence. CSE Final Year & Portfolio Architecture.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/api/v1/health")
def health_check():
    """System health check and component diagnostics."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "database": check_db_connection(),
        "max_ai": max_service.get_status(),
        "mojo": mojo_bridge.get_status(),
    }

# Mount Frontend Static Assets
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse({"message": "RECOMAI API online. Frontend index not found."})

    # Fallback to index.html for client-side SPA routing
    @app.get("/{full_path:path}")
    async def catch_all_spa(full_path: str):
        # Don't hijack API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
            
        index_path = FRONTEND_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse({"message": "RECOMAI API online."})
