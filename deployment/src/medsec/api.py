from fastapi import HTTPException, UploadFile
import requests
import re
from schema import ResponseErrorDefault
import schema
from gvm.connections import UnixSocketConnection
from gvm.protocols.latest import Osp
from gvm.transforms import EtreeTransform
from lxml import etree
import lib_openvas
import lib_spyderisk
import base64
import json
import asyncio
from logger import get_logger
import logging

LOGGER = get_logger('TVRA', '/proc/1/fd/1')

default_responses = {
    400: {"description":"Bad request","model": ResponseErrorDefault},
    401: {"description":"Unauthorized","model": ResponseErrorDefault},
    409: {"description":"Conflict","model": ResponseErrorDefault},
    406: {"description":"Not Acceptable","model": ResponseErrorDefault},
    503: {"description":"Service unavaiable","model": ResponseErrorDefault}}

def get_report(scanid: str, type: str, debug: bool = False,format="full"):
    """Get a vulnerability scan report.
    
    Retrieves a report for a completed vulnerability scan in either HTML or JSON format.
    
    Args:
        scanid (str): Unique identifier of the scan
        type (str): Report format, either 'html' or 'json'
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        Union[str, dict]: HTML string for HTML reports, or dict for JSON reports
        
    Raises:
        HTTPException(404): If scan ID not found
        HTTPException(500): If report generation fails
        
    Note:
        Connects to OpenVAS 24.3.0 via Unix socket at /run/ospd/ospd-openvas.sock
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)
    LOGGER.info("API: Generate report for scan id: {0}".format(scanid))
    path = '/run/ospd/ospd-openvas.sock'
    connection = UnixSocketConnection(path=path)
    transform = EtreeTransform()
    osp = Osp(connection=connection, transform=transform)
    with osp:
        response = osp.get_scans(scan_id=scanid)
        try:
            progress = int(response.xpath("/get_scans_response/scan")[0].get('progress'))
        except IndexError:
            raise HTTPException(status_code=404, detail="Scan ID: '{0}' not found".format(scanid))
        if type.lower() == "html":
            LOGGER.info("Create HTML report.")
            report = lib_openvas.create_html_report(response)
            if debug:
                LOGGER.debug("Value: {0}".format(report))
            return report
        elif type.lower() == "json":
            LOGGER.info("Create JSON report with format: {0}".format(format))
            report = lib_openvas.convert_xml_to_json(response, format)
            if debug:
                LOGGER.debug("Value: {0}".format(report))
            return {"type": "json","report": report}

def get_progress(scanid: str, debug: bool = False):
    """Get the progress of a running vulnerability scan.
    
    Args:
        scanid (str): Unique identifier of the scan
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        dict: Contains 'progress' key with integer value 0-100
        
    Raises:
        HTTPException(404): If scan ID not found
        
    Note:
        Connects to OpenVAS 24.3.0 via Unix socket
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)
    LOGGER.info("API: Generate report for scan id: {0}".format(scanid))
    path = '/run/ospd/ospd-openvas.sock'
    connection = UnixSocketConnection(path=path)
    transform = EtreeTransform()
    osp = Osp(connection=connection, transform=transform)
    with osp:
        response = osp.get_scans(scan_id=scanid)
        try:
            progress = int(response.xpath("/get_scans_response/scan")[0].get('progress'))
        except IndexError:
            raise HTTPException(status_code=404, detail="Scan ID: '{0}' not found".format(scanid))
        if debug:
            LOGGER.debug("Value: {0}, Type: {1}".format(progress,type(progress)))
        return {"progress":progress}

def run_scan(name: str, scan: schema.Scan):
    """Start a new vulnerability scan.
    
    Initiates a new OpenVAS scan with the specified configuration.
    
    Args:
        name (str): Name identifier for the scan
        scan (schema.Scan): Scan configuration including:
            - target: Host/IP to scan
            - port_list: Optional custom port list
            - sshuser: Optional SSH username for authenticated scans
            - sshpass: Optional SSH password
            - sshkey: Optional SSH private key (base64 encoded)
            - debug: Enable debug logging
            - debug_ssh: Run SSH-specific tests only
            
    Returns:
        dict: Contains scan name and list of targets with their scan IDs
        
    Raises:
        HTTPException(400): If target format is invalid
        HTTPException(500): If scan initialization fails
        
    Note:
        Uses OpenVAS 24.3.0 for scanning
    """
    LOGGER.info("Scan details: {0}".format(scan))
    if scan.debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)
    if scan.target and not lib_openvas.check_valid_target(scan.target):
        LOGGER.error("Not a valid target: {0}".format(scan.target))
        raise HTTPException(status_code=400, detail={"error": "Invalid target format."})
    target_list = []
    path = '/run/ospd/ospd-openvas.sock'
    connection = UnixSocketConnection(path=path)
    transform = EtreeTransform()
    osp = lib_openvas.MedSecOSP(connection=connection, transform=transform)
    if scan.port_list:
        LOGGER.debug("Custom Ports: {0}".format(scan.port_list))
        ports = scan.port_list.upper()
    else:
        ports = "ALL_TCP_AND_NMAP_5_51_TOP_100_UDP"
    if scan.sshuser and (scan.sshpass or scan.sshkey):
        LOGGER.debug("SSH Mode. Check SSH attributes")
        if scan.sshkey:
            targets = lib_openvas.create_target_list(scan.target,scan.sshuser,sshkey=scan.sshkey,portlist=ports)
        else:
            targets = lib_openvas.create_target_list(scan.target,scan.sshuser,sshpass=scan.sshpass,portlist=ports)
    else:
        targets = lib_openvas.create_target_list(scan.target,portlist=ports)
    target_list.append(targets)
    LOGGER.debug("Target list: {0}".format(target_list))
    if scan.debug_ssh:
        import base64
        if scan.sshkey:
            LOGGER.debug("Decoded key: {0}".format(base64.b64decode(scan.sshkey)))
        vt_selection = lib_openvas.vt_selection_ssh_test
    else:
        vt_selection = lib_openvas.vt_selection_full_and_fast
    LOGGER.debug("Vt selection: {0}".format(vt_selection))
    LOGGER.debug("Loop over the target list")
    targets_scanid = []
    for target in target_list:
        response = osp.get_version()
        LOGGER.debug("Scanner version {0}".format(etree.tostring(response, pretty_print=True).decode('utf-8')))
        response = osp.start_scan(targets=target, vt_selection=vt_selection)
        LOGGER.info("start_scan response {0}".format(etree.tostring(response, pretty_print=True).decode('utf-8')))
        scan_id = response.xpath("/start_scan_response/id")[0].text
        LOGGER.info("Target: {0} Scan ID: {1}".format(target,scan_id))
        targets_scanid.append({"target": {"hosts":target[0]["hosts"],"ports":target[0]["ports"]}, "scan_id": scan_id})
        if scan.debug:
            LOGGER.debug("Targets list: {0}".format(targets_scanid))
    return {"name":name ,"targets": targets_scanid}

def get_plot_png(model_id: str, mode: str, debug: bool = False) -> bytes:
    """Get attack path plot for a SpydeRisk model.
    
    Generates a visual representation of attack paths in PNG format.
    
    Args:
        model_id (str): SpydeRisk model identifier
        mode (str): Risk calculation mode, either 'current' or 'future'
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        bytes: PNG image data
        
    Raises:
        HTTPException(401): If SpydeRisk authentication fails
        HTTPException(404): If plot generation fails
        HTTPException(500): If risk calculation fails
        
    Note:
        Requires successful login to SpydeRisk system-modeller/v3
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    # Login to SpydeRisk
    if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
        raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

    try:
        # Calculate risks first
        LOGGER.debug("Before calculate_risks")
        if not lib_spyderisk.calculate_risks(model_id):
            raise HTTPException(status_code=500, detail="Failed to calculate risks")

        # Generate plot
        LOGGER.debug(f"Generating plot for model {model_id} in {mode} mode")
        plot_img_b64 = lib_spyderisk.get_model_attack_path_plot(model_id, mode)
        
        if not plot_img_b64:
            raise HTTPException(status_code=404, detail="Failed to generate attack path plot")
            
        LOGGER.debug("Plot generated successfully")
        return base64.b64decode(plot_img_b64)
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to generate plot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_plot_threat_model(model_name,threat):
    if threat.debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)
    if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
        raise HTTPException(status_code=404, detail="Unable to login to SpydeRisk")
    model_id = lib_spyderisk.find_model(model_name)
    LOGGER.debug("Model ID found: {0}".format(model_id))
    if threat.mode:
        LOGGER.debug("Running plot mode: {0}".format(threat.mode))
        plot_img_b64 = lib_spyderisk.get_model_attack_path_plot(model_id,threat.mode)
    else:
        plot_img_b64 = lib_spyderisk.get_model_attack_path_plot(model_id)
    LOGGER.debug("Plot generated: {0}".format(plot_img_b64))
    #We have mode threat plot image, no start analysing with Threat Model Companion
    prompts = {
        "instructions": "Analyze the provided image and summarize any important details."
    }
    complete_system_message = lib_spyderisk.vision_prompts.format(prompts)
    # Prepare the payload for OpenAI API
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": lib_spyderisk.vision_prompts
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{plot_img_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000
    }

    # Define headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {threat.api_key}"
    }

    # Make the POST request to OpenAI API
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
    response_json = response.json()

    # Check for errors in the response
    if "choices" in response_json:
        content = response_json["choices"][0]["message"]["content"]
        return {"model_name": model_name, "report": content}
    else:
        raise HTTPException(status_code=404, detail="No response from the AI agent.")


def import_model(model_name,model):
    """
    A placeholder function for Import model. NOT YET IMPLEMENTED.
    """
    if model.debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)
    if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
        raise HTTPException(status_code=404, detail="Unable to login to SpydeRisk")
    #model_id = lib_spyderisk.find_model(model_name)
    #LOGGER.debug("Model ID found: {0}".format(model_id))
    #LOGGER.debug("Running plot mode: {0}".format(model))
    #plot_img_b64 = lib_spyderisk.get_model_attack_path_plot(model_id,model)
    #LOGGER.debug("Plot generated: {0}".format(plot_img_b64))
    return {"model_name": model_name, "info": "Not Yet Implemented !!!!"}

async def import_tvra_model(name: str, model_file: UploadFile, model: dict) -> dict:
    """Import a TVRA model into SpydeRisk"""
    if model.debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    LOGGER.info(f"Importing TVRA model: {name}")

    try:
        # Login to SpydeRisk
        if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
            raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

        # Read and validate the uploaded file
        try:
            contents = await model_file.read()
            model_json = contents.decode()
            # Basic JSON validation
            json.loads(model_json)
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. File must be UTF-8 encoded.")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

        # Import the model
        result = lib_spyderisk.import_tvra_model(name, model_json)
        return result

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to import model: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def _get_risk_level_value(risk_level: dict) -> int:
    """Convert risk level to numeric value for sorting
    
    Args:
        risk_level: Risk level dictionary with label
        
    Returns:
        int: Numeric value for sorting (higher = more severe)
    """
    risk_levels = {
        "VeryHigh": 5,
        "High": 4,
        "Medium": 3,
        "Low": 2,
        "VeryLow": 1,
        "Safe": 0  # For cases where risk level is not set
    }
    
    # Remove spaces and make it one word for comparison
    label = risk_level.get("label", "").replace(" ", "")
    return risk_levels.get(label, 0)

def simplify_threat(threat: dict) -> dict:
    """Simplify a threat object by keeping only specified fields
    
    Args:
        threat: Raw threat data
        
    Returns:
        dict: Simplified threat data
    """
    LOGGER.debug("Threat: {0}".format(threat))
    
    # Extract asset name from pattern.nodes[].assetLabel
    asset_name = ""
    if threat.get("pattern", {}).get("nodes"):
        for node in threat["pattern"]["nodes"]:
            if node.get("assetLabel"):
                asset_name = node["assetLabel"]
                break
    
    # Handle likelihood which may be None
    likelihood = {
        "label": "",
        "description": ""
    }
    if threat.get("likelihood"):
        likelihood = {
            "label": threat["likelihood"].get("label", ""),
            "description": threat["likelihood"].get("description", "")
        }
    
    # Handle riskLevel which may be None
    risk_level = {
        "label": "",
        "description": ""
    }
    if threat.get("riskLevel"):
        risk_level = {
            "label": threat["riskLevel"].get("label", ""),
            "description": threat["riskLevel"].get("description", "")
        }
    
    return {
        "description": threat.get("description", ""),
        "threatens_assets": asset_name,
        "likelihood": likelihood,
        "risk_level": risk_level
    }

def get_model_threats(model_id: str, raw: bool = False, debug: bool = False) -> dict:
    """Get threats for a SpydeRisk model.
    
    Retrieves and optionally processes threat data from a model.
    
    Args:
        model_id (str): SpydeRisk model identifier
        raw (bool, optional): Return unprocessed threat data if True. Defaults to False.
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        dict: Contains:
            - model_id: Model identifier
            - threats: List of threat data
            - raw: Whether data is raw or processed
            
    Raises:
        HTTPException(401): If SpydeRisk authentication fails
        HTTPException(500): If threat retrieval fails
        
    Note:
        Processed threats are sorted by risk level (VeryHigh to Safe)
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    LOGGER.info(f"Getting threats for model: {model_id}")

    try:
        # Login to SpydeRisk
        LOGGER.debug("Before login_to_spyderisk")
        if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
            raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

        # Calculate risks first
        LOGGER.debug("Before calculate_risks")
        if not lib_spyderisk.calculate_risks(model_id):
            raise HTTPException(status_code=500, detail="Failed to calculate risks")

        # Get threats
        LOGGER.debug("Before list_threats")
        threats_data = lib_spyderisk.list_threats(model_id)
        
        # Extract threats list from the nested structure
        LOGGER.debug("Threats data: {0}".format(threats_data))
        
        # Return raw data if requested, otherwise simplify and sort
        if raw:
            threats_list = threats_data
        else:
            threats_list = [simplify_threat(threat) for threat in threats_data]
            # Sort threats by risk level (highest first)
            threats_list.sort(key=lambda x: _get_risk_level_value(x["risk_level"]), reverse=True)
            LOGGER.debug("Sorted threats list: {0}".format(threats_list))
            
        return {
            "model_id": model_id,
            "threats": threats_list,
            "raw": raw
        }

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to get threats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_model_recommendations(model_id: str, acceptable_risk_level: str = "Medium", debug: bool = False) -> dict:
    """Get security recommendations for a SpydeRisk model.
    
    Calculates and retrieves security control recommendations based on risk analysis.
    
    Args:
        model_id (str): SpydeRisk model identifier
        acceptable_risk_level (str, optional): Maximum acceptable risk level. 
            One of: VeryHigh, High, Medium, Low, VeryLow, Safe. Defaults to "Medium".
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        dict: Contains:
            - model_id: Model identifier
            - recommendations: List of recommended security controls
            
    Raises:
        HTTPException(401): If SpydeRisk authentication fails
        HTTPException(500): If recommendation calculation fails
        
    Note:
        Requires successful login to SpydeRisk system-modeller/v3
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    LOGGER.info(f"Getting recommendations for model: {model_id}")

    try:
        # Login to SpydeRisk
        LOGGER.debug("Before login_to_spyderisk")
        if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
            raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

        # Calculate risks first
        LOGGER.debug("Before calculate_risks")
        if not lib_spyderisk.calculate_risks(model_id):
            raise HTTPException(status_code=500, detail="Failed to calculate risks")

        # Get recommendations
        LOGGER.debug("Before calculate_recommendations")
        recommendations = lib_spyderisk.calculate_recommendations(model_id, acceptable_risk_level)
        return {
            "model_id": model_id,
            "recommendations": recommendations
        }

    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def find_model_by_name(name: str, debug: bool = False) -> dict:
    """Find a SpydeRisk model by its name.
    
    Searches for and retrieves model information using its name.
    
    Args:
        name (str): Name of the model to find
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        dict: Contains:
            - model_id: SpydeRisk model identifier
            - model_name: Original model name
            
    Raises:
        HTTPException(401): If SpydeRisk authentication fails
        HTTPException(404): If model not found
        
    Note:
        Requires successful login to SpydeRisk system-modeller/v3
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    LOGGER.info(f"Finding model with name: {name}")

    # Login to SpydeRisk
    if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
        raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

    try:
        model_id = lib_spyderisk.find_model(name)
        return {
            "model_id": model_id,
            "model_name": name
        }
    except Exception as e:
        LOGGER.error(f"Failed to find model: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Model not found: {name}")

def list_all_models(debug: bool = False) -> dict:
    """List all available SpydeRisk models.
    
    Retrieves information about all models in the system.
    
    Args:
        debug (bool, optional): Enable debug logging. Defaults to False.
        
    Returns:
        dict: Contains:
            - models: List of model information, each containing:
                - model_id: SpydeRisk model identifier
                - name: Model name
                - description: Optional model description
                
    Raises:
        HTTPException(401): If SpydeRisk authentication fails
        HTTPException(500): If model listing fails
        
    Note:
        Requires successful login to SpydeRisk system-modeller/v3
    """
    if debug:
        LOGGER.info("Running in debug mode.")
        LOGGER.setLevel(logging.DEBUG)
        for handler in LOGGER.handlers:
            handler.setLevel(logging.DEBUG)

    LOGGER.info("Listing all available models")

    # Login to SpydeRisk
    if not lib_spyderisk.login_to_spyderisk("http://host.docker.internal:8089", "testadmin", "password"):
        raise HTTPException(status_code=401, detail="Failed to login to SpydeRisk")

    try:
        # Get list of models from SpydeRisk
        models_data = lib_spyderisk.list_models()
        
        # Transform the data into our response format
        models = []
        for model in models_data:
            models.append({
                "model_id": model["id"],
                "name": model["name"],
                "description": model.get("description")
            })
            
        return {"models": models}
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))