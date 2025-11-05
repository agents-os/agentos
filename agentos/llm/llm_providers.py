"""LLM Provider Functions for AgentOS"""

import os

import ollama
import requests
from dotenv import load_dotenv
from ollama import Options

load_dotenv()

# API Keys
GIT_HUB_TOKEN = os.getenv("GIT_HUB_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "").strip()


def get_github_response(query: str, system_prompt: str, model: str, temperature: float, messages: list):
    """Get response from GitHub Models API"""
    if not GIT_HUB_TOKEN:
        return "GitHub API key not set."

    try:
        url = "https://models.github.ai/inference/chat/completions"
        headers = {
            "Authorization": f"Bearer {GIT_HUB_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        }
        payload = {"model": model, "messages": messages, "temperature": temperature}

        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"GitHub API error: {e}"


def get_gemini_response(query: str, system_prompt: str, model: str, temperature: float, chat_history: dict):
    """Get response from Gemini API"""
    if not GEMINI_API_KEY:
        return "Gemini API key not set."

    try:
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

        resp = requests.post(url, json=payload)
        resp.raise_for_status()

        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini API error: {e}"


def get_cohere_response(query: str, system_prompt: str, model: str, temperature: float, chat_history: dict):
    """Get response from Cohere API"""
    if not COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY is not set")

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
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print("Cohere API error:", resp.text)
    resp.raise_for_status()

    return resp.json()["text"]


def get_openai_response(query: str, system_prompt: str, model: str, temperature: float, messages: list):
    """Get response from OpenAI API"""
    if not OPENAI_API_KEY:
        return "OpenAI API key not set."

    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": messages, "temperature": temperature}

        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"OpenAI API error: {e}"


def get_claude_response(query: str, system_prompt: str, model: str, temperature: float, chat_history: dict):
    """Get response from Claude API"""
    if not CLAUDE_API_KEY:
        return "Claude API key not set."

    try:
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

        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()

        return resp.json()["content"][0]["text"].strip()
    except requests.exceptions.HTTPError:
        if resp.status_code == 401:
            return "Claude API authentication error: Invalid key or headers."
        return f"Claude API error: {resp.text}"
    except Exception as e:
        return f"Claude API error: {e}"


def get_ollama_response(query: str, system_prompt: str, model: str, temperature: float, messages: list):
    """Get response from Ollama"""
    try:
        response = ollama.chat(
            model=model, options=Options(temperature=temperature), messages=messages
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Ollama error: {e}"
