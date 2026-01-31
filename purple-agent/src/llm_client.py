"""LiteLLM integration for provider-agnostic LLM access."""

from typing import Optional

import litellm


class LLMClient:
    """Wrapper around LiteLLM for provider-agnostic LLM access."""

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Configure LiteLLM
        litellm.drop_params = True  # Drop unsupported params gracefully

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

        response = await litellm.acompletion(
            model=self.model,
            messages=formatted_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

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

        # Try to use response_format if supported
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=formatted_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
        except Exception:
            # Fallback without response_format
            response = await litellm.acompletion(
                model=self.model,
                messages=formatted_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

        return response.choices[0].message.content

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
