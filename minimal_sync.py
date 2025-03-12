#!/usr/bin/env python3

import os
import sys
import time
import glob
import logging
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger()

# Constants
CREDENTIALS_FILE = os.path.join(os.getcwd(), "credentials.json")
TOKEN_FILE = os.path.join(os.getcwd(), "token.json")
COMFYUI_OUTPUT_DIR = "/workspace/ComfyUI/output"
FILE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

def authenticate(folder_id):
    """Authenticate with Google Drive and return a Drive instance."""
    try:
        # Print debug info
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Credentials file: {CREDENTIALS_FILE}")
        logger.info(f"Credentials file exists: {os.path.exists(CREDENTIALS_FILE)}")
        
        # Create GoogleAuth instance
        gauth = GoogleAuth()
        
        # Configure settings
        gauth.settings['client_config_file'] = CREDENTIALS_FILE
        gauth.settings['save_credentials'] = True
        gauth.settings['save_credentials_backend'] = 'file'
        gauth.settings['save_credentials_file'] = TOKEN_FILE
        gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
        
        # Load credentials
        gauth.LoadCredentialsFile(TOKEN_FILE)
        
        if gauth.credentials is None:
            logger.info("No credentials found. Starting authentication process...")
            gauth.CommandLineAuth()
        elif gauth.access_token_expired:
            logger.info("Credentials expired. Refreshing...")
            gauth.Refresh()
        else:
            logger.info("Using existing credentials.")
            gauth.Authorize()
        
        # Save credentials
        gauth.SaveCredentialsFile(TOKEN_FILE)
        
        # Create Drive instance
        drive = GoogleDrive(gauth)
        logger.info("Successfully authenticated with Google Drive")
        
        return drive
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise

def sync_files(drive, folder_id):
    """Sync files from ComfyUI output directory to Google Drive."""
    try:
        # Check if output directory exists
        if not os.path.exists(COMFYUI_OUTPUT_DIR):
            logger.error(f"Output directory {COMFYUI_OUTPUT_DIR} does not exist")
            return 0
        
        logger.info(f"Checking for files in {COMFYUI_OUTPUT_DIR}")
        
        # Find all files with the specified extensions
        all_files = []
        for ext in FILE_EXTENSIONS:
            pattern = os.path.join(COMFYUI_OUTPUT_DIR, f"*{ext}")
            all_files.extend(glob.glob(pattern))
        
        logger.info(f"Found {len(all_files)} files with supported extensions")
        
        # Upload files
        uploaded_count = 0
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            
            # Check if file already exists in Drive
            query = f"'{folder_id}' in parents and title='{file_name}' and trashed=false"
            file_list = drive.ListFile({'q': query}).GetList()
            
            if len(file_list) > 0:
                logger.info(f"File {file_name} already exists in Google Drive, skipping")
                continue
            
            # Upload file
            try:
                logger.info(f"Uploading {file_name} to Google Drive")
                file_metadata = {
                    'title': file_name,
                    'parents': [{'id': folder_id}]
                }
                
                file = drive.CreateFile(file_metadata)
                file.SetContentFile(file_path)
                file.Upload()
                
                logger.info(f"Successfully uploaded {file_name}")
                uploaded_count += 1
            except Exception as e:
                logger.error(f"Failed to upload {file_name}: {e}")
        
        logger.info(f"Uploaded {uploaded_count} files")
        return uploaded_count
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return 0

def main():
    # Check command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python minimal_sync.py <folder_id> [--once]")
        return 1
    
    folder_id = sys.argv[1]
    run_once = "--once" in sys.argv
    
    logger.info(f"Starting sync with folder ID: {folder_id}")
    
    try:
        # Authenticate
        drive = authenticate(folder_id)
        
        if run_once:
            # Run once
            sync_files(drive, folder_id)
        else:
            # Run continuously
            while True:
                try:
                    sync_files(drive, folder_id)
                except Exception as e:
                    logger.error(f"Error during sync: {e}")
                
                logger.info("Sleeping for 60 seconds")
                time.sleep(60)
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 