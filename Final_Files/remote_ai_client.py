"""
Universal AI client for making requests to various remote AI providers.
Supports OpenAI, Anthropic, Azure OpenAI, and remote Ollama instances.
No localhost dependencies - designed for containerized environments.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
import httpx
from config import ModelConfig, create_model_config

log = logging.getLogger(__name__)

class RemoteAIClient:
    """Client for interacting with remote AI model endpoints."""
    
    def __init__(self, config: ModelConfig):
        """Initialize with model configuration."""
        self.config = config
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def generate_text(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Generate text using the configured remote AI model."""
        try:
            if self.config.provider == "openai":
                return await self._call_openai(prompt, system_message)
            elif self.config.provider == "anthropic":
                return await self._call_anthropic(prompt, system_message)
            elif self.config.provider == "azure":
                return await self._call_azure_openai(prompt, system_message)
            elif self.config.provider == "ollama":
                return await self._call_ollama(prompt, system_message)
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
        except Exception as e:
            log.error(f"Failed to generate text with {self.config.provider}: {e}")
            raise
    
    async def _call_openai(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call OpenAI API."""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = await self.client.post(
            f"{self.config.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    async def _call_anthropic(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call Anthropic Claude API."""
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_message:
            payload["system"] = system_message
        
        response = await self.client.post(
            f"{self.config.base_url}/v1/messages",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["content"][0]["text"].strip()
    
    async def _call_azure_openai(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call Azure OpenAI API."""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "api-key": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        if self.config.additional_headers:
            headers.update(self.config.additional_headers)
        
        payload = {
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = await self.client.post(
            f"{self.config.base_url}/openai/deployments/{self.config.model_name}/chat/completions",
            headers=headers,
            json=payload,
            params={"api-version": headers.get("api-version", "2024-02-15-preview")}
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    async def _call_ollama(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Call remote Ollama API."""
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        
        payload = {
            "model": self.config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = await self.client.post(
            f"{self.config.base_url}/api/generate",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        return result["response"].strip()

# Synchronous wrapper for backwards compatibility
def call_remote_model(
    prompt: str, 
    system_message: Optional[str] = None,
    provider: str = "openai",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs
) -> str:
    """
    Synchronous wrapper for calling remote AI models.
    
    Args:
        prompt: The user prompt to send to the model
        system_message: Optional system message to set context
        provider: AI provider ('openai', 'anthropic', 'azure', etc.)
        api_key: API key for the provider
        base_url: Custom base URL (required for Azure and custom_ollama)
        model_name: Override default model name
        **kwargs: Additional configuration parameters
    
    Returns:
        Generated text from the AI model
        
    Example:
        # Using OpenAI
        result = call_remote_model(
            "What is AI?", 
            provider="openai", 
            api_key="sk-..."
        )
        
        # Using Azure OpenAI
        result = call_remote_model(
            "What is AI?",
            provider="azure",
            api_key="your-azure-key",
            base_url="https://your-resource.openai.azure.com"
        )
        
        # Using custom Ollama endpoint
        result = call_remote_model(
            "What is AI?",
            provider="custom_ollama",
            base_url="https://your-ollama-server.com"
        )
    """
    async def _async_call():
        config = create_model_config(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            **kwargs
        )
        async with RemoteAIClient(config) as client:
            return await client.generate_text(prompt, system_message)
    
    return asyncio.run(_async_call())
