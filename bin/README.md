# AgentOS Command Wrappers

This directory contains wrapper scripts that allow you to run `agentos` from anywhere.

## Usage

### Linux/macOS

Add to your PATH:
```bash
export PATH="$PATH:/path/to/AgentOS/bin"
```

Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export PATH="$PATH:'$(pwd)'/bin"' >> ~/.bashrc
source ~/.bashrc
```

Then run:
```bash
agentos --help
```

### Windows

Add to PATH:
1. Open System Properties → Environment Variables
2. Edit User PATH variable
3. Add: `C:\path\to\AgentOS\bin`
4. Restart terminal

Then run:
```cmd
agentos --help
```

## What These Scripts Do

- Automatically activate the virtual environment
- Run `agentos.py` with all arguments
- Work from any directory
