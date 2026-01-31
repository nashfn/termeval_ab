"""A2A server initialization for the purple agent."""

import argparse
import sys
from pathlib import Path

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.executor import PurpleAgentExecutor


def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the agent card for the purple agent."""
    return AgentCard(
        name="Terminal Agent",
        description="LLM-powered agent that executes terminal tasks for TerminalBench",
        url=f"http://{host}:{port}",
        version="0.1.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="execute_task",
                name="Execute Terminal Task",
                description="Execute terminal commands to complete a given task",
                tags=["terminal", "shell", "command"],
            ),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Terminal Agent")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9010, help="Port to bind to")
    parser.add_argument(
        "--model",
        default="anthropic/claude-sonnet-4-20250514",
        help="LLM model to use (LiteLLM format)",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=4096, help="Max tokens for LLM response"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0, help="LLM temperature"
    )
    args = parser.parse_args()

    agent_card = create_agent_card(args.host, args.port)

    executor = PurpleAgentExecutor(
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=None,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print(f"Starting Terminal Agent on {args.host}:{args.port}")
    print(f"Using model: {args.model}")
    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
