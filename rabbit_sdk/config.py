"""Configuration management for Rabbit SDK.""" 
#Rabbit/rabbit_sdk/config.py 

import os
import json
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    # API Keys
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
    "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
    
    # LLM Configuration
    "llm_provider": "gemini",  # options: gemini, openai 
    "llm_model": "gemini-2.0-flash",  # or "gpt-4" for OpenAI
    "temperature": 0.2,
    "max_tokens": 2048,
    
    # Browser Configuration
    "browser_type": "playwright",  # options: selenium, playwright
    "headless": False,  # Set to True for production
    "browser_timeout": 60,  # seconds
    "screenshot_dir": "./screenshots",
    
    # Agent Configuration
    "agent_name": "RabbitAgent",
    "task_timeout": 600,  # seconds
    "max_retries": 3,
    "memory_path": "./memory",
    
    # Logging
    "log_level": "INFO",
    "log_file": "./rabbit_sdk.log",
    
    # Advanced Settings
    "debug_mode": False,
    "save_session": True,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration with priority: config_path > environment variables > defaults.
    
    Args:
        config_path: Optional path to a configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with file config if provided
    if config_path and os.path.exists(config_path):
        file_config = load_config_file(config_path)
        config.update(file_config)
    
    # Override with environment variables
    for key in config:
        env_key = f"RABBIT_{key.upper()}"
        if env_key in os.environ:
            # Convert string environment variables to appropriate types
            env_value = os.environ[env_key]
            if isinstance(config[key], bool):
                config[key] = env_value.lower() in ('true', 'yes', '1', 'y')
            elif isinstance(config[key], int):
                config[key] = int(env_value)
            elif isinstance(config[key], float):
                config[key] = float(env_value)
            else:
                config[key] = env_value
    
    # Create directories if they don't exist
    os.makedirs(config["screenshot_dir"], exist_ok=True)
    os.makedirs(config["memory_path"], exist_ok=True)
    os.makedirs(os.path.dirname(config["log_file"]), exist_ok=True)
    
    return config


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to a file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration
        
    Returns:
        bool: Success status
    """
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False