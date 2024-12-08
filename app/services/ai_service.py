from typing import Dict, List, Tuple, Optional
import anthropic
from fastapi.logger import logger

from app.schemas.ai import ProductDescriptionRequest
from .template_manager import TemplateManager

from ..utils.image_helpers import ImageBuilder


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
        message_content = [
            {
                "type": "text",
                "text": self.template_manager.render_prompt(
                    "prompts/product_description/user.jinja2",
                    {
                        "product_name": request.product_name,
                        "product_description": request.product_description,
                        "audience": request.target_audience,
                        "tone": request.tone,
                        "style": request.style,
                    }
                )
            }
        ]

        # Add image if URL is provided
        if request.image_url:
            try:
                image_data = await self._fetch_image(str(request.image_url))
                if image_data['data'] and image_data['mime_type']:
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data['mime_type'],
                            "data": image_data['data']
                        }
                    })
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                # Continue without image if there's an error

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.template_manager.render_prompt(
                    "prompts/product_description/system.jinja2",
                    {
                        'audience': request.target_audience
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
            raise Exception(f"Error generating product description: {str(e)}")

    @staticmethod
    async def _fetch_image(image_url: str) -> Dict:
        """Fetch image from URL and convert to base64."""
        try:
            builder = ImageBuilder()
            builder = await builder.download(url=image_url)
            # Don't include the "data:image/..." prefix in base64 string
            base64_data = builder.resize(width=900).quality(85).base64().get()
            mime_type = builder.get_mime_type()

            # Remove any potential data URI prefix
            if isinstance(base64_data, str) and ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            return {
                'data': base64_data,
                'mime_type': mime_type
            }
        except Exception as e:
            logger.error(f"Error fetching image: {str(e)}")
            # Return None for both if image fetch fails
            return {
                'data': None,
                'mime_type': None
            }
