import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from .base_driver import BaseAIDriver
from ..schemas import AITextRequest, AITextResponse, AIGenerationMetadata, AIUsageMetadata, AITextGenerationError
from app.config.ai_models import ProviderConfig, AIProvider, get_ai_model_config


class OpenAIDriver(BaseAIDriver):
    """OpenAI driver for text generation using GPT models"""
    
    def __init__(self, api_key: str, config: Optional[ProviderConfig] = None, **kwargs):
        if AsyncOpenAI is None:
            raise ImportError("OpenAI library not installed. Install it with: pip install openai")
        
        super().__init__(api_key, **kwargs)
        
        # Use injected config or get default
        self.config = config or get_ai_model_config().get_provider_config(AIProvider.OPENAI)
        if not self.config:
            raise ValueError("OpenAI provider configuration not found")
        
        self.base_url = kwargs.get('base_url') or self.config.base_url
        self.organization = kwargs.get('organization') or self.config.organization
    
    @property
    def provider_name(self) -> str:
        return self.config.name
    
    @property
    def default_model(self) -> str:
        return self.config.default_model
    
    @property
    def supported_models(self) -> List[str]:
        return list(self.config.models.keys())
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client"""
        try:
            client_kwargs = {
                "api_key": self.api_key,
            }
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            if self.organization:
                client_kwargs["organization"] = self.organization
                
            self._client = AsyncOpenAI(**client_kwargs)
            
            # Test the connection with a simple API call
            await self._client.models.list()
            
        except Exception as e:
            raise AITextGenerationError(
                f"Failed to initialize OpenAI client: {str(e)}",
                self.provider_name
            )
    
    async def generate_text(self, request: AITextRequest) -> AITextResponse:
        """Generate text using OpenAI's API"""
        if not self._client:
            await self.initialize()
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            
            if request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Prepare API parameters, only include values explicitly provided
            api_params = {
                "model": request.model or self.default_model,
                "messages": messages,
            }

            if request.max_tokens is not None:
                api_params["max_tokens"] = request.max_tokens
            if request.temperature is not None:
                api_params["temperature"] = request.temperature
            if request.top_p is not None:
                api_params["top_p"] = request.top_p
            if request.frequency_penalty is not None:
                api_params["frequency_penalty"] = request.frequency_penalty
            if request.presence_penalty is not None:
                api_params["presence_penalty"] = request.presence_penalty
            if request.stop_sequences:
                api_params["stop"] = request.stop_sequences
            
            # Make API call
            completion = await self._client.chat.completions.create(**api_params)
            
            # Extract response data
            message = completion.choices[0].message
            usage = completion.usage
            finish_reason = completion.choices[0].finish_reason
            
            # Calculate cost
            cost = self.calculate_cost(
                api_params["model"],
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            # Create metadata
            # Build parameters metadata reflecting only what was sent
            parameters_meta: Dict[str, Any] = {
                "model": api_params["model"],
            }
            for key in ("temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"):
                if key in api_params:
                    parameters_meta[key] = api_params[key]

            metadata = AIGenerationMetadata(
                provider=self.provider_name,
                model=api_params["model"],
                request_id=request_id,
                created_at=datetime.fromtimestamp(completion.created),
                response_time_ms=int((time.time() - start_time) * 1000),
                usage=AIUsageMetadata(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    cost_usd=cost
                ),
                finish_reason=finish_reason,
                parameters=parameters_meta
            )
            
            return AITextResponse(
                text=message.content,
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            error_message = str(e)
            
            # Handle specific OpenAI errors
            if hasattr(e, 'response'):
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('error', {}).get('message', error_message)
                except:
                    pass
            
            raise AITextGenerationError(
                f"OpenAI API error: {error_message}",
                self.provider_name,
                getattr(e, 'code', None)
            )
    
    def validate_model(self, model: str) -> bool:
        """Validate if the model is supported"""
        return model in self.supported_models
    
    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing information for a model"""
        model_config = self.config.models.get(model)
        if not model_config:
            return {
                "input_cost_per_token": 0.0,
                "output_cost_per_token": 0.0
            }
        
        return {
            "input_cost_per_token": model_config.pricing.input_cost_per_token,
            "output_cost_per_token": model_config.pricing.output_cost_per_token
        }
    
    async def health_check(self) -> bool:
        """Check OpenAI service health"""
        try:
            if not self._client:
                await self.initialize()
            
            # Simple API call to check connectivity
            models = await self._client.models.list()
            return len(models.data) > 0
            
        except Exception:
            return False
