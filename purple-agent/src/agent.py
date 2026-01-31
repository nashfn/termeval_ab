"""Core terminal agent logic."""

from typing import Optional

from .llm_client import LLMClient
from .planner import TaskPlanner


class TerminalAgent:
    """LLM-powered agent that executes terminal tasks."""

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        api_key: str | None = None,
        api_base: str | None = None,
    ):
        self.llm_client = LLMClient(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=api_key,
            api_base=api_base,
        )
        self.planner = TaskPlanner(self.llm_client)

        # Conversation history per task
        self._task_histories: dict[str, list[dict]] = {}
        self._task_contexts: dict[str, dict] = {}

    async def start_task(
        self,
        task_id: str,
        instruction: str,
        context: dict,
    ) -> dict:
        """Start a new task and return the first action."""
        # Initialize conversation history for this task
        self._task_histories[task_id] = []
        self._task_contexts[task_id] = {
            "instruction": instruction,
            "working_directory": context.get("working_directory", "/workspace"),
            "environment": context.get("environment", {}),
        }

        # Add the initial instruction to history
        self._task_histories[task_id].append(
            {
                "role": "user",
                "content": f"Task: {instruction}\n\nWorking directory: {context.get('working_directory', '/workspace')}",
            }
        )

        # Generate first command
        response = await self.planner.plan_next_action(
            instruction=instruction,
            history=self._task_histories[task_id],
            context=self._task_contexts[task_id],
        )

        # Add assistant response to history
        self._task_histories[task_id].append(
            {
                "role": "assistant",
                "content": self._format_response_for_history(response),
            }
        )

        return response

    async def process_result(
        self,
        task_id: str,
        result: dict,
    ) -> dict:
        """Process command result and return next action."""
        if task_id not in self._task_histories:
            return {
                "action": "complete",
                "reasoning": "Task not found in history",
            }

        # Format the result message
        result_message = self._format_result_message(result)

        # Add result to history
        self._task_histories[task_id].append(
            {
                "role": "user",
                "content": result_message,
            }
        )

        # Get task context
        context = self._task_contexts.get(task_id, {})
        instruction = context.get("instruction", "")

        # Generate next action
        response = await self.planner.plan_next_action(
            instruction=instruction,
            history=self._task_histories[task_id],
            context=context,
        )

        # Add response to history
        self._task_histories[task_id].append(
            {
                "role": "assistant",
                "content": self._format_response_for_history(response),
            }
        )

        return response

    def _format_result_message(self, result: dict) -> str:
        """Format command result as a message for the conversation."""
        parts = ["Command execution result:"]

        if result.get("timed_out"):
            parts.append("⚠️ Command timed out")

        parts.append(f"Exit code: {result.get('exit_code', -1)}")

        stdout = result.get("stdout", "").strip()
        if stdout:
            parts.append(f"stdout:\n```\n{stdout}\n```")

        stderr = result.get("stderr", "").strip()
        if stderr:
            parts.append(f"stderr:\n```\n{stderr}\n```")

        return "\n\n".join(parts)

    def _format_response_for_history(self, response: dict) -> str:
        """Format agent response for conversation history."""
        if response.get("action") == "execute":
            command = response.get("command", {})
            cmd = command.get("command", "")
            reasoning = response.get("reasoning", "")
            return f"I'll run: {cmd}\n\nReasoning: {reasoning}"
        else:
            return f"Task complete. {response.get('reasoning', '')}"

    def clear_task(self, task_id: str) -> None:
        """Clear history for a completed task."""
        self._task_histories.pop(task_id, None)
        self._task_contexts.pop(task_id, None)
