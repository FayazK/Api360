from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import document_routes, chart_routes
from app.api.routes import pdf_routes
from app.api.routes import ai_routes


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
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(ai_routes.router, prefix="/api/ai", tags=["ai"])

app.mount("/static", StaticFiles(directory="static"), name="static")
