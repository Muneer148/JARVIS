# JARVIS

**A local-first, security-conscious personal AI work environment with a multi-agent execution layer and a SOC-inspired operations console.**

JARVIS is intended to become a dependable catalyst for research, coding, analysis, and cybersecurity work. It must show what it is doing, what tools and models it used, what changed, what failed, and where human approval was required.

> **Project status (31 October 2026):** the repository has a working single-agent Python foundation. The multi-agent control plane, FreeLLMAPI integration, isolated worker execution, persistent event pipeline, and operations dashboard are architectural targets—not completed features.

## What we are building

- A unified JARVIS interface for requests, task status, approvals, and results.
- A controlled orchestration layer: OpenClaw coordinates bounded tasks; Hermes is the primary reasoning and planning agent.
- Replaceable worker runtimes for coding, research, and specialist analysis.
- FreeLLMAPI as the intended local model gateway, with Ollama as a private/local fallback.
- An independent QA Sentinel that checks tests, scans, outputs, and evidence.
- A SOC-inspired **AI Agent Operations Console** that displays agent activity, tool calls, traces, failures, approvals, model usage, and security-relevant events.
- Least-privilege permissions, isolated workspaces, human approval for sensitive actions, and evidence-backed completion.

This is **not initially a full Security Operations Center or SIEM**. The dashboard is for observing and auditing JARVIS and its agents. Real endpoint, network, and enterprise security monitoring is a separate future scope.

## Read the design before adding features

| Document | Purpose |
|---|---|
| [Target architecture](docs/ARCHITECTURE.md) | Components, responsibilities, data flow, and system boundaries |
| [Agent operating model](docs/OPERATING_MODEL.md) | Workflows, handoffs, parallel agents, bounded swarms, and task ownership |
| [Security model](docs/SECURITY.md) | Threat model, permission boundaries, approvals, isolation, and hardening gates |
| [Operations console and telemetry](docs/OBSERVABILITY.md) | Dashboard design, logs, metrics, traces, event schema, and privacy |
| [Model routing strategy](docs/model-routing.md) | FreeLLMAPI, provider adapters, model roles, and compatibility checks |
| [Implementation roadmap](docs/ROADMAP.md) | Milestones, acceptance criteria, and the daily one-hour working cadence |
| [Repository audit](docs/AUDIT-2026-10-31.md) | What exists today, gaps, branch state, and known risks |

## Current implementation baseline

The current code line is on **dev/jarvis-v1**. It includes:

- A single-agent CLI loop with structured tool-call parsing and a bounded tool-round count.
- Local Ollama plus optional OmniRoute, NVIDIA, and OpenRouter provider adapters.
- A typed tool registry with JSON-schema-like descriptions, permissions, risk labels, and approval requirements.
- Read-only system/resource/project diagnostics.
- Deterministic Downloads analysis and organization with validation, post-action checks, and best-effort rollback.
- Local explicit memory tools and static public-page fetching with URL checks.
- Unit tests and a GitHub Actions test workflow.

It does not yet implement the multi-agent architecture or operations console described above. The audit records this distinction in detail.

## Working principles

1. **One task, one owner.** A coding task has one write owner and one isolated workspace.
2. **Workflow before swarm.** Use explicit, inspectable handoffs first; use a bounded swarm only when it provides a clear benefit.
3. **No hidden success.** A model saying it completed work is not proof. Tools, tests, and verification must provide evidence.
4. **Human control for consequential actions.** Installation, deletion, credential access, external side effects, deployments, and changes outside the approved workspace require approval.
5. **Least privilege and isolation.** Agents only receive the tools, files, network access, and credentials required for their task.
6. **Auditable, not theatrical.** The console shows real events and measured state, not decorative activity or fabricated SOC alerts.
7. **Provider independence.** A model or agent runtime can be replaced without rewriting the entire system.
8. **Cost-aware by design.** Free endpoints are treated as quota-limited services, not unlimited compute. Local models are fallbacks where practical.
9. **Evidence over hidden reasoning.** Store concise plans, decisions, tool events, outputs, and verification evidence—not private chain-of-thought.
10. **Build in vertical slices.** Every milestone should leave a working, testable system.

## Development setup for the current baseline

The current CI workflow uses Python 3.12. Use Python 3.12 or later for this code line, then:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py
```

The current default model configuration is in config/settings.py and .env.example. The existing provider routing is not yet the final FreeLLMAPI integration; see the model-routing document before changing it.

## Repository and branch discipline

- Keep main as the stable, reviewable baseline.
- Build implementation work on dev/jarvis-v1 or a clearly named feature branch.
- Keep architecture proposals and documentation reviewable on docs/jarvis-architecture-blueprint.
- Do not merge the diverged feature/voice-assistant branch without reviewing its differences against the current development line.
- Use pull requests for changes that affect architecture, security boundaries, tool execution, or orchestration.

## Security baseline

Never commit API keys, passwords, access tokens, cookies, private user documents, or local .env files. Keep terminal execution disabled until the security requirements in [SECURITY.md](docs/SECURITY.md) are implemented and tested.

---

**North-star outcome:** JARVIS should be a useful personal AI work environment whose actions are understandable, observable, bounded, verifiable, and under the user's control.
