"""Main LLM Interface for AgentOS"""

from agentos.core.utils import SYSTEM_PROMPT, chat_history
from agentos.llm.llm_providers import (
    get_github_response as _get_github,
    get_gemini_response as _get_gemini,
    get_cohere_response as _get_cohere,
    get_openai_response as _get_openai,
    get_claude_response as _get_claude,
    get_ollama_response as _get_ollama,
)

sysprompt = SYSTEM_PROMPT


def build_messages_from_history(history: dict, new_query: str, system_prompt: str = None):
    """Convert chat history into API-compatible messages"""
    prompt = system_prompt if system_prompt is not None else sysprompt
    messages = [{"role": "system", "content": prompt}]
    sorted_items = sorted(
        history.items(),
        key=lambda x: (
            x[0].rstrip("0123456789"),
            int("".join(filter(str.isdigit, x[0])) or 0),
        ),
    )
    for key, value in sorted_items:
        role = "user" if key.startswith("user") else "assistant"
        messages.append({"role": role, "content": value})
    messages.append({"role": "user", "content": new_query})
    return messages


def add_history_entry(role: str, content: str):
    """Add a new entry to the chat history"""
    count = sum(1 for k in chat_history if k.startswith(role))
    chat_history[f"{role}{count + 1}"] = content


def get_github_response(query: str, system_prompt: str = None, model="openai/gpt-4o-mini", temperature: float = 0.7):
    add_history_entry("user", query)
    messages = build_messages_from_history(chat_history, query, system_prompt=system_prompt)
    ans = _get_github(query, system_prompt or sysprompt, model, temperature, messages)
    add_history_entry("assistant", ans)
    return ans


def get_gemini_response(query: str, system_prompt: str = None, model="models/gemini-2.0-flash-lite", temperature: float = 0.7):
    add_history_entry("user", query)
    ans = _get_gemini(query, system_prompt or sysprompt, model, temperature, chat_history)
    add_history_entry("assistant", ans)
    return ans


def get_cohere_response(query: str, system_prompt: str = None, model="command-xlarge-nightly", temperature: float = 0.7):
    add_history_entry("user", query)
    ans = _get_cohere(query, system_prompt or sysprompt, model, temperature, chat_history)
    add_history_entry("assistant", ans)
    return ans


def get_openai_response(query: str, system_prompt: str = None, model="gpt-4o-mini", temperature: float = 0.7):
    add_history_entry("user", query)
    messages = build_messages_from_history(chat_history, query, system_prompt=system_prompt)
    ans = _get_openai(query, system_prompt or sysprompt, model, temperature, messages)
    add_history_entry("assistant", ans)
    return ans


def get_claude_response(query: str, system_prompt: str = None, model="claude-3-5-haiku-20241022", temperature: float = 0.7):
    add_history_entry("user", query)
    ans = _get_claude(query, system_prompt or sysprompt, model, temperature, chat_history)
    add_history_entry("assistant", ans)
    return ans


def get_ollama_response(query: str, system_prompt: str = None, model: str = "phi3", temperature: float = 0.7):
    add_history_entry("user", query)
    messages = build_messages_from_history(chat_history, query, system_prompt=system_prompt)
    ans = _get_ollama(query, system_prompt or sysprompt, model, temperature, messages)
    add_history_entry("assistant", ans)
    return ans
