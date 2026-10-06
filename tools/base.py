"""
Base Tool abstraction for JARVIS AI.
Compatible with Groq / OpenAI-style function calling schemas.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """
    Abstract base class for all JARVIS tools.

    Attributes:
        name (str): Unique tool identifier (e.g. 'open_app', 'get_system_info').
        description (str): Human and LLM-readable description of what the tool does.
        parameters (dict): JSON Schema describing arguments accepted by execute().
    """

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute tool functionality with provided parameters.

        Returns:
            Any: The result of tool execution (typically str for JARVIS responses).
        """
        pass

    def to_groq_schema(self) -> Dict[str, Any]:
        """
        Formats tool definitions into OpenAI/Groq function calling schema format.

        Returns:
            dict: Groq-compatible tool specification dictionary.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
