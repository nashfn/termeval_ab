"""A2A request handler for the purple agent."""

import asyncio
import json
from typing import AsyncIterable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import Event
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

from .agent import TerminalAgent


class PurpleAgentExecutor(AgentExecutor):
    """Executor that handles A2A requests for the purple agent."""

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ):
        self.agent = TerminalAgent(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: asyncio.Queue[Event],
    ) -> None:
        """Execute a request from the A2A protocol."""
        task = context.current_task
        if task is None:
            return

        # Extract the request from the task
        user_message = self._get_last_user_message(task)
        if not user_message:
            await self._send_error(event_queue, task, "No user message found")
            return

        request_text = self._extract_text(user_message)

        try:
            # Parse the incoming message
            request_data = json.loads(request_text)
            message_type = request_data.get("type")

            if message_type == "task_instruction":
                await self._handle_task_instruction(event_queue, task, request_data)
            elif message_type == "command_result":
                await self._handle_command_result(event_queue, task, request_data)
            else:
                await self._send_error(
                    event_queue, task, f"Unknown message type: {message_type}"
                )
        except json.JSONDecodeError:
            await self._send_error(event_queue, task, "Invalid JSON in request")
        except Exception as e:
            await self._send_error(event_queue, task, str(e))

    async def _handle_task_instruction(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
        request_data: dict,
    ) -> None:
        """Handle a new task instruction from the green agent."""
        # Update task status to working
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.working),
            )
        )

        # Initialize new task in agent
        task_id = request_data.get("task_id", "")
        instruction = request_data.get("instruction", "")
        context = request_data.get("context", {})

        response = await self.agent.start_task(task_id, instruction, context)

        # Send response
        await self._send_response(event_queue, task, response)

    async def _handle_command_result(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
        request_data: dict,
    ) -> None:
        """Handle command execution result from the green agent."""
        task_id = request_data.get("task_id", "")
        result = {
            "stdout": request_data.get("stdout", ""),
            "stderr": request_data.get("stderr", ""),
            "exit_code": request_data.get("exit_code", -1),
            "timed_out": request_data.get("timed_out", False),
        }

        response = await self.agent.process_result(task_id, result)

        # Send response
        await self._send_response(event_queue, task, response)

    async def _send_response(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
        response: dict,
    ) -> None:
        """Send agent response back to the green agent."""
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.completed),
                artifact=Message(
                    role=Role.agent,
                    parts=[TextPart(text=json.dumps(response))],
                ),
            )
        )

    async def _send_error(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
        error: str,
    ) -> None:
        """Send error response."""
        response = {
            "action": "complete",
            "reasoning": f"Error: {error}",
        }
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.failed),
                artifact=Message(
                    role=Role.agent,
                    parts=[TextPart(text=json.dumps(response))],
                ),
            )
        )

    def _get_last_user_message(self, task: Task) -> Message | None:
        """Get the last user message from the task history."""
        if task.history:
            for msg in reversed(task.history):
                if msg.role == Role.user:
                    return msg
        return None

    def _extract_text(self, message: Message) -> str:
        """Extract text content from a message."""
        texts = []
        for part in message.parts:
            if isinstance(part, TextPart):
                texts.append(part.text)
        return " ".join(texts)

    def cancel(self, context: RequestContext, event_queue: asyncio.Queue[Event]):
        """Cancel the current execution."""
        pass
