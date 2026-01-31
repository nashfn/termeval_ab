"""A2A messaging utilities for the purple agent."""

import json
from typing import Any


class MessageFormatter:
    """Utilities for formatting A2A messages."""

    @staticmethod
    def format_execute_response(
        command: str,
        reasoning: str = "",
        timeout: int = 30,
        workdir: str | None = None,
    ) -> dict:
        """Format an execute command response."""
        cmd_obj = {
            "command": command,
            "timeout": timeout,
        }
        if workdir:
            cmd_obj["workdir"] = workdir

        return {
            "action": "execute",
            "command": cmd_obj,
            "reasoning": reasoning,
        }

    @staticmethod
    def format_complete_response(reasoning: str = "") -> dict:
        """Format a task completion response."""
        return {
            "action": "complete",
            "reasoning": reasoning,
        }

    @staticmethod
    def parse_command_result(message: str) -> dict:
        """Parse a command result from a message."""
        try:
            data = json.loads(message)
            return {
                "stdout": data.get("stdout", ""),
                "stderr": data.get("stderr", ""),
                "exit_code": data.get("exit_code", -1),
                "timed_out": data.get("timed_out", False),
            }
        except json.JSONDecodeError:
            return {
                "stdout": message,
                "stderr": "",
                "exit_code": 0,
                "timed_out": False,
            }

    @staticmethod
    def parse_task_instruction(message: str) -> dict:
        """Parse a task instruction from a message."""
        try:
            data = json.loads(message)
            return {
                "task_id": data.get("task_id", ""),
                "instruction": data.get("instruction", ""),
                "context": data.get("context", {}),
            }
        except json.JSONDecodeError:
            return {
                "task_id": "",
                "instruction": message,
                "context": {},
            }
