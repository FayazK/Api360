from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ProductDescriptionRequest(BaseModel):
    product_description: str = Field(..., description="Basic product description or details")  # Made required
    image_url: HttpUrl = Field(..., description="URL of the product image")  # Made required
    target_audience: Optional[str] = Field(None, description="Target audience for the product")
    industry: Optional[str] = Field(None, description="Industry of the product")
    specialization: Optional[str] = Field(None, description="Specialization of the product")
    tone: Optional[str] = Field("professional", description="Tone of the description (casual, professional, luxury)")
    style: Optional[str] = Field("informative", description="Writing style (informative, persuasive, technical)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_description": "High-end office chair with ergonomic features",
                "image_url": "https://example.com/chair-image.jpg",
                "target_audience": "Office professionals and remote workers",
                "tone": "professional",
                "style": "persuasive"
            }
        }

class ProductDescriptionResponse(BaseModel):
    description: str
