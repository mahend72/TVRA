from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any, Optional

from prompts import threat_json_prompts
from remote_ai_client import call_remote_model

app = FastAPI(title="Threat-Model API")
log = logging.getLogger(__name__)

class ThreatModelRequest(BaseModel):
    threat_model: Dict[str, Any]
    detected_threats: Dict[str, Any]
    # AI Configuration - runtime parameters
    provider: str = "openai"  # Required: AI provider
    api_key: Optional[str] = None  # Required for most providers
    base_url: Optional[str] = None  # Required for Azure and custom_ollama
    model_name: Optional[str] = None  # Override default model
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

def call_remote_ai_model(
    prompt: str, 
    provider: str = "openai",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    Call a remote AI model and return its output.
    Supports OpenAI, Anthropic, Azure OpenAI, and remote Ollama instances.
    """
    try:
        system_message = (
            "You are an expert cybersecurity analyst specializing in threat modeling. "
            "Analyze the provided threat model and identify new threats not already detected. "
            "Follow the instructions precisely and output results in the requested format."
        )
        return call_remote_model(
            prompt=prompt,
            system_message=system_message,
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
    except Exception as e:
        log.error(f"Remote AI model call failed: {e}")
        raise HTTPException(status_code=500, detail=f"Remote AI model generation failed: {str(e)}")

@app.post("/process-threat-model")
async def process_threat_model(req: ThreatModelRequest):
    try:
        # Fill in the system‐style prompt from your prompts.py
        prompt = threat_json_prompts.format(
            detected_threats=req.detected_threats,
            threat_model=req.threat_model
        )
        # Call remote AI model with configuration
        raw = call_remote_ai_model(
            prompt=prompt,
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            model_name=req.model_name,
            max_tokens=req.max_tokens,
            temperature=req.temperature
        )
        return {"response": raw}

    except HTTPException as he:
        raise he
    except Exception as e:
        log.error(f"Internal error processing threat model: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")