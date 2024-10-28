from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import chart_routes
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(chart_routes.router, prefix="/api/charts", tags=["charts"])

app.mount("/static", StaticFiles(directory="static"), name="static")
