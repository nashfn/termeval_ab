"""Test script execution for verifying task completion."""

from .task_loader import TerminalBenchTask
from .sandbox_manager import SandboxManager


class TestRunner:
    """Executes test scripts to verify task completion."""

    def __init__(self):
        self._sandbox_manager: SandboxManager | None = None

    async def run_test(
        self,
        sandbox_id: str,
        task: TerminalBenchTask,
        sandbox_manager: SandboxManager | None = None,
    ) -> dict:
        """Run the test script for a task and return the result."""
        if sandbox_manager is None:
            if self._sandbox_manager is None:
                self._sandbox_manager = SandboxManager()
            sandbox_manager = self._sandbox_manager

        # Execute the test script
        result = await sandbox_manager.execute_command(
            sandbox_id,
            task.test_script,
            timeout=60,
            workdir=task.working_directory,
        )

        # Determine pass/fail based on exit code
        passed = result["exit_code"] == 0

        # Calculate reward
        reward = task.expected_reward if passed else 0.0

        return {
            "passed": passed,
            "reward": reward,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "error": result["stderr"] if not passed else None,
        }

    async def run_custom_test(
        self,
        sandbox_id: str,
        test_script: str,
        workdir: str = "/workspace",
        sandbox_manager: SandboxManager | None = None,
    ) -> dict:
        """Run a custom test script."""
        if sandbox_manager is None:
            if self._sandbox_manager is None:
                self._sandbox_manager = SandboxManager()
            sandbox_manager = self._sandbox_manager

        result = await sandbox_manager.execute_command(
            sandbox_id,
            test_script,
            timeout=60,
            workdir=workdir,
        )

        return {
            "passed": result["exit_code"] == 0,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
        }
