"""Docker container management for task sandboxes."""

import asyncio
from typing import Optional

import docker
from docker.models.containers import Container

from .task_loader import TerminalBenchTask


class SandboxManager:
    """Manages Docker containers for isolated task execution."""

    def __init__(self):
        self._client: Optional[docker.DockerClient] = None
        self._containers: dict[str, Container] = {}

    def _get_client(self) -> docker.DockerClient:
        """Get or create Docker client."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    async def create_sandbox(self, task: TerminalBenchTask) -> str:
        """Create a Docker sandbox for a task."""
        client = self._get_client()

        # Pull image if needed
        try:
            client.images.get(task.docker_image)
        except docker.errors.ImageNotFound:
            await asyncio.to_thread(client.images.pull, task.docker_image)

        # Create container
        container = await asyncio.to_thread(
            client.containers.create,
            image=task.docker_image,
            command="sleep infinity",
            working_dir=task.working_directory,
            environment=task.environment,
            detach=True,
            tty=True,
            stdin_open=True,
            network_mode="none",  # Isolated network
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=50000,  # 50% CPU limit
        )

        # Start container
        await asyncio.to_thread(container.start)

        # Run setup commands
        for cmd in task.setup_commands:
            await self.execute_command(container.id, cmd)

        self._containers[container.id] = container
        return container.id

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = 30,
        workdir: Optional[str] = None,
    ) -> dict:
        """Execute a command in the sandbox."""
        client = self._get_client()

        try:
            container = client.containers.get(sandbox_id)
        except docker.errors.NotFound:
            return {
                "stdout": "",
                "stderr": "Container not found",
                "exit_code": -1,
                "timed_out": False,
            }

        exec_kwargs = {
            "cmd": ["/bin/sh", "-c", command],
            "stdout": True,
            "stderr": True,
            "demux": True,
        }

        if workdir:
            exec_kwargs["workdir"] = workdir

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(container.exec_run, **exec_kwargs),
                timeout=timeout,
            )

            stdout = result.output[0] if result.output[0] else b""
            stderr = result.output[1] if result.output[1] else b""

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": result.exit_code,
                "timed_out": False,
            }

        except asyncio.TimeoutError:
            return {
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -1,
                "timed_out": True,
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "timed_out": False,
            }

    async def cleanup_sandbox(self, sandbox_id: str) -> None:
        """Remove a sandbox container."""
        client = self._get_client()

        try:
            container = client.containers.get(sandbox_id)
            await asyncio.to_thread(container.stop, timeout=5)
            await asyncio.to_thread(container.remove, force=True)
        except docker.errors.NotFound:
            pass
        except Exception:
            # Force remove on any error
            try:
                container = client.containers.get(sandbox_id)
                await asyncio.to_thread(container.remove, force=True)
            except Exception:
                pass

        self._containers.pop(sandbox_id, None)

    async def cleanup_all(self) -> None:
        """Remove all sandbox containers."""
        for sandbox_id in list(self._containers.keys()):
            await self.cleanup_sandbox(sandbox_id)
