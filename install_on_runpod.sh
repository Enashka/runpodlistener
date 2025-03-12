#!/bin/bash
# Installation script for RunPod ComfyUI Image Sync
# Updated version for GitHub raw content

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Define persistent storage location
PERSISTENT_DIR="/workspace"
INSTALL_DIR="$PERSISTENT_DIR/runpodlistener"

# Prompt for Google Drive folder ID
read -p "Enter your Google Drive folder ID: " GOOGLE_DRIVE_FOLDER_ID
if [ -z "$GOOGLE_DRIVE_FOLDER_ID" ]; then
  echo "Google Drive folder ID is required"
  exit 1
fi

# Create installation directory
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone the repository
echo "Cloning the repository..."
if [ -d ".git" ]; then
  git pull
else
  git clone https://github.com/Enashka/runpodlistener.git .
fi

# Create .env file
echo "Creating .env file..."
cp .env.example .env
sed -i "s|GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id|GOOGLE_DRIVE_FOLDER_ID=$GOOGLE_DRIVE_FOLDER_ID|" .env

# Install dependencies using the existing Python environment
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for credentials in persistent storage
CREDS_FILE="$INSTALL_DIR/credentials.json"
TOKEN_FILE="$INSTALL_DIR/token.json"

if [ ! -f "$CREDS_FILE" ]; then
  echo ""
  echo "You need to provide a credentials.json file for Google Drive API."
  echo "Please follow these steps:"
  echo "1. Go to https://console.cloud.google.com/"
  echo "2. Create a new project"
  echo "3. Enable the Google Drive API"
  echo "4. Create OAuth credentials (Desktop app)"
  echo "5. Download the credentials JSON file"
  echo "6. Upload it to your RunPod instance as credentials.json"
  echo ""
  read -p "Press Enter when you have uploaded credentials.json to $INSTALL_DIR..."

  if [ ! -f "$CREDS_FILE" ]; then
    echo "credentials.json not found. Please upload it and try again."
    exit 1
  fi
else
  echo "Found existing credentials.json file."
fi

# Create a systemd service file for auto-start
echo "Creating startup service..."
cat > /etc/systemd/system/runpod-sync.service << EOL
[Unit]
Description=RunPod ComfyUI Image Sync
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python $INSTALL_DIR/src/main.py
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl enable runpod-sync
systemctl start runpod-sync

echo ""
echo "Installation complete!"
echo "The sync service is now running in the background."
echo "You can check its status with: systemctl status runpod-sync"
echo "View logs with: journalctl -u runpod-sync"
echo ""

# Check if token file exists
if [ ! -f "$TOKEN_FILE" ]; then
  echo "Note: You need to authenticate with Google Drive the first time."
  echo "Run the following command to authenticate:"
  echo "  cd $INSTALL_DIR && python src/main.py --once"
  echo ""
  echo "After authentication, the token will be saved to your persistent storage"
  echo "and will be available for future RunPod sessions."
else
  echo "Found existing token.json file. Authentication should be automatic."
fi 