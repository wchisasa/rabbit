"""Utility tools for general purpose functionality in the agent system."""

import os
import json
import time
import re
import urllib.parse
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import base64
import hashlib


class UtilityTools:
    """Utility tools for general purpose operations for the agent."""
    
    def __init__(self, config=None):
        """Initialize the utility tools with optional configuration."""
        self.config = config or {}
    
    def get_current_time(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Get current time in specified format.
        
        Args:
            format_str: Format string for the timestamp
            
        Returns:
            str: Formatted current time
        """
        return datetime.now().strftime(format_str)
    
    def parse_url(self, url: str) -> Dict[str, str]:
        """Parse a URL into its components.
        
        Args:
            url: The URL to parse
            
        Returns:
            Dict[str, str]: URL components
        """
        parsed = urllib.parse.urlparse(url)
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "username": parsed.username,
            "password": parsed.password,
            "hostname": parsed.hostname,
            "port": parsed.port
        }
    
    def build_url(self, parts: Dict[str, str]) -> str:
        """Build a URL from components.
        
        Args:
            parts: Dictionary of URL components
            
        Returns:
            str: Constructed URL
        """
        return urllib.parse.urlunparse((
            parts.get("scheme", ""),
            parts.get("netloc", ""),
            parts.get("path", ""),
            parts.get("params", ""),
            parts.get("query", ""),
            parts.get("fragment", "")
        ))
    
    def url_encode(self, text: str) -> str:
        """URL encode a string.
        
        Args:
            text: String to encode
            
        Returns:
            str: URL encoded string
        """
        return urllib.parse.quote(text)
    
    def url_decode(self, text: str) -> str:
        """URL decode a string.
        
        Args:
            text: String to decode
            
        Returns:
            str: URL decoded string
        """
        return urllib.parse.unquote(text)
    
    def load_json(self, path: str) -> Any:
        """Load JSON from a file.
        
        Args:
            path: Path to the JSON file
            
        Returns:
            Any: Parsed JSON content
        """
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(self, data: Any, path: str, pretty: bool = False) -> bool:
        """Save data as JSON to a file.
        
        Args:
            data: Data to save
            path: Path to save the JSON file
            pretty: Whether to format the JSON for readability
            
        Returns:
            bool: Success status
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def parse_json_string(self, json_str: str) -> Any:
        """Parse a JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Any: Parsed JSON data
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
    def to_json_string(self, data: Any, pretty: bool = False) -> str:
        """Convert data to a JSON string.
        
        Args:
            data: Data to convert
            pretty: Whether to format the JSON for readability
            
        Returns:
            str: JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def regex_match(self, pattern: str, text: str) -> List[str]:
        """Find all regex matches in text.
        
        Args:
            pattern: Regex pattern
            text: Text to search in
            
        Returns:
            List[str]: List of matched strings
        """
        return re.findall(pattern, text)
    
    def regex_replace(self, pattern: str, replacement: str, text: str) -> str:
        """Replace regex matches in text.
        
        Args:
            pattern: Regex pattern to match
            replacement: Replacement string
            text: Text to perform replacements in
            
        Returns:
            str: Text with replacements
        """
        return re.sub(pattern, replacement, text)
    
    def sleep(self, seconds: float) -> None:
        """Sleep for specified number of seconds.
        
        Args:
            seconds: Number of seconds to sleep
        """
        time.sleep(seconds)
    
    def create_directory(self, path: str) -> bool:
        """Create directory if it doesn't exist.
        
        Args:
            path: Directory path
            
        Returns:
            bool: Success status
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists.
        
        Args:
            path: File path
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return os.path.isfile(path)
    
    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists.
        
        Args:
            path: Directory path
            
        Returns:
            bool: True if directory exists, False otherwise
        """
        return os.path.isdir(path)
    
    def list_directory(self, path: str) -> List[str]:
        """List contents of a directory.
        
        Args:
            path: Directory path
            
        Returns:
            List[str]: List of files and directories
        """
        if not os.path.isdir(path):
            return []
        return os.listdir(path)
    
    def read_file(self, path: str, binary: bool = False) -> Optional[Union[str, bytes]]:
        """Read file content.
        
        Args:
            path: File path
            binary: Whether to read in binary mode
            
        Returns:
            Optional[Union[str, bytes]]: File content or None if error
        """
        try:
            mode = 'rb' if binary else 'r'
            encoding = None if binary else 'utf-8'
            with open(path, mode, encoding=encoding) as f:
                return f.read()
        except Exception:
            return None
    
    def write_file(self, path: str, content: Union[str, bytes], binary: bool = False) -> bool:
        """Write content to a file.
        
        Args:
            path: File path
            content: Content to write
            binary: Whether to write in binary mode
            
        Returns:
            bool: Success status
        """
        try:
            mode = 'wb' if binary else 'w'
            encoding = None if binary else 'utf-8'
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def append_to_file(self, path: str, content: str) -> bool:
        """Append content to a file.
        
        Args:
            path: File path
            content: Content to append
            
        Returns:
            bool: Success status
        """
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete a file.
        
        Args:
            path: File path
            
        Returns:
            bool: Success status
        """
        try:
            if os.path.isfile(path):
                os.remove(path)
                return True
            return False
        except Exception:
            return False
    
    def base64_encode(self, data: Union[str, bytes]) -> str:
        """Encode data in base64.
        
        Args:
            data: String or bytes to encode
            
        Returns:
            str: Base64 encoded string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    
    def base64_decode(self, data: str, to_str: bool = True) -> Union[str, bytes]:
        """Decode base64 data.
        
        Args:
            data: Base64 string to decode
            to_str: Whether to convert result to string
            
        Returns:
            Union[str, bytes]: Decoded data
        """
        result = base64.b64decode(data)
        if to_str:
            try:
                return result.decode('utf-8')
            except UnicodeDecodeError:
                return result
        return result
    
    def calculate_hash(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """Calculate hash digest of data.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm to use (md5, sha1, sha256, etc.)
            
        Returns:
            str: Hex digest of hash
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        hash_func = getattr(hashlib, algorithm)
        return hash_func(data).hexdigest()
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            str: Domain name
        """
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc