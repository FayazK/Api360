import os
import uuid
from typing import Optional, Dict, Any, Tuple, BinaryIO, List
from fastapi import UploadFile, HTTPException
from pathlib import Path
from wand.image import Image
from wand.color import Color
import mimetypes
from fastapi.logger import logger

from app.core.config import settings
from app.schemas.image import (
    ImageFormat, ResizeMode, CompressionType, CropPosition,
    ImageConversionRequest
)


class ImageService:
    """Service for handling image conversion and processing."""

    # Supported MIME types and their extensions
    SUPPORTED_MIMETYPES = {
        'image/jpeg': ['jpg', 'jpeg'],
        'image/png': ['png'],
        'image/webp': ['webp'],
        'image/gif': ['gif'],
        'image/tiff': ['tiff', 'tif'],
        'image/bmp': ['bmp'],
        'image/svg+xml': ['svg'],
        'image/heif': ['heif', 'heic'],
        'image/avif': ['avif']
    }

    def __init__(self):
        """Initialize the image service."""
        self.output_dir = Path(settings.CHART_SAVE_DIR)  # Reuse existing setting
        self.output_url_path = settings.CHART_URL_PATH

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate_image(self, file: UploadFile) -> str:
        """Validate if the uploaded file is a supported image format.

        Args:
            file: The uploaded file to validate

        Returns:
            str: The detected MIME type of the image

        Raises:
            HTTPException: If the file is not a supported image format
        """
        # Get content type from the file or try to guess from filename
        content_type = file.content_type or mimetypes.guess_type(file.filename)[0]

        # Check if content type is supported
        if not content_type or content_type not in self.SUPPORTED_MIMETYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {content_type}. Supported formats: {', '.join(self.SUPPORTED_MIMETYPES.keys())}"
            )

        return content_type

    async def process_image(
            self,
            file: UploadFile,
            options: ImageConversionRequest
    ) -> Dict[str, Any]:
        """Process an image according to the specified options.

        Args:
            file: The uploaded image file
            options: Image conversion and processing options

        Returns:
            Dict containing information about the processed image
        """
        # Validate file format
        self.validate_image(file)

        # Read image data
        image_data = await file.read()

        try:
            # Generate filename for output
            original_filename = file.filename
            filename_base = Path(original_filename).stem
            output_format = options.output_format.lower()
            unique_id = str(uuid.uuid4())[:8]
            output_filename = f"{filename_base}_{unique_id}.{output_format}"
            output_path = self.output_dir / output_filename

            # Process image with Wand
            with Image(blob=image_data) as img:
                # Simple format conversion if convert_only is True
                if options.convert_only:
                    img.format = output_format.upper()
                else:
                    # Apply transformations based on options
                    self._apply_transformations(img, options)

                # Save the processed image
                img.save(filename=str(output_path))

                # Get image information for response
                response_data = {
                    "url": f"{self.output_url_path}/{output_filename}",
                    "format": output_format,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": os.path.getsize(output_path),
                    "original_filename": original_filename
                }

            return response_data

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing image: {str(e)}"
            )

    def _apply_transformations(self, img: Image, options: ImageConversionRequest) -> None:
        """Apply various image transformations based on the options.

        Args:
            img: Wand Image object to transform
            options: Configuration options for transformations
        """
        # Auto-orient based on EXIF data
        if options.auto_orient:
            img.auto_orient()

        # Apply cropping if requested
        if options.crop and options.crop_width and options.crop_height:
            self._apply_crop(img, options)

        # Apply resizing if requested
        if options.resize and (options.width or options.height):
            self._apply_resize(img, options)

        # Set compression type and quality
        if options.compression_type:
            compression = options.compression_type == CompressionType.LOSSLESS
            if options.output_format in ['jpg', 'jpeg', 'webp']:
                img.compression_quality = options.quality or 85
                if options.output_format == 'webp':
                    img.options['webp:lossless'] = 'true' if compression else 'false'
            elif options.output_format == 'png' and compression:
                img.options['png:compression-level'] = '9'  # Maximum compression for PNG

        # Strip metadata if requested
        if options.strip_metadata:
            img.strip()

        # Set background color for transparent images if specified
        if options.background_color and img.alpha_channel:
            bg_color = Color(options.background_color)
            img.background_color = bg_color
            img.alpha_channel = 'remove'

        # Apply sharpening if requested
        if options.sharpen:
            img.sharpen(radius=0, sigma=1.0)

        # Set output format
        img.format = options.output_format.upper()

    def _apply_crop(self, img: Image, options: ImageConversionRequest) -> None:
        """Apply cropping based on options.

        Args:
            img: Wand Image object to crop
            options: Configuration options for cropping
        """
        width, height = img.width, img.height
        crop_width, crop_height = options.crop_width, options.crop_height

        # Ensure crop dimensions don't exceed image dimensions
        crop_width = min(crop_width, width)
        crop_height = min(crop_height, height)

        # Calculate crop position
        if options.crop_position == CropPosition.CUSTOM and options.crop_x is not None and options.crop_y is not None:
            # Use custom coordinates
            left = options.crop_x
            top = options.crop_y
        else:
            # Calculate position based on named positions
            left, top = self._calculate_crop_position(
                width, height, crop_width, crop_height, options.crop_position or CropPosition.CENTER
            )

        # Apply crop
        img.crop(left=left, top=top, width=crop_width, height=crop_height)

    def _apply_resize(self, img: Image, options: ImageConversionRequest) -> None:
        """Apply resizing based on options.

        Args:
            img: Wand Image object to resize
            options: Configuration options for resizing
        """
        width, height = options.width, options.height

        # If only one dimension is specified, calculate the other based on aspect ratio
        if width is None and height is not None:
            width = int(img.width * (height / img.height))
        elif height is None and width is not None:
            height = int(img.height * (width / img.width))

        # Apply resize based on mode
        if options.resize_mode == ResizeMode.PRESERVE_RATIO:
            img.resize(width=width, height=height, filter='lanczos', preserve_aspect_ratio=True)
        elif options.resize_mode == ResizeMode.STRETCH:
            img.resize(width=width, height=height, filter='lanczos')
        elif options.resize_mode == ResizeMode.PAD:
            # Preserve aspect ratio and pad with background color
            background = Color('white')
            if options.background_color:
                background = Color(options.background_color)

            # Create a new image with the target dimensions
            with Image(width=width, height=height, background=background) as padded_img:
                # Calculate scaled dimensions preserving aspect ratio
                scale = min(width / img.width, height / img.height)
                scaled_width = int(img.width * scale)
                scaled_height = int(img.height * scale)

                # Resize the original image
                img.resize(width=scaled_width, height=scaled_height, filter='lanczos')

                # Calculate position to center the resized image
                left = (width - scaled_width) // 2
                top = (height - scaled_height) // 2

                # Paste the resized image onto the padded image
                padded_img.composite(img, left=left, top=top)

                # Copy the padded image back to the original
                img.size = padded_img.size
                img.import_pixels(width=width, height=height,
                                  x=0, y=0, channel_map='RGBA',
                                  storage='char', pixels=padded_img.export_pixels())

    @staticmethod
    def _calculate_crop_position(
            width: int,
            height: int,
            crop_width: int,
            crop_height: int,
            position: CropPosition
    ) -> Tuple[int, int]:
        """Calculate the top-left corner coordinates for cropping.

        Args:
            width: Original image width
            height: Original image height
            crop_width: Width of the crop area
            crop_height: Height of the crop area
            position: Named position for the crop

        Returns:
            Tuple of (left, top) coordinates
        """
        if position == CropPosition.CENTER:
            left = (width - crop_width) // 2
            top = (height - crop_height) // 2
        elif position == CropPosition.TOP_LEFT:
            left, top = 0, 0
        elif position == CropPosition.TOP_RIGHT:
            left, top = width - crop_width, 0
        elif position == CropPosition.BOTTOM_LEFT:
            left, top = 0, height - crop_height
        elif position == CropPosition.BOTTOM_RIGHT:
            left, top = width - crop_width, height - crop_height
        else:
            # Default to center
            left = (width - crop_width) // 2
            top = (height - crop_height) // 2

        # Ensure coordinates are within bounds
        left = max(0, min(left, width - crop_width))
        top = max(0, min(top, height - crop_height))

        return left, top

    async def process_images_batch(
            self,
            files: List[UploadFile],
            options: ImageConversionRequest
    ) -> Dict[str, Any]:
        """Process multiple images according to the specified options.

        Args:
            files: List of uploaded image files
            options: Image conversion and processing options

        Returns:
            Dict containing information about all processed images and batch stats
        """
        results = []
        errors = []

        for file in files:
            try:
                # Process each image
                result = await self.process_image(file, options)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return {
            "results": results,
            "errors": errors,
            "total_images": len(files),
            "successful_conversions": len(results),
            "failed_conversions": len(errors)
        }

    async def process_images_with_individual_options(
            self,
            files: List[UploadFile],
            items: List[Dict]
    ) -> Dict[str, Any]:
        """Process multiple images with individual options for each.

        Args:
            files: List of uploaded image files
            items: List of dictionaries containing file_index and conversion_options

        Returns:
            Dict containing information about all processed images and batch stats
        """
        results = []
        errors = []

        for item in items:
            try:
                file_index = item["file_index"]
                options = item["conversion_options"]

                # Ensure file index is valid
                if file_index < 0 or file_index >= len(files):
                    raise ValueError(f"Invalid file_index: {file_index}")

                # Process the image with its specific options
                result = await self.process_image(files[file_index], options)
                results.append(result)
            except Exception as e:
                filename = files[item["file_index"]].filename if 0 <= item["file_index"] < len(files) else "unknown"
                logger.error(f"Error processing {filename}: {str(e)}")
                errors.append({
                    "file_index": item["file_index"],
                    "filename": filename,
                    "error": str(e)
                })

        return {
            "results": results,
            "errors": errors,
            "total_images": len(items),
            "successful_conversions": len(results),
            "failed_conversions": len(errors)
        }