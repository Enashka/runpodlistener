# RunPod ComfyUI Image Sync

A tool to automatically sync images generated by ComfyUI on RunPod to Google Drive.

## Overview

This application monitors the output directory of ComfyUI on RunPod and automatically uploads new images to Google Drive as they are generated. This allows for seamless access to your AI-generated images on your local machine through Google Drive sync.

## Features

- Monitors ComfyUI output directory on RunPod
- Automatically uploads new images to Google Drive
- Configurable sync intervals
- Authentication with Google Drive API
- Logging and error handling
- Works with ephemeral RunPod instances

## Requirements

- RunPod account with ComfyUI setup
- Google Drive account
- Google Cloud Platform account (for API access)

## Installation on RunPod

### Option 1: One-Line Installation (Easiest)

Run this single command on your RunPod instance:

```bash
wget -O - https://raw.githubusercontent.com/Enashka/runpodlistener/main/direct_install.sh | bash
```

### Option 2: Manual Download and Install

1. SSH into your RunPod instance
2. Download the installation script:
   ```bash
   wget https://raw.githubusercontent.com/Enashka/runpodlistener/main/install_on_runpod.sh
   ```
3. Make it executable:
   ```bash
   chmod +x install_on_runpod.sh
   ```
4. Run the installation script:
   ```bash
   sudo ./install_on_runpod.sh
   ```
5. Follow the prompts to complete the installation

### Option 3: Full Manual Installation

1. SSH into your RunPod instance
2. Clone this repository:
   ```bash
   cd /workspace
   git clone https://github.com/Enashka/runpodlistener.git
   cd runpodlistener
   ```
3. Set up Google Drive API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API
   - Create OAuth credentials (Desktop app)
   - Download the credentials JSON file
   - Upload it to your RunPod instance as `credentials.json`

4. Configure the application:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your specific settings:
   - `GOOGLE_DRIVE_FOLDER_ID`: The ID of the Google Drive folder where you want to store the images

5. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. Run the application:
   ```bash
   python src/main.py
   ```

## Adding to RunPod Template

If you want to automatically start the sync tool whenever you create a new RunPod instance, you can add the following to your RunPod template's startup script:

```bash
# Clone and set up the sync tool
cd /workspace
git clone https://github.com/Enashka/runpodlistener.git
cd runpodlistener

# Configure
cp .env.example .env
sed -i "s|GOOGLE_DRIVE_FOLDER_ID=your_google_drive_folder_id|GOOGLE_DRIVE_FOLDER_ID=YOUR_FOLDER_ID|" .env

# Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start in background
nohup python src/main.py > sync.log 2>&1 &
```

Replace `YOUR_FOLDER_ID` with your actual Google Drive folder ID.

## Credential Security

This tool requires access to your Google Drive, which means it needs credentials to authenticate. Here's how to keep your credentials secure:

### Keeping Credentials Safe

1. **Never commit credentials to GitHub**
   - The `.gitignore` file already excludes sensitive files like `credentials.json` and `token.json`
   - Always upload these files directly to your RunPod instance, not to GitHub

2. **Use RunPod's persistent storage**
   - Store your credentials in RunPod's persistent storage area
   - This way, they persist between pod sessions but aren't in your GitHub repo
   - The default location is `/workspace/runpodlistener/`

3. **First-time setup only**
   - You only need to set up credentials once if using persistent storage
   - The token will be automatically refreshed when needed

### Credential Files

- **credentials.json**: Your Google API client credentials
  - Download from Google Cloud Console
  - Upload directly to your RunPod instance
  - Store in `/workspace/runpodlistener/`

- **token.json**: Your OAuth access token
  - Generated after first authentication
  - Automatically stored in `/workspace/runpodlistener/`
  - Persists between pod sessions if in persistent storage

## First Run Authentication

The first time you run the application, you'll need to authenticate with Google:

1. Run the application with the `--once` flag:
   ```bash
   python src/main.py --once
   ```
2. You'll see a URL in the console. Copy this URL.
3. Open the URL in a browser on your local machine (not on RunPod)
4. Sign in to your Google account and grant the requested permissions
5. Copy the authorization code
6. Paste it into the RunPod terminal when prompted

After the first authentication, a token file will be created and stored for future use.

## Configuration Options

You can configure the application by editing the `.env` file:

- `COMFYUI_OUTPUT_DIR`: Path to the ComfyUI output directory
- `GOOGLE_DRIVE_FOLDER_ID`: ID of the Google Drive folder to upload to
- `SYNC_INTERVAL`: How often to check for new files (in seconds)
- `FILE_EXTENSIONS`: File extensions to sync (comma-separated)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `LOG_FILE`: Path to the log file

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:
1. Delete the `token.json` file
2. Ensure your `credentials.json` file is correct
3. Run the application again to re-authenticate

### File Syncing Issues

If files aren't being synced:
1. Check that the ComfyUI output directory is correct
2. Verify that your Google Drive folder ID is correct
3. Check the log file for errors

## License

MIT
