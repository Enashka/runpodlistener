#!/bin/bash
# Startup script for RunPod to set up and run the image sync tool

# Define persistent storage location
PERSISTENT_DIR="/workspace"
INSTALL_DIR="$PERSISTENT_DIR/runpodlistener"

# Check if already installed
if [ -d "$INSTALL_DIR" ]; then
  echo "RunPod Image Sync already installed, updating..."
  cd $INSTALL_DIR
  git pull
else
  # Clone the repository
  echo "Cloning the image sync repository..."
  mkdir -p $INSTALL_DIR
  cd $INSTALL_DIR
  git clone https://github.com/Enashka/runpodlistener.git .
fi

# Create and configure .env file if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo "Configuring environment variables..."
  cp .env.example .env
  # No need to set RUNPOD_POD_ID since we're running directly on the pod
  sed -i 's/RUNPOD_API_KEY=your_runpod_api_key/RUNPOD_API_KEY=/' .env
  sed -i 's/RUNPOD_POD_ID=your_runpod_pod_id/RUNPOD_POD_ID=/' .env
  
  # If GOOGLE_DRIVE_FOLDER_ID is set as an environment variable, use it
  if [ ! -z "$GOOGLE_DRIVE_FOLDER_ID" ]; then
    sed -i "s|GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id|GOOGLE_DRIVE_FOLDER_ID=${GOOGLE_DRIVE_FOLDER_ID}|" .env
  else
    echo "WARNING: GOOGLE_DRIVE_FOLDER_ID not set. You'll need to edit .env manually."
  fi
else
  echo "Using existing .env configuration."
fi

# Check for credentials
if [ ! -f "$INSTALL_DIR/credentials.json" ]; then
  echo "WARNING: credentials.json not found. Authentication will fail."
  echo "Please upload your Google Drive API credentials to $INSTALL_DIR/credentials.json"
else
  echo "Found credentials.json file."
fi

# Set up Python environment
echo "Setting up Python environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the sync tool in the background
echo "Starting image sync tool in the background..."
nohup python src/main.py > sync.log 2>&1 &

echo "Image sync tool started. Check sync.log for details." 