from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.ai.schemas import AIProvider


class AITextGenerationRequest(BaseModel):
    """API request model for AI text generation"""
    
    prompt: str = Field(..., description="The text prompt for generation", min_length=1)
    system_prompt: Optional[str] = Field(None, description="System prompt for context")
    provider: Optional[AIProvider] = Field(None, description="AI provider to use (defaults to configured default)")
    model: Optional[str] = Field(None, description="Specific model to use (provider default if not specified)")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Creativity level (0.0-2.0)")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    stop_sequences: Optional[List[str]] = Field(None, description="Stop sequences")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables for prompt template")
    
    class Config:
        use_enum_values = True


class AITextGenerationResponse(BaseModel):
    """API response model for AI text generation"""
    
    text: str = Field(..., description="Generated text")
    success: bool = Field(..., description="Whether generation was successful")
    provider: str = Field(..., description="AI provider used")
    model: str = Field(..., description="Model used")
    request_id: str = Field(..., description="Unique request identifier")
    created_at: datetime = Field(..., description="Generation timestamp")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    
    # Usage information
    prompt_tokens: int = Field(..., description="Number of tokens in prompt")
    completion_tokens: int = Field(..., description="Number of tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")
    
    # Additional metadata
    finish_reason: str = Field(..., description="Reason why generation finished")
    parameters: Dict[str, Any] = Field(..., description="Parameters used for generation")
    
    error: Optional[str] = Field(None, description="Error message if generation failed")


class AIProvidersResponse(BaseModel):
    """Response model for available AI providers"""
    
    providers: Dict[str, Dict[str, Any]] = Field(..., description="Available providers and their info")
    default_provider: str = Field(..., description="Default provider")
    configured_providers: List[str] = Field(..., description="List of configured providers")


class AIHealthCheckResponse(BaseModel):
    """Response model for AI service health check"""
    
    healthy: bool = Field(..., description="Overall health status")
    providers: Dict[str, bool] = Field(..., description="Health status per provider")
    configured: bool = Field(..., description="Whether any providers are configured")
    message: str = Field(..., description="Health status message")