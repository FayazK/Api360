from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ProductDescriptionRequest(BaseModel):
    product_features: Optional[List[str]] = Field(None, description="List of product features/attributes")
    product_description: str =  Field(None, description="Basic product description or details")
    image_url: Optional[HttpUrl] = Field(None, description="URL of the product image")
    target_audience: Optional[str] = Field(None, description="Target audience for the product")
    industry: Optional[str] = Field(None, description="Industry of the product")
    specialization: Optional[str] = Field(None, description="Specialization of the product")
    tone: Optional[str] = Field("professional", description="Tone of the description (casual, professional, luxury)")
    style: Optional[str] = Field("informative", description="Writing style (informative, persuasive, technical)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_features": [
                    "Adjustable lumbar support",
                    "Breathable mesh back",
                    "360-degree swivel"
                ],
                "product_description": "High-end office chair with ergonomic features",
                "image_url": "https://example.com/chair-image.jpg",
                "target_audience": "Office professionals and remote workers",
                "tone": "professional",
                "style": "persuasive"
            }
        }


class ProductDescriptionResponse(BaseModel):
    description: str
