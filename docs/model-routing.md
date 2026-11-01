# JARVIS model and gateway routing

**Status:** this document separates the current code path from the intended target. Do not treat the target integration as implemented.

## 1. Routing principles

- Model routing and agent orchestration are separate concerns.
- FreeLLMAPI is the intended local gateway/router; it is not itself a model and does not create unlimited free tokens.
- An agent runtime may require a protocol that differs from the gateway's exposed endpoint. Compatibility must be tested for each runtime.
- Keep Ollama as an optional private/local fallback when the selected local model is stable and fits available memory/VRAM.
- Select models by role and measured performance, not by the number of models available.
- Log the actual provider, model ID, adapter, latency, usage where available, fallback, and error status.
- Never silently switch providers without recording the route change.

## 2. Current repository behavior

The current development code contains:
- Ollama chat adapter.
- OmniRoute local gateway adapter.
- NVIDIA hosted inference adapter.
- OpenRouter hosted inference adapter.
- Heuristic local/cloud provider selection.
- Local fallback when an optional cloud path raises a handled RuntimeError.

The existing default is configured through config/settings.py and .env.example. The current implementation does **not** yet use FreeLLMAPI. It also does not yet assign distinct models to Hermes, coding workers, research workers, and QA Sentinel.

Do not update provider logic by changing environment variables alone and assume the architecture is complete. Add a FreeLLMAPI adapter, tests, and event instrumentation first.

## 3. Intended FreeLLMAPI integration

The locally observed FreeLLMAPI desktop service is version 0.16.14 and listens on loopback at 127.0.0.1:31415.

Expected OpenAI-compatible base endpoint for the adapter:
- Base URL: http://127.0.0.1:31415/v1
- Chat completion path: /chat/completions
- Model catalogue path: /models (subject to the running app's API behavior/configuration)

Implementation requirements:
1. Make the base URL configurable; do not hardcode a user's machine-specific endpoint throughout the code.
2. Keep gateway credentials and upstream provider keys outside the repository and outside agent-visible logs.
3. Test the model list endpoint and a small structured-response request.
4. Handle timeout, 401, 403, 404, 429, 5xx, malformed response, empty completion, and content-filter errors distinctly.
5. Record the actual selected model ID from the response where available.
6. Preserve provider-reported usage only when the API returns it.
7. Implement fallback policy in one central router and emit a model.fallback event.
8. Do not retry non-idempotent tool actions merely because a model/provider request failed.
9. Keep direct provider adapters temporarily if needed for diagnostics, but consolidate the normal path behind a stable adapter interface.

A local HTTP listener must remain bound to loopback unless the user explicitly approves a separately designed remote-access use case. Do not expose the gateway to the LAN or public internet as a convenience.

## 4. Runtime compatibility matrix

A provider model passing a chat-completion smoke test does not prove it works with Hermes, Paperclip, Claude Code, OpenCode, or another worker.

Maintain a matrix such as:

| Runtime | Required API/protocol | Gateway/model test | Tool calling | Streaming | Status |
|---|---|---|---|---|---|
| Hermes | Verify the runtime's configured provider protocol | Pending repo integration | Pending | Pending | Not connected |
| Paperclip | Verify orchestration's model/runtime interface | Pending | Pending | Pending | Not connected |
| Claude Code | Verify compatible Anthropic/provider endpoint and tool behavior | Pending | Pending | Pending | Not connected |
| OpenCode | Verify provider adapter and tool behavior | Pending | Pending | Pending | Not installed/integrated |
| DeepSeek Harness | Verify required API/runtime interface | Pending | Pending | Pending | Experimental/not integrated |
| Current JARVIS Agent | OpenAI-compatible chat adapter used by current code | Existing direct adapters tested | Textual TOOL_CALL protocol in current planner | Non-streaming | Implemented baseline |

Do not infer compatibility from an endpoint being described as OpenAI-compatible. Test the exact client and feature set.

## 5. Model roles and candidate selection

| Logical role | Desired behavior | Candidate approach |
|---|---|---|
| Planner/reasoner | Strong instruction following, reliable structured output, tool discipline, evidence-aware planning | Hermes plus a measured general reasoning model |
| Coder | Repository understanding, precise diffs, tool use, tests, low regression rate | Claude Code when usable; OpenCode fallback; specialist coding runtime experimental |
| Researcher | Accurate retrieval, clear source/evidence references, uncertainty handling | Evidence-oriented model with restricted web/document tools |
| QA reviewer | Independent defect finding and challenge of unsupported claims | Separate model/provider where possible, combined with deterministic tests |
| Local fallback | Privacy, offline use, acceptable speed, stability | Ollama model measured on the actual laptop |
| Specialist components | Embedding, reranking, parsing, OCR, speech, vision | Dedicated endpoint/model only when the feature exists |

One model may serve multiple roles initially. Add another endpoint only when evaluation demonstrates a meaningful benefit.

## 6. Current observed smoke-test record

These results are observations from tests performed with the local gateway/provider setup. They are not exhaustive benchmarks and may change with account configuration, endpoint availability, or provider quotas.

- Google Gemini 3.6 Flash returned the expected structured JSON in a test through the configured Google path.
- NVIDIA NIM Mistral Large 4 returned the expected structured JSON in a direct endpoint test.
- Several NVIDIA NIM and OpenRouter models passed basic model tests.
- Other model tests returned rate limits, timeouts, account availability errors, temporary upstream failures, or empty responses.
- The local Qwen 3.5 4B model was observed to run fully on the laptop GPU.
- The local Qwen 3.5 9B model experienced VRAM pressure and intermittent CUDA/server failure.

DeepSeek V4.1 Flash, GLM 5.3 Flash, Gemma 4 variants, MiniMax M3.1 Flash, and other recently listed endpoints must be re-tested and benchmarked before a role is assigned. Treat listings as candidates, not guaranteed availability.

## 7. Model evaluation protocol

For every candidate, record:

1. Provider and exact model identifier.
2. Date and endpoint/runtime used.
3. Basic correctness on a deterministic structured-output test.
4. Tool-call compliance, including malformed/extra arguments.
5. Long-context behavior using the context size actually accepted, not marketing claims.
6. Latency, timeout behavior, empty responses, and fallback behavior.
7. Token usage and cost where the provider exposes trustworthy values.
8. Rate-limit and cooldown behavior.
9. Reliability across repeated trials.
10. Data-handling constraints: whether the request leaves the device and what content is sent.

A candidate is ready for a role only after its tests pass for that role and runtime. A model that is good at chat may be poor at tool calling or code changes. Embedding, reranking, parsing, and safety-classification endpoints are specialist services, not general-purpose agents.

## 8. Recommended initial route

- Normal local-only diagnostics can use the current Ollama path when the selected model is stable.
- Hosted reasoning and coding should route through the local FreeLLMAPI gateway when the specific runtime adapter has been validated.
- If FreeLLMAPI or its upstream provider fails, record the failure and use an explicitly configured fallback only when the task's privacy classification permits sending data to that provider.
- Keep sensitive/private tasks local unless the user explicitly approves an external provider.
- Never silently downgrade a task's privacy boundary in order to make a model call succeed.

## 9. Security requirements

- Store provider keys only in the gateway's protected local configuration or an approved local secret store.
- Do not commit .env files, database files, logs containing credentials, or API request dumps.
- Do not pass gateway admin controls or upstream keys to agents.
- Redact authorization headers and sensitive payload fields from error logs.
- Keep the gateway loopback-only by default.
- Record provider/model/fallback metadata without recording secret values.
- Do not treat a model output as a verified result until its tools/tests return evidence.

## 10. Implementation sequence

1. Instrument the existing model router so current routes and failures are visible.
2. Add the FreeLLMAPI adapter behind the existing model interface.
3. Add tests using a mocked OpenAI-compatible server; no real API key is required in CI.
4. Add an opt-in local smoke test using a configured model.
5. Validate Hermes against the adapter.
6. Validate Paperclip and each worker runtime separately.
7. Add role-based model registry only after runtime compatibility is known.
8. Add dynamic fallback and budgets with explicit privacy classification and events.
