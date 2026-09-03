#!/bin/bash

#First build the project
cd /Assurance/src
make
# Start the FastAPI server 
cd /Assurance/api
uvicorn main:app --host 0.0.0.0 --port 8080 --reload