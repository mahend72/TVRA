from fastapi import FastAPI, Security, Depends, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.encoders import jsonable_encoder
import api
import schema
from fastapi import HTTPException
from typing import Dict, Any


app = FastAPI(
    title="TVRA API",
    description="""
    TVRA (Threat, Vulnerability and Risk Assessment) API provides endpoints for:
    - Running vulnerability scans using OpenVAS 24.3.0
    - Managing threat models in SpydeRisk
    - Analyzing security risks and generating recommendations
    
    ## Key Features
    * Vulnerability Scanning
    * Threat Modeling
    * Risk Assessment
    * Security Recommendations
    
    ## Authentication
    API uses SpydeRisk authentication for threat modeling operations.
    """,
    version="1.0.0",
    contact={
        "name": "TVRA Support",
        "email": "support@tvra.example.com"
    }
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example responses for documentation
example_report_json_response = {
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

example_scan_request = {
    "target": "192.168.1.100",
    "port_list": "T:22,80,443",
    "sshuser": "admin",
    "sshkey": "base64_encoded_key_here",
    "debug": True,
    "debug_ssh": False
}

example_scan_response = {
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

example_threat_response = {
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
    "raw": False
}

print("INFO:    Access API at <localhost:8000>/docs")

@app.get("/v1/report/{scanid}/json",
         response_model=schema.ResponseGetReportJson,
         responses={
             200: {
                 "description": "Successful response",
                 "content": {
                     "application/json": {
                         "example": example_report_json_response
                     }
                 }
             },
             **api.default_responses
         },
         tags=["report"])
async def get_report_json(scanid: str, format: str = "simple", debug: bool = False):
    """Get vulnerability scan report in JSON format.
    
    Retrieves detailed scan results and findings from OpenVAS 24.3.0.
    
    Args:
        scanid: Unique identifier of the scan
        format: Format of the report (simple, full)
        debug: Enable debug logging
        
    Returns:
        JSON object containing:
            - type: "json"
            - report: Detailed scan findings
            
    Example Response:
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
            
    Raises:
        404: Scan ID not found
        500: Report generation failed
    """
    return api.get_report(scanid.strip(), "json", debug, format)

@app.get("/v1/report/{scanid}/html",
         response_class=HTMLResponse, 
         responses=api.default_responses, 
         tags=["report"])
async def get_report_html(scanid: str, debug: bool = False):
    """Get vulnerability scan report in HTML format.
    
    Generates a formatted HTML report suitable for viewing or downloading.
    
    Args:
        scanid: Unique identifier of the scan
        debug: Enable debug logging
        
    Returns:
        HTML formatted report containing:
            - Executive summary
            - Vulnerability findings
            - Remediation recommendations
            
    Raises:
        404: Scan ID not found
        500: Report generation failed
    """
    return HTMLResponse(content=api.get_report(scanid.strip(), "html", debug), status_code=200)

@app.get("/v1/report/progress/{scanid}",
         response_model=schema.ResponseGetProgress, 
         responses=api.default_responses, 
         tags=["report"])
async def get_progress(scanid: str, debug: bool = False):
    """Get vulnerability scan progress.
    
    Retrieves current progress percentage of a running scan.
    
    Args:
        scanid: Unique identifier of the scan
        debug: Enable debug logging
        
    Returns:
        JSON object containing:
            - progress: Integer 0-100 indicating completion percentage
            
    Raises:
        404: Scan ID not found
    """
    return api.get_progress(scanid.strip(), debug)

@app.put("/v1/scan/{name}",
         response_model=schema.ResponseScan,
         responses={
             200: {
                 "description": "Scan started successfully",
                 "content": {
                     "application/json": {
                         "example": example_scan_response
                     }
                 }
             },
             **api.default_responses
         },
         tags=["scan"])
def start_scan(
    name: str,
    scan: schema.Scan = Body(
        ...,
        example=example_scan_request,
        description="Scan configuration parameters"
    )
):
    """Start a new vulnerability scan.
    
    Initiates an OpenVAS 24.3.0 scan with specified configuration.
    
    Args:
        name: Identifier for the scan
        scan: Scan configuration including:
            - target: Host/IP to scan
            - port_list: Optional custom port list
            - sshuser: Optional SSH username
            - sshpass: Optional SSH password
            - sshkey: Optional SSH key (base64)
            - debug: Enable debug logging
            - debug_ssh: Run SSH tests only
            
    Example Request:
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
    
    Example Response:
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
            
    Raises:
        400: Invalid target format
        500: Scan initialization failed
    """
    return api.run_scan(name.strip(), scan)

@app.put("/v1/threat/{name}", response_model=schema.ResponseGetThreat, responses=api.default_responses, tags=["threat"])
def run_threat_moddeling(name: str, threat: schema.Threat):
    """
    Get Attack Path Plot for the spyderisk model and run Threat Moddeling Companion analysis.
    """
    return api.get_plot_threat_model(name.strip(),threat)

@app.get("/v1/threat/{model_id}/plot",
         response_class=Response,
         responses=api.default_responses, 
         tags=["threat"])
def get_attack_path_plot(model_id: str, mode: str = "current", debug: bool = False):
    """Get attack path visualization.
    
    Generates a PNG visualization of attack paths in a SpydeRisk model.
    
    Args:
        model_id: SpydeRisk model identifier
        mode: Risk calculation mode ("current" or "future")
        debug: Enable debug logging
        
    Returns:
        PNG image showing:
            - Assets and their relationships
            - Attack vectors
            - Risk levels
            
    Raises:
        401: SpydeRisk authentication failed
        404: Model not found
        500: Plot generation failed
    """
    return Response(
        content=api.get_plot_png(model_id.strip(), mode, debug),
        media_type="image/png"
    )


@app.put("/v1/model/{name}", response_model=schema.TVRAModelResponse, responses=api.default_responses, tags=["model"])
async def import_model(
    name: str, 
    model_file: UploadFile = File(...),
    debug: bool = False
):
    """
    Import TVRA model into SpydeRisk.
    
    Parameters:
    - name: Name for the imported model
    - model_file: JSON file containing the TVRA model data
    - debug: Enable debug logging
    """
    model = schema.TVRAModel(debug=debug)
    return await api.import_tvra_model(name.strip(), model_file, model)

@app.get("/v1/threat/get_threats",
         response_model=schema.ThreatListResponse,
         responses={
             200: {
                 "description": "Threats retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": example_threat_response
                     }
                 }
             },
             **api.default_responses
         },
         tags=["threat"])
def get_threats(model_id: str, raw: bool = False, debug: bool = False):
    """Get model threats.
    
    Retrieves threat analysis results from a SpydeRisk model.
    
    Args:
        model_id: SpydeRisk model identifier
        raw: Return unprocessed threat data
        debug: Enable debug logging
        
    Example Response:
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
            
    Raises:
        401: SpydeRisk authentication failed
        500: Threat analysis failed
    """
    return api.get_model_threats(model_id.strip(), raw, debug)

@app.get("/v1/threat/get_recommendations",
         response_model=schema.RecommendationResponse, 
         responses=api.default_responses, 
         tags=["threat"])
def get_recommendations(model_id: str, acceptable_risk_level: str = "Medium", debug: bool = False):
    """Get security recommendations.
    
    Generates security control recommendations based on risk analysis.
    
    Args:
        model_id: SpydeRisk model identifier
        acceptable_risk_level: Maximum acceptable risk level
            (VeryHigh, High, Medium, Low, VeryLow, Safe)
        debug: Enable debug logging
        
    Returns:
        JSON object containing:
            - model_id: Model identifier
            - recommendations: List of recommended controls
            
    Raises:
        401: SpydeRisk authentication failed
        500: Recommendation generation failed
    """
    return api.get_model_recommendations(model_id.strip(), acceptable_risk_level, debug)

@app.get("/v1/model/find/{name}",
         response_model=schema.FindModelResponse, 
         responses=api.default_responses, 
         tags=["model"])
def find_model(name: str, debug: bool = False):
    """Find model by name.
    
    Searches for a SpydeRisk model using its name.
    
    Args:
        name: Model name to search for
        debug: Enable debug logging
        
    Returns:
        JSON object containing:
            - model_id: SpydeRisk model identifier
            - model_name: Original model name
            
    Raises:
        401: SpydeRisk authentication failed
        404: Model not found
    """
    return api.find_model_by_name(name.strip(), debug)

@app.get("/v1/model/list",
         response_model=schema.ListModelsResponse, 
         responses=api.default_responses, 
         tags=["model"])
def list_models(debug: bool = False):
    """List all models.
    
    Retrieves information about all available SpydeRisk models.
    
    Args:
        debug: Enable debug logging
        
    Returns:
        JSON object containing:
            - models: List of model information
                - model_id: Model identifier
                - name: Model name
                - description: Optional description
                
    Raises:
        401: SpydeRisk authentication failed
        500: Model listing failed
    """
    return api.list_all_models(debug)