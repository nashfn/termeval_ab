# AgentBeats TerminalBench Implementation Plan

## Overview

Create AgentBeats green and purple agents for TerminalBench evaluation in `/Users/arunesh/nash/nashhub/termeval_ab`.

**Green Agent (Evaluator)**: Orchestrates TerminalBench tasks, manages Docker sandboxes, runs test scripts, scores results.

**Purple Agent (Participant)**: LLM-powered terminal task executor using LiteLLM for provider-agnostic LLM support.

---

## Project Structure

```
/Users/arunesh/nash/nashhub/termeval_ab/
├── README.md
├── pyproject.toml
├── scenario.toml
├── sample.env
│
├── green-agent/                      # TerminalBench Evaluator
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       ├── __init__.py
│       ├── server.py                 # A2A server initialization
│       ├── executor.py               # A2A request handler
│       ├── agent.py                  # Core evaluator logic
│       ├── messenger.py              # A2A messaging utilities
│       ├── task_loader.py            # TerminalBench task loading
│       ├── sandbox_manager.py        # Docker container management
│       ├── test_runner.py            # Test script execution
│       └── metrics.py                # Scoring and reporting
│
├── purple-agent/                     # Terminal Agent
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       ├── __init__.py
│       ├── server.py                 # A2A server initialization
│       ├── executor.py               # A2A request handler
│       ├── agent.py                  # Core terminal agent logic
│       ├── messenger.py              # A2A messaging utilities
│       ├── llm_client.py             # LiteLLM integration
│       └── planner.py                # Task planning/reasoning
│
└── shared/
    ├── __init__.py
    └── protocol.py                   # A2A message type definitions
```

---

## Implementation Details

### 1. Green Agent (TerminalBench Evaluator)

**Core Responsibilities:**
- Load TerminalBench tasks via Harbor framework
- Create isolated Docker sandbox for each task
- Send task instructions to purple agent via A2A protocol
- Execute commands returned by purple agent in sandbox
- Return stdout/stderr/exit_code to purple agent
- Run test scripts to verify task completion
- Score and report results

**Key Components:**

| File | Purpose |
|------|---------|
| `agent.py` | Main evaluation loop, A2A message handling, multi-turn orchestration |
| `task_loader.py` | Load tasks from TerminalBench via `harbor` Python package |
| `sandbox_manager.py` | Docker SDK integration for container lifecycle |
| `test_runner.py` | Execute task test scripts, parse reward output |
| `metrics.py` | Aggregate pass/fail rates, turns, timing |

**A2A Flow (Green → Purple → Green):**
1. Send `TaskInstruction` (task_id, instruction, context)
2. Receive `AgentResponse` (action=execute, command={...})
3. Execute command in sandbox, return `CommandResult`
4. Repeat until `AgentResponse` has action=complete
5. Run test script, record result

---

### 2. Purple Agent (Terminal Agent)

**Core Responsibilities:**
- Receive task instructions from green agent
- Use LLM to plan terminal commands
- Return commands to green agent for execution
- Process command results and plan next steps
- Signal completion when task is done

**Key Components:**

| File | Purpose |
|------|---------|
| `agent.py` | Handle task instructions and command results, maintain conversation history |
| `llm_client.py` | LiteLLM wrapper for provider-agnostic LLM access |
| `planner.py` | LLM prompting to generate next command or completion signal |

**LiteLLM Integration:**
```python
# Supports 100+ providers with same interface:
# anthropic/claude-sonnet-4-20250514
# openai/gpt-4o
# google/gemini-2.0-flash
# ollama/llama3
litellm.acompletion(model="anthropic/claude-sonnet-4-20250514", messages=[...])
```

---

### 3. A2A Message Protocol

```
Green Agent                              Purple Agent
    |                                        |
    |  TaskInstruction                       |
    |  {task_id, instruction, context}       |
    |--------------------------------------->|
    |                                        |
    |  AgentResponse (execute)               |
    |  {action:"execute", command:{...}}     |
    |<---------------------------------------|
    |                                        |
    |  [Execute in Docker sandbox]           |
    |                                        |
    |  CommandResult                         |
    |  {stdout, stderr, exit_code}           |
    |--------------------------------------->|
    |                                        |
    |  ... repeat until complete ...         |
    |                                        |
    |  AgentResponse (complete)              |
    |  {action:"complete", reasoning:...}    |
    |<---------------------------------------|
    |                                        |
    |  [Run test script, record score]       |
```

---

### 4. Scenario Configuration

**scenario.toml:**
```toml
[green_agent]
endpoint = "http://127.0.0.1:9009"
command = "python green-agent/src/server.py --host 127.0.0.1 --port 9009"

[[participants]]
name = "terminal_agent"
endpoint = "http://127.0.0.1:9010"
command = "python purple-agent/src/server.py --host 127.0.0.1 --port 9010"

[config]
dataset = "terminal-bench-core"
version = "2.0"
max_turns = 50
task_timeout = 600
model = "anthropic/claude-sonnet-4-20250514"
```

---

### 5. Dependencies

**Green Agent:**
- `a2a` - A2A protocol SDK
- `uvicorn` - ASGI server
- `docker` - Docker SDK for Python
- `harbor` - TerminalBench task loading
- `pydantic` - Data validation
- `httpx` - HTTP client

**Purple Agent:**
- `a2a` - A2A protocol SDK
- `uvicorn` - ASGI server
- `litellm` - LLM-agnostic SDK
- `pydantic` - Data validation
- `httpx` - HTTP client

---

### 6. Environment Variables

**sample.env:**
```
# LLM API Keys (set based on provider)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Optional
LITELLM_VERBOSE=false
```

---

## Verification Plan

1. **Unit Tests**: Test each component in isolation (task_loader, sandbox_manager, llm_client, planner)

2. **A2A Conformance**: Verify agent card endpoints and message handling

3. **Integration Test**:
   ```bash
   # Terminal 1: Start green agent
   python green-agent/src/server.py --port 9009

   # Terminal 2: Start purple agent
   python purple-agent/src/server.py --port 9010 --model anthropic/claude-sonnet-4-20250514

   # Terminal 3: Run scenario
   uv run agentbeats-run scenario.toml --show-logs
   ```

4. **End-to-End**: Run against subset of TerminalBench tasks, verify pass/fail matches expected

---

## Key Files to Create

1. `/Users/arunesh/nash/nashhub/termeval_ab/green-agent/src/agent.py` - Evaluation orchestration loop
2. `/Users/arunesh/nash/nashhub/termeval_ab/green-agent/src/sandbox_manager.py` - Docker container management
3. `/Users/arunesh/nash/nashhub/termeval_ab/purple-agent/src/agent.py` - Terminal task handler
4. `/Users/arunesh/nash/nashhub/termeval_ab/purple-agent/src/llm_client.py` - LiteLLM wrapper
5. `/Users/arunesh/nash/nashhub/termeval_ab/purple-agent/src/planner.py` - LLM-based command planning
6. `/Users/arunesh/nash/nashhub/termeval_ab/scenario.toml` - AgentBeats scenario config

---

## Sources

- [AgentBeats Tutorial](https://github.com/RDI-Foundation/agentbeats-tutorial)
- [Green Agent Template](https://github.com/RDI-Foundation/green-agent-template)
- [Agent Template (Purple)](https://github.com/RDI-Foundation/agent-template)
- [TerminalBench](https://github.com/laude-institute/terminal-bench)
- [Harbor Framework](https://github.com/laude-institute/harbor)
- [LiteLLM](https://github.com/BerriAI/litellm)
