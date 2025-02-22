# app/api/v1/endpoints/image_routes.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from app.schemas.image import ImageConversionRequest, ImageConversionResponse
from app.services.image_service import ImageService

router = APIRouter()


@router.post("/convert", response_model=ImageConversionResponse, summary="Convert Image Format")
async def convert_image(
        file: UploadFile = File(...),
        conversion_options: ImageConversionRequest = Depends(),
):
    """
    Convert an image from one format to another with optional processing.

    - **file**: The image file to convert
    - **conversion_options**: Options for conversion and processing

    Returns:
        Information about the converted image including URL
    """
    image_service = ImageService()

    # Check file size
    if file.size > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 20MB"
        )

    # Process the image
    result = await image_service.process_image(
        file=file,
        options=conversion_options
    )

    return result