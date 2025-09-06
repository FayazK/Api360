from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.api.v1.endpoints import document_routes, chart_routes, pdf_routes, image_routes, ai_routes
from app.core.config import settings
from app.core.storage_engine import init_storage_engine, get_storage_engine
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize storage engine
    init_storage_engine(settings)
    
    # Start background cleanup task
    async def cleanup_task():
        while True:
            try:
                storage = get_storage_engine()
                await storage.async_cleanup_temp_files()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                print(f"Cleanup task error: {e}")
                await asyncio.sleep(3600)
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown: Cancel background tasks
    cleanup_task_handle.cancel()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_routes.router, prefix="/api/documents", tags=["documents"])
app.include_router(chart_routes.router, prefix="/api/charts", tags=["charts"])
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(image_routes.router, prefix="/api/images", tags=["images"])
app.include_router(ai_routes.router, prefix="/api/ai", tags=["ai"])

# Mount static files - keep for legacy support and add new storage endpoint
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/storage", StaticFiles(directory="storage/public"), name="storage")


@app.get("/api/storage/stats")
async def get_storage_stats():
    """Get storage statistics."""
    storage = get_storage_engine()
    return storage.get_storage_stats()


@app.post("/api/storage/cleanup")
async def cleanup_storage(background_tasks: BackgroundTasks):
    """Trigger manual storage cleanup."""
    storage = get_storage_engine()
    background_tasks.add_task(storage.async_cleanup_temp_files)
    return {"message": "Cleanup task started"}
