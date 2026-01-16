"""AgentOS LLM Module - Universal LLM Support with 6+ Providers"""

from agentos.llm.answerer import (
    add_history_entry,
    build_messages_from_history,
)
from agentos.llm.answerer import (
    get_claude_response as claude_chat,
)
from agentos.llm.answerer import (
    get_cohere_response as cohere_chat,
)
from agentos.llm.answerer import (
    get_gemini_response as gemini_chat,
)
from agentos.llm.answerer import (
    get_github_response as github_chat,
)
from agentos.llm.answerer import (
    get_ollama_response as ollama_chat,
)
from agentos.llm.answerer import (
    get_openai_response as openai_chat,
)
from agentos.llm.llm_providers import (
    get_claude_response,
    get_cohere_response,
    get_gemini_response,
    get_github_response,
    get_ollama_response,
    get_openai_response,
)

# Provider mapping for easy switching
PROVIDERS = {
    "github": get_github_response,
    "gemini": get_gemini_response,
    "cohere": get_cohere_response,
    "openai": get_openai_response,
    "claude": get_claude_response,
    "ollama": get_ollama_response,
}

# Default models for each provider
DEFAULT_MODELS = {
    "github": "openai/gpt-4o-mini",
    "gemini": "models/gemini-2.0-flash-lite",
    "cohere": "command-xlarge-nightly",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-haiku-20241022",
    "ollama": "phi3",
}


def get_provider(name: str):
    """Get LLM provider function by name."""
    return PROVIDERS.get(name.lower())


def get_default_model(provider: str) -> str:
    """Get default model for a provider."""
    return DEFAULT_MODELS.get(provider.lower(), "gpt-4o-mini")


__all__ = [
    # Raw providers
    "get_github_response",
    "get_gemini_response",
    "get_cohere_response",
    "get_openai_response",
    "get_claude_response",
    "get_ollama_response",
    # Chat providers (with history)
    "github_chat",
    "gemini_chat",
    "cohere_chat",
    "openai_chat",
    "claude_chat",
    "ollama_chat",
    # History helpers
    "add_history_entry",
    "build_messages_from_history",
    # Provider utilities
    "PROVIDERS",
    "DEFAULT_MODELS",
    "get_provider",
    "get_default_model",
]
