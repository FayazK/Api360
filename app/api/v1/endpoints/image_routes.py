from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional, List
from app.schemas.image import ImageConversionRequest, ImageConversionResponse, BatchImageConversionResponse, \
    BatchConversionWithIndividualOptionsRequest
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


@router.post("/batch-convert",
             response_model=BatchImageConversionResponse,
             summary="Convert Multiple Images")
async def convert_images_batch(
        files: List[UploadFile] = File(...),
        conversion_options: ImageConversionRequest = Depends(),
):
    """
    Convert multiple images with the same conversion settings.

    - **files**: List of image files to convert
    - **conversion_options**: Options for conversion and processing (applied to all images)

    Returns:
        Information about all converted images including URLs and batch statistics
    """
    image_service = ImageService()

    # Validate number of images
    if len(files) > 20:  # Limit to 20 images per request
        raise HTTPException(
            status_code=400,
            detail="Too many files. Maximum 20 files per request."
        )

    # Check total size of all files
    total_size = sum(file.size for file in files)
    if total_size > 50 * 1024 * 1024:  # 50MB total limit
        raise HTTPException(
            status_code=400,
            detail="Total file size too large. Maximum total size is 50MB"
        )

    # Process the images
    result = await image_service.process_images_batch(
        files=files,
        options=conversion_options
    )

    # Format the response according to the schema
    response = {
        "results": result["results"],
        "total_images": result["total_images"],
        "successful_conversions": result["successful_conversions"],
        "failed_conversions": result["failed_conversions"]
    }

    return response


@router.post("/batch-convert-custom",
             response_model=BatchImageConversionResponse,
             summary="Convert Multiple Images with Individual Options")
async def convert_images_with_individual_options(
        files: List[UploadFile] = File(...),
        options: BatchConversionWithIndividualOptionsRequest = Depends(),
):
    """
    Convert multiple images with individual conversion settings for each image.

    - **files**: List of image files to convert
    - **options**: JSON object with file_index and conversion_options for each file

    Returns:
        Information about all converted images including URLs and batch statistics
    """
    image_service = ImageService()

    # Validate number of images
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Too many files. Maximum 20 files per request."
        )

    # Validate total file size
    total_size = sum(file.size for file in files)
    if total_size > 50 * 1024 * 1024:  # 50MB total limit
        raise HTTPException(
            status_code=400,
            detail="Total file size too large. Maximum total size is 50MB"
        )

    # Validate all file indices are within range
    for item in options.items:
        if item.file_index < 0 or item.file_index >= len(files):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file_index: {item.file_index}. Must be between 0 and {len(files) - 1}"
            )

    # Process the images with individual options
    result = await image_service.process_images_with_individual_options(
        files=files,
        items=[{"file_index": item.file_index, "conversion_options": item.conversion_options}
               for item in options.items]
    )

    # Format the response
    response = {
        "results": result["results"],
        "total_images": result["total_images"],
        "successful_conversions": result["successful_conversions"],
        "failed_conversions": result["failed_conversions"]
    }

    return response