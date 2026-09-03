# TVRA System Diagrams

## System Architecture
```mermaid
graph TB
    subgraph Client
        UI[Web UI]
        CLI[CLI Client]
    end

    subgraph TVRA_API[TVRA API Service]
        API[FastAPI Application]
        Logger[Logging System]
        Cache[Cache Layer]
    end

    subgraph Security_Services
        OpenVAS[OpenVAS 24.3.0]
        SpydeRisk[SpydeRisk System]
    end

    subgraph Storage
        Reports[Report Storage]
        Models[Model Storage]
    end

    UI --> |HTTP/REST| API
    CLI --> |HTTP/REST| API
    API --> Logger
    API --> Cache
    API --> |Unix Socket| OpenVAS
    API --> |HTTP/REST| SpydeRisk
    OpenVAS --> Reports
    SpydeRisk --> Models
```

## Scan Workflow
```mermaid
sequenceDiagram
    participant Client
    participant API as TVRA API
    participant OpenVAS
    participant Storage

    Client->>API: PUT /v1/scan/{name}
    Note over Client,API: Scan configuration (target, ports, credentials)
    API->>OpenVAS: Initialize scan
    OpenVAS-->>API: Return scan ID
    API->>Client: Return scan details

    loop Progress Check
        Client->>API: GET /v1/report/progress/{scanid}
        API->>OpenVAS: Check progress
        OpenVAS-->>API: Return progress %
        API->>Client: Return progress
    end

    Client->>API: GET /v1/report/{scanid}/json
    API->>OpenVAS: Request report
    OpenVAS->>Storage: Generate report
    Storage-->>OpenVAS: Return report data
    OpenVAS-->>API: Return report
    API->>Client: Return formatted report
```

## Threat Analysis Flow
```mermaid
sequenceDiagram
    participant Client
    participant API as TVRA API
    participant SpydeRisk
    participant AI as OpenAI GPT-4

    Client->>API: PUT /v1/model/{name}
    Note over Client,API: Upload TVRA model
    API->>SpydeRisk: Import model
    SpydeRisk-->>API: Return model ID

    Client->>API: GET /v1/threat/{model_id}/plot
    API->>SpydeRisk: Calculate risks
    SpydeRisk->>SpydeRisk: Process model
    SpydeRisk-->>API: Return attack path plot
    API->>Client: Return PNG visualization

    Client->>API: GET /v1/threat/get_threats
    API->>SpydeRisk: Analyze threats
    SpydeRisk-->>API: Return threat data
    API->>Client: Return formatted threats

    Client->>API: PUT /v1/threat/{name}
    API->>SpydeRisk: Get model plot
    SpydeRisk-->>API: Return plot
    API->>AI: Analyze plot
    AI-->>API: Return analysis
    API->>Client: Return threat analysis
```

## Component Architecture
```mermaid
graph TB
    subgraph API_Layer[API Layer]
        Routes[FastAPI Routes]
        Middleware[CORS & Auth]
        Validation[Input Validation]
    end

    subgraph Core_Services[Core Services]
        Scanner[Vulnerability Scanner]
        ThreatAnalyzer[Threat Analyzer]
        RiskCalculator[Risk Calculator]
    end

    subgraph Integration[Integration Layer]
        OpenVASLib[lib_openvas]
        SpydeRiskLib[lib_spyderisk]
        AIConnector[OpenAI Connector]
    end

    subgraph External[External Services]
        OpenVAS[OpenVAS 24.3.0]
        SpydeRisk[SpydeRisk]
        OpenAI[OpenAI GPT-4]
    end

    Routes --> Middleware
    Middleware --> Validation
    Validation --> Core_Services
    Scanner --> OpenVASLib
    ThreatAnalyzer --> SpydeRiskLib
    RiskCalculator --> SpydeRiskLib
    ThreatAnalyzer --> AIConnector
    OpenVASLib --> OpenVAS
    SpydeRiskLib --> SpydeRisk
    AIConnector --> OpenAI
```

## Data Flow
```mermaid
graph LR
    subgraph Input[Input Sources]
        ScanConfig[Scan Configuration]
        TVRAModel[TVRA Model]
        UserQueries[User Queries]
    end

    subgraph Processing[Processing Layer]
        Scanner[Vulnerability Scanner]
        ModelProcessor[Model Processor]
        RiskAnalyzer[Risk Analyzer]
    end

    subgraph Analysis[Analysis Layer]
        ThreatDetection[Threat Detection]
        RiskAssessment[Risk Assessment]
        RecommendationEngine[Recommendation Engine]
    end

    subgraph Output[Output Layer]
        Reports[Vulnerability Reports]
        Visualizations[Attack Path Plots]
        Recommendations[Security Recommendations]
    end

    ScanConfig --> Scanner
    TVRAModel --> ModelProcessor
    UserQueries --> RiskAnalyzer

    Scanner --> ThreatDetection
    ModelProcessor --> RiskAssessment
    RiskAnalyzer --> RecommendationEngine

    ThreatDetection --> Reports
    RiskAssessment --> Visualizations
    RecommendationEngine --> Recommendations
```

## Authentication Flow
```mermaid
sequenceDiagram
    participant Client
    participant API as TVRA API
    participant SpydeRisk
    participant Cache

    Client->>API: Request requiring auth
    API->>Cache: Check cached credentials
    alt Credentials cached
        Cache-->>API: Return valid credentials
    else No valid credentials
        API->>SpydeRisk: Login request
        SpydeRisk-->>API: Authentication response
        API->>Cache: Store credentials
    end
    API->>SpydeRisk: Original request
    SpydeRisk-->>API: Response
    API->>Client: Processed response
```

## Error Handling Flow
```mermaid
graph TD
    subgraph Input[Input Validation]
        A[Request Received]
        B[Schema Validation]
        C[Parameter Validation]
    end

    subgraph Processing[Error Processing]
        D[Error Detection]
        E[Error Classification]
        F[Error Logging]
    end

    subgraph Response[Error Response]
        G[Format Error]
        H[Add Context]
        I[Send Response]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I

    B -- Invalid --> E
    C -- Invalid --> E
    D -- Success --> Success[Success Response]
```

## Model Management Flow
```mermaid
sequenceDiagram
    participant Client
    participant API as TVRA API
    participant Validator as Model Validator
    participant SpydeRisk
    participant Storage

    Client->>API: Upload TVRA model
    API->>Validator: Validate model format
    Validator-->>API: Validation result
    
    alt Valid model
        API->>SpydeRisk: Import model
        SpydeRisk->>Storage: Store model
        Storage-->>SpydeRisk: Confirm storage
        SpydeRisk-->>API: Return model ID
        API->>Client: Success response
    else Invalid model
        API->>Client: Validation error
    end

    Client->>API: Request model list
    API->>SpydeRisk: Get models
    SpydeRisk->>Storage: Fetch models
    Storage-->>SpydeRisk: Return models
    SpydeRisk-->>API: Model list
    API->>Client: Return formatted list
``` 