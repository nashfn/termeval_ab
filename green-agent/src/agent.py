"""Core evaluator logic for TerminalBench."""

import asyncio
import time
from typing import Optional

from .messenger import A2AMessenger
from .sandbox_manager import SandboxManager
from .task_loader import TaskLoader
from .test_runner import TestRunner
from .metrics import MetricsCollector


class TerminalBenchEvaluator:
    """Main evaluation loop for TerminalBench tasks."""

    def __init__(
        self,
        dataset: str,
        max_turns: int,
        task_timeout: int,
        participant_url: str,
    ):
        self.dataset = dataset
        self.max_turns = max_turns
        self.task_timeout = task_timeout
        self.participant_url = participant_url

        self.task_loader = TaskLoader(dataset)
        self.sandbox_manager = SandboxManager()
        self.test_runner = TestRunner()
        self.metrics = MetricsCollector()
        self.messenger = A2AMessenger(participant_url)

        self._status = "idle"
        self._current_task: Optional[str] = None

    def get_status(self) -> str:
        """Get current evaluator status."""
        if self._status == "idle":
            return "Evaluator is idle. Send 'run' to start evaluation."
        elif self._status == "running":
            return f"Evaluation in progress. Current task: {self._current_task}"
        elif self._status == "completed":
            return "Evaluation completed. Results available."
        return f"Status: {self._status}"

    async def run_evaluation(self) -> dict:
        """Run the full TerminalBench evaluation."""
        self._status = "running"
        self.metrics.reset()

        try:
            # Load tasks
            tasks = await self.task_loader.load_tasks()
            self.metrics.set_total_tasks(len(tasks))

            # Evaluate each task
            for task in tasks:
                self._current_task = task.task_id
                result = await self._evaluate_task(task)
                self.metrics.record_result(result)

            self._status = "completed"
            return self.metrics.get_results()

        except Exception as e:
            self._status = f"error: {e}"
            raise

    async def _evaluate_task(self, task) -> dict:
        """Evaluate a single TerminalBench task."""
        start_time = time.time()
        turns = 0
        error = None
        passed = False

        sandbox = None
        try:
            # Create sandbox for this task
            sandbox = await self.sandbox_manager.create_sandbox(task)

            # Send initial task instruction
            instruction = {
                "task_id": task.task_id,
                "instruction": task.instruction,
                "context": {
                    "working_directory": task.working_directory,
                    "environment": task.environment,
                },
            }

            response = await self.messenger.send_task_instruction(instruction)

            # Multi-turn execution loop
            while turns < self.max_turns:
                turns += 1

                if response.get("action") == "complete":
                    break

                if response.get("action") == "execute":
                    command = response.get("command", {})

                    # Execute command in sandbox
                    result = await self.sandbox_manager.execute_command(
                        sandbox,
                        command.get("command", ""),
                        timeout=command.get("timeout", 30),
                        workdir=command.get("workdir"),
                    )

                    # Send result back to participant
                    response = await self.messenger.send_command_result(
                        task.task_id, result
                    )

                # Check timeout
                if time.time() - start_time > self.task_timeout:
                    error = "Task timeout exceeded"
                    break

            # Run test script to verify completion
            if not error:
                test_result = await self.test_runner.run_test(sandbox, task)
                passed = test_result.get("passed", False)
                if not passed and test_result.get("error"):
                    error = test_result["error"]

        except asyncio.TimeoutError:
            error = "Task timeout"
        except Exception as e:
            error = str(e)
        finally:
            # Cleanup sandbox
            if sandbox:
                await self.sandbox_manager.cleanup_sandbox(sandbox)

        total_time = time.time() - start_time

        return {
            "task_id": task.task_id,
            "passed": passed,
            "reward": 1.0 if passed else 0.0,
            "turns": turns,
            "total_time": total_time,
            "error": error,
        }
