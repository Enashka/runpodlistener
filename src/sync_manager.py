import os
import time
import logging
import tempfile
import glob
import shutil
from typing import List, Set
from datetime import datetime

from src.config import COMFYUI_OUTPUT_DIR, SYNC_INTERVAL, FILE_EXTENSIONS
from src.utils.google_drive import GoogleDriveClient

logger = logging.getLogger(__name__)

class SyncManager:
    """Manager for synchronizing files from RunPod to Google Drive."""
    
    def __init__(self):
        self.drive_client = GoogleDriveClient()
        self.output_dir = COMFYUI_OUTPUT_DIR
        self.sync_interval = SYNC_INTERVAL
        self.file_extensions = FILE_EXTENSIONS
        self.synced_files: Set[str] = set()
        
        # Create a temporary directory for processing files
        self.temp_dir = tempfile.mkdtemp(prefix="runpod_sync_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        # Check if we're running directly on RunPod
        self.running_on_runpod = os.path.exists(self.output_dir)
        if self.running_on_runpod:
            logger.info(f"Running directly on RunPod, monitoring directory: {self.output_dir}")
        else:
            logger.warning(f"Not running on RunPod or output directory {self.output_dir} not found")
    
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
        if not self.running_on_runpod:
            logger.error("Not running on RunPod, cannot get files to sync")
            return []
        
        # Use glob to find all files in the output directory
        all_files = []
        for ext in self.file_extensions:
            pattern = os.path.join(self.output_dir, f"*{ext}")
            all_files.extend(glob.glob(pattern))
        
        # Filter out files that have already been synced
        files_to_sync = []
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            if (
                file_path not in self.synced_files and
                not self.drive_client.file_exists(file_name)
            ):
                files_to_sync.append(file_path)
        
        return files_to_sync
    
    def _upload_file(self, file_path: str) -> bool:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            True if successful, False otherwise
        """
        file_name = os.path.basename(file_path)
        
        try:
            # Upload the file to Google Drive
            self.drive_client.upload_file(file_path)
            
            # Add the file to the synced files set
            self.synced_files.add(file_path)
            
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
        
        if not self.running_on_runpod:
            logger.error("Not running on RunPod, cannot sync files")
            return 0
        
        files_to_sync = self._get_files_to_sync()
        logger.info(f"Found {len(files_to_sync)} files to sync")
        
        synced_count = 0
        for file_path in files_to_sync:
            if self._upload_file(file_path):
                synced_count += 1
        
        logger.info(f"Synced {synced_count} files")
        return synced_count
    
    def run(self):
        """Run the sync manager continuously."""
        logger.info("Starting sync manager")
        
        if not self.running_on_runpod:
            logger.error("Not running on RunPod, exiting")
            return
        
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
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info(f"Removed temporary directory: {self.temp_dir}") 