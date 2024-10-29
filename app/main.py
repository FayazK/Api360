from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import document_routes, chart_routes

app = FastAPI(title=settings.PROJECT_NAME)

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

app.mount("/static", StaticFiles(directory="static"), name="static")
