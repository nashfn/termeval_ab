# AgentBeats TerminalBench

AgentBeats green and purple agents for TerminalBench evaluation.

## Overview

- **Green Agent (Evaluator)**: Orchestrates TerminalBench tasks, manages Docker sandboxes, runs test scripts, scores results.
- **Purple Agent (Participant)**: LLM-powered terminal task executor using LiteLLM for provider-agnostic LLM support.

## Project Structure

```
termeval_ab/
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

## Setup

### Prerequisites

- Python 3.10+
- Docker (for sandbox execution)
- uv (recommended) or pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd termeval_ab
   ```

2. Install dependencies:
   ```bash
   # Install green agent
   cd green-agent && uv pip install -e . && cd ..

   # Install purple agent
   cd purple-agent && uv pip install -e . && cd ..
   ```

3. Configure environment variables:
   ```bash
   cp sample.env .env
   # Edit .env with your API keys
   ```

4. Ensure Docker is running:
   ```bash
   docker info
   ```

## Running Locally

### Start the Agents

```bash
# Terminal 1: Start green agent (evaluator)
python green-agent/src/server.py --host 127.0.0.1 --port 9009

# Terminal 2: Start purple agent (participant)
python purple-agent/src/server.py --host 127.0.0.1 --port 9010 --model anthropic/claude-sonnet-4-20250514
```

### Run the Scenario

```bash
# Terminal 3: Run AgentBeats scenario
uv run agentbeats-run scenario.toml --show-logs
```

## Configuration

### scenario.toml

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

### Supported LLM Providers

Via LiteLLM, supports 100+ providers including:
- `anthropic/claude-sonnet-4-20250514`
- `openai/gpt-4o`
- `google/gemini-2.0-flash`
- `ollama/llama3`

---

## Publishing to GitHub Container Registry (ghcr.io)

### Prerequisites

1. Create a GitHub Personal Access Token (PAT) with `write:packages` scope:
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Generate new token with `write:packages` and `read:packages` scopes

2. Login to ghcr.io:
   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

### Build and Push Images

```bash
# Set your GitHub username/org
export GITHUB_USER=your-username

# Build green agent
docker build -t ghcr.io/$GITHUB_USER/terminalbench-green-agent:latest ./green-agent
docker build -t ghcr.io/$GITHUB_USER/terminalbench-green-agent:v0.1.0 ./green-agent

# Build purple agent
docker build -t ghcr.io/$GITHUB_USER/terminalbench-purple-agent:latest ./purple-agent
docker build -t ghcr.io/$GITHUB_USER/terminalbench-purple-agent:v0.1.0 ./purple-agent

# Push green agent
docker push ghcr.io/$GITHUB_USER/terminalbench-green-agent:latest
docker push ghcr.io/$GITHUB_USER/terminalbench-green-agent:v0.1.0

# Push purple agent
docker push ghcr.io/$GITHUB_USER/terminalbench-purple-agent:latest
docker push ghcr.io/$GITHUB_USER/terminalbench-purple-agent:v0.1.0
```

### Make Packages Public (Optional)

1. Go to GitHub → Your Profile → Packages
2. Select each package → Package settings → Change visibility → Public

---

## Submitting to AgentBeats Portal

### Step 1: Prepare Your Submission

1. Ensure your agents are working locally:
   ```bash
   uv run agentbeats-run scenario.toml --show-logs
   ```

2. Push your Docker images to ghcr.io (see above)

3. Verify images are accessible:
   ```bash
   docker pull ghcr.io/$GITHUB_USER/terminalbench-green-agent:latest
   docker pull ghcr.io/$GITHUB_USER/terminalbench-purple-agent:latest
   ```

### Step 2: Create Submission Manifest

Create a `submission.toml` file:

```toml
[submission]
name = "TerminalBench Evaluation"
description = "LLM-powered terminal task executor for TerminalBench"
version = "0.1.0"
authors = ["Your Name <your.email@example.com>"]

[green_agent]
image = "ghcr.io/YOUR_USERNAME/terminalbench-green-agent:v0.1.0"
endpoint_port = 9009

[purple_agent]
image = "ghcr.io/YOUR_USERNAME/terminalbench-purple-agent:v0.1.0"
endpoint_port = 9010

[benchmark]
name = "terminal-bench-core"
version = "2.0"

[requirements]
docker = true
gpu = false
memory = "4GB"
```

### Step 3: Submit via AgentBeats CLI

```bash
# Install AgentBeats CLI if not already installed
pip install agentbeats-cli

# Login to AgentBeats portal
agentbeats login

# Validate your submission
agentbeats validate submission.toml

# Submit for evaluation
agentbeats submit submission.toml
```

### Step 4: Submit via AgentBeats Web Portal

1. Navigate to [AgentBeats Portal](https://agentbeats.ai) (or your organization's portal URL)

2. Sign in with your credentials

3. Click "New Submission"

4. Fill in the submission form:
   - **Name**: TerminalBench Evaluation
   - **Benchmark**: terminal-bench-core
   - **Green Agent Image**: `ghcr.io/YOUR_USERNAME/terminalbench-green-agent:v0.1.0`
   - **Purple Agent Image**: `ghcr.io/YOUR_USERNAME/terminalbench-purple-agent:v0.1.0`

5. Upload your `scenario.toml` configuration

6. Click "Submit for Evaluation"

### Step 5: Monitor Evaluation

```bash
# Check submission status
agentbeats status <submission-id>

# View logs
agentbeats logs <submission-id>

# Download results
agentbeats results <submission-id> --output results.json
```

Or monitor via the web portal dashboard.

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/publish.yml`:

```yaml
name: Build and Publish

on:
  push:
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push green agent
        uses: docker/build-push-action@v5
        with:
          context: ./green-agent
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ github.repository_owner }}/terminalbench-green-agent:${{ github.ref_name }}
            ${{ env.REGISTRY }}/${{ github.repository_owner }}/terminalbench-green-agent:latest

      - name: Build and push purple agent
        uses: docker/build-push-action@v5
        with:
          context: ./purple-agent
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ github.repository_owner }}/terminalbench-purple-agent:${{ github.ref_name }}
            ${{ env.REGISTRY }}/${{ github.repository_owner }}/terminalbench-purple-agent:latest
```

### Auto-Submit on Release

Add to your workflow:

```yaml
  submit:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install AgentBeats CLI
        run: pip install agentbeats-cli

      - name: Submit to AgentBeats
        env:
          AGENTBEATS_TOKEN: ${{ secrets.AGENTBEATS_TOKEN }}
        run: |
          agentbeats submit submission.toml --token $AGENTBEATS_TOKEN
```

---

## Troubleshooting

### Common Issues

**Docker permission denied:**
```bash
sudo usermod -aG docker $USER
# Then log out and back in
```

**ghcr.io authentication failed:**
```bash
# Ensure token has correct scopes
# Re-authenticate:
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

**Agent connection refused:**
```bash
# Check if agents are running
curl http://127.0.0.1:9009/.well-known/agent.json
curl http://127.0.0.1:9010/.well-known/agent.json
```

**LLM API errors:**
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Test LiteLLM directly
python -c "import litellm; print(litellm.completion(model='anthropic/claude-sonnet-4-20250514', messages=[{'role':'user','content':'hello'}]))"
```

---

## License

MIT License
