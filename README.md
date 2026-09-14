# JARVIS

A local-first, action-capable personal AI assistant.

## Architecture

```text
User -> JARVIS controller -> Model Router -> Brain -> tool decision -> Python tool -> result -> Brain -> response
                                  |              |
                                  |              +-- Ollama / Qwen3:8B (local)
                                  +----------------- NVIDIA hosted models (optional free endpoint)
```

JARVIS is intentionally built as an agent, not a text-only chatbot. The model plans and selects tools; Python performs deterministic actions; the safety layer validates actions and handles permission boundaries.

## Current stack

- Python 3.14+
- Ollama + Qwen3:8B for the permanent local brain
- Optional NVIDIA hosted inference through the OpenAI-compatible API
- Local-first model routing with cloud fallback
- Standard library first; optional dependencies are isolated

## Model routing

`JARVIS_BRAIN_MODE` supports:

- `local` — Ollama only
- `nvidia` — NVIDIA hosted model only
- `auto` — local-first; selected complex/long requests can use NVIDIA when `NVIDIA_API_KEY` is configured, with local fallback if the hosted endpoint fails

The NVIDIA model is configurable. The current default is `nvidia/nemotron-3.5-lightning-30b-a3b`. NVIDIA's model catalog currently lists multiple free inference endpoints, including Nemotron 3.5 Lightning, Nemotron 3 Super 120B, Nemotron 3 Ultra 550B, DeepSeek V4 Flash, and Kimi K3. Availability and usage limits can change, so JARVIS keeps Ollama as the permanent local fallback.

## Current capabilities

- Chat with the local Ollama model
- Optional NVIDIA hosted brain
- Model routing with local fallback
- Tool routing with structured `TOOL_CALL:<name>` decisions
- Analyze the Downloads folder
- Organize Downloads by deterministic file-extension rules
- Human approval before filesystem mutation
- Preflight validation
- Post-action verification
- Best-effort rollback if an execution step fails
- Safe terminal tool in disabled-by-default mode
- Interfaces for applications, browser, memory, vision and voice

## Windows setup

1. Install Ollama and make sure the Ollama service is running.
2. Pull the local model:

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

## NVIDIA hosted models

NVIDIA provides free serverless inference endpoints for development. Generate an API key from NVIDIA's developer site, then set it only in your local environment.

```powershell
$env:NVIDIA_API_KEY="YOUR_KEY_HERE"
$env:JARVIS_BRAIN_MODE="auto"
$env:JARVIS_NVIDIA_MODEL="nvidia/nemotron-3.5-lightning-30b-a3b"
.\.venv\Scripts\python.exe main.py
```

Do not paste the key into Python source code or commit it to GitHub. A `.env.example` template is included for configuration reference; a real `.env` should remain local and ignored.

## Safety model

Filesystem mutation follows:

```text
Analyze -> Plan -> Validate -> Human approval -> Execute -> Verify -> Roll back on failure
```

JARVIS never claims an action was completed merely because the model requested it. Python tools return the actual execution result.

## Roadmap

1. Core local + multi-model agent loop
2. More filesystem operations
3. Persistent memory
4. Terminal and application control with explicit permission scopes
5. MCP tool integration
6. Browser automation
7. Local speech-to-text and text-to-speech
8. Vision and computer interaction
9. Specialized model routing for embeddings, OCR, speech and vision
10. Optional additional free model providers

## Security

Never put API keys, passwords, tokens, browser cookies, personal documents, or `.env` files into this repository. JARVIS should run with the minimum permissions necessary.
