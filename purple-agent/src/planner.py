"""LLM-based command planning for terminal tasks."""

import json
import re
from typing import Optional

from .llm_client import LLMClient


SYSTEM_PROMPT = """You are an expert terminal agent that completes tasks by executing shell commands.

Your goal is to complete the given task by issuing shell commands one at a time.

## Response Format

You MUST respond with valid JSON in one of these two formats:

### To execute a command:
```json
{
  "action": "execute",
  "command": {
    "command": "your shell command here",
    "timeout": 30
  },
  "reasoning": "Brief explanation of why this command"
}
```

### To signal task completion:
```json
{
  "action": "complete",
  "reasoning": "Brief explanation of how the task was completed"
}
```

## Guidelines

1. Execute one command at a time and observe the output before proceeding
2. Use standard Unix/Linux commands
3. Check your work before signaling completion
4. Handle errors gracefully - if a command fails, try alternative approaches
5. Be efficient - don't run unnecessary commands
6. Set appropriate timeouts for long-running commands

## Common Patterns

- Creating files: use echo, cat, or printf
- Viewing files: use cat, head, tail, or less
- Finding files: use find, ls, or locate
- Text processing: use grep, sed, awk
- Directory navigation: use cd, pwd, ls

Remember: Respond ONLY with valid JSON. No additional text or explanation outside the JSON."""


class TaskPlanner:
    """Plans terminal commands to complete tasks using LLM."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def plan_next_action(
        self,
        instruction: str,
        history: list[dict],
        context: dict,
    ) -> dict:
        """Plan the next action based on task and history."""
        response = await self.llm_client.complete(
            messages=history,
            system_prompt=SYSTEM_PROMPT,
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """Parse LLM response into action dict."""
        # Try to extract JSON from the response
        response = response.strip()

        # Try direct JSON parse first
        try:
            return self._validate_action(json.loads(response))
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        if json_match:
            try:
                return self._validate_action(json.loads(json_match.group(1)))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return self._validate_action(json.loads(json_match.group(0)))
            except json.JSONDecodeError:
                pass

        # Fallback: try to interpret as command
        return self._interpret_as_command(response)

    def _validate_action(self, data: dict) -> dict:
        """Validate and normalize an action dict."""
        action = data.get("action", "complete")

        if action == "execute":
            command = data.get("command", {})
            if isinstance(command, str):
                command = {"command": command, "timeout": 30}
            elif isinstance(command, dict):
                if "command" not in command:
                    command["command"] = ""
                if "timeout" not in command:
                    command["timeout"] = 30

            return {
                "action": "execute",
                "command": command,
                "reasoning": data.get("reasoning", ""),
            }
        else:
            return {
                "action": "complete",
                "reasoning": data.get("reasoning", ""),
            }

    def _interpret_as_command(self, response: str) -> dict:
        """Try to interpret a non-JSON response as a command."""
        # Look for common command patterns
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            # Skip common non-command patterns
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            # Skip if it looks like explanation text
            if any(
                phrase in line.lower()
                for phrase in ["i will", "let me", "i'll", "let's", "we can", "we should"]
            ):
                continue
            # Check if it looks like a command
            if line.startswith("$"):
                line = line[1:].strip()
            if self._looks_like_command(line):
                return {
                    "action": "execute",
                    "command": {"command": line, "timeout": 30},
                    "reasoning": "Interpreted from response",
                }

        # Default to completion if no command found
        return {
            "action": "complete",
            "reasoning": response[:200] if len(response) > 200 else response,
        }

    def _looks_like_command(self, text: str) -> bool:
        """Check if text looks like a shell command."""
        common_commands = [
            "ls", "cd", "cat", "echo", "mkdir", "touch", "rm", "cp", "mv",
            "find", "grep", "sed", "awk", "head", "tail", "pwd", "chmod",
            "chown", "tar", "gzip", "unzip", "curl", "wget", "python",
            "pip", "npm", "node", "git", "docker", "make", "test", "bash",
            "sh", "export", "source", "which", "whereis", "df", "du",
        ]
        first_word = text.split()[0] if text.split() else ""
        first_word = first_word.lstrip("./")
        return first_word in common_commands or "/" in text.split()[0] if text.split() else False
