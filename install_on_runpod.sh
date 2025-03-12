#!/bin/bash
# Installation script for RunPod ComfyUI Image Sync

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Prompt for Google Drive folder ID
read -p "Enter your Google Drive folder ID: " GOOGLE_DRIVE_FOLDER_ID
if [ -z "$GOOGLE_DRIVE_FOLDER_ID" ]; then
  echo "Google Drive folder ID is required"
  exit 1
fi

# Create installation directory
INSTALL_DIR="/workspace/runpodlistener"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Clone the repository
echo "Cloning the repository..."
if [ -d ".git" ]; then
  git pull
else
  git clone https://github.com/yourusername/runpodlistener.git .
fi

# Create .env file
echo "Creating .env file..."
cp .env.example .env
sed -i "s|GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id|GOOGLE_DRIVE_FOLDER_ID=$GOOGLE_DRIVE_FOLDER_ID|" .env

# Set up Python environment
echo "Setting up Python environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Prompt for credentials.json
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

if [ ! -f "credentials.json" ]; then
  echo "credentials.json not found. Please upload it and try again."
  exit 1
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
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/main.py
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
echo "Note: The first time you run the service, you'll need to authenticate with Google."
echo "Run the following command to authenticate:"
echo "  cd $INSTALL_DIR && source venv/bin/activate && python src/main.py --once" 