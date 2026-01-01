#!/usr/bin/env python3
"""
Chat Mode Demo for AgentOS
Shows simple examples of using the chat mode
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and show the description"""
    print(f"\n{'=' * 60}")
    print(f"📝 {description}")
    print(f"{'=' * 60}")
    print(f"$ {cmd}\n")
    print("(This would launch an interactive chat session)")
    print("Command details above ↑\n")


def main():
    """Show various chat mode examples"""

    print("\n" + "=" * 60)
    print("🤖 AgentOS Chat Mode - Usage Examples")
    print("=" * 60)

    examples = [
        ("agentos chat", "Start a chat session with default OpenAI provider"),
        ("agentos chat --provider claude", "Chat with Claude (Anthropic)"),
        (
            "agentos chat --provider gemini --temperature 0.3",
            "Chat with Gemini (Google) with lower creativity",
        ),
        (
            "agentos chat --provider openai --model gpt-4",
            "Chat with OpenAI using GPT-4 model",
        ),
        (
            "agentos chat --provider ollama --model llama2",
            "Chat with local Ollama model (no API key needed)",
        ),
        (
            "agentos chat --provider github",
            "Chat using GitHub Models (free tier available)",
        ),
        (
            'agentos chat --system-prompt "You are a Python expert"',
            "Start with a custom system prompt",
        ),
        (
            "agentos chat --provider claude --temperature 0.5 --model claude-3-opus",
            "Advanced: Multiple options combined",
        ),
    ]

    for cmd, description in examples:
        run_command(cmd, description)

    print("\n" + "=" * 60)
    print("💡 Chat Commands (within a session)")
    print("=" * 60)
    print("""
Inside the chat session, you can use:
  • exit, quit   - End the chat session
  • clear        - Clear chat history
  • status       - Show conversation stats
  • help         - Show available commands

Example chat flow:
  You: What is machine learning?
  [Assistant responds...]
  You: Can you explain it for beginners?
  [Assistant continues with context from previous message...]
  You: clear
  [Chat history cleared]
  You: exit
  [Session ends]
""")

    print("\n" + "=" * 60)
    print("🔧 Configuration")
    print("=" * 60)
    print("""
Set API keys in your .env file:
  OPENAI_API_KEY=sk-...
  CLAUDE_API_KEY=sk-ant-...
  GEMINI_API_KEY=...
  GIT_HUB_TOKEN=github_pat_...
  COHERE_API_KEY=...

Or use Ollama locally (no keys needed):
  1. Install: https://ollama.ai
  2. Run: ollama serve
  3. Pull a model: ollama pull phi3
  4. Use: agentos chat --provider ollama
""")

    print("\n" + "=" * 60)
    print("✨ Features")
    print("=" * 60)
    print("""
✓ Multi-provider support (OpenAI, Claude, Gemini, GitHub, Cohere, Ollama)
✓ Rich terminal UI with markdown rendering
✓ Chat history management
✓ Customizable temperature and system prompts
✓ Color-coded output
✓ Supports all LLM providers in AgentOS
✓ Local offline support (Ollama)
✓ API-free options (GitHub, Ollama)
""")

    print("\n" + "=" * 60)
    print("📖 For more info: See MD/CHAT_MODE.md")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
