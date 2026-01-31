"""A2A server initialization for the green agent."""

import argparse
import sys
from pathlib import Path

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.executor import GreenAgentExecutor


def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the agent card for the green agent."""
    return AgentCard(
        name="TerminalBench Evaluator",
        description="Green agent that orchestrates TerminalBench evaluation tasks",
        url=f"http://{host}:{port}",
        version="0.1.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="evaluate",
                name="Evaluate TerminalBench Tasks",
                description="Load and evaluate TerminalBench tasks against a participant agent",
                tags=["evaluation", "benchmark", "terminal"],
            ),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="TerminalBench Evaluator Agent")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind to")
    parser.add_argument("--dataset", default="terminal-bench-core", help="Dataset name")
    parser.add_argument("--max-turns", type=int, default=50, help="Max turns per task")
    parser.add_argument(
        "--task-timeout", type=int, default=600, help="Task timeout in seconds"
    )
    parser.add_argument(
        "--participant-url",
        default="http://127.0.0.1:9010",
        help="Participant agent URL",
    )
    args = parser.parse_args()

    agent_card = create_agent_card(args.host, args.port)

    executor = GreenAgentExecutor(
        dataset=args.dataset,
        max_turns=args.max_turns,
        task_timeout=args.task_timeout,
        participant_url=args.participant_url,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=None,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print(f"Starting TerminalBench Evaluator on {args.host}:{args.port}")
    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
