from enum import Enum
from pydantic import BaseModel, validator, Field, constr, conint
from typing import Optional, List, Dict, Union, Literal, Any
import lib_openvas
import json
from lib_openvas import LOGGER
from fastapi import UploadFile, File

class Debug(BaseModel):
    """Debug configuration for API operations.
    
    Controls debug logging for various API operations.
    """
    debug: bool = Field(
        default=False, 
        description="Enable debug logging for detailed operation tracing",
        example=True
    )

class ScanID(BaseModel):
    """OpenVAS scan identifier.
    
    Used to reference specific vulnerability scans.
    """
    scanid: str = Field(
        default=None, 
        description="OpenVAS scanid",
        example="43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4"
    )
    debug: Optional[bool] = Field(
        default=False, 
        description="Enable debug messages. True/False",
        example=False
    )

class ReportType(BaseModel):
    """OpenVAS report format specification.
    
    Defines allowed report formats.
    """
    type: constr(regex="^(html|json)$") = Field(
        example="html", 
        description="Allowed report types: html, json"
    )

class Scan(BaseModel):
    """Vulnerability scan configuration.
    
    Defines parameters for OpenVAS 24.3.0 vulnerability scans.
    
    Example:
        ```json
        {
            "target": "192.168.1.100",
            "port_list": "T:22,80,443",
            "sshuser": "admin",
            "sshkey": "base64_encoded_key_here",
            "debug": true,
            "debug_ssh": false
        }
        ```
    """
    target: str = Field(
        ..., 
        description="Target host/IP address to scan",
        example="192.168.1.100"
    )
    debug: bool = Field(
        default=False, 
        description="Enable debug logging",
        example=True
    )
    port_list: Optional[str] = Field(
        None, 
        description="Custom port list. Defaults to ALL_TCP_AND_NMAP_5_51_TOP_100_UDP",
        example="T:22,80,443"
    )
    sshuser: Optional[str] = Field(
        None, 
        description="SSH username for authenticated scans",
        example="admin"
    )
    sshpass: Optional[str] = Field(
        None, 
        description="SSH password for authentication",
        example="password123"
    )
    sshkey: Optional[str] = Field(
        None, 
        description="Base64 encoded SSH private key",
        example="base64_encoded_key_here"
    )
    debug_ssh: bool = Field(
        default=False, 
        description="Run SSH-specific tests only",
        example=False
    )
    @validator('target')
    def check_target(cls, v):
        if not lib_openvas.check_valid_target(v):
            raise ValueError('Wrong target value. Value: {}'.format(v))
        return v

class Threat(BaseModel):
    """
    Base class for OpenAI threat modelling
    """
    api_key: str = Field(description="OpenAI API key")
    prompt_overwrite: Optional[str] = Field(description="Instructions to overwrite prompt")
    predefined_prompts: Optional[constr(regex="^(promptA|promptB)$")] = Field(example="promptB", description="Currently a placeholder where we could add ability to use diffrent then a default prompt but still a predefined, tested one.")
    mode: Optional[constr(regex="^(current|future)$")] = Field(example="json", description="Const: json")
    debug: Optional[bool] = Field(default=False, description="Extra verbose debug info")


class ResponseGetProgress(BaseModel):
    """Scan progress response.
    
    Contains current progress of a running scan.
    
    Example:
        ```json
        {
            "progress": 75
        }
        ```
    """
    progress: int = Field(
        ..., 
        description="Scan progress percentage (0-100)",
        ge=0,
        le=100,
        example=75
    )

class ScanItem(BaseModel):
    """Represents a single scan item with target and scan ID.
    
    Example:
        ```json
        {
            "target": {
                "hosts": "192.168.1.100",
                "ports": "T:22,80,443"
            },
            "scan_id": "43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4"
        }
        ```
    """
    target: Dict[str, str] = Field(
        ..., 
        example={
            "hosts": "192.168.1.100", 
            "ports": "T:22,80,443"
        }
    )
    scan_id: str = Field(
        ..., 
        example="43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4"
    )

class ResponseScan(BaseModel):
    """Scan initiation response.
    
    Contains information about initiated scan(s).
    
    Example:
        ```json
        {
            "name": "weekly_scan",
            "targets": [
                {
                    "target": {
                        "hosts": "192.168.1.100",
                        "ports": "T:22,80,443"
                    },
                    "scan_id": "43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4"
                }
            ]
        }
        ```
    """
    name: str = Field(
        ..., 
        description="Scan name identifier",
        example="weekly_scan"
    )
    targets: List[Dict[str, Any]] = Field(
        ..., 
        description="List of targets and their scan IDs",
        example=[{
            "target": {
                "hosts": "192.168.1.100",
                "ports": "T:22,80,443"
            },
            "scan_id": "43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4"
        }]
    )

class ResponseGetThreat(BaseModel):
    """
    Threat Response message.
    """
    model_name: str = Field(description="Plot model name")
    report: str = Field(description="Threat report content")

class ResponseGetReportJson(BaseModel):
    """JSON vulnerability scan report response.
    
    Contains formatted vulnerability scan results.
    
    Example:
        ```json
        {
            "type": "json",
            "report": {
                "scan_id": "43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4",
                "findings": [
                    {
                        "name": "SSH Weak Configuration",
                        "severity": "MEDIUM",
                        "description": "SSH server is using weak ciphers",
                        "solution": "Configure SSH to use strong ciphers only"
                    }
                ]
            }
        }
        ```
    """
    type: Literal["json"] = Field(
        "json", 
        description="Report format identifier"
    )
    report: List = Field(
        ..., 
        description="Detailed scan results and findings",
        example={
            "scan_id": "43f14b6a-f69c-4cd5-a3db-9cb4a6db93c4",
            "findings": [
                {
                    "name": "SSH Weak Configuration",
                    "severity": "MEDIUM",
                    "description": "SSH server is using weak ciphers",
                    "solution": "Configure SSH to use strong ciphers only"
                }
            ]
        }
    )

class ResponseErrorDefault(BaseModel):
    """Default error response.
    
    Standard error response format.
    """
    detail: str = Field(
        ..., 
        description="Error message details"
    )

class ResponseGetModel(BaseModel):
    """
    Threat Response message.
    """
    model_name: str = Field(description="Model name")
    info: str = Field(description="Extra info")

class TVRAModel(BaseModel):
    """TVRA model import configuration.
    
    Configuration for importing TVRA models into SpydeRisk.
    """
    debug: bool = Field(
        default=False, 
        description="Enable debug logging during model import"
    )


class TVRAModelResponse(BaseModel):
    """
    Response for TVRA model import
    """
    model_id: str = Field(description="SpydeRisk model ID")
    model_name: str = Field(description="Model name")
    status: str = Field(description="Import status")

class ThreatListRequest(BaseModel):
    """
    Request for getting threats list
    """
    model_id: str = Field(description="SpydeRisk model ID")
    debug: Optional[bool] = Field(default=False, description="Enable debug messages")

class SimplifiedThreat(BaseModel):
    """Simplified threat information.
    
    Example:
        ```json
        {
            "description": "Unauthorized access via SSH",
            "threatens_assets": "Web Server",
            "likelihood": {
                "label": "High",
                "description": "Likely to occur"
            },
            "risk_level": {
                "label": "High",
                "description": "Significant impact on system security"
            }
        }
        ```
    """
    description: str = Field(
        description="Threat description",
        example="Unauthorized access via SSH"
    )
    threatens_assets: str = Field(
        description="Asset being threatened",
        example="Web Server"
    )
    likelihood: Dict[str, str] = Field(
        description="Likelihood information",
        example={
            "label": "High",
            "description": "Likely to occur"
        }
    )
    risk_level: Dict[str, str] = Field(
        description="Risk level information",
        example={
            "label": "High",
            "description": "Significant impact on system security"
        }
    )

class ThreatListResponse(BaseModel):
    """Response for threats list.
    
    Example:
        ```json
        {
            "model_id": "model_123",
            "threats": [
                {
                    "description": "Unauthorized access via SSH",
                    "threatens_assets": "Web Server",
                    "likelihood": {
                        "label": "High",
                        "description": "Likely to occur"
                    },
                    "risk_level": {
                        "label": "High",
                        "description": "Significant impact on system security"
                    }
                }
            ],
            "raw": false
        }
        ```
    """
    model_id: str = Field(
        description="SpydeRisk model ID",
        example="model_123"
    )
    threats: List[Dict[str, Any]] = Field(
        description="List of threats",
        example=[{
            "description": "Unauthorized access via SSH",
            "threatens_assets": "Web Server",
            "likelihood": {
                "label": "High",
                "description": "Likely to occur"
            },
            "risk_level": {
                "label": "High",
                "description": "Significant impact on system security"
            }
        }]
    )
    raw: bool = Field(
        description="Whether the response is in raw (True) or simplified (False) format",
        example=False
    )

class RecommendationRequest(BaseModel):
    """
    Request for getting recommendations
    """
    model_id: str = Field(description="SpydeRisk model ID")
    acceptable_risk_level: Optional[str] = Field(default="Medium", description="Acceptable risk level")
    debug: Optional[bool] = Field(default=False, description="Enable debug messages")

class RecommendationResponse(BaseModel):
    """
    Response for recommendations
    """
    model_id: str = Field(description="SpydeRisk model ID")
    recommendations: Dict[str, Any] = Field(description="List of recommendations")

class FindModelRequest(BaseModel):
    """
    Request for finding a model by name
    """
    name: str = Field(description="Name of the model to find")
    debug: Optional[bool] = Field(default=False, description="Enable debug messages")

class FindModelResponse(BaseModel):
    """
    Response for find model request
    """
    model_id: str = Field(description="SpydeRisk model ID")
    model_name: str = Field(description="Model name")

class ModelInfo(BaseModel):
    """
    Basic model information
    """
    model_id: str = Field(description="SpydeRisk model ID")
    name: str = Field(description="Model name")
    description: Optional[str] = Field(description="Model description")

class ListModelsResponse(BaseModel):
    """
    Response for listing models
    """
    models: List[ModelInfo] = Field(description="List of available models")