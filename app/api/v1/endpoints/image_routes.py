from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List, Optional
import base64
import json
from app.schemas.image import ImageConversionRequest, ImageConversionResponse, BatchImageConversionResponse, \
    BatchConversionWithIndividualOptionsRequest
from app.services.image_service import ImageService
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest
from app.schemas.ai_image import (
    ImageGenerationAPIRequest,
    ImageGenerationAPIResponse,
    ImageGenImage,
)

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


@router.post("/generate", response_model=ImageGenerationAPIResponse, summary="Generate or Edit Images (AI)")
async def generate_ai_image(
    request: ImageGenerationAPIRequest,
):
    """
    Generate or edit images using pluggable AI image providers.

    - Required: `prompt`
    - Optional: `provider`, `model`, `ratio`, `negative_prompt`, `temperature`, `top_p`, `stop_sequences`,
      `system_prompt`, `safety`, `images_b64` (for image→image / multi-image fusion), and `extra`.

    This endpoint passes only user-specified fields to the underlying provider driver.
    """
    try:
        # Decode input images from base64 if provided
        image_inputs: Optional[List[bytes]] = None
        if request.images_b64:
            image_inputs = []
            for b64 in request.images_b64:
                try:
                    image_inputs.append(base64.b64decode(b64))
                except Exception:
                    raise HTTPException(status_code=422, detail="Invalid base64 in images_b64")

        engine = ImageEngine()  # No default provider to honor pass-through policy
        req = ImageGenerationRequest(
            prompt=request.prompt,
            provider=request.provider,
            model=request.model,
            ratio=request.ratio,
            negative_prompt=request.negative_prompt,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop_sequences,
            system_prompt=request.system_prompt,
            safety=request.safety,
            image_inputs=image_inputs,
            extra=request.extra or {},
        )

        result = engine.generate(req)

    return ImageGenerationAPIResponse(
        provider=result.provider,
        model=result.model,
        images=[
            ImageGenImage(
                b64_data=img.b64_data,
                mime_type=img.mime_type,
                url=img.url,
                path=img.path,
                metadata=img.metadata,
            )
            for img in result.images
        ],
        metadata=result.metadata,
    )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-multipart", response_model=ImageGenerationAPIResponse, summary="Generate/Edit Images (multipart upload)")
async def generate_ai_image_multipart(
    prompt: str = Form(..., description="Main text prompt"),
    provider: Optional[str] = Form(None, description="Provider key, e.g., 'gemini-nano-banana' or 'imagen'"),
    model: Optional[str] = Form(None, description="Model name for the provider"),
    ratio: Optional[str] = Form(None, description="Aspect ratio guidance, e.g., '1:1', '16:9'"),
    negative_prompt: Optional[str] = Form(None, description="What to avoid in the image"),
    temperature: Optional[float] = Form(None),
    top_p: Optional[float] = Form(None),
    stop_sequences: Optional[str] = Form(None, description="JSON array of stop sequences"),
    system_prompt: Optional[str] = Form(None),
    safety: Optional[str] = Form(None, description="JSON object for safety settings"),
    extra: Optional[str] = Form(None, description="JSON object of provider-specific params"),
    files: Optional[List[UploadFile]] = File(None, description="One or more input images for image→image or composition"),
    mask: Optional[UploadFile] = File(None, description="Optional mask image for inpainting (driver support varies)"),
):
    """
    Multipart variant of the image generation endpoint.

    - Upload one or more images via `files` for image→image or multi-image fusion.
    - Provide other parameters as form fields; `stop_sequences`, `safety`, and `extra` accept JSON strings.
    """
    try:
        # Parse JSON-ish fields
        parsed_stop = None
        if stop_sequences:
            try:
                parsed = json.loads(stop_sequences)
                if not isinstance(parsed, list):
                    raise ValueError
                parsed_stop = parsed
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for stop_sequences; expected a JSON array")

        parsed_safety = None
        if safety:
            try:
                parsed_safety = json.loads(safety)
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for safety; expected a JSON object")

        parsed_extra = {}
        if extra:
            try:
                parsed_extra = json.loads(extra)
                if not isinstance(parsed_extra, dict):
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for extra; expected a JSON object")

        # Read uploaded files
        image_inputs: Optional[List[bytes]] = None
        if files:
            if len(files) > 10:
                raise HTTPException(status_code=400, detail="Too many files. Maximum 10 allowed.")
            image_inputs = []
            for f in files:
                try:
                    image_inputs.append(await f.read())
                except Exception:
                    raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {f.filename}")

        # Optional mask
        mask_bytes = None
        if mask is not None:
            try:
                mask_bytes = await mask.read()
            except Exception:
                raise HTTPException(status_code=400, detail="Failed to read mask file")

        engine = ImageEngine()
        req = ImageGenerationRequest(
            prompt=prompt,
            provider=provider,
            model=model,
            ratio=ratio,
            negative_prompt=negative_prompt,
            temperature=temperature,
            top_p=top_p,
            stop=parsed_stop,
            system_prompt=system_prompt,
            safety=parsed_safety,
            image_inputs=image_inputs,
            mask=mask_bytes,
            extra=parsed_extra,
        )

        result = engine.generate(req)

        return ImageGenerationAPIResponse(
            provider=result.provider,
            model=result.model,
            images=[
                ImageGenImage(
                    b64_data=img.b64_data,
                    mime_type=img.mime_type,
                    url=img.url,
                    path=img.path,
                    metadata=img.metadata,
                )
                for img in result.images
            ],
            metadata=result.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image generation (multipart) failed: {str(e)}")


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
