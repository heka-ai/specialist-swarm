#!/bin/bash

# Quick start script for the Deal Desk Swarm Dashboard

echo "=========================================="
echo "Deal Desk Swarm - Dashboard Launcher"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip install flask
fi

# Check required files
if [ ! -f ".coordinator_id" ] || [ ! -f ".environment_id" ]; then
    echo "Error: Swarm not set up."
    echo "Please run the setup scripts first:"
    echo "  python setup_environment.py"
    echo "  python create_specialists.py"
    echo "  python upload_skills.py"
    echo "  python create_coordinator.py"
    exit 1
fi

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f ".env" ]; then
        echo "Loading environment variables from .env..."
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo "Error: ANTHROPIC_API_KEY not set and .env not found."
        exit 1
    fi
fi

# Start the dashboard server
echo ""
echo "Starting dashboard server..."
echo "Open your browser at: http://localhost:5000"
echo ""
python dashboard_server.py
