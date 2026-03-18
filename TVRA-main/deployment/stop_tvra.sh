#!/bin/bash

if [ ! -f "docker-compose.yml" ]; then
    echo "[ERROR]: docker-compose.yml file not found. Please change to the TVRA toolkit folder and try again."
    exit 1
fi

if groups $USER | grep &>/dev/null '\bdocker\b' || [ "$EUID" -eq 0 ]; then
    echo "[INFO]: You have sufficient permissions (docker group or root user)."
else
    echo "[ERROR]: You are neither a member of the docker group nor running as root. Please add yourself to the docker group or run with sudo."
    exit 1
fi

if ! command -v docker-compose &>/dev/null; then
    echo "[ERROR]: docker-compose could not be found. Please install docker-compose and try again."
    exit 1
else
    echo "[INFO]: docker-compose is available."
fi

echo "[INFO]: Stopping TVRA ..."
if ! docker-compose down; then
    echo "[ERROR]: Failed to stop containers. Please check docker-compose logs."
    exit 1
fi

echo "[INFO] TVRA stop completed."