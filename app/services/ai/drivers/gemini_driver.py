import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import asyncio

try:
    from google import genai
    from google.genai import types as genai_types  # noqa: F401  # may be useful if extended later
except ImportError:
    genai = None

from .base_driver import BaseAIDriver
from ..schemas import (
    AITextRequest,
    AITextResponse,
    AIGenerationMetadata,
    AIUsageMetadata,
    AITextGenerationError,
)
from app.config.ai_models import ProviderConfig, AIProvider, get_ai_model_config
from loguru import logger


class GeminiDriver(BaseAIDriver):
    """Google Gemini driver using google-genai SDK"""

    def __init__(self, api_key: str, config: Optional[ProviderConfig] = None, **kwargs):
        if genai is None:
            raise ImportError("google-genai library not installed. Install it with: pip install google-genai")

        super().__init__(api_key, **kwargs)

        # Use injected config or get default
        self.config = config or get_ai_model_config().get_provider_config(AIProvider.GEMINI)
        if not self.config:
            raise ValueError("Gemini provider configuration not found")

        # google-genai client is synchronous; we will call it via asyncio.to_thread
        self._client = None

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
        try:
            # Create client; auto-uses env or explicit key; pass api_key explicitly
            self._client = genai.Client(api_key=self.api_key)

            # Basic call to ensure connectivity: list models (run in thread)
            await asyncio.to_thread(lambda: list(self._client.models.list()))
        except Exception as e:
            raise AITextGenerationError(
                f"Failed to initialize Gemini client: {str(e)}",
                self.provider_name,
            )

    async def generate_text(self, request: AITextRequest) -> AITextResponse:
        if not self._client:
            await self.initialize()

        request_id = str(uuid.uuid4())

        try:
            # Build contents; if system prompt is provided, prepend it.
            if request.system_prompt:
                contents: Any = f"{request.system_prompt}\n\n{request.prompt}"
            else:
                contents = request.prompt

            # Build API parameters; only include explicitly provided values
            api_params: Dict[str, Any] = {
                "model": request.model or self.default_model,
                "contents": contents,
            }
            # Not sending optional generation config to allow provider defaults
            # If needed later, map request.temperature -> generation_config.temperature and
            # request.max_tokens -> generation_config.max_output_tokens etc.

            # Call sync SDK in a thread
            response = await asyncio.to_thread(
                lambda: self._client.models.generate_content(**api_params)
            )

            # Log raw provider response for debugging (tokens/cost extraction)
            def _safe_dump(obj: Any) -> str:
                try:
                    # google-genai objects may have to_dict()
                    if hasattr(obj, "to_dict"):
                        return json.dumps(obj.to_dict(), default=str)
                    return json.dumps(obj, default=str)
                except Exception:
                    try:
                        return str(obj)
                    except Exception:
                        return "<unserializable>"

            logger.debug(
                "Gemini raw response (model={}, request_id={}): {}",
                api_params.get("model"),
                request_id,
                _safe_dump(response),
            )

            # Extract response text
            text = getattr(response, "text", None)
            if text is None:
                # Some SDK versions return candidates; fall back
                try:
                    candidates = getattr(response, "candidates", [])
                    if candidates:
                        text = getattr(candidates[0], "content", None)
                        if text and hasattr(text, "parts") and text.parts:
                            # parts may contain text in part.text
                            part0 = text.parts[0]
                            text = getattr(part0, "text", None) or str(part0)
                except Exception:
                    pass
            if text is None:
                text = ""

            # Usage metrics (if available)
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            try:
                usage = getattr(response, "usage_metadata", None)
                if usage is not None:
                    prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                    completion_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
                    total_tokens = int(getattr(usage, "total_token_count", prompt_tokens + completion_tokens) or (prompt_tokens + completion_tokens))
            except Exception:
                pass

            # Finish reason (if available)
            finish_reason = "stop"
            try:
                candidates = getattr(response, "candidates", [])
                if candidates:
                    fr = getattr(candidates[0], "finish_reason", None)
                    if fr is not None:
                        finish_reason = getattr(fr, "value", None) or getattr(fr, "name", None) or str(fr)
                        finish_reason = str(finish_reason).lower()
            except Exception:
                pass

            # Build metadata; parameters only include what was actually sent
            parameters_meta: Dict[str, Any] = {"model": api_params["model"]}

            metadata = AIGenerationMetadata(
                provider=self.provider_name,
                model=api_params["model"],
                request_id=request_id,
                created_at=datetime.now(),
                response_time_ms=0,  # service fills this on return
                usage=AIUsageMetadata(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    cost_usd=self.calculate_cost(api_params["model"], prompt_tokens, completion_tokens),
                ),
                finish_reason=finish_reason,
                parameters=parameters_meta,
            )

            return AITextResponse(text=text, metadata=metadata, success=True)

        except Exception as e:
            # Log raw error for debugging
            try:
                logger.exception("Gemini API error for model {}: {}", request.model or self.default_model, str(e))
            except Exception:
                pass
            raise AITextGenerationError(
                f"Gemini API error: {str(e)}",
                self.provider_name,
            )

    def validate_model(self, model: str) -> bool:
        return model in self.supported_models

    def get_model_pricing(self, model: str) -> Dict[str, float]:
        model_config = self.config.models.get(model)
        if not model_config:
            return {
                "input_cost_per_token": 0.0,
                "output_cost_per_token": 0.0,
            }
        return {
            "input_cost_per_token": model_config.pricing.input_cost_per_token,
            "output_cost_per_token": model_config.pricing.output_cost_per_token,
        }

    async def health_check(self) -> bool:
        try:
            if not self._client:
                await self.initialize()
            # simple call
            await asyncio.to_thread(lambda: list(self._client.models.list()))
            return True
        except Exception:
            return False
