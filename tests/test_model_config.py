"""Tests for Final_Files/config.py — remote AI model configuration.

These exercise pure, deterministic logic used by the AI-assisted threat
modelling and mitigation services (no network access, no secrets).
"""
import pytest

from config import (
    ModelConfig,
    create_model_config,
    get_provider_info,
    get_supported_providers,
)


def test_get_supported_providers_includes_known_providers():
    providers = get_supported_providers()
    for expected in ("openai", "anthropic", "azure", "groq", "together", "custom_ollama"):
        assert expected in providers


def test_create_model_config_openai_uses_template_defaults():
    cfg = create_model_config("openai", api_key="sk-test-placeholder")
    assert cfg.provider == "openai"
    assert cfg.base_url == "https://api.openai.com/v1"
    assert cfg.model_name == "gpt-4o-mini"
    assert cfg.api_key == "sk-test-placeholder"


def test_create_model_config_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_model_config("not-a-real-provider", api_key="x")


def test_create_model_config_requires_api_key_for_openai():
    with pytest.raises(ValueError, match="API key required"):
        create_model_config("openai")


def test_create_model_config_azure_requires_base_url():
    with pytest.raises(ValueError, match="requires base_url"):
        create_model_config("azure", api_key="test-key")


def test_create_model_config_azure_with_base_url_succeeds():
    cfg = create_model_config(
        "azure", api_key="test-key", base_url="https://my-resource.openai.azure.com"
    )
    assert cfg.provider == "azure"
    assert cfg.base_url == "https://my-resource.openai.azure.com"


@pytest.mark.parametrize(
    "bad_url",
    ["localhost", "127.0.0.1", "http://localhost:8000", "http://127.0.0.1:11434"],
)
def test_model_config_rejects_localhost_endpoints(bad_url):
    with pytest.raises(ValueError, match="Localhost endpoints not allowed"):
        ModelConfig(provider="custom_ollama", base_url=bad_url, model_name="llama3.1:8b")


def test_get_provider_info_flags_api_key_and_base_url_requirements():
    openai_info = get_provider_info("openai")
    assert openai_info["requires_api_key"] is True
    assert openai_info["requires_base_url"] is False

    ollama_info = get_provider_info("custom_ollama")
    assert ollama_info["requires_api_key"] is False
    assert ollama_info["requires_base_url"] is True
