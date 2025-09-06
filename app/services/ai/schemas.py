from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config.ai_models import AIProvider


class AITextRequest(BaseModel):
    prompt: str = Field(..., description="The text prompt for generation")
    system_prompt: Optional[str] = Field(None, description="System prompt for context")
    provider: AIProvider = Field(default=AIProvider.OPENAI, description="AI provider to use")
    model: Optional[str] = Field(None, description="Specific model to use (provider default if not specified)")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Creativity level (0.0-1.0)")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(0.0, description="Frequency penalty (-2.0 to 2.0)")
    presence_penalty: Optional[float] = Field(0.0, description="Presence penalty (-2.0 to 2.0)")
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables for prompt template")
    
    class Config:
        use_enum_values = True


class AIUsageMetadata(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None


class AIGenerationMetadata(BaseModel):
    provider: str
    model: str
    request_id: str
    created_at: datetime
    response_time_ms: int
    usage: AIUsageMetadata
    finish_reason: str
    parameters: Dict[str, Any]


class AITextResponse(BaseModel):
    text: str = Field(..., description="Generated text")
    metadata: AIGenerationMetadata = Field(..., description="Generation metadata")
    success: bool = Field(True, description="Whether generation was successful")
    error: Optional[str] = Field(None, description="Error message if generation failed")


class AITextGenerationError(Exception):
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(self.message)
