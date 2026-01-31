"""A2A messaging utilities for communicating with participant agent."""

import json
from typing import Any

import httpx


class A2AMessenger:
    """Handles A2A protocol communication with participant agent."""

    def __init__(self, participant_url: str):
        self.participant_url = participant_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=60.0)
        self._session_id: str | None = None

    async def send_task_instruction(self, instruction: dict) -> dict:
        """Send a task instruction to the participant agent."""
        message = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "id": instruction["task_id"],
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "type": "task_instruction",
                                    "task_id": instruction["task_id"],
                                    "instruction": instruction["instruction"],
                                    "context": instruction.get("context", {}),
                                }
                            ),
                        }
                    ],
                }
            },
        }

        if self._session_id:
            message["params"]["sessionId"] = self._session_id

        response = await self._send_request(message)
        return self._parse_agent_response(response)

    async def send_command_result(self, task_id: str, result: dict) -> dict:
        """Send command execution result to the participant agent."""
        message = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "id": task_id,
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "type": "command_result",
                                    "task_id": task_id,
                                    "stdout": result.get("stdout", ""),
                                    "stderr": result.get("stderr", ""),
                                    "exit_code": result.get("exit_code", -1),
                                    "timed_out": result.get("timed_out", False),
                                }
                            ),
                        }
                    ],
                },
                "sessionId": self._session_id,
            },
        }

        response = await self._send_request(message)
        return self._parse_agent_response(response)

    async def _send_request(self, message: dict) -> dict:
        """Send a JSON-RPC request to the participant agent."""
        url = f"{self.participant_url}/"
        response = await self._client.post(
            url,
            json=message,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        result = response.json()

        # Store session ID from response
        if "result" in result and "sessionId" in result["result"]:
            self._session_id = result["result"]["sessionId"]

        return result

    def _parse_agent_response(self, response: dict) -> dict:
        """Parse the agent response from JSON-RPC result."""
        if "error" in response:
            raise Exception(f"Agent error: {response['error']}")

        result = response.get("result", {})

        # Extract the agent's message
        artifact = result.get("artifact", {})
        parts = artifact.get("parts", [])

        for part in parts:
            if part.get("type") == "text":
                try:
                    return json.loads(part["text"])
                except json.JSONDecodeError:
                    # If not JSON, treat as completion message
                    return {"action": "complete", "reasoning": part["text"]}

        return {"action": "complete", "reasoning": "No response"}

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
