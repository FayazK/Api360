from typing import Optional, Tuple, Union
import aiohttp
from PIL import Image
import io
import base64
from fastapi import HTTPException
from dataclasses import dataclass
from enum import Enum


class ImageFormat(Enum):
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"


@dataclass
class ImageDimensions:
    width: Optional[int] = None
    height: Optional[int] = None


class ImageBuilder:
    def __init__(self):
        self._image: Optional[Image.Image] = None
        self._image_data: Optional[bytes] = None
        self._quality: int = 85
        self._format: ImageFormat = ImageFormat.JPEG
        self._max_size: int = 10 * 1024 * 1024  # 10MB
        self._dimensions: ImageDimensions = ImageDimensions()
        self._background_color: tuple = (255, 255, 255)  # white

    async def download(self, url: str) -> 'ImageBuilder':
        """Download image from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to fetch image: HTTP {response.status}"
                        )

                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self._max_size:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Image too large. Maximum size: {self._max_size / 1024 / 1024}MB"
                        )

                    self._image_data = await response.read()
                    if len(self._image_data) > self._max_size:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Image too large. Maximum size: {self._max_size / 1024 / 1024}MB"
                        )

                    self._image = Image.open(io.BytesIO(self._image_data))
                    return self

        except aiohttp.ClientError as e:
            raise HTTPException(status_code=400, detail=f"Error fetching image: {str(e)}")

    def resize(self, width: Optional[int] = None, height: Optional[int] = None) -> 'ImageBuilder':
        """Resize image maintaining aspect ratio."""
        if not self._image:
            raise HTTPException(status_code=400, detail="No image loaded")

        if width or height:
            self._dimensions.width = width
            self._dimensions.height = height

            original_width, original_height = self._image.size
            new_width, new_height = self._calculate_dimensions(
                original_width, original_height, width, height
            )

            if (new_width, new_height) != (original_width, original_height):
                self._image = self._image.resize(
                    (new_width, new_height),
                    Image.Resampling.LANCZOS
                )

        return self

    def quality(self, value: int) -> 'ImageBuilder':
        """Set image quality (1-100)."""
        self._quality = max(1, min(100, value))
        return self

    def format(self, format: Union[str, ImageFormat]) -> 'ImageBuilder':
        """Set output format."""
        if isinstance(format, str):
            format = ImageFormat(format.upper())
        self._format = format
        return self

    def max_size(self, size_in_mb: float) -> 'ImageBuilder':
        """Set maximum file size in MB."""
        self._max_size = int(size_in_mb * 1024 * 1024)
        return self

    def background(self, color: tuple) -> 'ImageBuilder':
        """Set background color for transparent images."""
        self._background_color = color
        return self

    def base64(self) -> 'ImageBuilder':
        """Convert image to base64."""
        if not self._image:
            raise HTTPException(status_code=400, detail="No image loaded")

        # Handle image mode
        if self._image.mode == 'RGBA':
            background = Image.new('RGB', self._image.size, self._background_color)
            background.paste(self._image, mask=self._image.split()[3])
            self._image = background
        elif self._image.mode not in ['RGB', 'L']:
            self._image = self._image.convert('RGB')

        # Save to buffer
        buffer = io.BytesIO()
        self._image.save(
            buffer,
            format=self._format.value,
            quality=self._quality if self._format == ImageFormat.JPEG else None,
            optimize=True
        )

        self._image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return self

    def get(self) -> Union[str, bytes, Image.Image]:
        """Get the processed image."""
        if isinstance(self._image_data, str):  # base64 string
            return self._image_data
        elif isinstance(self._image_data, bytes):  # raw bytes
            return self._image_data
        elif self._image:  # PIL Image
            return self._image
        else:
            raise HTTPException(status_code=400, detail="No image data available")

    @staticmethod
    def _calculate_dimensions(
            original_width: int,
            original_height: int,
            target_width: Optional[int],
            target_height: Optional[int]
    ) -> Tuple[int, int]:
        """Calculate new dimensions maintaining aspect ratio."""
        if target_width is None and target_height is None:
            return original_width, original_height

        aspect_ratio = original_width / original_height

        if target_width and target_height:
            return target_width, target_height
        elif target_width:
            new_height = int(target_width / aspect_ratio)
            return target_width, new_height
        else:  # target_height is provided
            new_width = int(target_height * aspect_ratio)
            return new_width, target_height