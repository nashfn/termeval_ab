"""A2A server initialization for the purple agent."""

import argparse
import os
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
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
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
    parser = argparse.ArgumentParser(
        description="Terminal Agent - LLM-powered task executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use Anthropic Claude
  python server.py --model anthropic/claude-sonnet-4-20250514

  # Use Nebius Cloud
  python server.py --model nebius/meta-llama/Meta-Llama-3.1-70B-Instruct \\
    --api-base https://api.studio.nebius.ai/v1 \\
    --api-key $NEBIUS_API_KEY

  # Use local Ollama
  python server.py --model ollama/llama3 \\
    --api-base http://localhost:11434

  # Use custom OpenAI-compatible endpoint
  python server.py --model openai/mistral-7b \\
    --api-base http://localhost:8000/v1

Environment Variables:
  NEBIUS_API_KEY, NEBIUS_API_BASE    - Nebius Cloud credentials
  OPENAI_API_KEY, OPENAI_API_BASE    - OpenAI or compatible endpoint
  ANTHROPIC_API_KEY                  - Anthropic API key
  AZURE_API_KEY, AZURE_API_BASE      - Azure OpenAI credentials
  OLLAMA_API_BASE                    - Ollama server URL
  LITELLM_VERBOSE                    - Enable verbose logging (true/false)
        """,
    )

    # Server configuration
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9010, help="Port to bind to")

    # LLM configuration
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-20250514"),
        help="LLM model in LiteLLM format: provider/model-name (default: anthropic/claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="Custom API base URL (overrides environment variable)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (overrides environment variable, not recommended for CLI)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max tokens for LLM response (default: 4096)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM sampling temperature (default: 0.0)",
    )

    args = parser.parse_args()

    agent_card = create_agent_card(args.host, args.port)

    executor = PurpleAgentExecutor(
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        api_key=args.api_key,
        api_base=args.api_base,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=None,
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # Print startup info
    print(f"Starting Terminal Agent on {args.host}:{args.port}")
    print(f"Model: {args.model}")
    if args.api_base:
        print(f"API Base: {args.api_base}")
    print(f"Max Tokens: {args.max_tokens}, Temperature: {args.temperature}")
    print("-" * 50)

    uvicorn.run(app.build(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
