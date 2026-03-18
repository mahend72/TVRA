"""
Configuration for remote AI model endpoints.
Supports runtime configuration for containerized/Kubernetes deployment.
All endpoints must be publicly accessible - no localhost allowed.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ModelConfig:
    """Configuration for a remote model endpoint."""
    provider: str
    base_url: str
    model_name: str
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60
    additional_headers: Optional[Dict[str, str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.base_url or self.base_url.startswith(('localhost', '127.0.0.1', 'http://localhost', 'http://127.0.0.1')):
            raise ValueError(f"Invalid base_url '{self.base_url}'. Localhost endpoints not allowed in containerized environments. Use publicly accessible URLs only.")
        
        if self.provider in ["openai", "anthropic", "azure"] and not self.api_key:
            raise ValueError(f"API key required for provider '{self.provider}'")

# Default template configurations (without API keys - must be provided at runtime)
PROVIDER_TEMPLATES = {
    "openai": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "anthropic": {
        "provider": "anthropic", 
        "base_url": "https://api.anthropic.com",
        "model_name": "claude-3-haiku-20240307",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "azure": {
        "provider": "azure",
        "model_name": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.7,
        "additional_headers": {"api-version": "2024-02-15-preview"}
        # base_url must be provided at runtime
    },
    "groq": {
        "provider": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "llama-3.1-8b-instant",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "together": {
        "provider": "together",
        "base_url": "https://api.together.xyz/v1",
        "model_name": "meta-llama/Llama-3-8b-chat-hf",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "huggingface": {
        "provider": "huggingface",
        "base_url": "https://api-inference.huggingface.co/models",
        "model_name": "microsoft/DialoGPT-medium",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "custom_ollama": {
        "provider": "ollama",
        "model_name": "llama3.1:8b",
        "max_tokens": 4000,
        "temperature": 0.7
        # base_url must be provided at runtime - should be publicly accessible Ollama instance
    }
}

def create_model_config(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    timeout: Optional[int] = None,
    additional_headers: Optional[Dict[str, str]] = None
) -> ModelConfig:
    """
    Create a model configuration with runtime parameters.
    
    Args:
        provider: The AI provider ('openai', 'anthropic', 'azure', 'groq', 'together', 'huggingface', 'custom_ollama')
        api_key: API key for the provider (required for most providers)
        base_url: Custom base URL (required for Azure and custom_ollama)
        model_name: Override default model name
        max_tokens: Override default max tokens
        temperature: Override default temperature
        timeout: Override default timeout
        additional_headers: Additional headers for requests
    
    Returns:
        ModelConfig: Configured model instance
        
    Raises:
        ValueError: If provider is unsupported or required parameters are missing
    """
    if provider not in PROVIDER_TEMPLATES:
        raise ValueError(f"Unsupported provider: {provider}. Available: {list(PROVIDER_TEMPLATES.keys())}")
    
    # Start with template
    template = PROVIDER_TEMPLATES[provider].copy()
    
    # Override with provided parameters
    if api_key is not None:
        template["api_key"] = api_key
    if base_url is not None:
        template["base_url"] = base_url
    if model_name is not None:
        template["model_name"] = model_name
    if max_tokens is not None:
        template["max_tokens"] = max_tokens
    if temperature is not None:
        template["temperature"] = temperature
    if timeout is not None:
        template["timeout"] = timeout
    if additional_headers is not None:
        template["additional_headers"] = additional_headers
    
    # Special handling for providers that require base_url at runtime
    if provider == "azure" and "base_url" not in template:
        raise ValueError("Azure provider requires base_url parameter (your Azure OpenAI endpoint)")
    
    if provider == "custom_ollama" and "base_url" not in template:
        raise ValueError("custom_ollama provider requires base_url parameter (publicly accessible Ollama endpoint)")
    
    return ModelConfig(**template)

def get_supported_providers() -> list:
    """Get list of supported AI providers."""
    return list(PROVIDER_TEMPLATES.keys())

def get_provider_info(provider: str) -> Dict[str, Any]:
    """Get information about a specific provider."""
    if provider not in PROVIDER_TEMPLATES:
        raise ValueError(f"Unsupported provider: {provider}")
    
    info = PROVIDER_TEMPLATES[provider].copy()
    info["requires_api_key"] = provider in ["openai", "anthropic", "azure", "groq", "together", "huggingface"]
    info["requires_base_url"] = provider in ["azure", "custom_ollama"]
    
    return info
