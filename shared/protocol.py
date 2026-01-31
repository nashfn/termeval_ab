"""A2A message type definitions for TerminalBench evaluation."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Action types for agent responses."""

    EXECUTE = "execute"
    COMPLETE = "complete"


class Command(BaseModel):
    """A command to execute in the sandbox."""

    command: str = Field(..., description="The shell command to execute")
    timeout: int = Field(default=30, description="Command timeout in seconds")
    workdir: Optional[str] = Field(default=None, description="Working directory")


class TaskInstruction(BaseModel):
    """Message from green agent to purple agent with task details."""

    task_id: str = Field(..., description="Unique task identifier")
    instruction: str = Field(..., description="Natural language task instruction")
    context: dict = Field(
        default_factory=dict,
        description="Additional context (filesystem state, environment info)",
    )


class CommandResult(BaseModel):
    """Result of executing a command in the sandbox."""

    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    exit_code: int = Field(..., description="Exit code (0 = success)")
    timed_out: bool = Field(default=False, description="Whether command timed out")


class AgentResponse(BaseModel):
    """Response from purple agent to green agent."""

    action: ActionType = Field(..., description="Action type: execute or complete")
    command: Optional[Command] = Field(
        default=None, description="Command to execute (if action=execute)"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Agent's reasoning for this action"
    )


class EvaluationResult(BaseModel):
    """Result of evaluating a single task."""

    task_id: str = Field(..., description="Task identifier")
    passed: bool = Field(..., description="Whether the task was completed successfully")
    reward: float = Field(default=0.0, description="Reward score (0.0 to 1.0)")
    turns: int = Field(..., description="Number of turns taken")
    total_time: float = Field(..., description="Total execution time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BenchmarkResults(BaseModel):
    """Aggregated results for a benchmark run."""

    dataset: str = Field(..., description="Dataset name")
    total_tasks: int = Field(..., description="Total number of tasks")
    passed: int = Field(..., description="Number of tasks passed")
    failed: int = Field(..., description="Number of tasks failed")
    pass_rate: float = Field(..., description="Pass rate (0.0 to 1.0)")
    avg_turns: float = Field(..., description="Average turns per task")
    avg_time: float = Field(..., description="Average time per task in seconds")
    results: list[EvaluationResult] = Field(
        default_factory=list, description="Individual task results"
    )
