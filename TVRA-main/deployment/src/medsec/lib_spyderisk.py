import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from bs4 import BeautifulSoup
import os
import http.client
import base64
import time
from typing import Dict, Any, List, Optional, Tuple
import math
from tvra_parser import TVRAParser
from logger import get_logger

# Use stdout for logging when not in Docker container
try:
    LOGGER = get_logger('TVRA', '/proc/1/fd/1')
except PermissionError:
    LOGGER = get_logger('TVRA', '/dev/stdout')

HOME_PATH = os.environ['MEDSEC_HOME']

LOGIN_URL = None
SESS = requests.Session()
SESS.verify = False

#SESS.headers.update({'Upgrade-Insecure-Requests': '1','Origin': 'https://172.16.220.254'})
#r = SESS.get('http://host.docker.internal:8089/system-modeller/sso/login')
#print(r.text)

vision_prompts = """
You should perform following step to do threat modeling on this image:\
1 - Recognize and understand all components (e.g., sensors, gateways) and data flows (e.g.,
communication protocols) in this diagram. \
- **For components**, focus on identifying their roles and how they interact with other
components.\
- **For data flows**, focus on identifying how data moves between components and the
methods used to secure these transfers.\
2 - Perform a detailed STRIDE threat modeling analysis on each component and data flow.\
- **For components** (e.g., sensors, gateways), focus on aspects such as functionality,
security configurations, and potential vulnerabilities at the hardware and software levels.
Analyze how each component might be targeted individually in a STRIDE threat model.\
- **For data flows** (e.g., communication protocols, data transfer paths), focus on
aspects such as data integrity, confidentiality, transmission methods, and potential
interception points. Analyze how data flows between components might be targeted in a
STRIDE threat model.\
Consider the healthcare context and specific security challenges related to IoMT systems
when performing the threat modeling.\
3 - Output the STRIDE matrix in a table format, only including columns for
<component/dataflow>, <Threat>, <STRIDE Classification>, <Mitigation Method>, <brief
rationale for each mitigation>.\

NOTE: Threats from the following json have already been identified. You can ignore these threats and only return the ones that are not\
present in the json

Here are already identified threats : {}
"""

def extract_hidden_values(url):
    """
    Find login URL for Keycloak SSO
    :return: Bol so we can throw exception if can't find it
    """
    LOGGER.debug("Extracting values for SSO login.")
    r = SESS.get('{0}/system-modeller/sso/login'.format(url))
    soup = BeautifulSoup(r.content, 'html.parser')
    global LOGIN_URL
    login_input = soup.find(id = "kc-form-login")
    if login_input['action']:
        LOGIN_URL = login_input['action']
        LOGGER.debug("Login URL found.")
        return True
    else:
        LOGGER.debug("Login URL not found.")
        return False

def keycloak_login(username,password):
    """
    Use global LOGIN_URL to send POST request with credentials to Keyclock.
    :param username:
    :param password:
    :return: Bol to throw exception if we can't login
    """
    LOGGER.debug("Sending POST request to login to Keyclock.")
    login_data = {'username':username,'password':password,'credentialId':''}
    r = SESS.post(LOGIN_URL, login_data)
    soup = BeautifulSoup(r.content, 'html.parser')
    welcome_div = soup.find("div",{"class":"welcome-page"})
    #print(r.text)
    if welcome_div:
        LOGGER.debug("Loing successful.")
        return True
    else:
        LOGGER.debug("Loing failed.")
        return False



def login_to_spyderisk(url,username,password):
    """
    Wrapper function to login to spyderisk
    :param username:
    :param password:
    :return: Nothing, it's setting correct cookies in our Request session
    """
    if not LOGIN_URL:
        if extract_hidden_values(url):
            if keycloak_login(username,password):
                return True
            else:
                raise Exception("Failed to login to Spyderisk.")
        else:
            raise Exception("Unable to extract values Keycloak Login URL from SpydeRisk.")
    LOGGER.debug("Already logged in.")
    return True

def list_models():
    """
    List all available models from SpydeRisk
    :return: List of model dictionaries containing id, name, and description
    """
    LOGGER.debug("Getting list of all models")
    r = SESS.get('http://host.docker.internal:8089/system-modeller/models')
    if r.status_code == 200:
        LOGGER.debug("Successfully retrieved models list")
        return r.json()
    else:
        raise Exception(f"Failed to get models list: {r.text}")

def get_model_attack_path_plot(model_id: str, mode: str = "current") -> Optional[str]:
    """Get attack path plot for a model
    
    Args:
        model_id: SpydeRisk model ID
        mode: Risk calculation mode ("current" or "future")
    
    Returns:
        Base64 encoded PNG image or None if failed
    """
    LOGGER.debug(f"Getting attack path plot for model {model_id} in {mode} mode")
    
    # Get model authorization
    r = SESS.get(f'http://host.docker.internal:8089/system-modeller/models/{model_id}/authz')
    
    if r.status_code != 200:
        LOGGER.error(f"Failed to get model authorization. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        return None
        
    authz_dict = r.json()
    if not authz_dict.get("readUrl"):
        LOGGER.error("User has no readURL permission to generate attack path")
        return None

    # Add delay between requests
    time.sleep(1)
    
    # Generate plot
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/adaptor/api/v2/models/{authz_dict["readUrl"]}/path_plot',
        params={
            'risk_mode': mode.upper(),
            'export_format': 'png'
        }
    )
    
    if r.status_code == 200:
        LOGGER.debug("Successfully generated attack path plot")
        return base64.b64encode(r.content).decode('ascii')
    else:
        LOGGER.error(f"Failed to generate attack path plot. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        return None

def find_model(name):
    """
    Find model id to use for asset discovery
    :param name:
    :return: model id
    """
    r = SESS.get('http://host.docker.internal:8089/system-modeller/models')
    for m in r.json():
        if m["name"] == name:
            LOGGER.debug("List model data: %s" % m["id"])
            return(m["id"])
    raise Exception("Unable to find model id for Name:" % name)

def find_assets(model_id):
    """
    Find all assets with TVRA metadata
    :param model_id:
    :return: list of assets
    """
    meta_obj_list = []
    r = SESS.get('http://host.docker.internal:8089/system-modeller/models/{ID}/assets'.format(ID=model_id))
    for a in r.json():
        if a["metadata"]:
            meta_dict = {"label": a["label"], "assetId":a["id"]}
            for m in a["metadata"]:
                LOGGER.debug("Print asset metadata: %s" % m)
                if m["key"].startswith("TVRA"):
                    meta_dict.update({m["key"]: m["value"]})
            meta_dict.update({"model_id":model_id})
            meta_obj_list.append(meta_dict)
    LOGGER.debug("Print TVRA asset found list: %s" % meta_obj_list)
    if not meta_obj_list:
        raise Exception("Unable to find assets to scan")
    else:
        return meta_obj_list

def find_assets_to_scan(model_name):
    """
    Wrapper function to return list of assets to scan, including IP and all credentials
    :param model_name:
    :return: asset to scan with OpenVAS
    """
    model_id = find_model(model_name)
    assets = find_assets(model_id)
    assets_to_scan = []
    for a in assets:
        if "TVRA_HOST" in a and "TVRA_SCAN" in a and a["TVRA_SCAN"].lower() == "yes":
            assets_to_scan.append(a)
        else:
            LOGGER.debug("Warning asset MISSING TVRA_HOST or TVRA_SCAN disabled: %s" % a)
    return assets_to_scan

def get_asset_metadata(model_id,asset_id):
    """
    Get asset metadata we need as when updating METADATA you need to send all existing metadata as well.
    :param model_id:
    :param asset_id:
    :return:
    """
    LOGGER.debug("Get metadata attributes")
    r = SESS.get('http://host.docker.internal:8089/system-modeller/models/{ID}/assets/{AssetID}/meta'.format(ID=model_id,AssetID=asset_id))
    meta = r.json()
    LOGGER.debug("All metadata attributes: %s" % meta)
    return meta

def add_item_to_asset_metadata(model_id,asset_id,key,value):
    """
    Add item to asset metadata.
    :param model_id:
    :param asset_id:
    :return:
    """
    headers = {'Content-Type': 'application/json'}
    meta = get_asset_metadata(model_id,asset_id)
    LOGGER.debug("All metadata attributes: %s" % meta)
    meta.append({"key":key,"value":value})
    LOGGER.debug("Updated metadata attributes: %s" % meta)
    r = SESS.put('http://host.docker.internal:8089/system-modeller/models/{ID}/assets/{AssetID}/meta'.format(ID=model_id,AssetID=asset_id), json=meta,headers=headers)
    LOGGER.debug("Response code: %s" % r.text)
    if not r.status_code == 200:
        raise Exception("Unable to Add new metadata, ERROR: %s" % r.text)



def get_asset_twas(model_id,asset_id):
    """
    Get ExploitTW set we use to control OpenVAS vulnerability disclosure
    :param model_id: model to use
    :param asset_id: asset id
    :return: exploitTW dict
    """
    LOGGER.debug("Get trustworthniness attributes")
    r = SESS.get('http://host.docker.internal:8089/system-modeller/models/{ID}/assets/{AssetID}/twas'.format(ID=model_id,AssetID=asset_id))
    twas = r.json()
    LOGGER.debug("All trustworthniness attributes: %s" % twas)
    for tw in twas:
        if tw.endswith("system#TWAS-ExploitTW-d84d60c5"):
            return(twas[tw])


#Default SpyderRisk TW needed for updates
assertedTWLevel_dict = { "safe" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelSafe","label":"Safe","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":5,"id":"586e2b37"},
                   "very_high" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelVeryHigh","label":"Very High","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":4,"id":"ee582022"},
                   "high" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelHigh","label":"High","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":3,"id":"5869494c"},
                   "medium" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelMedium","label":"Medium","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":2,"id":"eb89635f"},
                   "low" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelLow","label":"Low","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":1,"id":"76771280"},
                   "very_low" : {"uri":"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevelVeryLow","label":"Very Low","description":None,"parents":["http://it-innovation.soton.ac.uk/ontologies/trustworthiness/core#TrustworthinessLevel"],"value":0,"id":"628708ea"}
}

def set_asset_twas(model_id,asset_id,exploitTWset,assertedTWLevel):
    """
    Set new trustworthniness attribute for ExploitTW.
    :param model_id:  Model to use
    :param asset_id:  Asset to use
    :param exploitTWset: Current exploitTW value
    :param assertedTWLevel: new asserted level key from assertedTWLevel_dict
    :return:
    """
    LOGGER.debug("Set trustworthniness attributes explitTW {0} new asserstTW {1}".format(exploitTWset,assertedTWLevel))
    headers = {'Content-Type': 'application/json'}
    #Update assetedTWLevel
    LOGGER.debug("Orginal exploitTWset: %s" % exploitTWset)
    exploitTWset["assertedTWLevel"] = assertedTWLevel_dict[assertedTWLevel]
    LOGGER.debug("Updated exploitTWset: %s" % exploitTWset)
    r = SESS.put('http://host.docker.internal:8089/system-modeller/models/{ID}/assets/{AssetID}/twas'.format(ID=model_id,AssetID=asset_id),headers=headers,json=exploitTWset)
    LOGGER.debug("Set Asset TWAS http return text: %s" % r.text)
    if "completed" in r.text:
        return True
    else:
        raise Exception("Unable to set new ExploitTW value.")

def parse_openvas_json(openvas_json_file,qod=70,severity=7.0):
    """
    Open and parse OpenVAS report JSON file and return only alerts
    :param openvas_json:
    :return:
    """
    vulns_list = []
    with open("{0}/www/completed/{1}.json".format(HOME_PATH,openvas_json_file), 'r', encoding='utf-8') as f:
        openvas_json = json.load(f)
        LOGGER.debug("OpenVAS JSON" % openvas_json)
        for r in openvas_json["get_scans_response"]["scan"]["results"]["result"]:
            if r["@type"] == "Alarm" and int(r["@qod"]) >= qod and float(r["@severity"]) >= severity:
                vulns_list.append(r)
                print(r)
    return vulns_list

risk_matrix = {"very_high": 8.5,"high": 7.0,"medium":6.0,"low":4.0,"very_low":3.0}
def calculate_the_risk(vulns_list):
    """
    Based on vulnerbility score, provide ExploitTW in range very low to safe
    :param vulns_list: List of dict obj per vuln
    :return: String with TW score, e.g. very_low
    """
    #Add some extra logic
    #Any 9.0 and qod 80 is straight very_high
    for v in vulns_list:
        if float(v["@severity"]) >= 9.0 and int(v["@qod"]) >= 80:
            return "very_high"
    #If we have two or more 7.0 vulns and qod 80 then very_high
    vuln_score = 0
    for v in vulns_list:
        if float(v["@severity"]) >= 7.0 and int(v["@qod"]) >= 80:
            vuln_score += float(v["@severity"])
    if vuln_score >= 10:
        return "very_high"
    #Same but for lower qod return High
    for v in vulns_list:
        if float(v["@severity"]) >= 7.0 and int(v["@qod"]) >= 30:
            vuln_score += float(v["@severity"])
    if vuln_score >= 10:
        return "high"
    #For everything else do basic risk_matrix
    for v in vulns_list:
        if float(v["@severity"]) >= risk_matrix["very_high"]:
            return "very_high"
        elif float(v["@severity"]) >= risk_matrix["high"]:
            return "high"
        elif float(v["@severity"]) >= risk_matrix["medium"]:
            return "medium"
        elif float(v["@severity"]) >= risk_matrix["low"]:
            return "low"
        elif float(v["@severity"]) >= risk_matrix["very_low"]:
            return "very_low"
        else:
            return "safe"
    return "safe"

def create_model(name: str) -> str:
    """Create a new model in SpydeRisk"""
    LOGGER.debug(f"Creating new model with name: {name}")
    
    # First try to find and delete existing model
    try:
        existing_model_id = find_model(name)
        LOGGER.debug(f"Found existing model with ID: {existing_model_id}")
        delete_model(existing_model_id)
        LOGGER.debug(f"Deleted existing model: {name}")
    except Exception as e:
        LOGGER.debug(f"No existing model found: {str(e)}")
    
    # Create new model
    data = {
        "name": name,
        "domainGraph": "http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain-network"
    }
    
    r = SESS.post('http://host.docker.internal:8089/system-modeller/models/', json=data)
    
    if r.status_code == 201:
        model_data = r.json()
        LOGGER.debug(f"Model created successfully with ID: {model_data['id']}")
        return model_data['id']
    else:
        raise Exception(f"Failed to create model: {r.text}")

def delete_model(model_id: str) -> bool:
    """Delete an existing model"""
    LOGGER.debug(f"Deleting model with ID: {model_id}")
    
    r = SESS.delete(f'http://host.docker.internal:8089/system-modeller/models/{model_id}')
    
    if r.status_code == 200:
        LOGGER.debug("Model deleted successfully")
        return True
    else:
        raise Exception(f"Failed to delete model: {r.text}")

def create_asset(model_id: str, name: str, asset_type: str, x: int = 4800, y: int = 4700) -> dict:
    """Create a new asset in the model"""
    LOGGER.debug(f"Creating asset: {name} of type: {asset_type}")
    
    data = {
        "label": name,
        "type": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#{asset_type}",
        "asserted": True,
        "visible": True,
        "iconX": x,
        "iconY": y,
        "population": "http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#PopLevelSingleton"
    }
    
    r = SESS.post(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/assets/',
        json=data
    )
    
    if r.status_code == 201:
        asset_data = r.json()
        LOGGER.debug(f"Asset created successfully with ID: {asset_data['asset']['id']}")
        return asset_data['asset']
    else:
        raise Exception(f"Failed to create asset: {r.text}")

def create_relation(model_id: str, from_id: str, to_id: str, relation_type: str = "relatesTo") -> dict:
    """Create a relationship between assets"""
    LOGGER.debug(f"Creating relation from {from_id} to {to_id}")
    
    data = {
        "fromID": from_id,
        "toID": to_id,
        "label": relation_type,
        "type": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#{relation_type}",
        "asserted": True,
        "visible": True
    }
    
    r = SESS.post(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/relations/',
        json=data
    )
    
    if r.status_code == 201:
        relation_data = r.json()
        LOGGER.debug("Relation created successfully")
        return relation_data['relation']
    else:
        raise Exception(f"Failed to create relation: {r.text}")

def get_control_sets(model_id: str, asset_id: str) -> Dict[str, Any]:
    """Get control sets for an asset"""
    LOGGER.debug(f"Getting control sets for asset: {asset_id}")
    
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/assets/{asset_id}/controlsets'
    )
    
    if r.status_code == 200:
        return r.json()
    else:
        LOGGER.error(f"Failed to get control sets. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to get control sets")

def set_control(model_id: str, asset_id: str, control_data: Dict[str, Any]) -> bool:
    """Set control for an asset"""
    LOGGER.debug(f"Setting control for asset: {asset_id}")
    
    # Get control sets to find the correct control URI
    control_sets = get_control_sets(model_id, asset_id)
    
    # Find the control set URI for this control
    control_kind = control_data.get('kind', '').strip()
    if not control_kind:
        LOGGER.error(f"Control set has empty or missing kind field for asset {asset_id}")
        raise Exception(f"Control set has empty kind field for asset {asset_id}")
    
    control_name = control_kind[2:] if control_kind.startswith('CS') else control_kind
    control_uri = None
    
    for uri, control_set in control_sets.items():
        if control_set.get('label') == control_name:
            control_uri = uri
            break
    
    if not control_uri:
        LOGGER.error(f"Could not find control set for {control_name}")
        raise Exception(f"Control set {control_name} not found for asset {asset_id}")
    
    # Map coverage level to proper format, default to 'Safe' if not present
    coverage_level = control_data.get('coverageLevel', 'Safe')
    # Remove any spaces and ensure first letter is capitalized
    coverage_level = ''.join(coverage_level.split()).capitalize()
    
    control_set = {
        "uri": control_uri,
        "proposed": control_data.get('proposed', True),
        "workInProgress": control_data.get('workInProgress', False),
        "coverageLevel": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevel{coverage_level}"
    }
    
    time.sleep(1)  # Add delay between requests
    
    # Update control
    r = SESS.put(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/assets/{asset_id}/control',
        json=control_set
    )
    
    if r.status_code == 200:
        response_data = r.json()  # API returns JSON with controls list
        LOGGER.debug(f"Successfully set control: {response_data}")
        return True
    else:
        LOGGER.error(f"Failed to set control. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception(f"Failed to set control: {r.text}")

def get_twas(model_id: str, asset_id: str) -> Dict[str, Any]:
    """Get trustworthiness attributes for an asset"""
    LOGGER.debug(f"Getting TWAS for asset: {asset_id}")
    
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/assets/{asset_id}/twas'
    )
    
    if r.status_code == 200:
        return r.json()
    else:
        LOGGER.error(f"Failed to get TWAS. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to get TWAS")

def set_trustworthiness_level(model_id: str, asset_id: str, twas_data: Dict[str, Any]) -> bool:
    """Set trustworthiness attributes for an asset"""
    LOGGER.debug(f"Setting trustworthiness for asset: {asset_id}")
    
    # Get TWAS to find the correct URI
    twas_sets = get_twas(model_id, asset_id)
    
    # Find the TWAS URI for this attribute
    twas_kind = twas_data.get('kind', '').strip()
    if not twas_kind:
        LOGGER.error(f"TWAS has empty or missing kind field for asset {asset_id}")
        raise Exception(f"TWAS has empty kind field for asset {asset_id}")
    
    twas_name = twas_kind[4:] if twas_kind.startswith('TWAS') else twas_kind
    twas_uri = None

    for uri, twas_set in twas_sets.items():
        if twas_set.get('attribute', {}).get('label') == twas_name:
            twas_uri = uri
            break

    if not twas_uri:
        LOGGER.error(f"Could not find TWAS for {twas_name}")
        raise Exception(f"TWAS {twas_name} not found for asset {asset_id}")
    
    # Prepare TWAS data using the found URI
    twas_set = {
        "uri": twas_uri,
        "assertedTWLevel": {
            "uri": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#TrustworthinessLevel{twas_data['level']}"
        }
    }
    
    time.sleep(1)  # Add delay between requests
    
    # Update TWAS
    r = SESS.put(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/assets/{asset_id}/twas',
        json=twas_set
    )
    
    if r.status_code == 200:
        LOGGER.debug("Successfully set trustworthiness level")
        return True
    else:
        LOGGER.error(f"Failed to set TWAS. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception(f"Failed to set trustworthiness level: {r.text}")

def set_misbehaviour_impact(model_id: str, misbehaviour_id: str, impact_level: str) -> bool:
    """Set impact level for a misbehaviour"""
    LOGGER.debug(f"Setting impact {impact_level} for misbehaviour: {misbehaviour_id}")
    
    data = {
        "id": misbehaviour_id,
        "uri": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/system#MS-{misbehaviour_id}",
        "impactLevel": {
            "uri": f"http://it-innovation.soton.ac.uk/ontologies/trustworthiness/domain#ImpactLevel{impact_level}"
        }
    }
    
    r = SESS.put(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/misbehaviours/{misbehaviour_id}/impact',
        json=data
    )
    
    if r.status_code == 200 and r.text == "completed":
        LOGGER.debug("Successfully set misbehaviour impact")
        return True
    else:
        raise Exception(f"Failed to set misbehaviour impact: {r.text}")

def check_validation_progress(model_id: str, max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Check validation progress until complete"""
    attempts = 0
    while attempts < max_attempts:
        r = SESS.get(f'http://host.docker.internal:8089/system-modeller/models/{model_id}/validationprogress')
        
        if r.status_code == 200:
            progress = r.json()
            LOGGER.debug(f"Validation progress response: {progress}")
            
            if progress.get("status", "").lower() == "completed":
                LOGGER.debug("Validation completed successfully")
                return True
            elif progress.get("status", "").lower() == "error":
                LOGGER.error(f"Validation failed: {progress.get('message', 'Unknown error')}")
                raise Exception(f"Model validation failed: {progress.get('message', 'Unknown error')}")
        else:
            LOGGER.error(f"Failed to check validation progress. Status code: {r.status_code}")
            LOGGER.error(f"Response: {r.text}")
            raise Exception("Failed to check validation progress")
            
        attempts += 1
        time.sleep(delay)
        
    raise Exception(f"Validation timed out after {max_attempts} attempts")

def validate_model(model_id: str) -> bool:
    """Trigger model validation and wait for completion"""
    LOGGER.debug(f"Starting validation for model: {model_id}")
    
    # Trigger validation
    r = SESS.get(f'http://host.docker.internal:8089/system-modeller/models/{model_id}/validated')
    
    if r.status_code != 202:  # Changed from 200 to 202 for Accepted status
        LOGGER.error(f"Failed to start validation. Status code: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to start model validation")
        
    # Wait for validation to complete
    return check_validation_progress(model_id)

def calculate_risks(model_id: str, mode: str = "FUTURE") -> bool:
    """Calculate risks for the model
    
    Args:
        model_id: ID of the model
        mode: Risk calculation mode ("CURRENT" or "FUTURE")
    """
    LOGGER.debug(f"Starting risk calculation for model: {model_id}")
    
    # Trigger risk calculation
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/calc_risks_blocking',
        params={'mode': mode, 'save': 'true'}
    )
    
    if r.status_code != 200:
        LOGGER.error(f"Failed to start risk calculation. Status code: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to start risk calculation")
        
    # Wait for calculation to complete
    return check_risk_calculation_progress(model_id)

def check_risk_calculation_progress(model_id: str, max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Check risk calculation progress"""
    attempts = 0
    while attempts < max_attempts:
        r = SESS.get(f'http://host.docker.internal:8089/system-modeller/models/{model_id}/riskcalcprogress')
        
        if r.status_code == 200:
            progress = r.json()
            LOGGER.debug(f"Risk calculation progress: {progress}")
            
            if progress.get("progress", 0) >= 0.9:
                LOGGER.debug("Risk calculation completed successfully")
                return True
            elif progress.get("status", "").lower() == "error":
                LOGGER.error(f"Risk calculation failed: {progress.get('message', 'Unknown error')}")
                raise Exception(f"Risk calculation failed: {progress.get('message')}")
        else:
            LOGGER.error(f"Failed to check risk calculation progress. Status: {r.status_code}")
            LOGGER.error(f"Response: {r.text}")
            raise Exception("Failed to check risk calculation progress")
        
        attempts += 1
        time.sleep(delay)
    
    raise Exception(f"Risk calculation timed out after {max_attempts} attempts")

def list_threats(model_id: str, use_cache: bool = False) -> List[Dict[str, Any]]:
    """Get list of threats for a model"""
    LOGGER.debug(f"Getting threats for model: {model_id}")
    
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/threats',
        params={'cached': str(use_cache).lower()}
    )
    
    if r.status_code == 200:
        threats = r.json()
        LOGGER.debug(f"Retrieved {len(threats)} threats")
        return threats
    else:
        LOGGER.error(f"Failed to get threats. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to get threats")

def calculate_recommendations(model_id: str, acceptable_risk_level: str = "Medium", max_attempts: int = 30, delay: float = 1.0) -> list:
    """Calculate and retrieve recommendations for a model"""
    LOGGER.debug(f"Starting recommendations calculation for model: {model_id}")
    
    # Format risk level for URL
    risk_level_param = f"domain#RiskLevel{acceptable_risk_level}"
    
    # Start recommendations calculation
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/recommendations',
        params={
            'riskMode': 'FUTURE',
            'acceptableRiskLevel': risk_level_param,
            'targetURIs': ''
        }
    )
    
    if r.status_code != 202:
        LOGGER.error(f"Failed to start recommendations calculation. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to start recommendations calculation")
        
    try:
        job_id = r.json().get("jobId")
        if not job_id:
            raise Exception("No job ID found in response")
        LOGGER.debug(f"Got recommendations job ID: {job_id}")
    except Exception as e:
        LOGGER.error(f"Failed to parse job ID from response: {str(e)}")
        raise Exception("Failed to parse recommendations job ID")

    # Wait for calculation to complete
    if check_recommendations_progress(model_id, max_attempts, delay):
        time.sleep(2)  # Wait before getting results
        return get_recommendations_results(model_id, job_id)
    return []

def check_recommendations_progress(model_id: str, max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Check recommendations calculation progress"""
    attempts = 0
    while attempts < max_attempts:
        r = SESS.get(f'http://host.docker.internal:8089/system-modeller/models/{model_id}/recommendationsprogress')
        
        if r.status_code == 200:
            progress = r.json()
            LOGGER.debug(f"Recommendations progress: {progress}")
            
            if progress.get("status", "").lower() == "completed":
                LOGGER.debug("Recommendations calculation completed successfully")
                return True
            elif progress.get("status", "").lower() == "error":
                LOGGER.error(f"Recommendations calculation failed: {progress.get('message')}")
                raise Exception(f"Recommendations calculation failed: {progress.get('message')}")
        else:
            LOGGER.error(f"Failed to check recommendations progress. Status: {r.status_code}")
            LOGGER.error(f"Response: {r.text}")
            raise Exception("Failed to check recommendations progress")
        
        attempts += 1
        time.sleep(delay)
    
    raise Exception(f"Recommendations calculation timed out after {max_attempts} attempts")

def get_recommendations_results(model_id: str, job_id: str) -> list:
    """Get recommendations results"""
    r = SESS.get(
        f'http://host.docker.internal:8089/system-modeller/models/{model_id}/recommendations/{job_id}/result'
    )
    
    if r.status_code == 200:
        LOGGER.debug("Recommendations found: %s", r.json())
        return r.json()
    else:
        LOGGER.error(f"Failed to get recommendations results. Status: {r.status_code}")
        LOGGER.error(f"Response: {r.text}")
        raise Exception("Failed to get recommendations results")

def calculate_circular_position(center_x: int, center_y: int, radius: int, angle: float) -> Tuple[int, int]:
    """Calculate position on a circle given center, radius and angle"""
    x = center_x + int(radius * math.cos(angle))
    y = center_y + int(radius * math.sin(angle))
    return x, y

def import_tvra_model(name: str, model_json: str) -> Dict[str, Any]:
    """Import a TVRA model into SpydeRisk"""
    LOGGER.debug(f"In function import_tvra_model: Importing TVRA model: {name}")
    
    # Parse the model
    parser = TVRAParser(json.loads(model_json))
    assets, domains = parser.parse()
    
    # Create new model
    model_id = create_model(name)
    LOGGER.debug(f"Created model with ID: {model_id}")
    
    # Track asset mappings
    asset_id_map = {}
    
    # Get connection counts and find the most connected asset
    connection_counts = parser.get_connection_counts()
    center_asset_id = max(connection_counts.items(), key=lambda x: x[1])[0]
    
    # Define circle parameters
    center_x = 4800  # Center X coordinate
    center_y = 4700  # Center Y coordinate
    radius = 400     # Circle radius
    
    # Place center asset first
    center_asset = assets[center_asset_id]
    LOGGER.debug(f"Creating center asset: {center_asset.name}")
    spyderisk_asset = create_asset(
        model_id=model_id,
        name=center_asset.name,
        asset_type=center_asset.kind,
        x=center_x,
        y=center_y
    )
    asset_id_map[center_asset_id] = spyderisk_asset['id']
    
    # Place other assets in a circle
    other_assets = {k: v for k, v in assets.items() if k != center_asset_id}
    num_assets = len(other_assets)
    
    for i, (asset_id, asset) in enumerate(other_assets.items()):
        # Calculate angle for this asset
        angle = (2 * math.pi * i) / num_assets
        
        # Calculate position on circle
        pos_x, pos_y = calculate_circular_position(center_x, center_y, radius, angle)
        
        LOGGER.debug(f"Creating asset: {asset.name}")
        LOGGER.debug(f"  Kind: {asset.kind}")
        LOGGER.debug(f"  Position: ({pos_x}, {pos_y})")
        
        spyderisk_asset = create_asset(
            model_id=model_id,
            name=asset.name,
            asset_type=asset.kind,
            x=pos_x,
            y=pos_y
        )
        asset_id_map[asset_id] = spyderisk_asset['id']
    
    # Create relationships
    for domain in domains.values():
        LOGGER.debug(f"Processing domain: {domain.name}")
        
        from_asset = next((a for a in assets.values() if a.name.lower() == domain.get_from_asset().lower()), None)
        to_asset = next((a for a in assets.values() if a.name.lower() == domain.get_to_asset().lower()), None)
        
        if not from_asset or not to_asset:
            LOGGER.warning(f"Skipping relation - missing assets")
            continue
        
        from_id = asset_id_map.get(from_asset.id)
        to_id = asset_id_map.get(to_asset.id)
        
        if not from_id or not to_id:
            LOGGER.warning(f"Skipping relation - missing SpydeRisk IDs")
            continue
        
        create_relation(
            model_id=model_id,
            from_id=from_id,
            to_id=to_id,
            relation_type=domain.kind or domain.name or "relatesTo"
        )
    
    # Validate model before setting attributes
    LOGGER.debug("Validating model")
    if not validate_model(model_id):
        LOGGER.error("Model validation failed")
        return {
            "model_id": model_id,
            "model_name": name,
            "status": "validation_failed"
        }
    
    LOGGER.debug("Model validation successful")

    # Set misbehaviours
    LOGGER.debug("Setting misbehaviours")
    for asset_id, asset in assets.items():
        spyderisk_id = asset_id_map[asset_id]
        LOGGER.debug(f"Processing misbehaviours for asset: {asset.name}")
        
        for misb in asset.resolved_misbehaviours:
            if not misb.has_level:
                LOGGER.debug(f"Skipping misbehaviour {misb.kind} - no level specified")
                continue
                
            LOGGER.debug(f"Setting misbehaviour: {misb.kind}")
            LOGGER.debug(f"Level: {misb.level}")
            
            try:
                set_misbehaviour_impact(
                    model_id=model_id,
                    misbehaviour_id=misb.id,
                    impact_level=misb.level
                )
                LOGGER.debug("Misbehaviour impact set successfully")
            except Exception as e:
                LOGGER.error(f"Failed to set misbehaviour impact: {str(e)}")

    # Set trustworthiness attributes
    LOGGER.debug("Setting trustworthiness attributes")
    for asset_id, asset in assets.items():
        spyderisk_id = asset_id_map[asset_id]
        LOGGER.debug(f"Processing TWAS for asset: {asset.name}")
        
        for twa in asset.resolved_twas:
            if not twa.has_level:
                LOGGER.debug(f"Skipping TWAS {twa.kind} - no level specified")
                continue
                
            LOGGER.debug(f"Setting TWAS: {twa.kind}")
            LOGGER.debug(f"Level: {twa.trustworthiness_level}")
            
            try:
                set_trustworthiness_level(
                    model_id=model_id,
                    asset_id=spyderisk_id,
                    twas_data={
                        "kind": twa.kind,
                        "level": twa.trustworthiness_level
                    }
                )
                LOGGER.debug("TWAS set successfully")
            except Exception as e:
                LOGGER.error(f"Failed to set TWAS: {str(e)}")

    # Set controls
    LOGGER.debug("Setting controls")
    for asset_id, asset in assets.items():
        spyderisk_id = asset_id_map[asset_id]
        LOGGER.debug(f"Processing controls for asset: {asset.name}")
        
        for ctrl in asset.resolved_controls:
            if not ctrl.has_coverage_level:
                LOGGER.debug(f"Skipping control {ctrl.kind} - no coverage level specified")
                continue
                
            LOGGER.debug(f"Setting control: {ctrl.kind}")
            LOGGER.debug(f"Proposed: {ctrl.is_proposed}")
            LOGGER.debug(f"Coverage Level: {ctrl.coverage_level}")
            
            try:
                set_control(
                    model_id=model_id,
                    asset_id=spyderisk_id,
                    control_data={
                        "kind": ctrl.kind,
                        "proposed": ctrl.is_proposed,
                        "coverageLevel": ctrl.coverage_level
                    }
                )
                LOGGER.debug("Control set successfully")
            except Exception as e:
                LOGGER.error(f"Failed to set control: {str(e)}")
    
    # Return all required fields for TVRAModelResponse
    return {
        "model_id": model_id,
        "model_name": name,
        "status": "success"
    }
