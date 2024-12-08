# app/api/routes/ai_routes.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger

from app.schemas.ai import ProductDescriptionRequest, ProductDescriptionResponse
from app.services.ai_service import AIService
from app.core.config import settings

router = APIRouter()

async def get_ai_service():
    return AIService(api_key=settings.ANTHROPIC_API_KEY)

@router.post("/product-description",
             response_model=ProductDescriptionResponse,
             summary="Generate Product Description")
@router.post("/product-description",
             response_model=ProductDescriptionResponse,
             summary="Generate Product Description")
async def generate_product_description(
    request: ProductDescriptionRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Generate an SEO-optimized product description based on provided details."""
    try:
        description = await ai_service.generate_product_description(request)
        return ProductDescriptionResponse(description=description)
    except Exception as e:
        logger.error(f"Error in product description endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )