#!/usr/bin/env python3

# Updated version with config.yaml support
# Author: Enashka

import os
import sys
import time
import glob
import logging
import yaml
import datetime
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage

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
CONFIG_FILE = os.path.join(os.getcwd(), "config.yaml")

# Load configuration
def load_config():
    """Load configuration from config.yaml file."""
    default_config = {
        "folder_id": "",
        "sync_interval": 60,
        "output_directory": "/workspace/ComfyUI/output",
        "file_extensions": [".png", ".jpg", ".jpeg"]
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {CONFIG_FILE}")
                
                # Merge with default config to ensure all required values exist
                if config is None:
                    config = {}
                    
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        
                return config
        else:
            logger.warning(f"Config file {CONFIG_FILE} not found, using default configuration")
            return default_config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return default_config

# Global config
CONFIG = load_config()

def authenticate(folder_id):
    """Authenticate with Google Drive and return a Drive instance."""
    try:
        # Print debug info
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Credentials file: {CREDENTIALS_FILE}")
        logger.info(f"Credentials file exists: {os.path.exists(CREDENTIALS_FILE)}")
        
        # Create GoogleAuth instance
        gauth = GoogleAuth()
        logger.info("Created GoogleAuth instance")
        
        # Configure settings
        logger.info("Configuring settings...")
        gauth.settings['client_config_backend'] = 'file'
        gauth.settings['client_config_file'] = CREDENTIALS_FILE
        gauth.settings['save_credentials'] = True
        gauth.settings['save_credentials_backend'] = 'file'
        gauth.settings['save_credentials_file'] = TOKEN_FILE
        gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
        logger.info("Settings configured")
        
        # Load credentials
        logger.info("Loading credentials file...")
        gauth.LoadCredentialsFile(TOKEN_FILE)
        logger.info("Credentials file loaded")
        
        if gauth.credentials is None:
            logger.info("No credentials found. Starting authentication process...")
            try:
                # Directly create flow and credentials instead of using CommandLineAuth
                logger.info("Reading client config from credentials file...")
                with open(CREDENTIALS_FILE, 'r') as f:
                    client_config = json.loads(f.read())['installed']
                
                logger.info("Creating OAuth2WebServerFlow...")
                flow = OAuth2WebServerFlow(
                    client_id=client_config['client_id'],
                    client_secret=client_config['client_secret'],
                    scope='https://www.googleapis.com/auth/drive',
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                
                auth_url = flow.step1_get_authorize_url()
                logger.info(f"Please go to this URL and authorize the app: {auth_url}")
                logger.info("After authorization, copy the code and enter it here:")
                auth_code = input("Enter the authorization code: ")
                
                logger.info("Getting credentials from auth code...")
                credentials = flow.step2_exchange(auth_code)
                
                # Set the credentials in GoogleAuth
                gauth.credentials = credentials
                logger.info("Credentials obtained successfully")
            except Exception as e:
                logger.error(f"Error during authentication: {e}")
                raise
        elif gauth.access_token_expired:
            logger.info("Credentials expired. Refreshing...")
            gauth.Refresh()
        else:
            logger.info("Using existing credentials.")
            gauth.Authorize()
        
        # Save credentials
        logger.info("Saving credentials...")
        gauth.SaveCredentialsFile(TOKEN_FILE)
        logger.info("Credentials saved successfully")
        
        # Create Drive instance
        drive = GoogleDrive(gauth)
        logger.info("Successfully authenticated with Google Drive")
        
        return drive
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise

class SyncManager:
    def __init__(self, drive, folder_id):
        self.drive = drive
        self.folder_id = folder_id
        self.output_dir = CONFIG["output_directory"]
        self.sync_interval = CONFIG["sync_interval"]
        self.file_extensions = CONFIG["file_extensions"]
        
        # Record the start time to only process files created after this time
        self.start_time = datetime.datetime.now()
        logger.info(f"Starting sync manager at {self.start_time}")
        
        # Keep track of uploaded files to prevent re-uploading
        self.uploaded_files = set()
        
        # Check if output directory exists
        if os.path.exists(self.output_dir):
            logger.info(f"Monitoring directory: {self.output_dir}")
        else:
            logger.warning(f"Output directory {self.output_dir} not found")
    
    def is_new_file(self, file_path):
        """Check if a file was created after the tool started running."""
        try:
            # Get file creation time
            file_ctime = os.path.getctime(file_path)
            file_time = datetime.datetime.fromtimestamp(file_ctime)
            
            # Check if file was created after the tool started
            return file_time > self.start_time
        except Exception as e:
            logger.error(f"Error checking file time: {e}")
            # If we can't determine, assume it's not new
            return False
    
    def get_new_files(self):
        """Get files created after the tool started running."""
        if not os.path.exists(self.output_dir):
            logger.error(f"Output directory {self.output_dir} does not exist")
            return []
        
        # Find all files with the specified extensions
        all_files = []
        for ext in self.file_extensions:
            pattern = os.path.join(self.output_dir, f"*{ext}")
            all_files.extend(glob.glob(pattern))
        
        # Filter for new files only and exclude already uploaded files
        new_files = [f for f in all_files if self.is_new_file(f) and f not in self.uploaded_files]
        
        if new_files:
            logger.info(f"Found {len(new_files)} new files to sync")
        
        return new_files
    
    def upload_file(self, file_path):
        """Upload a file to Google Drive."""
        try:
            file_name = os.path.basename(file_path)
            
            # Upload file
            logger.info(f"Uploading {file_name} to Google Drive")
            file_metadata = {
                'title': file_name,
                'parents': [{'id': self.folder_id}]
            }
            
            file = self.drive.CreateFile(file_metadata)
            file.SetContentFile(file_path)
            file.Upload()
            
            # Add to uploaded files set to prevent re-uploading
            self.uploaded_files.add(file_path)
            
            logger.info(f"Successfully uploaded {file_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {file_name}: {e}")
            return False
    
    def sync_files(self):
        """Sync new files to Google Drive."""
        logger.info("Checking for new files")
        
        new_files = self.get_new_files()
        
        uploaded_count = 0
        for file_path in new_files:
            if self.upload_file(file_path):
                uploaded_count += 1
        
        if uploaded_count > 0:
            logger.info(f"Uploaded {uploaded_count} new files")
        else:
            logger.info("No new files to upload")
        
        return uploaded_count
    
    def run(self):
        """Run the sync manager continuously."""
        logger.info("Starting sync manager")
        
        try:
            while True:
                try:
                    self.sync_files()
                except Exception as e:
                    logger.error(f"Error during sync: {e}")
                
                logger.info(f"Sleeping for {self.sync_interval} seconds")
                time.sleep(self.sync_interval)
        except KeyboardInterrupt:
            logger.info("Sync manager stopped by user")

def main():
    # Get folder ID from config or command line
    folder_id = CONFIG["folder_id"]
    
    # Override with command line argument if provided
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        folder_id = sys.argv[1]
        logger.info(f"Using folder ID from command line: {folder_id}")
    
    # Check if folder ID is set
    if not folder_id:
        logger.error("Google Drive folder ID not set. Please set it in config.yaml or provide it as a command line argument.")
        return 1
    
    run_once = "--once" in sys.argv
    
    # Get sync interval from config
    sync_interval = CONFIG["sync_interval"]
    logger.info(f"Using sync interval of {sync_interval} seconds")
    
    logger.info(f"Starting sync with folder ID: {folder_id}")
    
    try:
        # Authenticate
        drive = authenticate(folder_id)
        
        # Create sync manager
        sync_manager = SyncManager(drive, folder_id)
        
        if run_once:
            # Run once
            sync_manager.sync_files()
        else:
            # Run continuously
            sync_manager.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 