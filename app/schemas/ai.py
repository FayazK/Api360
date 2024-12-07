# app/schemas/ai.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class ProductDescriptionRequest(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    product_features: Optional[List[str]] = Field(None, description="List of product features/attributes")
    product_description: Optional[str] = Field(None, description="Basic product description or details")
    image_url: Optional[HttpUrl] = Field(None, description="URL of the product image")
    target_audience: Optional[str] = Field(None, description="Target audience for the product")
    tone: Optional[str] = Field("professional", description="Tone of the description (casual, professional, luxury)")
    word_count: Optional[int] = Field(150, description="Desired word count for the description", ge=50, le=500)
    style: Optional[str] = Field("informative", description="Writing style (informative, persuasive, technical)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Ergonomic Office Chair XL-500",
                "product_features": [
                    "Adjustable lumbar support",
                    "Breathable mesh back",
                    "360-degree swivel"
                ],
                "product_description": "High-end office chair with ergonomic features",
                "image_url": "https://example.com/chair-image.jpg",
                "target_audience": "Office professionals and remote workers",
                "tone": "professional",
                "word_count": 200,
                "style": "persuasive"
            }
        }

class ProductDescriptionResponse(BaseModel):
    description: str
    keywords: List[str]
    seo_title: str
    image_analysis: Optional[dict] = None