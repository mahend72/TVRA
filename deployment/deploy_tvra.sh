#!/bin/bash

# Function to print usage instructions
usage() {
    echo "[INFO]: Usage: $0 [--standalone true]"
    exit 1
}

# Default value for standalone
standalone=false

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
#        --persistence_path) persistence_storage_path="$2"; shift ;;
        --standalone) standalone="$2"; shift ;;
        *) echo "[INFO]: Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Check if the docker-compose.yml file is present in the current directory
if [ ! -f "docker-compose.yml" ]; then
    echo "[ERROR]: docker-compose.yml file not found. Please change to the TVRA toolkit folder and try again."
    exit 1
fi

# Check if the user is in the docker group or running as root (UID 0)
if groups $USER | grep &>/dev/null '\bdocker\b' || [ "$EUID" -eq 0 ]; then
    echo "[INFO]: You have sufficient permissions (docker group or root user)."
else
    echo "[ERROR]: You are neither a member of the docker group nor running as root. Please add yourself to the docker group or run with sudo."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &>/dev/null; then
    echo "[ERROR]: docker-compose could not be found. Please install docker-compose and try again."
    exit 1
else
    echo "[INFO]: docker-compose is available."
fi

# Pull the latest images using docker-compose
echo "[INFO]: Running docker-compose pull..."
if ! docker-compose pull; then
    echo "[ERROR]: Failed to pull docker images."
    exit 1
fi

# Start services based on --standalone flag
if [ "$standalone" == "true" ]; then
    echo "[INFO]: Standalone mode enabled. Running ospd_openvas only..."
    if ! docker-compose up -d ospd_openvas; then
        echo "[ERROR]: Failed to start TVRA standalone mode."
        exit 1
    fi
else
    echo "[INFO]: Standalone mode disabled. Running TVRA..."
    if ! docker-compose up -d ; then
        echo "[ERROR]: Failed to start TVRA."
        exit 1
    fi
fi

# Monitor the logs for the message "[TVRA] Loading VTs"
echo "[INFO]: TVRA VTs loading progress..."
while true; do
    LOADING_VTS=$(docker-compose logs | grep '\[TVRA\] Loading VTs' | tail -1)
    READY=$(docker-compose logs | grep '\[TVRA\] Ready for connection' | tail -1)
    if [ "${READY}" ]; then
        echo "[INFO]: Loading VTs 100% completed."
        break
    else
        echo "$LOADING_VTS"
    fi
    sleep 30
done

# Print final message only if not in standalone mode
if [ "$standalone" != "true" ]; then
    echo '[INFO]: Add 'SERVER IP host.docker.internal' to your Linux /etc/hosts or Windows c:\Windows\Syste32\drivers\etc\hosts file to access scanner results and SpydeRisk interface.'
    echo '[INFO]: Scanner API URL:   http://host.docker.internal:8000/docs'
    echo '[INFO]: SpydeRisk URL: http://host.docker.internal:8089'
else
    echo '[INFO]: Scanner API URL:   http://<IP>:8000/docs'
fi
