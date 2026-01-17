"""LLM Provider Functions for AgentOS - With Retry Logic and Exponential Backoff"""

import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

import ollama
import requests
from dotenv import load_dotenv
from ollama import Options

# Load .env from multiple locations (in order of priority)
# 1. Current working directory
# 2. ~/.agentos/.env (user config)
# 3. ~/.agentos/source/agentos/.env (installed location)
load_dotenv()  # Current directory
load_dotenv(Path.home() / ".agentos" / ".env")  # User config
load_dotenv(Path.home() / ".agentos" / "source" / "agentos" / ".env")  # Install dir

logger = logging.getLogger(__name__)

# API Keys
GIT_HUB_TOKEN = os.getenv("GIT_HUB_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip()

# Retry configuration
MAX_RETRIES = 3
INITIAL_DELAY = 1.0
MAX_DELAY = 30.0
EXPONENTIAL_BASE = 2.0


def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = INITIAL_DELAY * (EXPONENTIAL_BASE**attempt)
    delay = min(delay, MAX_DELAY)
    # Add jitter (0-50% of delay)
    jitter = delay * random.uniform(0, 0.5)
    return delay + jitter


def _should_retry(exception: Exception, attempt: int) -> bool:
    """Determine if we should retry based on the exception type."""
    if attempt >= MAX_RETRIES:
        return False

    # Retry on connection errors, timeouts, and rate limits
    if isinstance(
        exception,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ),
    ):
        return True

    # Retry on HTTP 429 (rate limit) or 5xx (server errors)
    if isinstance(exception, requests.exceptions.HTTPError):
        status_code = exception.response.status_code if exception.response else 0
        return status_code == 429 or status_code >= 500

    return False


def _retry_api_call(func, *args, **kwargs):
    """Execute an API call with retry logic."""
    last_exception = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if _should_retry(e, attempt):
                delay = _calculate_backoff(attempt)
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
            else:
                break

    raise last_exception


def get_github_response(
    query: str, system_prompt: str, model: str, temperature: float, messages: list
):
    """Get response from GitHub Models API with retry logic"""
    if not GIT_HUB_TOKEN:
        return "GitHub API key not set."

    def _make_request():
        url = "https://models.github.ai/inference/chat/completions"
        headers = {
            "Authorization": f"Bearer {GIT_HUB_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        }
        payload = {"model": model, "messages": messages, "temperature": temperature}

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    try:
        return _retry_api_call(_make_request)
    except Exception as e:
        logger.error(f"GitHub API error after retries: {e}")
        return f"GitHub API error: {e}"


def get_gemini_response(
    query: str, system_prompt: str, model: str, temperature: float, chat_history: dict
):
    """Get response from Gemini API with retry logic"""
    if not GEMINI_API_KEY:
        return "Gemini API key not set."

    def _make_request():
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
        contents = []
        contents.append({"role": "user", "parts": [{"text": system_prompt}]})

        sorted_items = sorted(
            chat_history.items(),
            key=lambda x: (
                x[0].rstrip("0123456789"),
                int("".join(filter(str.isdigit, x[0])) or 0),
            ),
        )
        for key, value in sorted_items:
            role = "user" if key.startswith("user") else "model"
            contents.append({"role": role, "parts": [{"text": value}]})

        contents.append({"role": "user", "parts": [{"text": query}]})
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    try:
        return _retry_api_call(_make_request)
    except Exception as e:
        logger.error(f"Gemini API error after retries: {e}")
        return f"Gemini API error: {e}"


def get_cohere_response(
    query: str, system_prompt: str, model: str, temperature: float, chat_history: dict
):
    """Get response from Cohere API with retry logic"""
    if not COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY is not set")

    def _make_request():
        url = "https://api.cohere.ai/v1/chat"
        headers = {
            "Authorization": f"Bearer {COHERE_API_KEY}",
            "Content-Type": "application/json",
        }

        sorted_items = sorted(
            chat_history.items(),
            key=lambda x: (
                x[0].rstrip("0123456789"),
                int("".join(filter(str.isdigit, x[0])) or 0),
            ),
        )
        history_lines = []
        for key, value in sorted_items:
            role_label = "User" if key.startswith("user") else "Assistant"
            history_lines.append(f"{role_label}: {value}")
        history_text = "\n".join(history_lines)

        if history_text:
            message = f"{system_prompt}\n{history_text}\nUser: {query}"
        else:
            message = f"{system_prompt}\n{query}"

        payload = {"model": model, "message": message, "temperature": temperature}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["text"]

    try:
        return _retry_api_call(_make_request)
    except Exception as e:
        logger.error(f"Cohere API error after retries: {e}")
        raise


def get_openai_response(
    query: str, system_prompt: str, model: str, temperature: float, messages: list
):
    """Get response from OpenAI API with retry logic"""
    if not OPENAI_API_KEY:
        return "OpenAI API key not set."

    def _make_request():
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": messages, "temperature": temperature}

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    try:
        return _retry_api_call(_make_request)
    except Exception as e:
        logger.error(f"OpenAI API error after retries: {e}")
        return f"OpenAI API error: {e}"


def get_claude_response(
    query: str, system_prompt: str, model: str, temperature: float, chat_history: dict
):
    """Get response from Claude API with retry logic"""
    if not CLAUDE_API_KEY:
        return "Claude API key not set."

    def _make_request():
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        content_blocks = [{"type": "text", "text": system_prompt}]
        sorted_items = sorted(
            chat_history.items(),
            key=lambda x: (
                x[0].rstrip("0123456789"),
                int("".join(filter(str.isdigit, x[0])) or 0),
            ),
        )
        for key, value in sorted_items:
            content_blocks.append({"type": "text", "text": value})
        content_blocks.append({"type": "text", "text": query})

        messages = [{"role": "user", "content": content_blocks}]
        payload = {
            "model": model,
            "max_tokens": 1000,
            "messages": messages,
            "temperature": temperature,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    try:
        return _retry_api_call(_make_request)
    except requests.exceptions.HTTPError as e:
        if hasattr(e, "response") and e.response is not None:
            if e.response.status_code == 401:
                return "Claude API authentication error: Invalid key or headers."
            return f"Claude API error: {e.response.text}"
        return f"Claude API error: {e}"
    except Exception as e:
        logger.error(f"Claude API error after retries: {e}")
        return f"Claude API error: {e}"


def get_ollama_response(
    query: str, system_prompt: str, model: str, temperature: float, messages: list
):
    """Get response from Ollama with retry logic"""

    def _make_request():
        response = ollama.chat(
            model=model, options=Options(temperature=temperature), messages=messages
        )
        return response["message"]["content"]

    try:
        return _retry_api_call(_make_request)
    except Exception as e:
        logger.error(f"Ollama error after retries: {e}")
        return f"Ollama error: {e}"
