import os
import requests
import time
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Tuple, Callable
import logging
load_dotenv()

class APIService:
    """
    A centralized API service class for handling all API requests in the application.
    Features:
    - Token management with automatic refresh
    - Request queueing for time-related events
    - Error handling and retries
    - Centralized endpoint configuration
    """

    def __init__(self):
        self.base_url = os.getenv('API_URL')
        self.token = None
        self.refresh_token = None
        self.user_data = None
        self.logger = self._setup_logger()
        self.request_timeout = 10  # seconds
        self.max_retries = 3
        self.token_refresh_callback = None

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for API operations"""
        logger = logging.getLogger("api_service")
        logger.setLevel(logging.INFO)
        
        # Create console handler and set formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def set_auth_token(self, token: str, refresh_token: str, user_data: Dict[str, Any]) -> None:
        """Set the authentication token, refresh token and user data for subsequent requests"""
        self.token = token
        self.refresh_token = refresh_token
        self.user_data = user_data
    
    def set_token_refresh_callback(self, callback: Callable[[str], Tuple[str, str]]) -> None:
        """Set a callback function that will be called when a token needs to be refreshed
        
        The callback should accept the refresh token and return a tuple of (new_token, new_refresh_token)
        """
        self.token_refresh_callback = callback
    
    def clear_auth_token(self) -> None:
        """Clear the authentication token on logout"""
        self.token = None
        self.refresh_token = None
        self.user_data = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token if available"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        return headers
    
    def _refresh_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            bool: True if token refresh was successful, False otherwise
        """
        if not self.refresh_token:
            self.logger.error("Cannot refresh token: No refresh token available")
            return False
            
        if not self.token_refresh_callback:
            self.logger.error("Cannot refresh token: No refresh callback set")
            return False
            
        try:
            self.logger.info("Attempting to refresh access token...")
            new_token, new_refresh_token = self.token_refresh_callback(self.refresh_token)
            
            if new_token and new_refresh_token:
                self.token = new_token
                self.refresh_token = new_refresh_token
                self.logger.info("Access token refreshed successfully")
                return True
            else:
                self.logger.error("Token refresh failed: Invalid tokens returned")
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None, retry_count: int = 0, 
                     token_refresh_attempt: bool = False) -> Optional[Dict]:
        """
        Make an HTTP request with retry logic, error handling, and token refresh
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data (for POST/PUT)
            files: Files to upload
            retry_count: Current retry attempt number
            token_refresh_attempt: Whether this request is after a token refresh attempt
            
        Returns:
            Response data as dictionary or None if failed
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers() if not files else {
            key: val for key, val in self._get_headers().items() 
            if key != "Content-Type"  # Remove Content-Type when uploading files
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.request_timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data if not files else None,
                                        files=files, data=data if files else None, 
                                        timeout=self.request_timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=self.request_timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=self.request_timeout)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Handle unauthorized error (token expired)
            if response.status_code == 401 and not token_refresh_attempt:
                self.logger.info("Received 401 Unauthorized - attempting token refresh")
                if self._refresh_token():
                    # Retry the request with the new token
                    return self._make_request(method, endpoint, data, files, retry_count, True)
                else:
                    self.logger.error("Token refresh failed, unable to retry request")
                    return None
                
            response.raise_for_status()
            return response if response.content else None
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {str(e)}")
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying request ({retry_count + 1}/{self.max_retries})...")
                time.sleep(1)  # Wait 1 second before retrying
                return self._make_request(method, endpoint, data, files, retry_count + 1, token_refresh_attempt)
            return None
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timed out: {str(e)}")
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying request ({retry_count + 1}/{self.max_retries})...")
                time.sleep(1)
                return self._make_request(method, endpoint, data, files, retry_count + 1, token_refresh_attempt)
            return None
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error: {str(e)}")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return None
            
    # Convenience methods for API calls
    def get(self, endpoint: str) -> Optional[Dict]:
        """Make a GET request"""
        return self._make_request("GET", endpoint)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Optional[Dict]:
        """Make a POST request"""
        return self._make_request("POST", endpoint, data, files)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make a PUT request"""
        return self._make_request("PUT", endpoint, data)
    
    def delete(self, endpoint: str) -> Optional[Dict]:
        """Make a DELETE request"""
        return self._make_request("DELETE", endpoint)