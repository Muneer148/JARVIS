# JARVIS

A local-first, action-capable personal AI assistant.

## Architecture

```text
User
  |
  v
JARVIS Agent Core
  |-- Tool Router -> deterministic Python tools -> verified results -> Agent Core
  |
  `-- Model Router
        |-- Ollama (local/private/default)
        |-- OmniRoute (local gateway -> configured upstream)
        |-- NVIDIA (direct optional gateway)
        `-- OpenRouter (direct optional gateway)
```

JARVIS is intentionally an agent, not a text-only chatbot. The model decides when a tool is needed; Python performs deterministic actions; the safety layer validates actions and handles permission boundaries. Model routing and tool routing are separate concerns.

## Current stack

- Python 3.14+
- Ollama + Qwen3:8B for the permanent local brain
- Optional OmniRoute local gateway
- Optional NVIDIA hosted inference
- Optional OpenRouter direct gateway
- Local-first model routing with fallback
- Standard library first; optional voice/vision/browser dependencies are isolated

## Model routing

`JARVIS_BRAIN_MODE` supports:

- `local` — Ollama only
- `cloud` — try OmniRoute, then NVIDIA, then OpenRouter, then local fallback
- `nvidia` — direct NVIDIA endpoint, with local fallback on failure
- `openrouter` — direct OpenRouter endpoint, with local fallback on failure
- `omniroute` — local OmniRoute gateway, with local fallback on failure
- `auto` — Ollama for routine requests; selected complex/long requests prefer OmniRoute when configured, then NVIDIA, then OpenRouter, then Ollama

The important distinction is that **OmniRoute is a gateway/router, not another model**. JARVIS can therefore keep one model-routing interface while the local OmniRoute instance decides which configured upstream provider/model to use.

### OmniRoute setup

OmniRoute runs separately from JARVIS. Its default OpenAI-compatible API is:

```text
http://localhost:20128/v1
```

JARVIS expects a local OmniRoute API key because the installed OmniRoute server may require authentication. Configure the key only in the local environment:

```powershell
$env:JARVIS_OMNIROUTE_ENABLED="true"
$env:OMNIROUTE_API_KEY="YOUR_LOCAL_OMNIROUTE_KEY"
$env:JARVIS_OMNIROUTE_MODEL="auto"
.\.venv\Scripts\python.exe main.py
```

If you use a non-default OmniRoute endpoint, set `OMNIROUTE_BASE_URL` or the full `JARVIS_OMNIROUTE_URL`. Do not commit API keys, passwords, tokens, cookies, or local `.env` files.

JARVIS does **not** need to configure hundreds of OmniRoute providers. One working provider path is enough to validate the architecture; additional providers can be added later.

## NVIDIA hosted models

NVIDIA hosted inference can be enabled directly or selected by `auto` when OmniRoute is unavailable. Availability and usage limits can change, so Ollama remains the permanent local fallback.

```powershell
$env:NVIDIA_API_KEY="YOUR_KEY_HERE"
$env:JARVIS_BRAIN_MODE="auto"
$env:JARVIS_NVIDIA_MODEL="nvidia/nemotron-3.5-lightning-30b-a3b"
.\.venv\Scripts\python.exe main.py
```

Never paste the key into Python source code or commit it to GitHub.

## OpenRouter direct gateway

OpenRouter is an optional external aggregation gateway. It is independent of the local OmniRoute process and is used only when configured.

```powershell
$env:OPENROUTER_API_KEY="YOUR_KEY_HERE"
$env:JARVIS_BRAIN_MODE="openrouter"
.\.venv\Scripts\python.exe main.py
```

Use a model identifier supported by your OpenRouter account/configuration through `JARVIS_OPENROUTER_MODEL`.

## Diagnostics and evidence

JARVIS now has read-only diagnostics for the local environment:

- `system_info` — OS, Python and machine architecture
- `resource_info` — logical CPU count, RAM usage and disk usage
- `project_health` — required project paths, Git status, Python version and the local pytest suite

Tool results are treated as verified evidence. JARVIS is instructed not to replace current tool evidence with generic assumptions about Python versions or project compatibility.

## Current capabilities

- Chat with the local Ollama model
- Multi-provider model routing with local fallback
- Explicit cloud escalation through OmniRoute/NVIDIA/OpenRouter
- Multi-tool agent loop
- Structured tool calls with optional JSON arguments
- System and resource diagnostics
- JARVIS project-health diagnostics
- Downloads inspection and deterministic filesystem organization
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

5. Install the test dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
```

6. Run the tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

7. Run JARVIS:

```powershell
.\.venv\Scripts\python.exe main.py
```

The router tests mock network providers, so they do not require API keys or live cloud services.

## Safety model

Filesystem mutation follows:

```text
Analyze -> Plan -> Validate -> Human approval -> Execute -> Verify -> Roll back on failure
```

JARVIS never claims an action was completed merely because the model requested it. Python tools return the actual execution result.

## Roadmap

1. Core local + multi-model agent loop
2. Harden multi-tool reasoning and tool schemas
3. More filesystem operations
4. Persistent memory
5. Terminal and application control with explicit permission scopes
6. MCP tool integration
7. Browser automation
8. Local speech-to-text and text-to-speech
9. Vision and computer interaction
10. Specialized model routing for embeddings, OCR, speech and vision
11. Additional free/optional model providers

## Security

Never put API keys, passwords, tokens, browser cookies, personal documents, or `.env` files into this repository. JARVIS should run with the minimum permissions necessary.
