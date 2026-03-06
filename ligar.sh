#!/bin/bash

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting backend server HTTP server on 0.0.0.0:8000..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

