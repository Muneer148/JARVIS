# JARVIS model routing

JARVIS separates **model routing** from **tool routing**.

## Model routing

The model router can use:

- `local` — Ollama only.
- `omniroute` — the local OmniRoute gateway, which can forward requests to configured upstream providers.
- `nvidia` — NVIDIA's OpenAI-compatible API directly.
- `openrouter` — OpenRouter's OpenAI-compatible API directly.
- `cloud` — try configured cloud gateways in this order: OmniRoute, NVIDIA, OpenRouter; fall back to Ollama if all fail.
- `auto` — keep routine requests on Ollama and escalate explicitly complex/long requests to the first configured cloud gateway.

Cloud credentials are runtime configuration only. **Never commit API keys to Git.**

## Tool routing

Tool selection remains inside the agent planner. A cloud model does not bypass the local tool registry: after the model returns a `TOOL_CALL`, JARVIS executes the registered local tool and sends the verified result back through the model loop.

## Recommended rollout

1. Validate Ollama and the local agent loop.
2. Configure one cloud upstream through OmniRoute.
3. Test `auto` routine → local.
4. Test `auto` complex → cloud.
5. Test cloud failure → local fallback.
6. Test a cloud model requesting a local tool.
7. Add additional cloud providers only after the first path is stable.

## Runtime configuration

JARVIS reads the repository-local `.env` file. Existing process environment variables take precedence.

Typical variables are:

```text
JARVIS_BRAIN_MODE=auto
JARVIS_MODEL=qwen3:8b

JARVIS_OMNIROUTE_ENABLED=true
OMNIROUTE_API_KEY=<local OmniRoute key>
OMNIROUTE_BASE_URL=http://localhost:20128/v1
JARVIS_OMNIROUTE_MODEL=auto

NVIDIA_API_KEY=<NVIDIA key>
JARVIS_NVIDIA_MODEL=<configured NVIDIA model>

OPENROUTER_API_KEY=<OpenRouter key>
JARVIS_OPENROUTER_MODEL=<configured OpenRouter model>
```

Only set credentials for providers that are actually configured. The keys above are placeholders and must never be replaced with real secrets in committed files.
