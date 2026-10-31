# JARVIS target architecture

**Status:** target design reviewed against the repository on 31 October 2026. Planned components are not represented as implemented.

## 1. Product objective

JARVIS is a local-first personal AI work environment for research, planning, coding, analysis, and approved actions. Its defining requirements are usefulness, observability, security, verifiability, provider independence, and cost awareness.

The dashboard is a **JARVIS Agent Operations Console with SOC-inspired UX**. It observes JARVIS itself. It is not initially a full SOC, SIEM, endpoint monitoring platform, or enterprise network monitoring product.

## 2. Logical architecture

The architecture has three planes.

**Control plane**
- JARVIS interface: user requests, run history, status, approvals, and final results.
- OpenClaw: control tower for task assignment, sequencing, handoffs, pause/resume, budgets, and stop conditions.
- Hermes: primary reasoning and planning agent. It interprets requests, prepares concise plans, defines acceptance criteria, and produces task briefs.
- Policy gate: applies tool allowlists, risk rules, workspace scope, budgets, and approval requirements.

**Execution plane**
- Coding workers: Claude Code when its runtime/provider path is usable; OpenCode as an alternative; DeepSeek Harness as an experimental specialist.
- Research and analysis workers: gather evidence and return source-linked findings; read-only by default.
- QA Sentinel: independent tests, lint/type checks, static/security scans, diff review, and verification.
- Tool adapters: deterministic filesystem, Git, browser/research, terminal, and future MCP integrations.
- Workspace manager: creates per-task branches/worktrees, enforces ownership, and collects diffs and artifacts.

**Model plane**
- FreeLLMAPI is the intended local model gateway at the currently observed loopback service 127.0.0.1:31415.
- Configured upstreams may include NVIDIA NIM, Google AI Studio, OpenRouter, and other explicitly configured providers.
- Ollama provides private/local fallback inference when a model is feasible on the laptop.
- A model adapter normalizes requests, tool calls, usage, errors, and provider metadata for each supported runtime.

**Observability plane**
- Event and audit pipeline records runs, tasks, agent handoffs, model calls, tool executions, approvals, tests, errors, and security events.
- Run/task state store retains lifecycle state and references to evidence.
- Read-only operations dashboard presents activity, traces, approvals, health, and model usage.

These are logical boundaries. They are not claims that every component is installed or running today.

## 3. Component ownership

| Component | Owns | Current status |
|---|---|---|
| JARVIS interface | User interaction, run status, approvals, results | CLI exists; unified UI planned |
| OpenClaw | Delegation, task sequencing, run limits, handoffs | Not integrated |
| Hermes | Reasoning, planning, acceptance criteria, task briefs | Not integrated |
| FreeLLMAPI | Local model gateway and provider selection | Installed/tested separately; repo adapter absent |
| Model adapters | Normalized model requests and health/usage events | Ollama, OmniRoute, NVIDIA, OpenRouter exist; FreeLLMAPI planned |
| Workers | Bounded coding/research/specialist tasks | Not integrated |
| QA Sentinel | Independent verification and evidence | Not implemented as a separate role |
| Policy gate | Allowlist, privilege checks, approvals, budgets | Partial foundation exists |
| Workspace manager | Isolated branch/worktree and write ownership | Not implemented |
| Event pipeline | Correlated, structured audit data | Not implemented |
| Operations console | Read-only visualisation of actual activity | Not implemented |

OpenClaw coordinates work; it does not grant permissions. Hermes plans; it does not receive unrestricted machine access. Workers execute assigned tasks; they cannot expand their own scope. QA Sentinel verifies; the worker cannot approve its own result. FreeLLMAPI is a gateway, not a model and not a source of unlimited free inference.

## 4. Model strategy

Choose models by role and measured performance, not by assigning a different model to every named agent. Keep a registry of role, provider, exact model ID, compatible runtime adapter, tool-call support, structured-output reliability, context limit observed, latency, usage/quota, and last test result.

| Role | Initial strategy |
|---|---|
| Reasoning/planning | Hermes with a validated gateway model |
| Coding | Claude Code if compatible and quota is available; OpenCode fallback; experimental harness only after evaluation |
| Research | Evidence-first worker with restricted public-web/document tools |
| QA review | Independent reviewer, preferably a different model/provider from the coder, plus deterministic tests |
| UI/UX | Optional specialist, only when the task needs it |
| Local fallback | Ollama model selected against measured memory/VRAM and stability |
| Embedding/reranking/parsing | Specialist components, not general reasoning agents |

FreeLLMAPI being OpenAI-compatible does not prove that every worker runtime can use it. Test protocol compatibility separately for each runtime, including tool calls, streaming, context behavior, model names, and failures.

### Current smoke-test notes

These are observed smoke tests, not a benchmark or an availability promise:
- Gemini 3.6 Flash returned a correct structured JSON response through the configured Google path.
- NVIDIA NIM Mistral Large 4 returned a correct structured JSON response in a direct endpoint test.
- Some NVIDIA and OpenRouter model tests passed; others encountered rate limits, temporary failures, account restrictions, or empty responses.
- Qwen 3.5 4B was observed to run fully on the laptop GPU. Qwen 3.5 9B was unstable under VRAM pressure.

DeepSeek V4.1 Flash, GLM 5.3 Flash, Gemma 4 variants, and newly listed models remain candidates until tested against the current account, provider, gateway, runtime, and task-specific evaluation. A model-list entry is not evidence of unlimited quota or production readiness.

## 5. Request lifecycle

1. Intake creates a run ID, captures the requested outcome, and classifies sensitivity.
2. Policy gate selects the workspace, allowed tools, network scope, budget, and approvals.
3. Hermes creates a concise plan, bounded subtasks, acceptance criteria, and risk notes.
4. OpenClaw creates task records and assigns one owner per task.
5. Workers act in isolated workspaces. Each tool call is authorized and emits an event.
6. The run pauses for approval when an action crosses a permission boundary.
7. QA Sentinel runs deterministic checks and independent review. Failures return to the task owner with a retry limit.
8. Integration collects the diff and artifacts. Human approval is required before merge, deployment, deletion, or external side effects.
9. JARVIS reports changed files, checks, evidence, unresolved risks, and run ID.
10. Run/task state and telemetry are persisted for later review.

## 6. State, artifacts, and concurrency

Persist run/task state instead of treating the chat transcript as the source of truth. Store run ID, status, plan summary, acceptance criteria, risk, budgets, task owner, dependencies, workspace ID, retries, approvals, artifacts, and final outcome.

Store bulky outputs in run-specific artifact folders. Workers receive only the task brief, necessary files, allowed tools, and acceptance criteria. Do not expose unrelated conversations or secrets.

Use SQLite for local run/task metadata and event indexing initially. Keep artifacts as files. The dashboard reads state; it cannot edit audit history.

Every coding task gets a dedicated branch or Git worktree. One task has one write owner. Reviewers may read a workspace while the owner works, but they return comments and evidence rather than editing the same files. Integration is a separate diff-review, test, and approval step.

## 7. Operations console

The target dashboard has seven core areas:
1. Run overview: active, completed, failed, and paused runs; duration and token/cost totals when available.
2. Agent activity stream: real events such as Hermes planning, OpenClaw assignment, worker edits, and QA failures.
3. Trace timeline: one run expanded into agent handoffs, model calls, tools, approvals, and tests.
4. Tool/command audit: tool, redacted arguments, permission scope, workspace, outcome, duration, and evidence.
5. Approval queue: pending actions showing target, risk, requested scope, and approve/deny outcome.
6. Model/provider health: model selection, fallback route, latency, rate limits, errors, and token usage where exposed.
7. Security events: denied actions, out-of-scope access, suspicious network destinations, secret-redaction events, and repeated loops.

The UI must distinguish observed facts, inferred warnings, and unverified model claims. No fabricated activity or decorative alerts.

## 8. Telemetry concepts

- Logs/events say what happened at a point in time.
- Metrics aggregate behavior over time, such as success rate, latency, and tool errors.
- Traces show the causal path of one request across the control plane, agents, models, and tools.

Propagate run/trace IDs and parent-child span IDs across runtimes. Begin with structured local events and a trace-compatible schema. Introduce OpenTelemetry APIs/Collector when integrations and volume justify them. References: [OpenTelemetry logs](https://opentelemetry.io/docs/concepts/signals/logs/) and [OpenTelemetry trace context](https://opentelemetry.io/docs/specs/otel/overview/).

## 9. Initial non-goals

Do not start with a full SOC/SIEM, enterprise endpoint/network telemetry, always-running agents, unbounded swarms, automatic deployments or external account actions, Kubernetes, or extensive voice/vision/desktop automation. Stabilise agent execution, policy, audit, and verification first.

## 10. Definition of done

A feature is done only when it has a named owner and bounded scope; documented permissions and side effects; reproducible tests or verification; correlated events; known failure/rollback behavior; visible dashboard evidence; and updated documentation that reflects what is actually implemented.
