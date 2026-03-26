"""
Abstract model provider interface for generating paper summaries.
Supports both local models (Ollama) and paid APIs (OpenAI, Claude, etc.)
"""

from abc import ABC, abstractmethod


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    def generate_summary(self, prompt: str) -> str:
        """
        Generate a summary using the model.

        Args:
            prompt: The formatted prompt for the model

        Returns:
            The generated summary text

        Raises:
            Exception: If the model fails to generate a response
        """
        pass


class OllamaProvider(ModelProvider):
    """Local Ollama model provider."""

    def __init__(self, model_name: str = "llama3.2"):
        """
        Initialize Ollama provider.

        Args:
            model_name: Name of the Ollama model to use (default: llama3.2)
        """
        self.model_name = model_name
        import ollama

        self.ollama = ollama

    def generate_summary(self, prompt: str) -> str:
        """Generate summary using local Ollama model."""
        response = self.ollama.chat(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI researcher and technical writer.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]


class OpenAIProvider(ModelProvider):
    """OpenAI API model provider."""

    def __init__(self, api_key: str = None, model_name: str = "gpt-4"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model_name: Model to use (default: gpt-4)
        """
        self.model_name = model_name
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def generate_summary(self, prompt: str) -> str:
        """Generate summary using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AI researcher and technical writer.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


class AnthropicProvider(ModelProvider):
    """Anthropic Claude API model provider."""

    def __init__(self, api_key: str = None, model_name: str = "claude-3-opus-20240229"):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            model_name: Model to use (default: claude-3-opus-20240229)
        """
        self.model_name = model_name
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)

    def generate_summary(self, prompt: str) -> str:
        """Generate summary using Anthropic Claude API."""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system="You are an expert AI researcher and technical writer.",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return response.content[0].text


def get_model_provider(provider_type: str = "ollama", **kwargs) -> ModelProvider:
    """
    Factory function to get a model provider instance.

    Args:
        provider_type: Type of provider ('ollama', 'openai', 'anthropic')
        **kwargs: Additional arguments to pass to the provider

    Returns:
        ModelProvider instance

    Raises:
        ValueError: If provider_type is not supported
    """
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    if provider_type.lower() not in providers:
        raise ValueError(
            f"Unknown provider: {provider_type}. "
            f"Supported providers: {list(providers.keys())}"
        )

    return providers[provider_type.lower()](**kwargs)
