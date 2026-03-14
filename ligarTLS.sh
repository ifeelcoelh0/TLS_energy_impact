#!/bin/bash

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting HTTPS backend server..."
cd backend

echo "Exporting keys"
export TLS_ENERGY_API_KEY=123456789
export TLS_ENERGY_HMAC_SECRET=987654321

python -m uvicorn app.main:app \
--host 0.0.0.0 \
--port 8443 \
--ssl-certfile ../certs/server.crt \
--ssl-keyfile ../certs/server.key \
--ssl-ca-certs ../certs/ca.crt \
--ssl-cert-reqs 2 \
--access-log
