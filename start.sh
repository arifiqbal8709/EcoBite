#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "------------------------------------------------"
echo "Starting ShareMeal Application (Frontend + Backend)"
echo "------------------------------------------------"

# Check if .venv exists and activate if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the Python backend which serves the frontend static files
echo "Running backend/app.py..."
python3 backend/app.py
