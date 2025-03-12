#!/bin/bash
# Script to run the sync application on RunPod

# Set up Python environment
echo "Setting up Python environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting sync application..."
python src/main.py "$@" 