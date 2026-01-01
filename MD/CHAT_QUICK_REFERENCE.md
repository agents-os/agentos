# 💬 AgentOS Chat Mode - Quick Reference

## One-Liners

```bash
# Default OpenAI chat
agentos chat

# Claude (Anthropic)
agentos chat -p claude

# Gemini (Google) - faster responses
agentos chat -p gemini

# Local offline Ollama
agentos chat -p ollama

# Custom model
agentos chat --model gpt-4

# Less creative answers
agentos chat --temperature 0.3

# More creative answers
agentos chat --temperature 0.9

# Custom instruction
agentos chat --system-prompt "You are a Linux expert"

# All combined
agentos chat -p claude --temperature 0.5 --system-prompt "Be concise"
```

## Providers at a Glance

| Provider | Speed  | Quality    | Free? | Offline? | Command     |
| -------- | ------ | ---------- | ----- | -------- | ----------- |
| OpenAI   | ⚡⚡   | ⭐⭐⭐⭐⭐ | ❌    | ❌       | `-p openai` |
| Claude   | ⚡     | ⭐⭐⭐⭐⭐ | ❌    | ❌       | `-p claude` |
| Gemini   | ⚡⚡⚡ | ⭐⭐⭐⭐   | ❌    | ❌       | `-p gemini` |
| GitHub   | ⚡⚡   | ⭐⭐⭐⭐   | ✅    | ❌       | `-p github` |
| Cohere   | ⚡     | ⭐⭐⭐⭐   | ❌    | ❌       | `-p cohere` |
| Ollama   | ⚡     | ⭐⭐⭐     | ✅    | ✅       | `-p ollama` |

## Chat Commands (Inside Session)

| Command          | What it does                |
| ---------------- | --------------------------- |
| `exit` or `quit` | End the chat                |
| `clear`          | Delete conversation history |
| `help`           | Show command list           |
| `status`         | Show # of messages          |

## Setup (One-Time)

### Get API Keys

1. OpenAI: https://platform.openai.com/api-keys
2. Claude: https://console.anthropic.com/
3. Gemini: https://aistudio.google.com/app/apikey
4. GitHub: https://github.com/settings/tokens
5. Cohere: https://dashboard.cohere.com/api-keys

### Configure `.env`

```bash
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...
GEMINI_API_KEY=...
GIT_HUB_TOKEN=github_pat_...
COHERE_API_KEY=...
```

### Setup Ollama (Free Local)

```bash
# 1. Download from https://ollama.ai
# 2. Install and run
ollama serve

# 3. In another terminal, pull a model
ollama pull phi3
ollama pull mistral
ollama pull neural-chat

# 4. Use it
agentos chat -p ollama
```

## Use Cases

### Quick Answers

```bash
agentos chat -p gemini  # Fast response
```

### Code Help

```bash
agentos chat -p claude --system-prompt "You are a coding expert"
```

### Factual Accuracy

```bash
agentos chat --temperature 0.2  # Lower = more factual
```

### Creative Brainstorming

```bash
agentos chat --temperature 0.9  # Higher = more creative
```

### No Internet

```bash
agentos chat -p ollama
```

### Free Option

```bash
agentos chat -p github
```

## Troubleshooting

| Problem              | Solution                                                            |
| -------------------- | ------------------------------------------------------------------- |
| "Invalid provider"   | Check spelling, use: github, gemini, cohere, openai, claude, ollama |
| "API key not set"    | Add key to `.env` file with correct variable name                   |
| "No response"        | Check internet, verify API service, try different provider          |
| Ollama won't connect | Run `ollama serve` in another terminal first                        |
| Slow responses       | Try faster provider like Gemini or GitHub                           |
| Expensive API calls  | Switch to GitHub (free) or Ollama (free, local)                     |

## Temperature Guide

- **0.0** - Most factual, repetitive
- **0.3** - Factual, analytical answers
- **0.7** - Balanced (default)
- **1.0** - Most creative, unpredictable

## System Prompt Examples

```bash
# Python expert
agentos chat -s "You are a Python expert who writes clean, efficient code"

# Concise answers
agentos chat -s "Keep responses under 100 words"

# Beginner friendly
agentos chat -s "Explain concepts for someone new to programming"

# Professional tone
agentos chat -s "Use a professional, business tone. No casual language"

# Technical focus
agentos chat -s "Focus on technical details and implementation"
```

## Pro Tips

💡 **Tip 1:** Start with Gemini or GitHub for speed
💡 **Tip 2:** Use Claude for complex reasoning
💡 **Tip 3:** Use `--temperature 0.3` for homework help
💡 **Tip 4:** Use `--temperature 0.9` for creative writing
💡 **Tip 5:** Use `clear` command to reset context if answers drift
💡 **Tip 6:** Use `ollama` for privacy - no data sent to cloud

## Model Defaults

```bash
agentos chat                    # → gpt-4o-mini (OpenAI)
agentos chat -p claude          # → claude-3-5-haiku
agentos chat -p gemini          # → models/gemini-2.0-flash-lite
agentos chat -p github          # → openai/gpt-4o-mini
agentos chat -p cohere          # → command-xlarge-nightly
agentos chat -p ollama          # → phi3
```

Override with `--model`:

```bash
agentos chat --model gpt-4
agentos chat -p claude --model claude-3-opus-20240229
agentos chat -p ollama --model llama2
```

## Session Example

```
$ agentos chat -p claude

🤖 AgentOS Chat Mode
Provider: claude
Model: claude-3-5-haiku-20241022

You: What is machine learning?
Assistant: Machine learning is a subset of artificial intelligence...

You: Can you give me an example?
Assistant: Sure! A practical example would be...

You: clear
✓ Chat history cleared

You: exit
👋 Goodbye!
```

---

**Full Guide:** See [CHAT_MODE.md](./CHAT_MODE.md)
**Implementation Details:** See [CHAT_MODE_IMPLEMENTATION.md](./CHAT_MODE_IMPLEMENTATION.md)
