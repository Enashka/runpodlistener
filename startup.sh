#!/bin/bash
# Startup script for RunPod to set up and run the image sync tool

# Clone the repository
echo "Cloning the image sync repository..."
cd /workspace
git clone https://github.com/yourusername/runpodlistener.git
cd runpodlistener

# Create and configure .env file
echo "Configuring environment variables..."
cp .env.example .env
# No need to set RUNPOD_POD_ID since we're running directly on the pod
sed -i 's/RUNPOD_API_KEY=your_runpod_api_key/RUNPOD_API_KEY=/' .env
sed -i 's/RUNPOD_POD_ID=your_runpod_pod_id/RUNPOD_POD_ID=/' .env
sed -i "s|GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id|GOOGLE_DRIVE_FOLDER_ID=${GOOGLE_DRIVE_FOLDER_ID}|" .env

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