# Open-Source Agent Ecosystem Research

**Status:** Research baseline; not an endorsement or completed security audit  
**Scope:** Candidate projects to study or selectively integrate into JARVIS  
**Architecture principle:** JARVIS remains an independently designed system. External repositories are references, adapters, or optional subsystems—not replacements for the JARVIS core.

## 1. Executive summary

The initial landscape review identified **31 relevant repositories across 10 engineering areas**. They do not all compete with JARVIS. Some are complete assistant runtimes; others solve a narrow problem such as workflow orchestration, persistent memory, browser control, security evaluation, or voice.

The useful question is therefore not “Which project should replace JARVIS?” It is “Which capability, design pattern, protocol, or isolated component is worth learning from?”

A repository's popularity, feature list, or claim to be open source is not proof that it is secure, production-ready, or suitable for this project. Before adopting code, review its current source, release activity, dependency tree, license, telemetry, data flows, permission model, and security history.

## 2. Candidate repository register

The categories below are functional groupings, not a ranking. License labels are an initial research signal only; verify the exact current license and the license of every dependency or subcomponent before copying, modifying, or distributing code.

### A. Complete assistants and agent runtimes

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| OpenClaw | [openclaw/openclaw](https://github.com/openclaw/openclaw) | Personal-assistant gateway, sessions, channels, skills and tool integrations | Gateway boundaries, session model, permissions and skill lifecycle |
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Agent runtime with memory, skills, subagents and scheduled work | Skill creation, delegation, execution backends and memory |
| OpenJarvis | [open-jarvis/OpenJarvis](https://github.com/open-jarvis/OpenJarvis) | Modular local-first personal AI stack | Separation of intelligence, engine, agents, tools/memory and learning |
| Letta | [letta-ai/letta-code](https://github.com/letta-ai/letta-code) | Stateful agent runtime and persistent memory/identity concepts | Memory hierarchy, durable state and agent identity |

### B. Multi-agent orchestration and management

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| Paperclip | [paperclipai/paperclip](https://github.com/paperclipai/paperclip) | Agent-organisation control plane: goals, ownership, budgets, approvals and audit history | Supervisor/control-plane concepts and governance |
| LangGraph | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | Stateful graph workflows, checkpointing and human-in-the-loop execution | Explicit state transitions, retries, interrupts and resumability |
| Agno | [agno-agi/agno](https://github.com/agno-agi/agno) | Agent teams, tools, durable execution and observability | Agent/team interfaces and durable execution |
| CrewAI | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | Role-oriented agent teams and workflows | Role/task contracts and delegation |
| AutoGen | [microsoft/autogen](https://github.com/microsoft/autogen) | Multi-agent collaboration framework | Conversation and collaboration patterns; check project direction and licensing carefully |
| Pydantic AI | [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | Typed agent execution and validated structured outputs | Typed inputs/outputs, validation and provider abstraction |
| Deep Agents | [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) | Planning, filesystem tools and subagent delegation for complex tasks | Planning and delegation patterns, with strict JARVIS-side policy enforcement |

**Important distinction:** Paperclip is a control plane for managing agent work, not an agent framework or an execution sandbox. It can manage external runtimes; it does not make those runtimes safe by itself.

### C. Memory and knowledge graphs

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| Graphify | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | Code/document knowledge graph; code relationships can be extracted from syntax trees | Codebase understanding, relationship extraction and provenance |
| Graphiti | [getzep/graphiti](https://github.com/getzep/graphiti) | Temporal knowledge graph for evolving facts and historical context | Time-aware memory, entity resolution and provenance |
| Cognee | [topoteretes/cognee](https://github.com/topoteretes/cognee) | Document, code and conversation ingestion into structured knowledge | Ingestion pipeline and graph-based retrieval |
| Mem0 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | Persistent user/session/agent memory extraction and retrieval | Memory extraction, updates and retrieval evaluation |

These projects address different problems. Graphify is particularly relevant to codebase understanding; Graphiti focuses on temporal facts; Cognee on knowledge ingestion; Mem0 on extracted persistent memories. Do not install four competing memory systems as four independent sources of truth. Define a JARVIS memory interface and evaluate specialised backends against the same test set.

### D. Model routing and inference gateways

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| LiteLLM | [BerriAI/litellm](https://github.com/BerriAI/litellm) | Multi-provider gateway, retries, load balancing and budgets | Provider adapters and routing policies |
| OmniRoute | [diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute) | Optional OpenAI-compatible local gateway already considered in the JARVIS stack | Keep as an optional gateway; avoid unnecessary duplicate routing layers |

JARVIS should own its model-selection policy and retain direct local Ollama access. A gateway is an optional transport/provider layer, not the JARVIS brain.

### E. Tools, protocols and integrations

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| MCP Servers | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Example servers exposing tools and resources through MCP | Protocol interoperability and scoped tool adapters |
| Composio | [ComposioHQ/composio](https://github.com/ComposioHQ/composio) | Third-party application integrations and authentication/toolkits | Integration patterns; assess credential and data exposure |
| n8n | [n8n-io/n8n](https://github.com/n8n-io/n8n) | Workflow automation and event-driven integrations | Optional external automation engine; review fair-code licensing |

MCP is a protocol boundary, not a trust boundary. Every connected server still needs identity, least privilege, input validation, network restrictions and auditing.

### F. Browser, computer-use and development agents

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| Browser Use | [browser-use/browser-use](https://github.com/browser-use/browser-use) | LLM-driven browser interaction | Browser-agent patterns and untrusted-page handling |
| Skyvern | [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) | Browser automation combining AI and computer vision | Workflow automation; review AGPL obligations and telemetry configuration |
| Playwright | [microsoft/playwright](https://github.com/microsoft/playwright) | Deterministic browser automation and testing | Preferred deterministic browser execution substrate |
| OpenHands | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | Software engineering agent and execution environment | Isolated coding workspaces and developer-agent workflows |

Prefer deterministic Playwright operations where possible. An LLM can plan or interpret a page, but it should not be granted unrestricted browser, download, credential, or host access.

### G. Security and guardrails

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| NeMo Guardrails | [NVIDIA/NeMo-Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) | Programmable conversational/agent guardrails | Policy and dialogue-constraint patterns |
| Invariant | [invariantlabs-ai/invariant](https://github.com/invariantlabs-ai/invariant) | Agent security and policy-oriented controls | Runtime validation and agent/tool security concepts |
| Promptfoo | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | Prompt/agent evaluation, red teaming and vulnerability testing | Security regression suites and adversarial tests |

A model-based guardrail must never be the only enforcement mechanism. JARVIS needs independent, deterministic authorization in trusted code.

### H. Observability and evaluation

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| Langfuse | [langfuse/langfuse](https://github.com/langfuse/langfuse) | LLM tracing, evaluation and observability | Trace design and evaluation workflows |
| Arize Phoenix | [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | LLM tracing and evaluation | Alternative observability candidate |
| Opik | [comet-ml/opik](https://github.com/comet-ml/opik) | LLM application tracing and evaluation | Alternative observability candidate |

Choose one initial observability path rather than deploying all three. Review data retention, redaction, telemetry and self-hosting configuration before sending traces anywhere.

### I. Voice

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| whisper.cpp | [ggerganov/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Local speech recognition | Offline STT adapter |
| Kokoro | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | Text-to-speech model and tooling | Local TTS adapter |

Voice is an interface, not a permission bypass. Spoken requests must pass through the same authorization and approval pipeline as typed requests.

### J. Execution isolation

| Project | Repository | What it offers | JARVIS research target |
|---|---|---|---|
| gVisor | [google/gvisor](https://github.com/google/gvisor) | Application-kernel sandboxing for container workloads | Stronger isolation for untrusted execution; assess platform compatibility and operational cost |

## 3. How these projects map to JARVIS

JARVIS should retain ownership of its core architecture:

1. **JARVIS Core:** identity, user context, interface, policy enforcement and lifecycle.
2. **Executive agent:** intent interpretation, planning and task decomposition.
3. **Department supervisors:** research, cybersecurity, development and personal productivity.
4. **Specialist agents:** narrowly scoped roles such as log analyst, code reviewer, document analyst or browser researcher.
5. **Deterministic execution layer:** Python tools, filesystem operations, browser automation, terminal, APIs and MCP adapters.

Cross-cutting services should include:

- Independent security control plane and permission enforcement.
- Model router with local inference as a first-class option.
- Memory and knowledge services with provenance and retention controls.
- Audit, tracing, evaluation and verification.
- Approval, rollback and recovery mechanisms.

A possible research-to-subsystem mapping:

| JARVIS subsystem | Projects to study |
|---|---|
| Executive orchestration and governance | Paperclip, LangGraph |
| Agent/team patterns | Agno, CrewAI, Hermes |
| Typed agent contracts | Pydantic AI |
| Stateful memory | Letta, Mem0 |
| Temporal knowledge | Graphiti |
| Codebase graph | Graphify |
| Knowledge ingestion | Cognee |
| Model gateway | OmniRoute, LiteLLM |
| Tool interoperability | MCP |
| Application integrations | Composio |
| Browser automation | Playwright, Browser Use, Skyvern |
| Coding workspace | OpenHands |
| Security evaluation | Promptfoo, Invariant, NeMo Guardrails |
| Observability | Langfuse, Phoenix, Opik |
| Speech | whisper.cpp, Kokoro |
| Execution isolation | gVisor |

## 4. Adoption decision framework

Every candidate must receive one of four decisions:

- **Adopt:** use an existing component or protocol after source, license, dependency and security review.
- **Adapt:** implement a JARVIS-owned version using lessons from the project.
- **Reference:** study architecture or ideas without importing its code.
- **Reject:** do not use because of poor fit, unacceptable risk, licensing constraints, maintenance concerns or unnecessary complexity.

Before any adoption, record:

- Exact repository URL, commit/tag and date reviewed.
- License for the repository and relevant subcomponents.
- Maintainer activity, release history and known security advisories.
- Dependencies, install scripts, network calls and telemetry.
- Data collected, stored, transmitted and retained.
- Authentication, authorization and sandbox boundaries.
- Secrets handling and default permissions.
- Integration surface, resource requirements and platform compatibility.
- Test results, known limitations and rollback/removal plan.

## 5. Compatibility and integration cautions

- The current JARVIS README specifies Python 3.14+. The OpenJarvis package metadata reviewed during the initial research specified Python 3.10–3.13. Do not install it into JARVIS's primary environment without verifying updated support. Use a separate environment or sidecar for experiments.
- Do not introduce a second model router without a clear requirement. Preserve JARVIS's existing model-router interface and direct local Ollama path.
- Do not let third-party agent frameworks bypass JARVIS's policy engine.
- Do not treat MCP servers, browser agents, workflow engines or memory backends as trusted by default.
- Keep optional integrations isolated so their dependencies cannot destabilize the core.
- Avoid multiple competing sources of truth for user memory, task state or permissions.
- Never commit API keys, tokens, cookies, private documents or local environment files.

## 6. Recommended research order

### Phase 1 — Core architecture
1. OpenJarvis
2. Paperclip
3. LangGraph
4. Hermes Agent
5. OpenClaw
6. Graphify

### Phase 2 — Memory and intelligence
7. Graphiti
8. Mem0
9. Cognee
10. Letta
11. Pydantic AI

### Phase 3 — Security and reliability
12. Promptfoo
13. Invariant
14. gVisor
15. MCP
16. One observability candidate

### Phase 4 — Capabilities
17. Playwright
18. Browser Use
19. OpenHands
20. Composio
21. whisper.cpp
22. Kokoro

This is an inspection order, not an installation plan. Do not install or integrate a candidate until its assessment is documented and approved.

## 7. Initial technical audit checklist

For each priority repository, inspect the actual source—not just its README—and answer:

1. What process runs, with what OS identity and privileges?
2. What files, directories, credentials and environment variables can it access?
3. What network destinations can it reach?
4. Can an agent invoke tools directly, or must it pass through a trusted broker?
5. How are tool arguments validated and authorized?
6. Can untrusted content influence tool selection or execution?
7. How are memory writes authenticated, attributed and reversed?
8. Are actions logged with enough evidence to reconstruct them?
9. What happens when a model, tool, provider or verification step fails?
10. Can the component be disabled or removed without damaging JARVIS?

## 8. Reference standards and reading

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP Top 10 for Agentic Applications](https://owasp.org/www-project-top-10-for-agentic-applications/)
- [OWASP AI Agent Security Cheat Sheet](https://cheatsheetseries.owasp.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

---

**Decision:** JARVIS remains an independently engineered, local-first assistant. The repositories in this register are candidate references and optional components. No project is approved for integration solely by appearing in this list.
