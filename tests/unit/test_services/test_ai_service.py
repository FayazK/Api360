import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.ai.factory import AITextGeneratorFactory, AITextGeneratorService
from app.config.ai_models import AIProvider
from app.services.ai.schemas import AITextRequest, AITextResponse
from app.services.ai.drivers.openai_driver import OpenAIDriver


class TestAITextGeneratorService:
    """Test cases for AI text generation service"""
    
    def setup_method(self):
        """Setup method run before each test"""
        # Reset the factory singleton for clean tests
        AITextGeneratorFactory.reset_service()
    
    def test_factory_singleton(self):
        """Test that factory returns the same instance"""
        service1 = AITextGeneratorFactory.get_service()
        service2 = AITextGeneratorFactory.get_service()
        assert service1 is service2
    
    def test_factory_is_service_available_no_keys(self):
        """Test factory detects no API keys configured"""
        with patch('app.services.ai.factory.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.GEMINI_API_KEY = None
            mock_settings.OPENROUTER_API_KEY = None
            
            assert not AITextGeneratorFactory.is_service_available()
    
    def test_factory_is_service_available_with_openai(self):
        """Test factory detects OpenAI key configured"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.GEMINI_API_KEY = None
            mock_settings.OPENROUTER_API_KEY = None
            
            assert AITextGeneratorFactory.is_service_available()
    
    def test_factory_get_available_providers(self):
        """Test factory returns available providers"""
        with patch('app.services.ai.factory.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.ANTHROPIC_API_KEY = None
            mock_settings.GEMINI_API_KEY = None
            mock_settings.OPENROUTER_API_KEY = None
            
            providers = AITextGeneratorFactory.get_available_providers()
            assert "openai" in providers
            assert len(providers) == 1
    
    def test_service_initialization(self):
        """Test service initializes with drivers"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            service = AITextGeneratorService()
            assert AIProvider.OPENAI in service.drivers
            assert isinstance(service.drivers[AIProvider.OPENAI], OpenAIDriver)
    
    @pytest.mark.asyncio
    async def test_service_driver_registration(self):
        """Test manual driver registration"""
        service = AITextGeneratorService()
        mock_driver = Mock()
        
        service.register_driver(AIProvider.OPENAI, mock_driver)
        
        retrieved_driver = service.get_driver(AIProvider.OPENAI)
        assert retrieved_driver is mock_driver
    
    def test_service_get_nonexistent_driver(self):
        """Test getting a driver that doesn't exist raises error"""
        service = AITextGeneratorService()
        
        with pytest.raises(Exception) as exc_info:
            service.get_driver(AIProvider.ANTHROPIC)
        
        assert "No driver registered for provider" in str(exc_info.value)


class TestOpenAIDriver:
    """Test cases for OpenAI driver"""
    
    def test_driver_properties(self):
        """Test driver basic properties"""
        with patch('app.services.ai.drivers.openai_driver.AsyncOpenAI'):
            driver = OpenAIDriver(api_key="test-key")
            
            assert driver.provider_name == "OpenAI"
            assert driver.default_model == "gpt-4o-mini"
            assert "gpt-4o-mini" in driver.supported_models
            assert "gpt-4o" in driver.supported_models
    
    def test_driver_validate_model(self):
        """Test model validation"""
        with patch('app.services.ai.drivers.openai_driver.AsyncOpenAI'):
            driver = OpenAIDriver(api_key="test-key")
            
            assert driver.validate_model("gpt-4o-mini")
            assert driver.validate_model("gpt-4o")
            assert not driver.validate_model("invalid-model")
    
    def test_driver_get_model_pricing(self):
        """Test getting model pricing"""
        with patch('app.services.ai.drivers.openai_driver.AsyncOpenAI'):
            driver = OpenAIDriver(api_key="test-key")
            
            pricing = driver.get_model_pricing("gpt-4o-mini")
            assert "input_cost_per_token" in pricing
            assert "output_cost_per_token" in pricing
            assert pricing["input_cost_per_token"] > 0
    
    def test_driver_calculate_cost(self):
        """Test cost calculation"""
        with patch('app.services.ai.drivers.openai_driver.AsyncOpenAI'):
            driver = OpenAIDriver(api_key="test-key")
            
            cost = driver.calculate_cost("gpt-4o-mini", 1000, 500)
            assert cost > 0
            assert isinstance(cost, float)
    
    @pytest.mark.asyncio
    async def test_driver_initialization_missing_library(self):
        """Test driver initialization without OpenAI library"""
        with patch('app.services.ai.drivers.openai_driver.AsyncOpenAI', None):
            with pytest.raises(ImportError) as exc_info:
                OpenAIDriver(api_key="test-key")
            
            assert "OpenAI library not installed" in str(exc_info.value)
