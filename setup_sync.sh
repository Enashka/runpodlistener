#!/bin/bash
# Setup script for ComfyUI Image Sync Tool
# Author: Enashka

# Create directory and navigate to it
mkdir -p /workspace/runpodlistener
cd /workspace/runpodlistener

# Download necessary files
echo "Downloading files..."
curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/minimal_sync.py
curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/config.yaml
curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/start.sh
chmod +x minimal_sync.py start.sh

# Install dependencies
echo "Installing dependencies..."
pip install pydrive2 python-dotenv pyyaml

# Prompt for Google Drive folder ID
echo "Please enter your Google Drive folder ID:"
read FOLDER_ID

# Update folder ID in config.yaml
echo "Updating folder ID in config.yaml..."
sed -i "s/YOUR_FOLDER_ID/$FOLDER_ID/" config.yaml

# Prompt for credentials.json
echo "IMPORTANT: You need to upload your credentials.json file to /workspace/runpodlistener/"
echo "Please use the RunPod file browser to upload it now."
echo "Press Enter once you've uploaded the credentials.json file..."
read

# Check if credentials.json exists
if [ ! -f "/workspace/runpodlistener/credentials.json" ]; then
    echo "Error: credentials.json not found. Please upload it and try again."
    exit 1
fi

# Run authentication
echo "Starting authentication process..."
python minimal_sync.py --once

# Check if token.json was created
if [ ! -f "/workspace/runpodlistener/token.json" ]; then
    echo "Error: Authentication failed. token.json not created."
    exit 1
fi

# Start the sync service
echo "Starting sync service..."
./start.sh

echo "Setup complete! The sync service is now running in the background."
echo "You can check the logs with: tail -f sync.log" 