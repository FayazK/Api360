from fastapi import APIRouter, Depends, HTTPException
from fastapi.logger import logger
from app.core.config import settings
from app.schemas.ai.product import ProductDescriptionResponse, ProductDescriptionRequest
from app.services.ai.base import AIService

router = APIRouter()

async def get_ai_service():
    return AIService(api_key=settings.ANTHROPIC_API_KEY)

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
    except HTTPException as he:
        # Re-raise HTTP exceptions as they already have proper error formatting
        raise he
    except Exception as e:
        logger.error(f"Error in product description endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the product description."
        )