import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.ai import (
    AITextGenerationRequest,
    AITextGenerationResponse,
    AIProvidersResponse,
    AIHealthCheckResponse
)
from app.services.ai.schemas import (
    AIProvider,
    AITextRequest,
    AITextResponse,
    AIGenerationMetadata,
    AIUsageMetadata,
    AITextGenerationError
)


class TestAPISchemas:
    """Test cases for API request/response schemas"""
    
    def test_ai_text_generation_request_valid(self):
        """Test valid AI text generation request"""
        request_data = {
            "prompt": "Hello, world!",
            "provider": "openai",
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        request = AITextGenerationRequest(**request_data)
        assert request.prompt == "Hello, world!"
        assert request.provider == AIProvider.OPENAI
        assert request.max_tokens == 100
        assert request.temperature == 0.7
    
    def test_ai_text_generation_request_minimal(self):
        """Test minimal AI text generation request"""
        request = AITextGenerationRequest(prompt="Test prompt")
        assert request.prompt == "Test prompt"
        assert request.provider is None
        assert request.max_tokens is None
        assert request.temperature is None
    
    def test_ai_text_generation_request_invalid_empty_prompt(self):
        """Test that empty prompt fails validation"""
        with pytest.raises(ValidationError) as exc_info:
            AITextGenerationRequest(prompt="")
        
        assert "at least 1 character" in str(exc_info.value)
    
    def test_ai_text_generation_request_invalid_temperature(self):
        """Test that invalid temperature fails validation"""
        with pytest.raises(ValidationError):
            AITextGenerationRequest(prompt="Test", temperature=3.0)  # Too high
        
        with pytest.raises(ValidationError):
            AITextGenerationRequest(prompt="Test", temperature=-1.0)  # Too low
    
    def test_ai_text_generation_request_invalid_max_tokens(self):
        """Test that invalid max_tokens fails validation"""
        with pytest.raises(ValidationError):
            AITextGenerationRequest(prompt="Test", max_tokens=0)  # Too low
        
        with pytest.raises(ValidationError):
            AITextGenerationRequest(prompt="Test", max_tokens=5000)  # Too high
    
    def test_ai_text_generation_response_valid(self):
        """Test valid AI text generation response"""
        response_data = {
            "text": "Generated text",
            "success": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "request_id": "test-123",
            "created_at": datetime.now(),
            "response_time_ms": 1500,
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
            "cost_usd": 0.001,
            "finish_reason": "stop",
            "parameters": {"temperature": 0.7}
        }
        
        response = AITextGenerationResponse(**response_data)
        assert response.text == "Generated text"
        assert response.success is True
        assert response.provider == "openai"
        assert response.total_tokens == 30
    
    def test_ai_providers_response_valid(self):
        """Test valid AI providers response"""
        response_data = {
            "providers": {
                "openai": {
                    "name": "OpenAI",
                    "healthy": True,
                    "models": ["gpt-4o-mini", "gpt-4o"]
                }
            },
            "default_provider": "openai",
            "configured_providers": ["openai"]
        }
        
        response = AIProvidersResponse(**response_data)
        assert "openai" in response.providers
        assert response.default_provider == "openai"
    
    def test_ai_health_check_response_valid(self):
        """Test valid AI health check response"""
        response_data = {
            "healthy": True,
            "providers": {"openai": True},
            "configured": True,
            "message": "All systems operational"
        }
        
        response = AIHealthCheckResponse(**response_data)
        assert response.healthy is True
        assert response.providers["openai"] is True
        assert response.configured is True


class TestInternalSchemas:
    """Test cases for internal service schemas"""
    
    def test_ai_provider_enum(self):
        """Test AI provider enum values"""
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.ANTHROPIC.value == "anthropic"
        assert AIProvider.GEMINI.value == "gemini"
        assert AIProvider.OPENROUTER.value == "openrouter"
    
    def test_ai_text_request_valid(self):
        """Test valid internal AI text request"""
        request = AITextRequest(
            prompt="Test prompt",
            provider=AIProvider.OPENAI,
            max_tokens=100,
            temperature=0.7
        )
        
        assert request.prompt == "Test prompt"
        assert request.provider == AIProvider.OPENAI
        assert request.max_tokens == 100
        assert request.temperature == 0.7
    
    def test_ai_usage_metadata_valid(self):
        """Test valid usage metadata"""
        usage = AIUsageMetadata(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            cost_usd=0.001
        )
        
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
        assert usage.cost_usd == 0.001
    
    def test_ai_generation_metadata_valid(self):
        """Test valid generation metadata"""
        usage = AIUsageMetadata(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        metadata = AIGenerationMetadata(
            provider="openai",
            model="gpt-4o-mini",
            request_id="test-123",
            created_at=datetime.now(),
            response_time_ms=1500,
            usage=usage,
            finish_reason="stop",
            parameters={"temperature": 0.7}
        )
        
        assert metadata.provider == "openai"
        assert metadata.model == "gpt-4o-mini"
        assert metadata.usage.total_tokens == 30
        assert metadata.finish_reason == "stop"
    
    def test_ai_text_response_valid(self):
        """Test valid AI text response"""
        usage = AIUsageMetadata(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        metadata = AIGenerationMetadata(
            provider="openai",
            model="gpt-4o-mini",
            request_id="test-123",
            created_at=datetime.now(),
            response_time_ms=1500,
            usage=usage,
            finish_reason="stop",
            parameters={"temperature": 0.7}
        )
        
        response = AITextResponse(
            text="Generated text",
            metadata=metadata,
            success=True
        )
        
        assert response.text == "Generated text"
        assert response.success is True
        assert response.metadata.provider == "openai"
    
    def test_ai_text_generation_error(self):
        """Test AI text generation error"""
        error = AITextGenerationError(
            message="Test error",
            provider="openai",
            error_code="invalid_request"
        )
        
        assert str(error) == "Test error"
        assert error.provider == "openai"
        assert error.error_code == "invalid_request"