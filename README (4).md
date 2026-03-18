# Remote AI Configuration Examples

This document shows how to configure different remote AI providers for containerized deployment.

## Environment Setup

All endpoints must be publicly accessible. No localhost URLs are allowed.

## Supported Providers

### 1. OpenAI
```json
{
  "provider": "openai",
  "api_key": "sk-your-openai-api-key",
  "model_name": "gpt-4o-mini"
}
```

### 2. Anthropic Claude
```json
{
  "provider": "anthropic", 
  "api_key": "sk-ant-your-anthropic-api-key",
  "model_name": "claude-3-haiku-20240307"
}
```

### 3. Azure OpenAI
```json
{
  "provider": "azure",
  "api_key": "your-azure-openai-key",
  "base_url": "https://your-resource.openai.azure.com",
  "model_name": "gpt-4"
}
```

### 4. Custom Ollama (Remote Server)
```json
{
  "provider": "custom_ollama",
  "base_url": "https://your-public-ollama-server.com",
  "model_name": "llama3.1:8b"
}
```

### 5. Groq
```json
{
  "provider": "groq",
  "api_key": "gsk_your-groq-api-key",
  "model_name": "llama-3.1-8b-instant"
}
```

### 6. Together AI
```json
{
  "provider": "together", 
  "api_key": "your-together-api-key",
  "model_name": "meta-llama/Llama-3-8b-chat-hf"
}
```

## Example API Calls

### Threat Model Processing
```bash
curl -X POST "http://your-api-server:8010/process-threat-model" \
  -H "Content-Type: application/json" \
  -d '{
    "threat_model": {...},
    "detected_threats": {...},
    "provider": "openai",
    "api_key": "sk-your-api-key"
  }'
```

### Mitigation Generation
```bash
curl -X POST "http://your-api-server:8000/mitigate" \
  -H "Content-Type: application/json" \
  -d '{
    "threats": [...],
    "provider": "azure",
    "api_key": "your-azure-key",
    "base_url": "https://your-resource.openai.azure.com" 
  }'
```

## Docker Deployment

When deploying in containers, ensure:

1. All API keys are passed as runtime parameters, not environment variables
2. All endpoints use publicly accessible URLs (no localhost)
3. For custom Ollama, deploy it on a public cloud instance first

## Kubernetes ConfigMaps/Secrets

Store API keys in Kubernetes secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-api-keys
type: Opaque
stringData:
  openai-key: "sk-your-openai-key"
  azure-key: "your-azure-key"
  anthropic-key: "sk-ant-your-anthropic-key"
```

Then inject them at runtime into API calls, not as environment variables.
