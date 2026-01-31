⏺ Done. I've updated the following files to support custom LLM endpoints like Nebius:

  sample.env - Comprehensive environment variable configuration:
  - API keys for all major providers (Anthropic, OpenAI, Google, Azure, AWS, Together AI, Groq)
  - Custom endpoint URLs (NEBIUS_API_BASE, OPENAI_API_BASE, AZURE_API_BASE, OLLAMA_API_BASE)
  - LiteLLM configuration options
  - Detailed documentation for each provider

  purple-agent/src/llm_client.py - Enhanced LLM client:
  - Provider-to-environment-variable mapping
  - Automatic endpoint resolution based on provider prefix
  - Special handling for Nebius (converts to OpenAI-compatible format)
  - Constructor accepts api_key and api_base overrides

  purple-agent/src/server.py - Added CLI options:
  - --api-base - Custom API base URL
  - --api-key - API key override
  - Usage examples in help text

  purple-agent/src/executor.py and agent.py - Pass through API config

  Usage examples:

  # Nebius Cloud
  python purple-agent/src/server.py \
    --model nebius/meta-llama/Meta-Llama-3.1-70B-Instruct \
    --api-base https://api.studio.nebius.ai/v1

  # Or via environment variables
  export NEBIUS_API_KEY=your-key
  export NEBIUS_API_BASE=https://api.studio.nebius.ai/v1
  python purple-agent/src/server.py --model nebius/meta-llama/Meta-Llama-3.1-70B-Instruct
------------------------------------------------------------------------------------------------------------------------
 Done. Here's a summary of the changes:

  1. nodejs_backend/src/agents/base.ts
  - Added ProjectInfo type with fields: id, name, description, language, url, repoOwner, repoName, branch
  - Added projectInfo property to ICodingAgent interface and CodingAgent base class
  - Added setProjectInfo() method to set project details (also updates projectId)

  2. nodejs_backend/src/agents/dummy-agent.ts
  - Updated getSystemPrompt() to include detailed project context:
    - Project name
    - Description (if available)
    - Primary language
    - Repository URL
    - GitHub owner/repo and branch (if available)

  3. nodejs_backend/src/controllers/chat.controller.ts
  - Updated both chat and chatStream functions to call agent.setProjectInfo() with the project data after creating the agent

  Now the LLM will receive a system prompt like:
  You are an expert code assistant...

  ## Current Project Context
  **Project Name:** react
  **Description:** The library for web and native user interfaces
  **Primary Language:** JavaScript
  **Repository URL:** https://github.com/facebook/react
  **GitHub:** facebook/react (branch: main)

  Use this project context to provide relevant and specific answers about the codebase.
