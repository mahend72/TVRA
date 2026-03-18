import requests
import pathlib
import json

def process_mitigations(
    threats_json_path,
    provider="openai",
    api_key=None,
    base_url=None,
    model_name=None,
    endpoint_url="http://127.0.0.1:8000/mitigate"
):
    """
    Process threats to generate mitigation strategies using remote AI.
    
    Args:
        threats_json_path: Path to JSON file containing threats
        provider: AI provider ('openai', 'anthropic', 'azure', 'custom_ollama', etc.)
        api_key: API key for the provider (required for most providers)
        base_url: Custom base URL (required for Azure and custom_ollama)
        model_name: Override default model name
        endpoint_url: URL of the mitigation processing endpoint
    
    Example Usage:
        # Using OpenAI
        result = process_mitigations(
            "threats.json",
            provider="openai",
            api_key="sk-..."
        )
        
        # Using Azure OpenAI
        result = process_mitigations(
            "threats.json",
            provider="azure",
            api_key="your-azure-key",
            base_url="https://your-resource.openai.azure.com"
        )
        
        # Using custom Ollama endpoint
        result = process_mitigations(
            "threats.json",
            provider="custom_ollama",
            base_url="https://your-ollama-server.com"
        )
    """
    # Read threats from JSON file
    threats_data = json.loads(pathlib.Path(threats_json_path).read_text(encoding="utf-8"))
    
    # Prepare payload with AI configuration
    payload = {
        "threats": threats_data,
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model_name": model_name
    }
    
    # Make the POST request
    response = requests.post(
        endpoint_url, 
        json=payload,
        headers={"Content-Type": "application/json"}, 
        timeout=300
    )
    response.raise_for_status()
    
    result = response.json()
    
    print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    print(f"Saved to: {result['file']}")
    
    return result

if __name__ == "__main__":
    # Example usage - Update this path to your actual threats file
    threats_file = "get_threats_OUTPUT.json"
    
    # Example 1: Using OpenAI (requires API key)
    print("=== Using OpenAI ===")
    result = process_mitigations(
        threats_file,
        provider="openai",
        api_key="your-openai-api-key-here"  # Replace with actual API key
    )
    
    # Example 2: Using custom Ollama endpoint (publicly accessible)
    print("\n=== Using Custom Ollama ===")
    result = process_mitigations(
        threats_file,
        provider="custom_ollama",
        base_url="https://your-ollama-server.com"  # Replace with actual URL
    )