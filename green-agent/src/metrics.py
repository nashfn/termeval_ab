"""Scoring and reporting for TerminalBench evaluation."""

from typing import Optional


class MetricsCollector:
    """Collects and aggregates evaluation metrics."""

    def __init__(self):
        self._results: list[dict] = []
        self._total_tasks: int = 0
        self._dataset: str = ""

    def reset(self):
        """Reset all metrics."""
        self._results = []
        self._total_tasks = 0

    def set_dataset(self, dataset: str):
        """Set the dataset name."""
        self._dataset = dataset

    def set_total_tasks(self, total: int):
        """Set the total number of tasks."""
        self._total_tasks = total

    def record_result(self, result: dict):
        """Record a single task result."""
        self._results.append(result)

    def get_results(self) -> dict:
        """Get aggregated results."""
        if not self._results:
            return {
                "dataset": self._dataset,
                "total_tasks": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "avg_turns": 0.0,
                "avg_time": 0.0,
                "total_reward": 0.0,
                "results": [],
            }

        passed = sum(1 for r in self._results if r.get("passed", False))
        failed = len(self._results) - passed

        total_turns = sum(r.get("turns", 0) for r in self._results)
        total_time = sum(r.get("total_time", 0) for r in self._results)
        total_reward = sum(r.get("reward", 0) for r in self._results)

        return {
            "dataset": self._dataset,
            "total_tasks": len(self._results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self._results) if self._results else 0.0,
            "avg_turns": total_turns / len(self._results) if self._results else 0.0,
            "avg_time": total_time / len(self._results) if self._results else 0.0,
            "total_reward": total_reward,
            "results": self._results,
        }

    def get_summary(self) -> str:
        """Get a human-readable summary."""
        results = self.get_results()

        lines = [
            "=" * 50,
            "TerminalBench Evaluation Summary",
            "=" * 50,
            f"Dataset: {results['dataset']}",
            f"Total Tasks: {results['total_tasks']}",
            f"Passed: {results['passed']}",
            f"Failed: {results['failed']}",
            f"Pass Rate: {results['pass_rate']:.1%}",
            f"Average Turns: {results['avg_turns']:.1f}",
            f"Average Time: {results['avg_time']:.1f}s",
            f"Total Reward: {results['total_reward']:.1f}",
            "=" * 50,
        ]

        return "\n".join(lines)

    def export_json(self) -> dict:
        """Export results as JSON-serializable dict."""
        return self.get_results()

    def get_task_result(self, task_id: str) -> Optional[dict]:
        """Get result for a specific task."""
        for result in self._results:
            if result.get("task_id") == task_id:
                return result
        return None
