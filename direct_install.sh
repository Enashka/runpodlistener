#!/bin/bash
# Direct installation script for RunPod ComfyUI Image Sync
# Uses the existing Python environment from ComfyUI

# Download the installation script
wget https://raw.githubusercontent.com/Enashka/runpodlistener/main/install_on_runpod.sh

# Make it executable
chmod +x install_on_runpod.sh

# Run the installation script
sudo ./install_on_runpod.sh 