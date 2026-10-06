"""
Tool Registry for JARVIS AI.
Manages tool registration, lookup, schema generation, and safe execution.
"""
import logging
from typing import Any, Dict, List, Optional
from tools.base import BaseTool

log = logging.getLogger("JARVIS.Tools")


class ToolRegistry:
    """
    Central registry for storing and executing JARVIS tools.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool instance in the registry.

        Args:
            tool (BaseTool): Instance of a BaseTool subclass.
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Expected BaseTool instance, got {type(tool).__name__}")
        if not tool.name:
            raise ValueError("Tool must have a non-empty 'name' attribute.")
        if tool.name in self._tools:
            log.warning(f"Overwriting existing tool registration: '{tool.name}'")
        self._tools[tool.name] = tool
        log.info(f"Registered tool: '{tool.name}'")

    def get(self, name: str) -> Optional[BaseTool]:
        """
        Retrieve a registered tool by name.

        Args:
            name (str): Tool identifier.

        Returns:
            Optional[BaseTool]: Registered tool instance or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List[str]: List of registered tool identifiers.
        """
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Generate OpenAI/Groq compatible tool schemas for all registered tools.

        Returns:
            List[dict]: List of tool schema dictionaries for Groq API payload.
        """
        return [tool.to_groq_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> Any:
        """
        Safely execute a registered tool by name with keyword arguments.

        Args:
            name (str): Name of tool to execute.
            **kwargs: Arguments to pass to tool.execute().

        Returns:
            Any: Result string or error description if execution fails.
        """
        tool = self.get(name)
        if not tool:
            err_msg = f"[ERROR] Tool '{name}' is not registered."
            log.error(err_msg)
            return err_msg

        try:
            return tool.execute(**kwargs)
        except Exception as e:
            err_msg = f"[ERROR] Execution failed for tool '{name}': {str(e)}"
            log.error(err_msg, exc_info=True)
            return err_msg
