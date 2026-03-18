import requests
import json

def process_threat_model_request(
    threat_model_path, 
    detected_threats_path,
    provider="openai",
    api_key=None,
    base_url=None,
    model_name=None,
    endpoint_url="http://127.0.0.1:8010/process-threat-model"
):
    """
    Process threat model using remote AI endpoint.
    
    Args:
        threat_model_path: Path to threat model JSON file
        detected_threats_path: Path to detected threats JSON file
        provider: AI provider ('openai', 'anthropic', 'azure', 'custom_ollama', etc.)
        api_key: API key for the provider (required for most providers)
        base_url: Custom base URL (required for Azure and custom_ollama)
        model_name: Override default model name
        endpoint_url: URL of the threat model processing endpoint
    
    Example Usage:
        # Using OpenAI
        result = process_threat_model_request(
            "threat_model.json",
            "detected_threats.json",
            provider="openai",
            api_key="sk-..."
        )
        
        # Using Azure OpenAI
        result = process_threat_model_request(
            "threat_model.json", 
            "detected_threats.json",
            provider="azure",
            api_key="your-azure-key",
            base_url="https://your-resource.openai.azure.com"
        )
        
        # Using custom Ollama endpoint
        result = process_threat_model_request(
            "threat_model.json",
            "detected_threats.json", 
            provider="custom_ollama",
            base_url="https://your-ollama-server.com"
        )
    """
    # Read the threat model JSON file
    with open(threat_model_path, "r") as file:
        threat_model = json.load(file)

    # Read the detected threats JSON file
    with open(detected_threats_path, "r") as file:
        detected_threats = json.load(file)

    # Prepare the request payload with AI configuration
    payload = {
        "threat_model": threat_model,
        "detected_threats": detected_threats,
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
        "model_name": model_name
    }

    # Make the POST request to the FastAPI endpoint
    response = requests.post(endpoint_url, json=payload)

    # Return the response
    if response.status_code == 200:
        print("Threat Model API Response:")
        print(json.dumps(response.json(), indent=4))
        return response.json()
    else:
        print(f"Threat Model API Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # Example usage - Update these paths to your actual files
    threat_model_path = "threat_model.json"
    detected_threats_path = "get_threats_OUTPUT.json"
    
    # Example 1: Using OpenAI (requires API key)
    print("=== Using OpenAI ===")
    result = process_threat_model_request(
        threat_model_path, 
        detected_threats_path,
        provider="openai",
        api_key="your-openai-api-key-here"  # Replace with actual API key
    )
    
    # Example 2: Using custom Ollama endpoint (publicly accessible)
    print("\n=== Using Custom Ollama ===") 
    result = process_threat_model_request(
        threat_model_path,
        detected_threats_path,
        provider="custom_ollama",
        base_url="https://your-ollama-server.com"  # Replace with actual URL
    )
    
    # Example 3: Using Azure OpenAI
    print("\n=== Using Azure OpenAI ===")
    result = process_threat_model_request(
        threat_model_path,
        detected_threats_path,
        provider="azure",
        api_key="your-azure-api-key",  # Replace with actual API key
        base_url="https://your-resource.openai.azure.com"  # Replace with actual endpoint
    )