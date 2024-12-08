import uuid
from typing import Dict
import aiohttp
import anthropic
from fastapi import HTTPException
from fastapi.logger import logger

from ..template_manager import TemplateManager
from ...schemas.ai.product import ProductDescriptionRequest
from ...utils.image_helpers import ImageBuilder, save_temp_image, get_base64_encoded_image, cleanup_temp_file


class AIService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-latest"
        self.template_manager = TemplateManager()

    async def generate_product_description(
            self, request: ProductDescriptionRequest
    ) -> str:
        """Generate product description using Claude with image analysis if provided."""

        # Initialize message content
        message_content = []

        # Add image if URL is provided
        if request.image_url:
            try:
                image_data = await self._fetch_image(str(request.image_url))
                message_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_data['mime_type'],
                        "data": image_data['data']
                    }
                })
            except HTTPException as he:
                # Re-raise HTTP exceptions with their original error messages
                raise he
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail="Unable to process the provided image. Please check the image URL and try again."
                )

        # Only proceed if image processing was successful
        message_content.append({
            "type": "text",
            "text": self.template_manager.render_prompt(
                "prompts/product_description/user.jinja2",
                {
                    "product_description": request.product_description,
                    "audience": request.target_audience,
                    "tone": request.tone,
                    "style": request.style,
                }
            )
        })

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.template_manager.render_prompt(
                    "prompts/product_description/system.jinja2",
                    {
                        'audience': request.target_audience,
                        'industry': request.industry,
                        'specialization': request.specialization
                    }
                ),
                messages=[{
                    "role": "user",
                    "content": message_content
                }]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error from Claude API: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating product description: {str(e)}"
            )

    @staticmethod
    async def _fetch_image(image_url: str) -> Dict:
        """Fetch image from URL and process for Claude."""
        try:
            # Download and process image
            builder = ImageBuilder()
            try:
                builder = await builder.download(url=image_url)
            except aiohttp.ClientError as e:
                if isinstance(e, aiohttp.ClientConnectorError):
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to connect to the image URL. Please check if the URL is accessible."
                    )
                elif isinstance(e, aiohttp.ClientResponseError):
                    if e.status == 404:
                        raise HTTPException(
                            status_code=400,
                            detail="Image not found at the provided URL."
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Error downloading image: HTTP {e.status}"
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Error downloading image. Please check the URL and try again."
                    )

            # Generate temp filename
            temp_filename = f"{uuid.uuid4()}.png"

            try:
                # Get processed image data and mime type
                processed_image = builder.resize(width=1000).get()
                mime_type = builder.get_mime_type()

                if not processed_image or not mime_type:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid image format or corrupted image file."
                    )

                # Save to temp file
                temp_path = save_temp_image(processed_image, temp_filename)

                try:
                    # Get base64 encoded image
                    base64_data = get_base64_encoded_image(temp_path)

                    return {
                        'data': base64_data,
                        'mime_type': mime_type
                    }
                finally:
                    # Clean up temp file
                    cleanup_temp_file(temp_path)

            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing image: {str(e)}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing image: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while processing the image."
            )
