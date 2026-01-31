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
