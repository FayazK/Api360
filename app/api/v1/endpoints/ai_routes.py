from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse

from app.schemas.ai import (
    AITextGenerationRequest, 
    AITextGenerationResponse, 
    AIProvidersResponse,
    AIHealthCheckResponse
)
from app.services.ai.factory import get_ai_service, AITextGeneratorFactory
from app.services.ai.schemas import AITextGenerationError, AITextRequest
from app.config.ai_models import AIProvider
from app.core.config import settings

router = APIRouter()


async def get_ai_text_service(request: Request):
    """Get the AI text generation service from app state or fallback factory."""
    try:
        svc = getattr(request.app.state, "ai_service", None)
        if svc is not None:
            return svc
        return await get_ai_service()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")


@router.post("/generate", response_model=AITextGenerationResponse)
async def generate_text(
    request: AITextGenerationRequest,
    ai_service = Depends(get_ai_text_service)
):
    """
    Generate text using AI models from various providers.
    
    This endpoint supports multiple AI providers and models, allowing you to:
    - Generate text with customizable parameters
    - Use prompt templates with variables
    - Get detailed metadata about token usage and costs
    - Specify different providers and models
    """
    
    try:
        # Create internal request with only user-provided params;
        # service/drivers will apply required defaults.
        ai_request = AITextRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop_sequences=request.stop_sequences,
            template_variables=request.template_variables
        )
        
        # Generate text
        response = await ai_service.generate_text(ai_request)
        
        # Convert to API response format
        return AITextGenerationResponse(
            text=response.text,
            success=response.success,
            provider=response.metadata.provider,
            model=response.metadata.model,
            request_id=response.metadata.request_id,
            created_at=response.metadata.created_at,
            response_time_ms=response.metadata.response_time_ms,
            prompt_tokens=response.metadata.usage.prompt_tokens,
            completion_tokens=response.metadata.usage.completion_tokens,
            total_tokens=response.metadata.usage.total_tokens,
            cost_usd=response.metadata.usage.cost_usd,
            finish_reason=response.metadata.finish_reason,
            parameters=response.metadata.parameters,
            error=response.error
        )
        
    except AITextGenerationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": e.message,
                "provider": e.provider,
                "error_code": e.error_code
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during text generation: {str(e)}"
        )


@router.get("/providers", response_model=AIProvidersResponse)
async def get_providers(ai_service = Depends(get_ai_text_service)):
    """
    Get information about available AI providers and their capabilities.
    
    Returns details about:
    - Available providers and their health status
    - Supported models per provider
    - Default configurations
    """
    
    try:
        providers_info = await ai_service.get_available_providers()
        configured_providers = AITextGeneratorFactory.get_available_providers()
        
        return AIProvidersResponse(
            providers=providers_info,
            default_provider=settings.AI_DEFAULT_PROVIDER,
            configured_providers=configured_providers
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching provider information: {str(e)}"
        )


@router.get("/health", response_model=AIHealthCheckResponse)
async def health_check():
    """
    Check the health status of AI services.
    
    Returns:
    - Overall health status
    - Per-provider health status
    - Configuration status
    """
    
    try:
        # Check if any providers are configured
        configured = AITextGeneratorFactory.is_service_available()
        
        if not configured:
            return AIHealthCheckResponse(
                healthy=False,
                providers={},
                configured=False,
                message="No AI providers are configured. Please set API keys in environment variables."
            )
        
        # Get service and check provider health
        ai_service = await get_ai_service()
        providers_info = await ai_service.get_available_providers()
        
        provider_health = {
            name: info["healthy"] 
            for name, info in providers_info.items()
        }
        
        overall_health = any(provider_health.values())
        
        message = "All systems operational" if overall_health else "All providers are currently unavailable"
        
        return AIHealthCheckResponse(
            healthy=overall_health,
            providers=provider_health,
            configured=True,
            message=message
        )
        
    except Exception as e:
        return AIHealthCheckResponse(
            healthy=False,
            providers={},
            configured=AITextGeneratorFactory.is_service_available(),
            message=f"Health check failed: {str(e)}"
        )


@router.post("/validate")
async def validate_request(
    request: AITextGenerationRequest,
    ai_service = Depends(get_ai_text_service)
):
    """
    Validate an AI text generation request without executing it.
    
    Useful for:
    - Checking if parameters are valid
    - Verifying provider/model availability
    - Estimating costs before generation
    """
    
    try:
        ai_request = AITextRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            provider=request.provider,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop_sequences=request.stop_sequences,
            template_variables=request.template_variables
        )
        
        is_valid = await ai_service.validate_request(ai_request)
        
        # Provider/model may be resolved by service; attempt to echo what would be used
        resolved_provider = ai_request.provider.value if ai_request.provider else settings.AI_DEFAULT_PROVIDER
        return {
            "valid": is_valid,
            "provider": resolved_provider,
            "model": ai_request.model,
            "message": "Request is valid" if is_valid else "Request validation failed"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "message": f"Validation error: {str(e)}"
            }
        )
