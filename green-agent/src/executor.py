"""A2A request handler for the green agent."""

import asyncio
from typing import AsyncIterable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import Event
from a2a.types import (
    FilePart,
    FileWithBytes,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

from .agent import TerminalBenchEvaluator


class GreenAgentExecutor(AgentExecutor):
    """Executor that handles A2A requests for the green agent."""

    def __init__(
        self,
        dataset: str,
        max_turns: int,
        task_timeout: int,
        participant_url: str,
    ):
        self.evaluator = TerminalBenchEvaluator(
            dataset=dataset,
            max_turns=max_turns,
            task_timeout=task_timeout,
            participant_url=participant_url,
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

        # Handle different request types
        if "run" in request_text.lower() or "evaluate" in request_text.lower():
            await self._run_evaluation(event_queue, task, request_text)
        elif "status" in request_text.lower():
            await self._send_status(event_queue, task)
        else:
            await self._send_help(event_queue, task)

    async def _run_evaluation(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
        request_text: str,
    ) -> None:
        """Run the TerminalBench evaluation."""
        # Update task status to working
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.working),
            )
        )

        try:
            # Run the evaluation
            results = await self.evaluator.run_evaluation()

            # Format results as response
            response_text = self._format_results(results)

            # Send completion event
            await event_queue.put(
                Event(
                    task_id=task.id,
                    status=TaskStatus(state=TaskState.completed),
                    artifact=Message(
                        role=Role.agent,
                        parts=[TextPart(text=response_text)],
                    ),
                )
            )
        except Exception as e:
            await self._send_error(event_queue, task, str(e))

    async def _send_status(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
    ) -> None:
        """Send current evaluator status."""
        status = self.evaluator.get_status()
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.completed),
                artifact=Message(
                    role=Role.agent,
                    parts=[TextPart(text=status)],
                ),
            )
        )

    async def _send_help(
        self,
        event_queue: asyncio.Queue[Event],
        task: Task,
    ) -> None:
        """Send help message."""
        help_text = """TerminalBench Evaluator Commands:

- "run" or "evaluate": Start the TerminalBench evaluation
- "status": Get current evaluation status

The evaluator will:
1. Load tasks from the TerminalBench dataset
2. Create Docker sandboxes for each task
3. Send task instructions to the participant agent
4. Execute returned commands in the sandbox
5. Run test scripts to verify completion
6. Report aggregate results
"""
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.completed),
                artifact=Message(
                    role=Role.agent,
                    parts=[TextPart(text=help_text)],
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
        await event_queue.put(
            Event(
                task_id=task.id,
                status=TaskStatus(state=TaskState.failed),
                artifact=Message(
                    role=Role.agent,
                    parts=[TextPart(text=f"Error: {error}")],
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

    def _format_results(self, results: dict) -> str:
        """Format evaluation results as a readable string."""
        lines = [
            "# TerminalBench Evaluation Results",
            "",
            f"Dataset: {results.get('dataset', 'unknown')}",
            f"Total Tasks: {results.get('total_tasks', 0)}",
            f"Passed: {results.get('passed', 0)}",
            f"Failed: {results.get('failed', 0)}",
            f"Pass Rate: {results.get('pass_rate', 0.0):.1%}",
            f"Avg Turns: {results.get('avg_turns', 0.0):.1f}",
            f"Avg Time: {results.get('avg_time', 0.0):.1f}s",
            "",
            "## Task Details",
            "",
        ]

        for result in results.get("results", []):
            status = "✓" if result.get("passed") else "✗"
            lines.append(
                f"- [{status}] {result.get('task_id')}: "
                f"{result.get('turns', 0)} turns, "
                f"{result.get('total_time', 0.0):.1f}s"
            )
            if result.get("error"):
                lines.append(f"  Error: {result['error']}")

        return "\n".join(lines)

    def cancel(self, context: RequestContext, event_queue: asyncio.Queue[Event]):
        """Cancel the current execution."""
        pass
