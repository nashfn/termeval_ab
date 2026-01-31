"""TerminalBench task loading via Harbor framework."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TerminalBenchTask:
    """Represents a single TerminalBench task."""

    task_id: str
    instruction: str
    working_directory: str
    environment: dict
    test_script: str
    docker_image: str
    setup_commands: list[str]
    expected_reward: float = 1.0
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TaskLoader:
    """Loads TerminalBench tasks from the Harbor framework."""

    def __init__(self, dataset: str):
        self.dataset = dataset
        self._tasks: list[TerminalBenchTask] = []

    async def load_tasks(self) -> list[TerminalBenchTask]:
        """Load tasks from the TerminalBench dataset."""
        try:
            # Try to load via Harbor
            from harbor import load_dataset

            dataset = load_dataset(self.dataset)
            self._tasks = [self._convert_task(t) for t in dataset.tasks]
        except ImportError:
            # Harbor not available, use sample tasks for testing
            self._tasks = self._get_sample_tasks()

        return self._tasks

    def _convert_task(self, harbor_task) -> TerminalBenchTask:
        """Convert a Harbor task to our internal format."""
        return TerminalBenchTask(
            task_id=harbor_task.id,
            instruction=harbor_task.instruction,
            working_directory=harbor_task.working_directory or "/workspace",
            environment=harbor_task.environment or {},
            test_script=harbor_task.test_script,
            docker_image=harbor_task.docker_image or "ubuntu:22.04",
            setup_commands=harbor_task.setup_commands or [],
            expected_reward=harbor_task.expected_reward or 1.0,
            tags=harbor_task.tags or [],
        )

    def _get_sample_tasks(self) -> list[TerminalBenchTask]:
        """Get sample tasks for testing when Harbor is not available."""
        return [
            TerminalBenchTask(
                task_id="sample-001",
                instruction="Create a file named 'hello.txt' containing the text 'Hello, World!'",
                working_directory="/workspace",
                environment={},
                test_script='test -f /workspace/hello.txt && grep -q "Hello, World!" /workspace/hello.txt',
                docker_image="ubuntu:22.04",
                setup_commands=[],
                tags=["file-operations", "basic"],
            ),
            TerminalBenchTask(
                task_id="sample-002",
                instruction="Create a directory named 'mydir' and inside it create a file named 'data.json' with valid JSON content: {\"key\": \"value\"}",
                working_directory="/workspace",
                environment={},
                test_script='test -d /workspace/mydir && test -f /workspace/mydir/data.json && python3 -c "import json; json.load(open(\'/workspace/mydir/data.json\'))"',
                docker_image="python:3.11-slim",
                setup_commands=[],
                tags=["file-operations", "json"],
            ),
            TerminalBenchTask(
                task_id="sample-003",
                instruction="Find all .txt files in /workspace and count how many there are. Write the count to a file called 'count.txt'",
                working_directory="/workspace",
                environment={},
                test_script="test -f /workspace/count.txt",
                docker_image="ubuntu:22.04",
                setup_commands=[
                    "mkdir -p /workspace/subdir",
                    "touch /workspace/a.txt /workspace/b.txt /workspace/subdir/c.txt",
                ],
                tags=["file-operations", "find"],
            ),
        ]

    def get_task_by_id(self, task_id: str) -> Optional[TerminalBenchTask]:
        """Get a specific task by ID."""
        for task in self._tasks:
            if task.task_id == task_id:
                return task
        return None
