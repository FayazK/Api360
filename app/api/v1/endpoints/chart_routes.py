from fastapi import APIRouter, Query, HTTPException
from app.schemas.chart import ChartData
from app.services.chart_service import create_chart
from app.services.common.exceptions import ValidationError, ServiceError
from app.core.storage_engine import get_storage_engine, StorageType
import uuid

router = APIRouter()

@router.post("/", summary="Create Chart")
async def chart(
    chart_data: ChartData,
    chart_type: str = Query(..., pattern="^(bar|pie|line|area)$"),
    title: str = Query(None)
):
    try:
        svg_data = await create_chart(chart_data, chart_type, title)
        filename = f"{uuid.uuid4()}.svg"
        storage = get_storage_engine()
        file_info = storage.store_bytes(
            data=svg_data,
            category="charts",
            filename=filename,
            content_type="image/svg+xml",
            storage_type=StorageType.PUBLIC,
        )
        return {"url": file_info["url"]}
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
