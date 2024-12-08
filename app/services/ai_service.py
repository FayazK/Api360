from typing import Dict, List, Tuple, Optional
import anthropic
from app.schemas.ai import ProductDescriptionRequest
from .template_manager import TemplateManager
from ..utils.image_helpers import ImageBuilder


class AIService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic()
        self.model = "claude-3-haiku-20241022"
        self.template_manager = TemplateManager()

    async def generate_product_description(
            self, request: ProductDescriptionRequest
    ) -> Tuple[str, List[str], str, Optional[Dict]]:

        image_data = await self._fetch_image(request.image_url)

        """
        Generate product description using Claude with image analysis if provided.
        """
        # Render system prompt
        system_prompt = self.template_manager.render_prompt(
            "prompts/product_description/system.jinja2",
            {
                'industry': request.industry if hasattr(request, 'industry') else None,
                'specialization': "product marketing",
                'audience': request.target_audience
            }
        )

        user_prompt = self.template_manager.render_prompt(
            "prompts/product_description/user.jinja2",
            {
                "product_name": request.product_name,
                "product_description": request.product_description,
                "industry": request.industry if hasattr(request, 'industry') else None,
                "specialization": request.specialization if hasattr(request, 'specialization') else None,
                "audience": request.target_audience,
                "usage_context": request.usage_context if hasattr(request, 'usage_context') else None,
                "tone": request.tone if hasattr(request, 'tone') else None,
                "style": request.style if hasattr(request, 'style') else None,
                "brand_guidelines": request.brand_guidelines if hasattr(request, 'brand_guidelines') else None,
            }
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_data['mime_type'],
                                "data": image_data['data'],
                            },
                        },
                    ],
                }
            ],
        )

        try:
            description = response.content[0].text
            return description

        except Exception as e:
            raise Exception(f"Error processing Claude response: {str(e)}")

    @staticmethod
    async def _fetch_image(image_url: str) -> Dict:
        """Fetch image from URL and convert to base64."""
        builder = await ImageBuilder.download(image_url)
        builder = builder.resize(width=900).quality(85).base64()
        result = builder.get()
        mime_type = builder.get_mime_type()

        return {
            'data': result,
            'mime_type': mime_type
        }
