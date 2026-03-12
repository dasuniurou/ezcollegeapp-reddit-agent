"""
LLM client abstraction supporting OpenAI and Google Gemini.
Switch provider via LLM_PROVIDER env var or config/settings.yaml.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified interface for OpenAI and Gemini chat completions."""

    SUPPORTED_PROVIDERS = ("openai", "gemini")

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Args:
            provider: "openai" or "gemini". Falls back to LLM_PROVIDER env var,
                      then to "openai" as default.
            model:    Model name override. If None, uses the provider default.
        """
        self.provider = (
            provider
            or os.getenv("LLM_PROVIDER", "openai")
        ).lower()

        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{self.provider}'. "
                f"Choose from: {self.SUPPORTED_PROVIDERS}"
            )

        self.model = model or self._default_model()
        self._client = self._build_client()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, system: str, user: str) -> str:
        """
        Send a chat message and return the assistant's reply as a string.

        Args:
            system: System prompt.
            user:   User message.

        Returns:
            The model's text response.
        """
        logger.debug("[%s/%s] Sending chat request", self.provider, self.model)
        if self.provider == "openai":
            return self._openai_chat(system, user)
        return self._gemini_chat(system, user)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _default_model(self) -> str:
        defaults = {
            "openai": "gpt-4o",
            "gemini": "gemini-1.5-pro",
        }
        return defaults[self.provider]

    def _build_client(self):
        if self.provider == "openai":
            from openai import OpenAI  # type: ignore

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY is not set.")
            return OpenAI(api_key=api_key)

        if self.provider == "gemini":
            import google.generativeai as genai  # type: ignore

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise EnvironmentError("GEMINI_API_KEY is not set.")
            genai.configure(api_key=api_key)
            return genai.GenerativeModel(self.model)

    def _openai_chat(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content.strip()

    def _gemini_chat(self, system: str, user: str) -> str:
        # Gemini combines system + user into a single prompt
        combined = f"{system}\n\n---\n\n{user}"
        response = self._client.generate_content(combined)
        return response.text.strip()
