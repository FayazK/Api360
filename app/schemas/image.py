from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List


class ImageFormat(str, Enum):
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"
    TIFF = "tiff"
    BMP = "bmp"
    SVG = "svg"
    HEIF = "heif"
    AVIF = "avif"


class ResizeMode(str, Enum):
    PRESERVE_RATIO = "preserve_ratio"
    STRETCH = "stretch"
    CROP = "crop"
    PAD = "pad"


class CompressionType(str, Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"


class CropPosition(str, Enum):
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CUSTOM = "custom"


class ImageConversionRequest(BaseModel):
    output_format: ImageFormat
    convert_only: bool = Field(False, description="If true, only convert format without additional processing")

    # Image quality options (only used if convert_only=False)
    compression_type: Optional[CompressionType] = Field(None, description="Type of compression to use")
    quality: Optional[int] = Field(None, ge=1, le=100, description="Image quality (1-100, higher is better)")

    # Resize options
    resize: Optional[bool] = Field(None, description="Whether to resize the image")
    width: Optional[int] = Field(None, gt=0, description="Target width in pixels")
    height: Optional[int] = Field(None, gt=0, description="Target height in pixels")
    resize_mode: Optional[ResizeMode] = Field(None, description="How to handle aspect ratio when resizing")

    # Cropping options
    crop: Optional[bool] = Field(None, description="Whether to crop the image")
    crop_position: Optional[CropPosition] = Field(None, description="Where to position the crop")
    crop_width: Optional[int] = Field(None, gt=0, description="Width of crop in pixels")
    crop_height: Optional[int] = Field(None, gt=0, description="Height of crop in pixels")
    crop_x: Optional[int] = Field(None, ge=0, description="X position for custom crop")
    crop_y: Optional[int] = Field(None, ge=0, description="Y position for custom crop")

    # Metadata options
    strip_metadata: Optional[bool] = Field(None, description="Remove all metadata from image")
    preserve_color_profile: Optional[bool] = Field(None, description="Preserve color profile information")

    # Advanced options
    auto_orient: Optional[bool] = Field(None, description="Automatically orient image based on EXIF data")
    background_color: Optional[str] = Field(None, description="Background color for transparent areas")
    sharpen: Optional[bool] = Field(None, description="Apply sharpening filter")

    @validator('crop_x', 'crop_y', always=True)
    def validate_crop_coordinates(cls, v, values):
        if values.get('crop_position') == CropPosition.CUSTOM and v is None:
            raise ValueError("crop_x and crop_y are required when crop_position is 'custom'")
        return v

    @validator('crop_width', 'crop_height', always=True)
    def validate_crop_dimensions(cls, v, values):
        if values.get('crop') and v is None:
            raise ValueError("crop_width and crop_height are required when crop is True")
        return v

    @validator('resize_mode', always=True)
    def validate_resize_mode(cls, v, values):
        if values.get('resize') and v is None:
            return ResizeMode.PRESERVE_RATIO  # Default to preserving ratio
        return v

    @validator('quality', always=True)
    def validate_quality(cls, v, values):
        if not values.get('convert_only') and values.get('compression_type') == CompressionType.LOSSY and v is None:
            return 85  # Default quality for lossy compression
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "output_format": "webp",
                "convert_only": False,
                "compression_type": "lossy",
                "quality": 85,
                "resize": True,
                "width": 800,
                "height": 600,
                "resize_mode": "preserve_ratio",
                "crop": False,
                "strip_metadata": True,
                "auto_orient": True
            }
        }


class ImageConversionResponse(BaseModel):
    url: str
    format: str
    width: int
    height: int
    size_bytes: int
    original_filename: str


class BatchImageConversionResponse(BaseModel):
    results: List[ImageConversionResponse]
    total_images: int
    successful_conversions: int
    failed_conversions: int

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "url": "/static/charts/image1_a1b2c3d4.webp",
                        "format": "webp",
                        "width": 800,
                        "height": 600,
                        "size_bytes": 24680,
                        "original_filename": "image1.jpg"
                    },
                    {
                        "url": "/static/charts/image2_e5f6g7h8.webp",
                        "format": "webp",
                        "width": 1024,
                        "height": 768,
                        "size_bytes": 35791,
                        "original_filename": "image2.png"
                    }
                ],
                "total_images": 2,
                "successful_conversions": 2,
                "failed_conversions": 0
            }
        }


class BatchImageItem(BaseModel):
    file_index: int
    conversion_options: ImageConversionRequest


class BatchConversionWithIndividualOptionsRequest(BaseModel):
    items: List[BatchImageItem]

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "file_index": 0,
                        "conversion_options": {
                            "output_format": "webp",
                            "quality": 85,
                            "resize": True,
                            "width": 800,
                            "height": 600
                        }
                    },
                    {
                        "file_index": 1,
                        "conversion_options": {
                            "output_format": "png",
                            "compression_type": "lossless",
                            "resize": True,
                            "width": 1024
                        }
                    }
                ]
            }
        }