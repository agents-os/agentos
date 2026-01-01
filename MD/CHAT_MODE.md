# AgentOS Chat Mode

A simple, interactive chat interface similar to Gemini, Claude Code, and Codex CLI.

## Quick Start

### Basic Usage

Start a chat session with the default OpenAI provider:

```bash
agentos chat
```

### Specify a Provider

Choose from available LLM providers:

```bash
# Claude (Anthropic)
agentos chat --provider claude

# Gemini (Google)
agentos chat --provider gemini

# Cohere
agentos chat --provider cohere

# GitHub Models
agentos chat --provider github

# Ollama (Local models)
agentos chat --provider ollama
```

### Advanced Options

```bash
# Specify a custom model
agentos chat --provider openai --model gpt-4

# Adjust temperature (creativity)
agentos chat --provider claude --temperature 0.3

# Use a custom system prompt
agentos chat --provider gemini --system-prompt "You are a helpful coding assistant"

# Combine options
agentos chat --provider openai --model gpt-4 --temperature 0.5 --system-prompt "You are a Python expert"
```

## Available Commands

Within a chat session, you can use these commands:

- **exit** or **quit** - End the chat session
- **clear** - Clear chat history
- **status** - Show number of messages in history
- **help** - Show available commands

## Examples

### Chat Session with Claude

```
$ agentos chat --provider claude

🤖 AgentOS Chat Mode
Provider: claude
Model: claude-3-5-haiku-20241022
Temperature: 0.7

You: What's the difference between Python lists and tuples?
[waiting for response...]
Assistant: Lists and tuples are both sequence types in Python, but they differ in several ways:
...

You: Can you give me an example?
```

### Using a Custom System Prompt

```bash
agentos chat --provider openai --system-prompt "You are a JavaScript expert who provides concise answers"
```

## Configuration

### Environment Variables

Make sure you have the appropriate API keys set in your `.env` file:

```bash
# For OpenAI
OPENAI_API_KEY=sk-...

# For Claude
CLAUDE_API_KEY=sk-ant-...

# For Gemini
GEMINI_API_KEY=...

# For GitHub Models
GIT_HUB_TOKEN=github_pat_...

# For Cohere
COHERE_API_KEY=...

# For Ollama (no key needed, but service must be running)
# Just have Ollama running locally on port 11434
```

## Supported LLM Providers

| Provider | Model                        | Default | Notes                          |
| -------- | ---------------------------- | ------- | ------------------------------ |
| OpenAI   | gpt-4o-mini                  | ✓       | Fast and capable               |
| Claude   | claude-3-5-haiku-20241022    | -       | Great for complex tasks        |
| Gemini   | models/gemini-2.0-flash-lite | -       | Google's latest model          |
| GitHub   | openai/gpt-4o-mini           | -       | Free tier available            |
| Cohere   | command-xlarge-nightly       | -       | Specialized capabilities       |
| Ollama   | phi3                         | -       | Run locally, no API key needed |

## Features

✨ **Rich Terminal Output**

- Beautiful formatting with syntax highlighting
- Markdown rendering for responses
- Color-coded messages

📝 **Chat History**

- Maintains conversation context
- Clear history when needed
- View conversation status

🔄 **Multi-Provider Support**

- Seamlessly switch between providers
- Compatible with all AgentOS-supported LLMs
- Provider defaults if model not specified

⚙️ **Customization**

- Adjustable temperature for response creativity
- Custom system prompts
- Verbose logging support

## Troubleshooting

### "Provider not found" error

Make sure you're using one of the supported providers: `github`, `gemini`, `cohere`, `openai`, `claude`, `ollama`

### API Key errors

Ensure your API keys are set in the `.env` file with the correct variable names (see Configuration section)

### No response or timeout

- Check your internet connection
- Verify the API service is running (especially for Ollama)
- Try increasing the timeout or check provider status

### Ollama connection issues

- Ensure Ollama is running: `ollama serve`
- Verify it's accessible at `localhost:11434`
- Try pulling a model: `ollama pull phi3`

## Tips

1. **Longer conversations**: Use a provider with larger context windows like Claude for longer discussions
2. **Quick responses**: Use providers like Gemini or GitHub for faster responses
3. **Local-only**: Use Ollama if you need a fully offline solution
4. **Code assistance**: Use Claude or GPT-4 for better code generation
5. **Temperature tuning**: Lower temperatures (0.1-0.3) for factual answers, higher (0.7-1.0) for creative tasks

## See Also

- [AgentOS Documentation](https://docs.agentos.dev)
- [Running Agents](../README.md)
- [LLM Configuration](../MD/PRODUCTION_READY.md)
