from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import time

from .schemas import AITextRequest, AITextResponse, AITextGenerationError
from app.config.ai_models import AIProvider
from app.core.config import settings
from .drivers.base_driver import BaseAIDriver
from ..template_manager import TemplateManager


class BaseAITextGenerator(ABC):
    """
    Base service class for AI text generation.
    Provides common functionality and delegates provider-specific operations to drivers.
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        self.drivers: Dict[AIProvider, BaseAIDriver] = {}
        self.template_manager = template_manager or TemplateManager()
        self._initialized = False
    
    def register_driver(self, provider: AIProvider, driver: BaseAIDriver):
        """Register a driver for a specific AI provider"""
        self.drivers[provider] = driver
    
    def get_driver(self, provider: AIProvider) -> BaseAIDriver:
        """Get the driver for a specific provider"""
        if provider not in self.drivers:
            raise AITextGenerationError(
                f"No driver registered for provider: {provider.value}",
                provider.value
            )
        return self.drivers[provider]
    
    async def initialize(self):
        """Initialize all registered drivers"""
        if self._initialized:
            return
            
        for provider, driver in self.drivers.items():
            try:
                await driver.initialize()
            except Exception as e:
                raise AITextGenerationError(
                    f"Failed to initialize {provider.value} driver: {str(e)}",
                    provider.value
                )
        
        self._initialized = True
    
    async def generate_text(self, request: AITextRequest) -> AITextResponse:
        """
        Generate text using the specified provider
        
        Args:
            request: AI text generation request
            
        Returns:
            AITextResponse with generated text and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Process prompt template if template variables are provided
        processed_prompt = await self._process_prompt_template(
            request.prompt, 
            request.template_variables
        )
        
        # Create a copy of the request with processed prompt
        processed_request = request.copy()
        processed_request.prompt = processed_prompt
        
        # Resolve provider: use request provider if given, otherwise service default
        resolved_provider: AIProvider
        if request.provider is None:
            try:
                resolved_provider = AIProvider(settings.AI_DEFAULT_PROVIDER)
            except Exception:
                # Fallback to first available driver if default not valid
                if not self.drivers:
                    raise AITextGenerationError(
                        "No AI providers are configured",
                        "unknown"
                    )
                resolved_provider = next(iter(self.drivers.keys()))
        else:
            resolved_provider = request.provider

        # Get the appropriate driver
        driver = self.get_driver(resolved_provider)
        
        # Validate model
        model = request.model or driver.default_model
        if not driver.validate_model(model):
            raise AITextGenerationError(
                f"Model {model} is not supported by {resolved_provider.value}",
                resolved_provider.value
            )
        
        # Set the model if it wasn't specified
        processed_request.model = model
        # Ensure provider is set on processed request for downstream use
        processed_request.provider = resolved_provider
        
        # Generate text using the driver
        start_time = time.time()
        try:
            response = await driver.generate_text(processed_request)
            response.metadata.response_time_ms = int((time.time() - start_time) * 1000)
            return response
        except Exception as e:
            raise AITextGenerationError(
                f"Text generation failed: {str(e)}",
                resolved_provider.value
            )
    
    async def _process_prompt_template(self, prompt: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """Process prompt with template variables if provided"""
        if not variables:
            return prompt
        
        try:
            # If prompt looks like a template path, render it
            if prompt.endswith('.jinja2') or '/' in prompt:
                return self.template_manager.render_prompt(prompt, variables)
            else:
                # Treat prompt as a Jinja2 template string
                from jinja2 import Template
                template = Template(prompt)
                return template.render(**variables)
        except Exception as e:
            # If template processing fails, return original prompt
            return prompt
    
    async def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available providers and their capabilities"""
        providers_info = {}
        
        for provider, driver in self.drivers.items():
            is_healthy = await driver.health_check()
            providers_info[provider.value] = {
                "name": driver.provider_name,
                "healthy": is_healthy,
                "default_model": driver.default_model,
                "supported_models": driver.supported_models,
            }
        
        return providers_info
    
    async def validate_request(self, request: AITextRequest) -> bool:
        """Validate an AI text generation request"""
        try:
            if not request.prompt.strip():
                return False
            
            # Resolve provider as in generate_text
            resolved_provider: AIProvider
            if request.provider is None:
                try:
                    resolved_provider = AIProvider(settings.AI_DEFAULT_PROVIDER)
                except Exception:
                    return False
            else:
                resolved_provider = request.provider

            if resolved_provider not in self.drivers:
                return False
            
            driver = self.get_driver(resolved_provider)
            model = request.model or driver.default_model
            
            return driver.validate_model(model)
        except:
            return False
