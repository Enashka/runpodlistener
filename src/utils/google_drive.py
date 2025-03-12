import os
import logging
from typing import List, Optional
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import CREDENTIALS_FILE, TOKEN_FILE, GOOGLE_DRIVE_FOLDER_ID

logger = logging.getLogger(__name__)

class GoogleDriveClient:
    """Client for interacting with Google Drive API."""
    
    def __init__(self):
        self.drive = None
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Drive API."""
        try:
            gauth = GoogleAuth()
            
            # Try to load saved client credentials
            gauth.LoadCredentialsFile(TOKEN_FILE)
            
            if gauth.credentials is None:
                # Authenticate if they're not available
                gauth.LocalWebServerAuth()
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved creds
                gauth.Authorize()
                
            # Save the current credentials to a file
            gauth.SaveCredentialsFile(TOKEN_FILE)
            
            self.drive = GoogleDrive(gauth)
            logger.info("Successfully authenticated with Google Drive")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upload_file(self, file_path: str, parent_folder_id: Optional[str] = None) -> GoogleDriveFile:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            parent_folder_id: ID of the folder to upload to (defaults to configured folder)
            
        Returns:
            The uploaded file object
        """
        if not self.drive:
            self.authenticate()
            
        folder_id = parent_folder_id or self.folder_id
        if not folder_id:
            raise ValueError("No folder ID provided and no default folder ID configured")
            
        try:
            file_name = os.path.basename(file_path)
            file_metadata = {
                'title': file_name,
                'parents': [{'id': folder_id}]
            }
            
            file = self.drive.CreateFile(file_metadata)
            file.SetContentFile(file_path)
            file.Upload()
            
            logger.info(f"Successfully uploaded {file_name} to Google Drive")
            return file
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Google Drive: {str(e)}")
            raise
    
    def list_files(self, folder_id: Optional[str] = None) -> List[GoogleDriveFile]:
        """
        List files in a Google Drive folder.
        
        Args:
            folder_id: ID of the folder to list files from (defaults to configured folder)
            
        Returns:
            List of file objects in the folder
        """
        if not self.drive:
            self.authenticate()
            
        folder_id = folder_id or self.folder_id
        if not folder_id:
            raise ValueError("No folder ID provided and no default folder ID configured")
            
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            file_list = self.drive.ListFile({'q': query}).GetList()
            return file_list
        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_id}: {str(e)}")
            raise
    
    def file_exists(self, file_name: str, folder_id: Optional[str] = None) -> bool:
        """
        Check if a file exists in a Google Drive folder.
        
        Args:
            file_name: Name of the file to check
            folder_id: ID of the folder to check in (defaults to configured folder)
            
        Returns:
            True if the file exists, False otherwise
        """
        if not self.drive:
            self.authenticate()
            
        folder_id = folder_id or self.folder_id
        if not folder_id:
            raise ValueError("No folder ID provided and no default folder ID configured")
            
        try:
            query = f"'{folder_id}' in parents and title='{file_name}' and trashed=false"
            file_list = self.drive.ListFile({'q': query}).GetList()
            return len(file_list) > 0
        except Exception as e:
            logger.error(f"Failed to check if file {file_name} exists: {str(e)}")
            raise 