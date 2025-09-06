from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..schemas import AITextRequest, AITextResponse


class BaseAIDriver(ABC):
    """
    Base class for AI drivers that implement text generation for specific providers.
    Each driver handles the provider-specific implementation details.
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the AI provider"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider"""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """Return list of supported models for this provider"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the client connection"""
        pass
    
    @abstractmethod
    async def generate_text(self, request: AITextRequest) -> AITextResponse:
        """
        Generate text using the provider's API
        
        Args:
            request: AI text generation request
            
        Returns:
            AITextResponse with generated text and metadata
        """
        pass
    
    @abstractmethod
    def validate_model(self, model: str) -> bool:
        """Validate if the model is supported by this provider"""
        pass
    
    @abstractmethod
    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a model
        
        Returns:
            Dict with 'input_cost_per_token' and 'output_cost_per_token'
        """
        pass
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        try:
            pricing = self.get_model_pricing(model)
            input_cost = input_tokens * pricing.get('input_cost_per_token', 0)
            output_cost = output_tokens * pricing.get('output_cost_per_token', 0)
            return input_cost + output_cost
        except:
            return 0.0
    
    async def health_check(self) -> bool:
        """Check if the provider service is available"""
        try:
            if not self._client:
                await self.initialize()
            return True
        except:
            return False