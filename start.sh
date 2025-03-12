#!/bin/bash
# Start script for ComfyUI Image Sync Tool
# Updated by Enashka

# Change to the script directory
cd "$(dirname "$0")"

# Run the sync script in the background
nohup python minimal_sync.py > sync.log 2>&1 &

echo "Sync service started in the background with PID $!"
echo "You can check the logs with: tail -f sync.log" 