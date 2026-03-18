# O-ETB Docker Build Guide

This guide explains how to build and run the O-ETB (Open Evidential Tool Bus) Docker container with local volume mounting for rapid development.

## Directory Structure

The build directory contains the following key files:

- `Dockerfile`: Defines the container build
- `entrypoint.sh`: Launches both FastAPI and O-ETB
- `Assurance/api/`: Contains Example FastAPI application as an idea to run as interface to O-ETB and to keep docker alive

## Building the Docker Image
The current build assume you have clone the main `https://github.com/MedSecurance/Assurance` git repo into the build directory !!!

1. Navigate to the build directory of your O-ETB repository:

```bash
cd Assurance/build
```

2. Build the Docker image:

```bash
docker build -t o-etb:latest
```

This will create a Docker image tagged as `o-etb:latest` that contains:
- Ubuntu 22.04 as the base OS
- SWI-Prolog installed from the stable PPA
- Python with FastAPI and other dependencies
- The built O-ETB executable
- The FastAPI server for O-ETB command execution

## Running the Container with Volume Mounting

To run the container while mounting your local Assurance directory for rapid development:

```bash
docker run -it --rm \
  -p 8080:8080 \
  -v "$(pwd)/Assurance:/Assurance" \
  o-etb:latest
```

This command:
- Maps port 8080 to access the FastAPI server
- Mounts your local Assurance directory to the container's `/Assurance` path
- Runs the container in interactive mode with a TTY
- Automatically removes the container when it exits

## Accessing the API

To access the auto-generated API documentation:

```
http://localhost:8080/docs
```

## Development Workflow

With volume mounting, you can:

1. Modify files in your local `Assurance` directory
2. Changes are immediately reflected in the running container
3. Restart the container only when necessary (e.g., after modifying Python API code)

Option 2:
Keep your User files in `build/files/KB` and then copy them to container KB. This way you can have better control of diffrent test cases.