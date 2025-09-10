import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.api.v1.endpoints import (
    chart_router,
    document_router,
    pdf_router,
    image_router,
    ai_router,
)
from app.core.config import Settings, settings
from app.core.storage_engine import init_storage_engine, get_storage_engine
from app.core.middleware import UploadSizeLimitMiddleware
from app.services.ai.factory import AITextGeneratorFactory
from app.core.logging_config import setup_logging
from loguru import logger as loguru_logger


logger = logging.getLogger("app")


def _lifespan_factory(app_settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialize Loguru logging: storage/logs/fastapi.log
        setup_logging(app_settings.STORAGE_BASE_PATH)
        # Startup: Initialize storage engine
        init_storage_engine(app_settings)

        # Start background cleanup task
        async def cleanup_task():
            while True:
                try:
                    storage = get_storage_engine()
                    await storage.async_cleanup_temp_files()
                except Exception as e:
                    logger.exception(f"Cleanup task error: {e}")
                await asyncio.sleep(3600)  # Run every hour

        cleanup_task_handle = asyncio.create_task(cleanup_task())

        # Initialize AI service if providers configured
        try:
            if AITextGeneratorFactory.is_service_available():
                app.state.ai_service = await AITextGeneratorFactory.initialize_service()
        except Exception as e:
            logger.warning(f"AI service initialization skipped/unavailable: {e}")

        yield

        # Shutdown: Cancel background tasks
        cleanup_task_handle.cancel()

    return lifespan


def create_app(app_settings: Settings | None = None) -> FastAPI:
    s = app_settings or settings
    app = FastAPI(title=s.PROJECT_NAME, lifespan=_lifespan_factory(s), debug=True)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(s.BACKEND_CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Upload size limit middleware
    app.add_middleware(UploadSizeLimitMiddleware, max_bytes=int(s.MAX_UPLOAD_SIZE))

    # Routers
    app.include_router(document_router, prefix="/api/documents", tags=["documents"])
    app.include_router(chart_router, prefix="/api/charts", tags=["charts"])
    app.include_router(pdf_router, prefix="/api/pdf", tags=["pdf"])
    app.include_router(image_router, prefix="/api/images", tags=["images"])
    app.include_router(ai_router, prefix="/api/ai", tags=["ai"])

    # Public storage mount
    app.mount("/storage", StaticFiles(directory="storage/public"), name="storage")

    @app.get("/api/storage/stats")
    async def get_storage_stats():
        storage = get_storage_engine()
        return storage.get_storage_stats()

    @app.post("/api/storage/cleanup")
    async def cleanup_storage(background_tasks: BackgroundTasks):
        storage = get_storage_engine()
        background_tasks.add_task(storage.async_cleanup_temp_files)
        return {"message": "Cleanup task started"}
    
    # Register global exception handlers
    async def unhandled_exception_handler(request: Request, exc: Exception):
        loguru_logger.exception(f"Unhandled exception for {request.method} {request.url}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Log HTTPExceptions as well (to capture 4xx/5xx raised intentionally)
    from fastapi import HTTPException

    async def http_exception_handler(request: Request, exc: HTTPException):
        # Use warning for 4xx, error for 5xx
        if 500 <= exc.status_code:
            loguru_logger.error(f"HTTP {exc.status_code} on {request.method} {request.url}: {exc.detail}")
        else:
            loguru_logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url}: {exc.detail}")
        # Defer to default JSON structure
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.add_exception_handler(HTTPException, http_exception_handler)

    return app


app = create_app()
