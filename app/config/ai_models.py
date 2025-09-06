from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
import yaml


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


@dataclass
class ModelPricing:
    """Pricing information for AI models"""
    input_cost_per_token: float
    output_cost_per_token: float
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate total cost for token usage"""
        return (input_tokens * self.input_cost_per_token) + (output_tokens * self.output_cost_per_token)


@dataclass  
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    provider: AIProvider
    pricing: ModelPricing
    context_length: int
    supports_functions: bool = False
    supports_vision: bool = False


@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    name: str
    provider: AIProvider
    default_model: str
    models: Dict[str, ModelConfig]
    base_url: Optional[str] = None
    organization: Optional[str] = None


class AIModelConfig:
    """Centralized configuration for AI models and providers"""
    
    def __init__(self):
        # Try to load from YAML first, fallback to built-ins
        loaded = self._load_from_yaml()
        self._providers = loaded if loaded else self._initialize_providers()

    def _load_from_yaml(self) -> Optional[Dict[AIProvider, ProviderConfig]]:
        """Load provider/model configuration from YAML file if present."""
        try:
            cfg_path = Path("config/ai_models.yaml")
            if not cfg_path.exists():
                return None
            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            providers: Dict[AIProvider, ProviderConfig] = {}
            raw_providers = (data or {}).get("providers", {})
            for key, entry in raw_providers.items():
                provider_enum = AIProvider(key)
                models: Dict[str, ModelConfig] = {}
                for model_name, m in entry.get("models", {}).items():
                    models[model_name] = ModelConfig(
                        name=model_name,
                        provider=provider_enum,
                        pricing=ModelPricing(
                            input_cost_per_token=float(m["pricing"].get("input_cost_per_token", 0.0)),
                            output_cost_per_token=float(m["pricing"].get("output_cost_per_token", 0.0)),
                        ),
                        context_length=int(m.get("context_length", 0)),
                        supports_functions=bool(m.get("supports_functions", False)),
                        supports_vision=bool(m.get("supports_vision", False)),
                    )

                providers[provider_enum] = ProviderConfig(
                    name=entry.get("name", provider_enum.value.title()),
                    provider=provider_enum,
                    default_model=entry.get("default_model"),
                    models=models,
                    base_url=entry.get("base_url"),
                    organization=entry.get("organization"),
                )

            return providers
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to load AI models from YAML: {e}")
            return None
    
    def _initialize_providers(self) -> Dict[AIProvider, ProviderConfig]:
        """Initialize all provider configurations"""
        return {
            AIProvider.OPENAI: self._get_openai_config(),
            # Add other providers here as they become available
        }
    
    def _get_openai_config(self) -> ProviderConfig:
        """Get OpenAI provider configuration"""
        models = {
            "gpt-4o": ModelConfig(
                name="gpt-4o",
                provider=AIProvider.OPENAI,
                pricing=ModelPricing(
                    input_cost_per_token=0.000005,   # $5 per 1M tokens
                    output_cost_per_token=0.000015   # $15 per 1M tokens
                ),
                context_length=128000,
                supports_functions=True,
                supports_vision=True
            ),
            "gpt-4o-mini": ModelConfig(
                name="gpt-4o-mini", 
                provider=AIProvider.OPENAI,
                pricing=ModelPricing(
                    input_cost_per_token=0.00000015,  # $0.15 per 1M tokens
                    output_cost_per_token=0.0000006   # $0.60 per 1M tokens
                ),
                context_length=128000,
                supports_functions=True,
                supports_vision=True
            ),
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                provider=AIProvider.OPENAI,
                pricing=ModelPricing(
                    input_cost_per_token=0.00001,    # $10 per 1M tokens
                    output_cost_per_token=0.00003    # $30 per 1M tokens
                ),
                context_length=128000,
                supports_functions=True,
                supports_vision=True
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider=AIProvider.OPENAI,
                pricing=ModelPricing(
                    input_cost_per_token=0.00003,    # $30 per 1M tokens
                    output_cost_per_token=0.00006    # $60 per 1M tokens
                ),
                context_length=8192,
                supports_functions=True
            ),
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider=AIProvider.OPENAI,
                pricing=ModelPricing(
                    input_cost_per_token=0.000001,   # $1 per 1M tokens
                    output_cost_per_token=0.000002   # $2 per 1M tokens
                ),
                context_length=16385,
                supports_functions=True
            )
        }
        
        return ProviderConfig(
            name="OpenAI",
            provider=AIProvider.OPENAI,
            default_model="gpt-4o-mini",
            models=models
        )
    
    def get_provider_config(self, provider: AIProvider) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self._providers.get(provider)
    
    def get_model_config(self, model_name: str, provider: AIProvider) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            return None
        return provider_config.models.get(model_name)
    
    def get_supported_models(self, provider: AIProvider) -> List[str]:
        """Get list of supported models for a provider"""
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            return []
        return list(provider_config.models.keys())
    
    def get_default_model(self, provider: AIProvider) -> Optional[str]:
        """Get default model for a provider"""
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            return None
        return provider_config.default_model
    
    def calculate_cost(self, model_name: str, provider: AIProvider, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for token usage"""
        model_config = self.get_model_config(model_name, provider)
        if not model_config:
            return 0.0
        return model_config.pricing.calculate_cost(input_tokens, output_tokens)
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available providers"""
        return list(self._providers.keys())


# Singleton instance
_ai_model_config = None


def get_ai_model_config() -> AIModelConfig:
    """Get the singleton AI model configuration instance"""
    global _ai_model_config
    if _ai_model_config is None:
        _ai_model_config = AIModelConfig()
    return _ai_model_config
