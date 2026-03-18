#!/bin/bash

usage() {
    echo "Usage: $0 --name <name> --target <target> [--sshuser <sshuser>] [--sshpass <sshpass>] [--sshkey <sshkey>] [--port_list <port_list>] [--debug] [--debug_ssh] [--spyderurl <spyderurl>] [--spyderuser <spyderuser>] [--spyderpass <spyderpass>] [--spydermodel <spydermodel>] [--progress]"
    exit 1
}

name=""
target=""
sshuser=""
sshpass=""
sshkey=""
port_list=""
background=""
debug=""
debug_ssh=""
spyderurl=""
spyderuser=""
spyderpass=""
spydermodel=""
progress=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --name) name="--name $2"; shift ;;
        --target) target="--target $2"; shift ;;
        --sshuser) sshuser="--sshuser $2"; shift ;;
        --sshpass) sshpass="--sshpass $2"; shift ;;
        --sshkey) sshkey="--sshkey $2"; shift ;;
        --port_list) port_list="--port_list $2"; shift ;;
        --debug) debug="--debug" ;;
        --debug_ssh) debug_ssh="--debug_ssh" ;;
        --spyderurl) spyderurl="--spyderurl $2"; shift ;;
        --spyderuser) spyderuser="--spyderuser $2"; shift ;;
        --spyderpass) spyderpass="--spyderpass $2"; shift ;;
        --spydermodel) spydermodel="--spydermodel $2"; shift ;;
        --progress) progress="True"; shift ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Check for mandatory argument
if [ -z "$name" ] || [ -z "$target" ]; then
    echo "Error: --name and --target are mandatory."
    usage
fi


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
#set -x
if ! docker-compose exec -d ospd_openvas run_scan ${name} ${target} ${sshuser} ${sshpass} ${sshkey} ${port_list} ${debug} ${debug_ssh} ${spyderurl} ${spyderuser} ${spyderpass} ${spydermodel} ; then
    echo "[ERROR]: Failed to run docker run_scan command. Please check docker-compose logs ospd_openvas for more details."
    exit 1
else
    echo "[INFO] Scan started."
fi

if [ -n "${progress}" ]; then
    echo "[INFO]: Viewing scan progress log. You can exit log view using Ctrl-C it won't stop the scan."
    sleep 6
    docker-compose logs -f ospd_openvas
fi