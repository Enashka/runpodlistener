#!/bin/bash
# Setup script for ComfyUI Image Sync Tool
# Author: Enashka

# Create directory and navigate to it
mkdir -p /workspace/runpodlistener
cd /workspace/runpodlistener

# Check each file individually and only download if it doesn't exist
echo "Checking for necessary files..."

# Check for minimal_sync.py
if [ ! -f "minimal_sync.py" ]; then
    echo "Downloading minimal_sync.py..."
    curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/minimal_sync.py
    chmod +x minimal_sync.py
else
    echo "minimal_sync.py already exists in persistent storage."
fi

# Check for config.yaml but ONLY download if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Downloading config.yaml..."
    curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/config.yaml
else
    echo "config.yaml already exists in persistent storage. Preserving your configuration."
fi

# Check for start.sh
if [ ! -f "start.sh" ]; then
    echo "Downloading start.sh..."
    curl -O https://raw.githubusercontent.com/Enashka/runpodlistener/main/start.sh
    chmod +x start.sh
else
    echo "start.sh already exists in persistent storage."
fi

# Install dependencies
echo "Installing dependencies..."
pip install pydrive2 python-dotenv pyyaml

# Check if folder ID is already configured
FOLDER_ID_CONFIGURED=false
# Check if folder_id in config.yaml is not the default "YOUR_FOLDER_ID"
if grep -q "folder_id:" config.yaml; then
    FOLDER_ID=$(grep "folder_id:" config.yaml | cut -d '"' -f 2)
    if [ "$FOLDER_ID" != "YOUR_FOLDER_ID" ] && [ ! -z "$FOLDER_ID" ]; then
        FOLDER_ID_CONFIGURED=true
        echo "Google Drive folder ID already configured in config.yaml: $FOLDER_ID"
    fi
fi

# Prompt for Google Drive folder ID if not configured
if [ "$FOLDER_ID_CONFIGURED" = false ]; then
    echo "Please enter your Google Drive folder ID:"
    read FOLDER_ID
    
    # Update folder ID in config.yaml
    echo "Updating folder ID in config.yaml..."
    sed -i "s/folder_id: \".*\"/folder_id: \"$FOLDER_ID\"/" config.yaml
fi

# Check if credentials.json exists
if [ -f "credentials.json" ]; then
    echo "credentials.json found in persistent storage."
else
    # Prompt for credentials.json
    echo "IMPORTANT: You need to upload your credentials.json file to /workspace/runpodlistener/"
    echo "Please use the RunPod file browser to upload it now."
    echo "Press Enter once you've uploaded the credentials.json file..."
    read
    
    # Check if credentials.json exists
    if [ ! -f "credentials.json" ]; then
        echo "Error: credentials.json not found. Please upload it and try again."
        exit 1
    fi
fi

# Check if token.json exists (already authenticated)
if [ -f "token.json" ]; then
    echo "Authentication token found in persistent storage. Skipping authentication."
else
    # Run authentication
    echo "Starting authentication process..."
    python minimal_sync.py --once
    
    # Check if token.json was created
    if [ ! -f "token.json" ]; then
        echo "Error: Authentication failed. token.json not created."
        exit 1
    fi
fi

# Start the sync service
echo "Starting sync service..."
./start.sh

echo "Setup complete! The sync service is now running in the background."
echo "You can check the logs with: tail -f sync.log" 