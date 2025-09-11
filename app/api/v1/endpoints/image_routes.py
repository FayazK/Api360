from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List, Optional, Tuple
import base64
import json
from app.schemas.image import ImageConversionRequest, ImageConversionResponse, BatchImageConversionResponse, \
    BatchConversionWithIndividualOptionsRequest
from app.services.image_service import ImageService
from app.services.ai.image import ImageEngine
from app.services.ai.image.types import ImageGenerationRequest
from app.services.ai.image.drivers.replicate.registry import ReplicateModelRegistry
from app.schemas.ai_image import (
    ImageGenerationAPIRequest,
    ImageGenerationAPIResponse,
    ImageGenImage,
)
from app.core.storage_engine import get_storage_engine, StorageType
import uuid
import mimetypes
import httpx

router = APIRouter()


def validate_replicate_request(request: ImageGenerationAPIRequest) -> None:
    """Validate replicate-specific request parameters."""
    if request.provider != "replicate":
        return
    
    # Check if model is supported
    model_id = request.model
    if not model_id:
        # Use default model
        return
    
    if not ReplicateModelRegistry.is_supported(model_id):
        supported_models = list(ReplicateModelRegistry.get_supported_models())
        raise HTTPException(
            status_code=400,
            detail=f"Replicate model '{model_id}' is not supported. "
                   f"Supported models: {', '.join(supported_models)}"
        )
    
    # Get driver class for validation
    driver_class = ReplicateModelRegistry.get_driver_class(model_id)
    if not driver_class:
        return
    
    # Create a temporary driver instance for parameter validation
    try:
        driver = driver_class()
        
        # Convert API request to internal request for validation
        image_inputs = None
        if request.images_b64:
            image_inputs = []
            for b64 in request.images_b64:
                try:
                    image_inputs.append(base64.b64decode(b64))
                except Exception:
                    raise HTTPException(status_code=422, detail="Invalid base64 in images_b64")
        
        internal_request = ImageGenerationRequest(
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
        
        # Map parameters and validate
        mapped_params = driver.map_parameters(internal_request)
        driver.validate_parameters(mapped_params)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Replicate validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replicate validation failed: {str(e)}")


def validate_replicate_multipart_request(
    prompt: str,
    provider: Optional[str],
    model: Optional[str],
    ratio: Optional[str],
    negative_prompt: Optional[str],
    temperature: Optional[float],
    top_p: Optional[float],
    stop_sequences: Optional[str],
    system_prompt: Optional[str],
    safety: Optional[str],
    extra: Optional[str],
    files: Optional[List[UploadFile]] = None,
) -> None:
    """Validate replicate-specific multipart request parameters."""
    if provider != "replicate":
        return
    
    # Check if model is supported
    if model and not ReplicateModelRegistry.is_supported(model):
        supported_models = list(ReplicateModelRegistry.get_supported_models())
        raise HTTPException(
            status_code=400,
            detail=f"Replicate model '{model}' is not supported. "
                   f"Supported models: {', '.join(supported_models)}"
        )
    
    # Get driver class for validation
    model_id = model or "bytedance/seedream-4"  # Default model
    driver_class = ReplicateModelRegistry.get_driver_class(model_id)
    if not driver_class:
        return
    
    # Basic parameter validation without creating actual requests
    try:
        driver = driver_class()
        
        # Parse JSON fields for validation
        parsed_stop = None
        if stop_sequences:
            try:
                parsed = json.loads(stop_sequences)
                if not isinstance(parsed, list):
                    raise ValueError("stop_sequences must be a JSON array")
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
                    raise ValueError("extra must be a JSON object")
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid JSON for extra; expected a JSON object")
        
        # Validate file count limits
        if files:
            if model_id == "bytedance/seedream-4" and len(files) > 10:
                raise HTTPException(status_code=400, detail="Seedream-4 supports maximum 10 input images")
            elif model_id == "black-forest-labs/flux-krea-dev" and len(files) > 1:
                raise HTTPException(status_code=400, detail="FLUX Krea [dev] supports only 1 input image")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Replicate validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Replicate validation failed: {str(e)}")

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

    For Replicate provider, only specific models are supported with dedicated parameter validation:
    - bytedance/seedream-4: Advanced text-to-image and editing up to 4K
    - black-forest-labs/flux-krea-dev: Distinctive aesthetic style and realism
    
    This endpoint passes only user-specified fields to the underlying provider driver.
    """
    try:
        # Validate replicate-specific requests
        validate_replicate_request(request)
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

        # Persist output images to public storage and include local URL
        storage = get_storage_engine()
        persisted_images: List[ImageGenImage] = []

        async def fetch_image_bytes_and_mime(img) -> Tuple[Optional[bytes], Optional[str]]:
            """Return image bytes and detected MIME type, if available.

            - For b64 input, returns decoded bytes and the Provided mime_type (if any).
            - For URL input, attempts to download and returns bytes and response content-type.
            """
            if img.b64_data:
                try:
                    data = base64.b64decode(img.b64_data)
                    return data, img.mime_type
                except Exception:
                    return None, None
            if img.url:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(img.url)
                        if resp.status_code == 200:
                            ctype = resp.headers.get("content-type")
                            if ctype:
                                ctype = ctype.split(";")[0].strip()
                            return resp.content, ctype
                except Exception:
                    return None, None
            return None, None

        for img in result.images:
            original_url = img.url
            # Try to fetch; prefer detected response content-type; otherwise carry driver-provided; else default
            data, detected_mime = await fetch_image_bytes_and_mime(img)
            mime = (detected_mime or img.mime_type or "image/png").lower()
            if not data and not detected_mime and original_url:
                guessed = mimetypes.guess_type(original_url)[0]
                if guessed:
                    mime = guessed.lower()
            local_url = None
            local_path = None
            if data:
                # Pick extension from MIME if possible
                ext = mimetypes.guess_extension(mime) or ".png"
                filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    info = storage.store_bytes(
                        data=data,
                        category="images",
                        filename=filename,
                        content_type=mime,
                        storage_type=StorageType.PUBLIC,
                    )
                    local_url = info.get("url")
                    local_path = info.get("path")
                except Exception:
                    # Storage failure should not break the whole response
                    pass

            metadata = dict(img.metadata or {})
            if original_url:
                metadata.setdefault("provider_url", original_url)

            persisted_images.append(
                ImageGenImage(
                    b64_data=img.b64_data,
                    mime_type=mime,
                    url=local_url or original_url,
                    path=local_path or img.path,
                    metadata=metadata,
                )
            )

        return ImageGenerationAPIResponse(
            provider=result.provider,
            model=result.model,
            images=persisted_images,
            metadata=result.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-multipart", response_model=ImageGenerationAPIResponse, summary="Generate/Edit Images (multipart upload)")
async def generate_ai_image_multipart(
    prompt: str = Form(..., description="Main text prompt"),
    provider: Optional[str] = Form(None, description="Provider key, e.g., 'replicate', 'gemini-nano-banana' or 'imagen'"),
    model: Optional[str] = Form(None, description="Model name for the provider. For replicate: 'bytedance/seedream-4', 'black-forest-labs/flux-krea-dev'"),
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
    
    For Replicate provider, only specific models are supported with dedicated parameter validation:
    - bytedance/seedream-4: Advanced text-to-image and editing up to 4K (max 10 input images)
    - black-forest-labs/flux-krea-dev: Distinctive aesthetic style and realism (max 1 input image)
    """
    try:
        # Validate replicate-specific requests
        validate_replicate_multipart_request(
            prompt, provider, model, ratio, negative_prompt, temperature, top_p,
            stop_sequences, system_prompt, safety, extra, files
        )
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

        # Replicate-specific parameter validation (mirror JSON endpoint)
        if provider == "replicate":
            try:
                # Determine model and get driver class
                model_id = model or "bytedance/seedream-4"
                driver_class = ReplicateModelRegistry.get_driver_class(model_id)
                if driver_class:
                    driver = driver_class()
                    mapped_params = driver.map_parameters(req)
                    driver.validate_parameters(mapped_params)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Replicate validation error: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Replicate validation failed: {str(e)}")

        result = engine.generate(req)

        # Persist output images to public storage and include local URL
        storage = get_storage_engine()
        persisted_images: List[ImageGenImage] = []

        async def fetch_image_bytes_and_mime(img) -> Tuple[Optional[bytes], Optional[str]]:
            """Return image bytes and detected MIME type, if available.

            - For b64 input, returns decoded bytes and the Provided mime_type (if any).
            - For URL input, attempts to download and returns bytes and response content-type.
            """
            if img.b64_data:
                try:
                    data = base64.b64decode(img.b64_data)
                    return data, img.mime_type
                except Exception:
                    return None, None
            if img.url:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(img.url)
                        if resp.status_code == 200:
                            ctype = resp.headers.get("content-type")
                            if ctype:
                                ctype = ctype.split(";")[0].strip()
                            return resp.content, ctype
                except Exception:
                    return None, None
            return None, None

        for img in result.images:
            original_url = img.url
            data, detected_mime = await fetch_image_bytes_and_mime(img)
            mime = (detected_mime or img.mime_type or "image/png").lower()
            if not data and not detected_mime and original_url:
                guessed = mimetypes.guess_type(original_url)[0]
                if guessed:
                    mime = guessed.lower()
            local_url = None
            local_path = None
            if data:
                ext = mimetypes.guess_extension(mime) or ".png"
                filename = f"{uuid.uuid4().hex}{ext}"
                try:
                    info = storage.store_bytes(
                        data=data,
                        category="images",
                        filename=filename,
                        content_type=mime,
                        storage_type=StorageType.PUBLIC,
                    )
                    local_url = info.get("url")
                    local_path = info.get("path")
                except Exception:
                    pass

            metadata = dict(img.metadata or {})
            if original_url:
                metadata.setdefault("provider_url", original_url)

            persisted_images.append(
                ImageGenImage(
                    b64_data=img.b64_data,
                    mime_type=mime,
                    url=local_url or original_url,
                    path=local_path or img.path,
                    metadata=metadata,
                )
            )

        return ImageGenerationAPIResponse(
            provider=result.provider,
            model=result.model,
            images=persisted_images,
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
