# TVRA Tool User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Vulnerability Scanning](#vulnerability-scanning)
4. [Threat Modeling](#threat-modeling)
5. [Risk Assessment](#risk-assessment)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Deployment Options](#deployment-options)

## Introduction

TVRA (Threat, Vulnerability and Risk Assessment) is an integrated security assessment tool that combines:
- Vulnerability scanning using OpenVAS 24.3.0
- Threat modeling with SpydeRisk
- AI-powered security analysis using OpenAI GPT-4

### Key Features
- Automated vulnerability scanning
- Attack path visualization
- Risk assessment and scoring
- Security recommendations
- AI-enhanced threat analysis
- Model management and versioning

## Getting Started

### Prerequisites
- Access to OpenVAS 24.3.0 instance
- SpydeRisk system-modeller/v3 credentials
- OpenAI API key (for AI-enhanced analysis)

### Authentication
The API uses SpydeRisk authentication for threat modeling operations. Credentials are automatically cached for improved performance.

**Default SpydeRisk Credentials**:
```
Username: testadmin
Password: password
```
**Note**: These are development credentials. For production deployments, make sure to change these credentials.

### Base URL
```
http://localhost:8000
```

### API Documentation
Access the interactive API documentation at:
```
http://localhost:8000/docs                                                 # TVRA API documentation
http://host.docker.internal:8089/system-modeller/swagger-ui/index.html    # SpydeRisk API documentation
```

The SpydeRisk GUI and API documentation are accessible through the `host.docker.internal` address, which allows containers to access services running on the host machine.

## Vulnerability Scanning

### Starting a New Scan

**Endpoint**: `PUT /v1/scan/{name}`

**Input Example**:
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

**Parameters**:
- `target`: Host/IP to scan (required)
- `port_list`: Custom port list (optional)
- `sshuser`: SSH username for authenticated scans
- `sshpass`: SSH password
- `sshkey`: Base64 encoded SSH private key
- `debug`: Enable debug logging
- `debug_ssh`: Run SSH-specific tests only

**Response Example**:
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

### Monitoring Scan Progress

**Endpoint**: `GET /v1/report/progress/{scanid}`

**Response Example**:
```json
{
    "progress": 75
}
```

### Getting Scan Results

**JSON Format**: `GET /v1/report/{scanid}/json`
**HTML Format**: `GET /v1/report/{scanid}/html`

**JSON Response Example**:
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

## Threat Modeling

### Importing TVRA Models

**Endpoint**: `PUT /v1/model/{name}`

**Input**:
- `name`: Model identifier
- `model_file`: JSON file containing TVRA model data
- `debug`: Enable debug logging

### Analyzing Threats

**Endpoint**: `GET /v1/threat/get_threats`

**Parameters**:
- `model_id`: SpydeRisk model identifier
- `raw`: Return unprocessed threat data (default: false)
- `debug`: Enable debug logging

**Response Example**:
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

### Visualizing Attack Paths

**Endpoint**: `GET /v1/threat/{model_id}/plot`

**Parameters**:
- `model_id`: SpydeRisk model identifier
- `mode`: Risk calculation mode ("current" or "future")
- `debug`: Enable debug logging

**Response**: PNG image showing:
- Assets and their relationships
- Attack vectors
- Risk levels

### Getting Security Recommendations

**Endpoint**: `GET /v1/threat/get_recommendations`

**Parameters**:
- `model_id`: SpydeRisk model identifier
- `acceptable_risk_level`: Maximum acceptable risk level
  - Options: VeryHigh, High, Medium, Low, VeryLow, Safe
  - Default: Medium
- `debug`: Enable debug logging

## Risk Assessment

### Risk Levels
The system uses the following risk levels:
1. VeryHigh: Critical security issues requiring immediate attention
2. High: Significant vulnerabilities that should be addressed soon
3. Medium: Moderate risks that should be planned for remediation
4. Low: Minor issues that should be monitored
5. VeryLow: Minimal risk issues
6. Safe: No significant risk identified

### Risk Calculation
Risk levels are calculated based on:
- Vulnerability severity
- Threat likelihood
- Asset importance
- Attack complexity
- Potential impact

## Best Practices

### Scanning Best Practices
1. Start with a limited port list for faster initial scans
2. Use authenticated scans when possible for better coverage
3. Schedule regular scans for continuous monitoring
4. Review HTML reports for detailed findings

### Threat Modeling Best Practices
1. Keep models up-to-date with system changes
2. Use descriptive names for models and assets
3. Set appropriate risk acceptance levels
4. Review and update threat models regularly

### Security Assessment Workflow
1. Run regular vulnerability scans
2. Import and maintain TVRA models
3. Analyze threats and attack paths
4. Review and implement recommendations
5. Monitor progress and reassess

## Troubleshooting

### Common Issues

#### Scan Issues
- Invalid target format
- SSH authentication failures
- Port access blocked
- Scan timeout

**Solution**: Check network connectivity, credentials, and firewall rules

#### Model Import Issues
- Invalid JSON format
- Missing required fields
- Authentication failures

**Solution**: Validate model format and SpydeRisk credentials

#### API Errors
- 400: Invalid request format
- 401: Authentication failed
- 404: Resource not found
- 500: Internal server error

**Solution**: Check request format and authentication status

### Getting Help
- Check API documentation at `/docs`
- Enable debug logging for detailed information
- Contact TVRA support at support@tvra.example.com

## API Reference

### Report Endpoints

#### Get JSON Report
```http
GET /v1/report/{scanid}/json
```

**Purpose**: Retrieves a detailed vulnerability scan report in JSON format from OpenVAS 24.3.0.

**Path Parameters**:
- `scanid` (string, required): Unique identifier returned from scan initiation

**Query Parameters**:
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
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

**Error Responses**:
- 404: Scan ID not found
- 500: Report generation failed

#### Get HTML Report
```http
GET /v1/report/{scanid}/html
```

**Purpose**: Generates a formatted HTML report suitable for viewing in browsers or saving as documentation.

**Path Parameters**:
- `scanid` (string, required): Unique identifier returned from scan initiation

**Query Parameters**:
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
- Content-Type: text/html
- Body: HTML formatted report containing:
  - Executive summary
  - Vulnerability findings
  - Remediation recommendations
  - Risk assessment

**Error Responses**:
- 404: Scan ID not found
- 500: Report generation failed

#### Check Scan Progress
```http
GET /v1/report/progress/{scanid}
```

**Purpose**: Monitors the progress of an ongoing vulnerability scan.

**Path Parameters**:
- `scanid` (string, required): Unique identifier returned from scan initiation

**Query Parameters**:
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
```json
{
    "progress": 75  // Integer between 0-100
}
```

**Error Responses**:
- 404: Scan ID not found

### Scan Endpoints

#### Start New Scan
```http
PUT /v1/scan/{name}
```

**Purpose**: Initiates a new vulnerability scan using OpenVAS 24.3.0.

**Path Parameters**:
- `name` (string, required): Identifier for the scan

**Request Body**:
```json
{
    "target": "192.168.1.100",           // Required: Host/IP to scan
    "port_list": "T:22,80,443",          // Optional: Custom port list
    "sshuser": "admin",                  // Optional: SSH username
    "sshkey": "base64_encoded_key_here", // Optional: SSH private key
    "debug": true,                       // Optional: Enable debug logging
    "debug_ssh": false                   // Optional: Run SSH tests only
}
```

**Success Response** (200):
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

**Error Responses**:
- 400: Invalid target format
- 500: Scan initialization failed

### Threat Endpoints

#### Get Attack Path Plot
```http
GET /v1/threat/{model_id}/plot
```

**Purpose**: Generates a visual representation of potential attack paths in PNG format.

**Path Parameters**:
- `model_id` (string, required): SpydeRisk model identifier

**Query Parameters**:
- `mode` (string, optional): Risk calculation mode
  - Values: "current" or "future"
  - Default: "current"
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
- Content-Type: image/png
- Body: PNG image visualizing:
  - System assets and relationships
  - Potential attack vectors
  - Risk levels for each path
  - Security controls

**Error Responses**:
- 401: SpydeRisk authentication failed
- 404: Model not found
- 500: Plot generation failed

#### Get Threat Analysis
```http
GET /v1/threat/get_threats
```

**Purpose**: Retrieves comprehensive threat analysis for a specific model.

**Query Parameters**:
- `model_id` (string, required): SpydeRisk model identifier
- `raw` (boolean, optional): Return unprocessed threat data
  - Default: false
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
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

**Error Responses**:
- 401: SpydeRisk authentication failed
- 500: Threat analysis failed

#### Get Security Recommendations
```http
GET /v1/threat/get_recommendations
```

**Purpose**: Generates actionable security recommendations based on risk analysis.

**Query Parameters**:
- `model_id` (string, required): SpydeRisk model identifier
- `acceptable_risk_level` (string, optional): Maximum acceptable risk
  - Values: VeryHigh, High, Medium, Low, VeryLow, Safe
  - Default: "Medium"
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
```json
{
    "model_id": "model_123",
    "recommendations": [
        {
            "control": "Implement SSH key authentication",
            "priority": "High",
            "impact": "Reduces risk of unauthorized access",
            "implementation": "Configure SSH to use public key authentication only"
        }
    ]
}
```

**Error Responses**:
- 401: SpydeRisk authentication failed
- 500: Recommendation generation failed

### Model Endpoints

#### Import TVRA Model
```http
PUT /v1/model/{name}
```

**Purpose**: Imports a TVRA model into SpydeRisk for analysis.

**Path Parameters**:
- `name` (string, required): Model identifier

**Request Body**:
- Content-Type: multipart/form-data
- Fields:
  - `model_file`: JSON file containing TVRA model data
  - `debug` (boolean, optional): Enable detailed logging

**Success Response** (200):
```json
{
    "model_id": "model_123",
    "model_name": "example_model",
    "status": "imported"
}
```

**Error Responses**:
- 400: Invalid model format
- 401: SpydeRisk authentication failed
- 500: Import failed

#### Find Model
```http
GET /v1/model/find/{name}
```

**Purpose**: Locates a specific model by its name.

**Path Parameters**:
- `name` (string, required): Model name to search for

**Query Parameters**:
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
```json
{
    "model_id": "model_123",
    "model_name": "example_model"
}
```

**Error Responses**:
- 401: SpydeRisk authentication failed
- 404: Model not found

#### List Models
```http
GET /v1/model/list
```

**Purpose**: Retrieves a list of all available models.

**Query Parameters**:
- `debug` (boolean, optional): Enable detailed logging
  - Default: false

**Success Response** (200):
```json
{
    "models": [
        {
            "model_id": "model_123",
            "name": "example_model",
            "description": "Production environment model"
        }
    ]
}
```

**Error Responses**:
- 401: SpydeRisk authentication failed
- 500: Listing failed

## Deployment Options

### Quick Start with Docker Compose

The TVRA tool can be deployed in two modes: production and development. Both modes use Docker Compose for orchestration.

#### Production Deployment

Use `docker-compose.yml` for production deployments:

```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The production deployment includes:
- TVRA API service (FastAPI)
- OpenVAS 24.3.0 scanner
- SpydeRisk system (Default credentials: testadmin/password)
- MongoDB database
- Keycloak authentication
- NGINX proxy

Configuration is managed through environment variables in `.env` file:
```env
PROXY_EXTERNAL_PORT=8089
SERVICE_PROTOCOL=http
SERVICE_PORT=8089
SPYDERISK_VERSION=latest
SPYDERISK_ADAPTOR_VERSION=latest

# Default SpydeRisk credentials (change for production)
KEYCLOAK_ADMIN_USERNAME=testadmin
KEYCLOAK_ADMIN_PASSWORD=password
```

#### Development Mode

Use `docker-compose-dev.yml` for development and testing:

```bash
# Start development environment
docker-compose -f docker-compose-dev.yml up -d

# View logs
docker-compose -f docker-compose-dev.yml logs -f

# Stop development environment
docker-compose -f docker-compose-dev.yml down
```

Key features of development mode:
- Local source code mapping for live updates
- Direct access to service ports
- Debug logging enabled
- Hot-reload for API changes

The development configuration maps the local source code:
```yaml
volumes:
  - type: bind
    source: ./src/medsec
    target: /root/medsec
```

This means any changes to files in `./src/medsec` are immediately reflected in the running service without rebuilding containers.

### Building Custom Container

You can customize the TVRA tool by building your own container using the provided `Dockerfile`:

```bash
# Build the container
docker build -t custom-tvra:latest .

# Run the custom container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/src/medsec:/root/medsec \
  --name custom-tvra \
  custom-tvra:latest
```

The `Dockerfile` includes:
- Ubuntu 22.04 base image
- OpenVAS 24.3.0 scanner components
- Required Python packages
- SpydeRisk integration tools
- Custom configurations

Key build arguments and versions:
```dockerfile
ENV GVM_LIBS_VERSION=22.9.1
ENV OPENVAS_SCANNER_VERSION=23.3.0
ENV OSPD_OPENVAS_VERSION=22.7.1
```

### Service Architecture

The complete stack includes:

1. **Proxy Service (NGINX)**
   - Handles routing and SSL termination
   - Port: ${PROXY_EXTERNAL_PORT}:80
   - Configurable through environment variables

2. **SpydeRisk System Modeller (SSM)**
   - Core threat modeling service
   - Depends on MongoDB and Keycloak
   - Manages knowledgebases and model storage

3. **Keycloak Authentication**
   - Handles user authentication
   - Configurable through environment variables
   - Health checks enabled

4. **MongoDB Database**
   - Persistent storage for models and configurations
   - Uses named volumes for data persistence

5. **System Modeller Adaptor**
   - FastAPI application for API integration
   - Runs with Gunicorn and Uvicorn workers
   - Handles API requests and transformations

6. **OpenVAS Scanner**
   - Vulnerability scanning service
   - Port: 8000:8000
   - Includes NVT plugins and advisories

### Network Configuration

All services run on a dedicated Docker network `smd_net` with:
- Internal DNS resolution
- Host machine access via `host.docker.internal`
- Exposed ports for required services

**Understanding host.docker.internal**:
- Special DNS name that resolves to the host machine from inside containers
- Required for inter-service communication, especially with SpydeRisk
- Automatically configured in the Docker Compose files
- Essential for development mode when services need to access each other
- Used by TVRA API to communicate with SpydeRisk running on port 8089

Example usage:
```python
# SpydeRisk API base URL inside containers
SPYDERISK_URL = "http://host.docker.internal:8089"

# Accessing SpydeRisk GUI and API docs
GUI_URL = "http://host.docker.internal:8089/system-modeller"
API_DOCS = "http://host.docker.internal:8089/system-modeller/swagger-ui/index.html"
```

### Persistent Storage

The system uses Docker volumes for persistent data:
```yaml
volumes:
  jena:              # For TDB storage
  knowledgebases:    # For domain models
  mongo-db:          # For MongoDB data
  mongo-configdb:    # For MongoDB config
```

### Development Tips

1. **Live Code Updates**
   - Edit files in `./src/medsec`
   - Changes are immediately available
   - No container rebuild needed

2. **Debugging**
   - Enable debug mode in API calls
   - Check logs with `docker-compose logs`
   - Access service directly through exposed ports

3. **Testing Changes**
   - Use development compose file
   - Monitor logs for errors
   - Use Swagger UI at `/docs` for API testing 