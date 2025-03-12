import os
import time
import logging
import tempfile
from typing import List, Set
from datetime import datetime

from src.config import COMFYUI_OUTPUT_DIR, SYNC_INTERVAL, FILE_EXTENSIONS
from src.utils.google_drive import GoogleDriveClient
from src.utils.runpod_api import RunPodClient

logger = logging.getLogger(__name__)

class SyncManager:
    """Manager for synchronizing files from RunPod to Google Drive."""
    
    def __init__(self):
        self.runpod_client = RunPodClient()
        self.drive_client = GoogleDriveClient()
        self.output_dir = COMFYUI_OUTPUT_DIR
        self.sync_interval = SYNC_INTERVAL
        self.file_extensions = FILE_EXTENSIONS
        self.synced_files: Set[str] = set()
        
        # Create a temporary directory for downloaded files
        self.temp_dir = tempfile.mkdtemp(prefix="runpod_sync_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
    
    def _is_valid_file(self, file_path: str) -> bool:
        """
        Check if a file is valid for syncing.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is valid, False otherwise
        """
        # Check if the file has a valid extension
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.file_extensions
    
    def _get_files_to_sync(self) -> List[str]:
        """
        Get a list of files to sync.
        
        Returns:
            List of file paths to sync
        """
        all_files = self.runpod_client.list_files(self.output_dir)
        
        # Filter out files that have already been synced or are not valid
        files_to_sync = []
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            if (
                self._is_valid_file(file_path) and 
                file_path not in self.synced_files and
                not self.drive_client.file_exists(file_name)
            ):
                files_to_sync.append(file_path)
        
        return files_to_sync
    
    def _download_and_upload_file(self, remote_path: str) -> bool:
        """
        Download a file from RunPod and upload it to Google Drive.
        
        Args:
            remote_path: Path to the file on RunPod
            
        Returns:
            True if successful, False otherwise
        """
        file_name = os.path.basename(remote_path)
        local_path = os.path.join(self.temp_dir, file_name)
        
        try:
            # In a real implementation, you would download the file from RunPod
            # For now, we'll use the RunPod API to get the file content
            command = f"cat {remote_path} | base64"
            result = self.runpod_client.execute_command(command)
            
            if result.get("status") != "success":
                logger.error(f"Failed to download {remote_path}: {result.get('error', 'Unknown error')}")
                return False
            
            # Decode the base64 content and write to a local file
            import base64
            content = result.get("output", "").strip()
            
            try:
                with open(local_path, "wb") as f:
                    f.write(base64.b64decode(content))
            except Exception as e:
                logger.error(f"Failed to write file {local_path}: {str(e)}")
                return False
            
            # Upload the file to Google Drive
            self.drive_client.upload_file(local_path)
            
            # Add the file to the synced files set
            self.synced_files.add(remote_path)
            
            # Remove the local file
            os.remove(local_path)
            
            logger.info(f"Successfully synced {file_name} to Google Drive")
            return True
        except Exception as e:
            logger.error(f"Failed to sync {file_name}: {str(e)}")
            return False
    
    def sync_files(self) -> int:
        """
        Sync files from RunPod to Google Drive.
        
        Returns:
            Number of files synced
        """
        logger.info("Starting file sync")
        
        files_to_sync = self._get_files_to_sync()
        logger.info(f"Found {len(files_to_sync)} files to sync")
        
        synced_count = 0
        for file_path in files_to_sync:
            if self._download_and_upload_file(file_path):
                synced_count += 1
        
        logger.info(f"Synced {synced_count} files")
        return synced_count
    
    def run(self):
        """Run the sync manager continuously."""
        logger.info("Starting sync manager")
        
        try:
            while True:
                try:
                    self.sync_files()
                except Exception as e:
                    logger.error(f"Error during sync: {str(e)}")
                
                logger.info(f"Sleeping for {self.sync_interval} seconds")
                time.sleep(self.sync_interval)
        except KeyboardInterrupt:
            logger.info("Sync manager stopped by user")
        finally:
            # Clean up the temporary directory
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Removed temporary directory: {self.temp_dir}")
    
    def cleanup(self):
        """Clean up resources."""
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info(f"Removed temporary directory: {self.temp_dir}") 