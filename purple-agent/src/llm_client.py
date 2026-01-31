"""LiteLLM integration for provider-agnostic LLM access."""

import os
from typing import Optional

import litellm


class LLMClient:
    """Wrapper around LiteLLM for provider-agnostic LLM access.

    Supports custom endpoints via environment variables or constructor arguments.

    Environment Variables:
        NEBIUS_API_KEY: API key for Nebius Cloud
        NEBIUS_API_BASE: Base URL for Nebius (e.g., https://api.studio.nebius.ai/v1)
        OPENAI_API_BASE: Base URL for OpenAI-compatible endpoints
        AZURE_API_BASE: Base URL for Azure OpenAI
        OLLAMA_API_BASE: Base URL for Ollama (default: http://localhost:11434)

    Model Format Examples:
        - anthropic/claude-sonnet-4-20250514
        - openai/gpt-4o
        - nebius/meta-llama/Meta-Llama-3.1-70B-Instruct
        - azure/my-deployment
        - ollama/llama3
        - openai/mistral-7b (with custom OPENAI_API_BASE)
    """

    # Provider to environment variable mapping
    PROVIDER_ENV_MAP = {
        "nebius": {"api_key": "NEBIUS_API_KEY", "api_base": "NEBIUS_API_BASE"},
        "openai": {"api_key": "OPENAI_API_KEY", "api_base": "OPENAI_API_BASE"},
        "azure": {"api_key": "AZURE_API_KEY", "api_base": "AZURE_API_BASE"},
        "ollama": {"api_base": "OLLAMA_API_BASE"},
        "together_ai": {"api_key": "TOGETHER_API_KEY"},
        "groq": {"api_key": "GROQ_API_KEY"},
    }

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        """Initialize the LLM client.

        Args:
            model: Model identifier in LiteLLM format (provider/model-name)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            api_key: Override API key (otherwise uses environment variable)
            api_base: Override API base URL (otherwise uses environment variable)
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Extract provider from model string
        self.provider = self._extract_provider(model)

        # Resolve API key and base URL
        self.api_key = api_key or self._get_api_key()
        self.api_base = api_base or self._get_api_base()

        # Configure LiteLLM
        litellm.drop_params = True  # Drop unsupported params gracefully

        # Set verbose mode from environment
        if os.getenv("LITELLM_VERBOSE", "").lower() == "true":
            litellm.set_verbose = True

    def _extract_provider(self, model: str) -> str:
        """Extract provider name from model string."""
        if "/" in model:
            return model.split("/")[0].lower()
        return "openai"  # Default provider

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment based on provider."""
        env_config = self.PROVIDER_ENV_MAP.get(self.provider, {})
        key_var = env_config.get("api_key")
        if key_var:
            return os.getenv(key_var)
        return None

    def _get_api_base(self) -> Optional[str]:
        """Get API base URL from environment based on provider."""
        env_config = self.PROVIDER_ENV_MAP.get(self.provider, {})
        base_var = env_config.get("api_base")
        if base_var:
            return os.getenv(base_var)
        return None

    def _get_completion_kwargs(self) -> dict:
        """Build kwargs for LiteLLM completion call."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        # Add custom API base if configured
        if self.api_base:
            kwargs["api_base"] = self.api_base

        # Add API key if configured
        if self.api_key:
            kwargs["api_key"] = self.api_key

        # Provider-specific configurations
        if self.provider == "nebius":
            # Nebius uses OpenAI-compatible API
            # Model format: nebius/model-name -> openai/model-name with custom base
            kwargs["model"] = self.model.replace("nebius/", "openai/", 1)
            kwargs["api_base"] = self.api_base or "https://api.studio.nebius.ai/v1"
            kwargs["api_key"] = self.api_key or os.getenv("NEBIUS_API_KEY")

        elif self.provider == "azure":
            # Azure requires additional configuration
            api_version = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
            kwargs["api_version"] = api_version

        return kwargs

    async def complete(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a completion from the LLM."""
        formatted_messages = []

        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        # Add conversation messages
        formatted_messages.extend(messages)

        kwargs = self._get_completion_kwargs()
        kwargs["messages"] = formatted_messages

        response = await litellm.acompletion(**kwargs)

        return response.choices[0].message.content

    async def complete_with_json(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a completion with JSON response format hint."""
        # Add JSON instruction to system prompt
        json_system = system_prompt or ""
        json_system += "\n\nIMPORTANT: Respond with valid JSON only. No additional text."

        formatted_messages = [
            {
                "role": "system",
                "content": json_system,
            }
        ]
        formatted_messages.extend(messages)

        kwargs = self._get_completion_kwargs()
        kwargs["messages"] = formatted_messages

        # Try to use response_format if supported
        try:
            kwargs["response_format"] = {"type": "json_object"}
            response = await litellm.acompletion(**kwargs)
        except Exception:
            # Fallback without response_format
            kwargs.pop("response_format", None)
            response = await litellm.acompletion(**kwargs)

        return response.choices[0].message.content

    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            "model": self.model,
            "provider": self.provider,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_base": self.api_base,
            "api_key_set": bool(self.api_key),
        }
