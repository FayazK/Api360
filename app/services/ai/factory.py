from typing import Optional, Dict, Any
from app.core.config import settings
from ..template_manager import TemplateManager

from .base import BaseAITextGenerator
from .drivers.openai_driver import OpenAIDriver
from .schemas import AITextGenerationError
from app.config.ai_models import get_ai_model_config, AIProvider


class AITextGeneratorService(BaseAITextGenerator):
    """
    Concrete implementation of the AI text generation service.
    Manages driver registration and initialization.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        super().__init__(template_manager)
        self._register_available_drivers()
    
    def _register_available_drivers(self):
        """Register all available drivers based on configuration"""
        ai_config = get_ai_model_config()
        
        # Register OpenAI driver if API key is available
        if settings.OPENAI_API_KEY:
            openai_config = ai_config.get_provider_config(AIProvider.OPENAI)
            openai_driver = OpenAIDriver(
                api_key=settings.OPENAI_API_KEY,
                config=openai_config,
                organization=getattr(settings, 'OPENAI_ORGANIZATION', None)
            )
            self.register_driver(AIProvider.OPENAI, openai_driver)
        
        # TODO: Add other providers as they become available
        # if settings.ANTHROPIC_API_KEY:
        #     anthropic_config = ai_config.get_provider_config(ConfigAIProvider.ANTHROPIC)
        #     anthropic_driver = AnthropicDriver(
        #         api_key=settings.ANTHROPIC_API_KEY,
        #         config=anthropic_config
        #     )
        #     self.register_driver(AIProvider.ANTHROPIC, anthropic_driver)


class AITextGeneratorFactory:
    """
    Factory class for creating and managing AI text generation service instances.
    Provides singleton pattern for service management.
    """
    
    _instance: Optional[AITextGeneratorService] = None
    _template_manager: Optional[TemplateManager] = None
    
    @classmethod
    def get_service(cls, template_manager: Optional[TemplateManager] = None) -> AITextGeneratorService:
        """
        Get or create the AI text generation service instance.
        
        Args:
            template_manager: Optional template manager instance
            
        Returns:
            AITextGeneratorService instance
        """
        if cls._instance is None:
            if template_manager is None:
                template_manager = TemplateManager(settings.TEMPLATES_DIR)
            
            cls._template_manager = template_manager
            cls._instance = AITextGeneratorService(template_manager)
        
        return cls._instance
    
    @classmethod
    async def initialize_service(cls, template_manager: Optional[TemplateManager] = None) -> AITextGeneratorService:
        """
        Initialize the AI service and all its drivers.
        
        Args:
            template_manager: Optional template manager instance
            
        Returns:
            Initialized AITextGeneratorService instance
        """
        service = cls.get_service(template_manager)
        await service.initialize()
        return service
    
    @classmethod
    def reset_service(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None
        cls._template_manager = None
    
    @classmethod
    def is_service_available(cls) -> bool:
        """Check if any AI providers are configured and available"""
        return bool(
            settings.OPENAI_API_KEY or 
            settings.ANTHROPIC_API_KEY or 
            settings.GEMINI_API_KEY or
            settings.OPENROUTER_API_KEY
        )
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of configured providers"""
        providers = []
        
        if settings.OPENAI_API_KEY:
            providers.append(AIProvider.OPENAI.value)
        
        if settings.ANTHROPIC_API_KEY:
            providers.append(AIProvider.ANTHROPIC.value)
        
        if settings.GEMINI_API_KEY:
            providers.append(AIProvider.GEMINI.value)
            
        if settings.OPENROUTER_API_KEY:
            providers.append(AIProvider.OPENROUTER.value)
        
        return providers
    
    @classmethod
    def validate_provider_configuration(cls, provider: str) -> bool:
        """Validate if a provider is properly configured"""
        provider_key_mapping = {
            AIProvider.OPENAI.value: settings.OPENAI_API_KEY,
            AIProvider.ANTHROPIC.value: settings.ANTHROPIC_API_KEY,
            AIProvider.GEMINI.value: settings.GEMINI_API_KEY,
            AIProvider.OPENROUTER.value: settings.OPENROUTER_API_KEY,
        }
        
        return bool(provider_key_mapping.get(provider))


# Convenience functions for easy access
async def get_ai_service() -> AITextGeneratorService:
    """Get the initialized AI text generation service"""
    return await AITextGeneratorFactory.initialize_service()


def create_ai_service(template_manager: Optional[TemplateManager] = None) -> AITextGeneratorService:
    """Create a new AI text generation service instance"""
    return AITextGeneratorFactory.get_service(template_manager)
