#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

# Run the sync script in the background
nohup python minimal_sync.py YOUR_FOLDER_ID > sync.log 2>&1 &

echo "Sync service started in the background with PID $!"
echo "You can check the logs with: tail -f sync.log" 