from fastapi import APIRouter, Query, HTTPException
from app.schemas.chart import ChartData
from app.services.chart_service import create_chart
from app.services.common.exceptions import ValidationError, ServiceError

router = APIRouter()

@router.post("/", summary="Create Chart")
async def chart(
    chart_data: ChartData,
    chart_type: str = Query(..., regex="^(bar|pie|line|area)$"),
    title: str = Query(None)
):
    try:
        return await create_chart(chart_data, chart_type, title)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Service Error",
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )