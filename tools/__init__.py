"""
JARVIS AI Tools Package.
Provides BaseTool abstraction and ToolRegistry container.
"""

from tools.base import BaseTool
from tools.registry import ToolRegistry

# Default global registry instance
registry = ToolRegistry()

__all__ = ["BaseTool", "ToolRegistry", "registry"]
