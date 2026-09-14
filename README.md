# JARVIS

A local-first, action-capable personal AI assistant.

## Architecture

```text
User -> JARVIS controller -> Ollama/Qwen -> tool decision -> Python tool -> result -> Qwen -> response
```

JARVIS is intentionally built as an agent, not a text-only chatbot. The LLM plans and selects tools; Python performs deterministic actions; the safety layer validates actions and handles permission boundaries.

## Current stack

- Python 3.14+
- Ollama
- Qwen3:8B by default
- Local-first execution
- Standard library first; optional dependencies are isolated

## Current capabilities

- Chat with the local Ollama model
- Tool routing with structured `TOOL_CALL:<name>` decisions
- Analyze the Downloads folder
- Organize Downloads by deterministic file-extension rules
- Human approval before filesystem mutation
- Preflight validation
- Post-action verification
- Best-effort rollback if an execution step fails
- Safe terminal tool in disabled-by-default mode
- Stubs/interfaces for applications, browser, memory, vision and voice

## Windows setup

1. Install Ollama and make sure the Ollama service is running.
2. Pull the model:

```powershell
ollama pull qwen3:8b
```

3. Clone this repository and enter it.
4. Create a virtual environment:

```powershell
python -m venv .venv
```

5. Run JARVIS without needing PowerShell execution-policy changes:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Configuration

Environment variables are optional. Defaults are designed for the user's current local setup:

- `JARVIS_OLLAMA_URL=http://localhost:11434/api/chat`
- `JARVIS_MODEL=qwen3:8b`
- `JARVIS_DOWNLOADS_DIR=~/Downloads`
- `JARVIS_TERMINAL_ENABLED=false`

## Safety model

Filesystem mutation follows:

```text
Analyze -> Plan -> Validate -> Human approval -> Execute -> Verify -> Roll back on failure
```

JARVIS never claims an action was completed merely because the model requested it. Python tools return the actual execution result.

## Roadmap

1. Core local agent loop
2. More filesystem operations
3. Terminal and application control with explicit permission scopes
4. Persistent memory
5. MCP tool integration
6. Browser automation
7. Local speech-to-text and text-to-speech
8. Vision and computer interaction
9. Optional cloud-model fallback

## Security

Never put API keys, passwords, tokens, browser cookies, personal documents, or `.env` files into this repository. JARVIS should run with the minimum permissions necessary.
