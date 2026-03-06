#!/bin/bash

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting HTTPS backend server..."
cd backend

python -m uvicorn app.main:app \
--host 0.0.0.0 \
--port 8443 \
--ssl-keyfile ../certs/key.pem \
--ssl-certfile ../certs/cert.pem
