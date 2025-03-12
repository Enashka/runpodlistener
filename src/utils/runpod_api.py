import logging
import os
from typing import List, Dict, Any, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import RUNPOD_API_KEY, RUNPOD_POD_ID

logger = logging.getLogger(__name__)

class RunPodClient:
    """Client for interacting with RunPod API."""
    
    BASE_URL = "https://api.runpod.io/v2"
    
    def __init__(self):
        self.api_key = RUNPOD_API_KEY
        self.pod_id = RUNPOD_POD_ID
        
        if not self.api_key:
            raise ValueError("RunPod API key not provided")
        
        if not self.pod_id:
            raise ValueError("RunPod Pod ID not provided")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_pod_status(self) -> Dict[str, Any]:
        """
        Get the status of the pod.
        
        Returns:
            Dictionary containing pod status information
        """
        url = f"{self.BASE_URL}/pod/{self.pod_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get pod status: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command on the pod.
        
        Args:
            command: Command to execute
            
        Returns:
            Dictionary containing command execution results
        """
        url = f"{self.BASE_URL}/pod/{self.pod_id}/execute"
        payload = {"command": command}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to execute command: {str(e)}")
            raise
    
    def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory on the pod.
        
        Args:
            directory: Directory to list files from
            
        Returns:
            List of file paths
        """
        command = f"ls -la {directory}"
        result = self.execute_command(command)
        
        if result.get("status") == "success":
            output = result.get("output", "")
            # Parse the ls output to extract filenames
            lines = output.strip().split("\n")
            # Skip the first line which is the total and start from the third line
            # to skip . and .. directories
            files = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    # The filename is the last part (or parts if it contains spaces)
                    filename = " ".join(parts[8:])
                    if filename not in [".", ".."]:
                        files.append(os.path.join(directory, filename))
            return files
        else:
            logger.error(f"Failed to list files in {directory}: {result.get('error', 'Unknown error')}")
            return []
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the pod to the local machine.
        
        Args:
            remote_path: Path to the file on the pod
            local_path: Path to save the file locally
            
        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder. In a real implementation, you would use
        # something like SCP or SFTP to download the file.
        # For now, we'll just log that this would happen.
        logger.info(f"Would download {remote_path} to {local_path}")
        return True
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists on the pod.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        command = f"[ -f {file_path} ] && echo 'exists' || echo 'not exists'"
        result = self.execute_command(command)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            return output == "exists"
        else:
            logger.error(f"Failed to check if file {file_path} exists: {result.get('error', 'Unknown error')}")
            return False 