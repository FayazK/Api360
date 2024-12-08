from fastapi import APIRouter, Query
from app.schemas.chart import ChartData
from app.services.chart_service import create_chart

router = APIRouter()

@router.post("/", summary="Create Chart")
async def chart(
    chart_data: ChartData,
    chart_type: str = Query(..., regex="^(bar|pie|line|area)$"),
    title: str = Query(None)
):
    return await create_chart(chart_data, chart_type, title)