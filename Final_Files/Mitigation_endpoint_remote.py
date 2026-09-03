"""
FastAPI + Remote AI Models (OpenAI, Anthropic, Azure, Ollama)
• Runtime configuration support for containerized environments
• one remote AI call per threat
• incremental disk-flush after every threat
"""

import json
import logging
import datetime
import pathlib
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from remote_ai_client import call_remote_model

app = FastAPI(title="Threat-Mitigation API")
log = logging.getLogger(__name__)

class MitigationRequest(BaseModel):
    threats: list[Dict[str, Any]]
    # AI Configuration - runtime parameters
    provider: str = "openai"  # Required: AI provider
    api_key: Optional[str] = None  # Required for most providers
    base_url: Optional[str] = None  # Required for Azure and custom_ollama
    model_name: Optional[str] = None  # Override default model
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

# ─── Constants ──────────────────────────────────────────────

SAVE_DIR = pathlib.Path("mitigation_outputs")
SAVE_DIR.mkdir(exist_ok=True)

SYSTEM_MSG = (
    "You are a cybersecurity expert specialising in threat modelling, "
    "mitigation planning, and secure architecture for IoT and medical systems."
)

PER_THREAT_PROMPT = (
    "Read the following threat object (JSON). "
    "Return ONLY a short field called 'mitigation_strategy' "
    "(2-4 sentences, reference ISO/OWASP/NIST, consider physical as well as software controls)."
)

# ─── Helpers ────────────────────────────────────────────────

def write_json(path: pathlib.Path, data: Any) -> None:
    """Pretty-print JSON to disk (UTF-8, atomic overwrite)."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

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
    Call a remote AI model and return its raw output.
    Supports OpenAI, Anthropic, Azure OpenAI, and remote Ollama instances.
    """
    try:
        system_message = (
            "You are a cybersecurity expert specialising in threat modelling, "
            "mitigation planning, and secure architecture for IoT and medical systems. "
            "Provide clear, actionable mitigation strategies referencing industry standards."
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

def get_mitigation(
    threat_obj: Dict[str, Any], 
    provider: str = "openai",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """
    Build a single-threat prompt, invoke the remote AI model, parse JSON.
    """
    prompt_block = (
        f"{SYSTEM_MSG}\n"
        f"{PER_THREAT_PROMPT}\n"
        f"{json.dumps(threat_obj, ensure_ascii=False)}"
    )
    raw = call_remote_ai_model(
        prompt=prompt_block,
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature
    )
    try:
        parsed = json.loads(raw)
        return parsed["mitigation_strategy"]
    except Exception as e:
        log.error("Bad JSON from remote AI model: %s", e, exc_info=True)
        # If JSON parsing fails, return the raw response
        return raw

# ─── Endpoint ───────────────────────────────────────────────

@app.post("/mitigate")
async def mitigate(req: MitigationRequest):
    """Process threats and generate mitigation strategies using configured AI provider."""
    if not isinstance(req.threats, list):
        raise HTTPException(status_code=400, detail="`threats` must be a list")

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outfile = SAVE_DIR / f"mitigations_{timestamp}.json"
    out: list = []

    for idx, th in enumerate(req.threats):
        try:
            th["mitigation_strategy"] = get_mitigation(
                threat_obj=th,
                provider=req.provider,
                api_key=req.api_key,
                base_url=req.base_url,
                model_name=req.model_name,
                max_tokens=req.max_tokens,
                temperature=req.temperature
            )
        except HTTPException as he:
            th["mitigation_strategy"] = f"⚠️ {he.detail}"
        except Exception as e:
            log.error(f"Failed to get mitigation for threat {idx}: {e}")
            th["mitigation_strategy"] = "⚠️ Generation failed"
        finally:
            out.append(th)
            write_json(outfile, out)
            log.info("Processed threat %d/%d", idx + 1, len(req.threats))

    return JSONResponse(content={"file": str(outfile), "data": out})

# Backwards compatibility endpoint (deprecated)
@app.post("/mitigate_legacy")
async def mitigate_legacy(request: Request):
    """Legacy endpoint for backwards compatibility. Use /mitigate instead."""
    payload = await request.json()
    threats = payload.get("threats")
    provider = payload.get("provider", "openai")
    api_key = payload.get("api_key")
    base_url = payload.get("base_url")
    
    # Convert to new format
    req = MitigationRequest(
        threats=threats,
        provider=provider,
        api_key=api_key,
        base_url=base_url
    )
    
    return await mitigate(req)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "threat-mitigation-api"}

@app.get("/providers")
async def list_providers():
    """List available AI providers and their requirements."""
    from config import get_supported_providers, get_provider_info
    
    providers = get_supported_providers()
    provider_details = {}
    
    for provider in providers:
        provider_details[provider] = get_provider_info(provider)
    
    return {
        "providers": provider_details,
        "note": "Specify provider and required parameters in request payload"
    }
