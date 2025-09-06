from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.config.ai_models import AIProvider, get_ai_model_config


@dataclass
class UsageCost:
    """Cost breakdown for AI usage"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    currency: str = "USD"
    provider: str = ""
    model: str = ""
    calculated_at: datetime = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.utcnow()


class PricingService:
    """Service for calculating AI usage costs across providers"""
    
    def __init__(self):
        self.ai_config = get_ai_model_config()
    
    def calculate_cost(
        self,
        provider: AIProvider,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> UsageCost:
        """
        Calculate cost for AI usage
        
        Args:
            provider: AI provider
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            UsageCost with detailed breakdown
        """
        model_config = self.ai_config.get_model_config(model, provider)
        
        if not model_config:
            return UsageCost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                provider=provider.value,
                model=model
            )
        
        input_cost = input_tokens * model_config.pricing.input_cost_per_token
        output_cost = output_tokens * model_config.pricing.output_cost_per_token
        total_cost = input_cost + output_cost
        
        return UsageCost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            provider=provider.value,
            model=model
        )
    
    def get_model_pricing_info(self, provider: AIProvider, model: str) -> Dict[str, Any]:
        """
        Get pricing information for a specific model
        
        Args:
            provider: AI provider
            model: Model name
            
        Returns:
            Dictionary with pricing information
        """
        model_config = self.ai_config.get_model_config(model, provider)
        
        if not model_config:
            return {
                "model": model,
                "provider": provider.value,
                "available": False,
                "pricing": None
            }
        
        return {
            "model": model,
            "provider": provider.value,
            "available": True,
            "pricing": {
                "input_cost_per_token": model_config.pricing.input_cost_per_token,
                "output_cost_per_token": model_config.pricing.output_cost_per_token,
                "input_cost_per_1k": model_config.pricing.input_cost_per_token * 1000,
                "output_cost_per_1k": model_config.pricing.output_cost_per_token * 1000,
                "input_cost_per_1m": model_config.pricing.input_cost_per_token * 1_000_000,
                "output_cost_per_1m": model_config.pricing.output_cost_per_token * 1_000_000,
                "currency": "USD"
            },
            "features": {
                "context_length": model_config.context_length,
                "supports_functions": model_config.supports_functions,
                "supports_vision": model_config.supports_vision
            }
        }
    
    def estimate_cost(
        self,
        provider: AIProvider,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> UsageCost:
        """
        Estimate cost before making API call
        
        Args:
            provider: AI provider
            model: Model name
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            UsageCost estimate
        """
        return self.calculate_cost(
            provider,
            model,
            estimated_input_tokens,
            estimated_output_tokens
        )
    
    def get_cheapest_model(self, provider: AIProvider, estimated_tokens: int) -> Optional[str]:
        """
        Find the cheapest model for a given provider and estimated token count
        
        Args:
            provider: AI provider
            estimated_tokens: Estimated total tokens (input + output)
            
        Returns:
            Name of cheapest model or None if no models available
        """
        provider_config = self.ai_config.get_provider_config(provider)
        if not provider_config:
            return None
        
        cheapest_model = None
        lowest_cost = float('inf')
        
        # Assume 70% input, 30% output for estimation
        estimated_input = int(estimated_tokens * 0.7)
        estimated_output = int(estimated_tokens * 0.3)
        
        for model_name, model_config in provider_config.models.items():
            cost = model_config.pricing.calculate_cost(estimated_input, estimated_output)
            if cost < lowest_cost:
                lowest_cost = cost
                cheapest_model = model_name
        
        return cheapest_model


# Singleton instance
_pricing_service = None


def get_pricing_service() -> PricingService:
    """Get the singleton pricing service instance"""
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service

