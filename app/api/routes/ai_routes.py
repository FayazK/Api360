# app/api/routes/ai_routes.py

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.ai import ProductDescriptionRequest, ProductDescriptionResponse
from app.services.ai_service import AIService
from app.core.config import settings

router = APIRouter()

async def get_ai_service():
    return AIService(api_key=settings.OPENAI_API_KEY)

@router.post("/product-description",
             response_model=ProductDescriptionResponse,
             summary="Generate Product Description")
async def generate_product_description(
    request: ProductDescriptionRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Generate an SEO-optimized product description based on provided details.
    """
    try:
        description, keywords, seo_title = await ai_service.generate_product_description(request)
        return ProductDescriptionResponse(
            description=description,
            keywords=keywords,
            seo_title=seo_title
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating product description: {str(e)}"
        )