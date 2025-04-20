# Rabbit/rabbit_sdk/__init__.py 
"""
Initializes the Rabbit SDK package, making key components available for import.
"""
"""
Rabbit SDK - A framework for building autonomous agents with browser capabilities. 
"""

__version__ = "0.1.0"

from .agent import RabbitAgent
from .browser_controller import BrowserController
from .llm_manager import LLMManager
from .memory_manager import MemoryManager
from .planner import Planner

__all__ = [
    "RabbitAgent",
    "BrowserController",
    "LLMManager",
    "MemoryManager",
    "Planner",
]


