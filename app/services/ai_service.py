from typing import Dict, List, Tuple, Optional
import anthropic
import aiohttp
from app.schemas.ai import ProductDescriptionRequest
from .template_manager import TemplateManager
import base64

# Create an instance of the Anthropic API client
client = anthropic.Anthropic()

# Set the default model
DEFAULT_MODEL="claude-3-haiku-20241022"

class AIService:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"
        self.template_manager = TemplateManager()

    async def generate_product_description(
            self, request: ProductDescriptionRequest
    ) -> Tuple[str, List[str], str, Optional[Dict]]:
        """
        Generate product description using Claude with image analysis if provided.
        """
        # Render system prompt
        system_prompt = self.template_manager.render_system_prompt(
            industry=request.industry if hasattr(request, 'industry') else None,
            specialization="product marketing",
            audience=request.target_audience
        )

        # Prepare main description prompt
        description_variables = {
            "product_name": request.product_name,
            "product_description": request.product_description,
            "product_features": request.product_features,
            "target_audience": request.target_audience,
            "tone": request.tone,
            "style": request.style,
            "word_count": request.word_count,
        }

        main_prompt = self.template_manager.render_prompt(
            "prompts/product/description.jinja2",
            description_variables
        )

        messages = []
        image_analysis = None

        # Handle image analysis if provided
        if request.image_url:
            try:
                image_data = await self._fetch_image(request.image_url)

                # Render image analysis prompt
                image_prompt = self.template_manager.render_prompt(
                    "prompts/product/image_analysis.jinja2",
                    {"product_name": request.product_name}
                )

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": image_prompt
                            }
                        ]
                    }
                )

                image_response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=messages,
                    system=system_prompt
                )

                image_analysis = image_response.content[0].text

                # Add image analysis to main prompt
                main_prompt += f"\n\nImage Analysis:\n{image_analysis}"

            except Exception as e:
                print(f"Error processing image: {str(e)}")
                pass

        # Generate product description
        messages = [
            {
                "role": "user",
                "content": main_prompt
            }
        ]

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=messages,
            system=system_prompt
        )

        try:
            description = response.content[0].text

            # Generate SEO keywords using template
            seo_prompt = self.template_manager.render_prompt(
                "prompts/product/seo.jinja2",
                {
                    "product_name": request.product_name,
                    "category": request.category if hasattr(request, 'category') else None
                }
            )

            keyword_messages = [
                {
                    "role": "user",
                    "content": f"{seo_prompt}\n\nBased on this description:\n{description}"
                }
            ]

            keywords_response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=keyword_messages
            )

            keywords = keywords_response.content[0].text.split(',')
            seo_title = f"{request.product_name} - {keywords[0]}"

            return description.strip(), [k.strip() for k in keywords], seo_title, image_analysis

        except Exception as e:
            raise Exception(f"Error processing Claude response: {str(e)}")

    async def _fetch_image(self, image_url: str) -> str:
        """Fetch image from URL and convert to base64."""
        async with aiohttp.ClientSession() as session:
            async with session.get(str(image_url)) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return base64.b64encode(image_data).decode('utf-8')
                else:
                    raise Exception(f"Failed to fetch image: {response.status}")