"""Thin wrapper around the local Ollama HTTP API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import ollama

from src.utils.logging import get_logger

logger = get_logger(__name__)

ChatMessage = dict[str, str]


@dataclass
class OllamaClient:
    """Stateful client bound to one Ollama model and host."""

    model: str = "gemma2:2b"
    host: str = "http://localhost:11434"
    options: dict[str, Any] = field(default_factory=dict)
    client: ollama.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.client = ollama.Client(host=self.host)

    @staticmethod
    def prompt_messages(prompt: str, system: str | None = None) -> list[ChatMessage]:
        """Build the single-turn chat message list."""
        messages: list[ChatMessage] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def prompt_message_content(response: Any) -> str:
        """Extract assistant content from old and new model response from ollama."""
        message = response.get("message", {}) if isinstance(response, dict) else getattr(response, "message", None)
        if message is None:
            return ""
        if isinstance(message, dict):
            return str(message.get("content", ""))
        return str(getattr(message, "content", ""))

    def generate(self, prompt: str, system: str | None = None) -> str:
        """Run a single-turn completion and return the assistant content."""
        logger.debug("Calling Ollama model=%s host=%s", self.model, self.host)
        response = self.client.chat(
            model=self.model, messages=self.prompt_messages(prompt, system),
            options=self.options or None)
        return self.prompt_message_content(response)

    def ensure_model(self) -> None:
        """Pull the model when it is not available locally."""
        try:
            self.client.show(self.model)
            logger.info("Ollama model %s is ready.", self.model)
            return
        except Exception as exc:
            logger.info("Ollama model %s unavailable (%s); pulling ...", self.model, exc)

        self.client.pull(self.model)
