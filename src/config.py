import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# RunPod configuration
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_POD_ID = os.getenv("RUNPOD_POD_ID")
COMFYUI_OUTPUT_DIR = os.getenv("COMFYUI_OUTPUT_DIR", "/workspace/ComfyUI/output")

# Google Drive configuration
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# Sync configuration
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "60"))  # seconds
FILE_EXTENSIONS = os.getenv("FILE_EXTENSIONS", ".png,.jpg,.jpeg").split(",")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "runpod_sync.log") 