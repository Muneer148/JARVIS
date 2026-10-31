# JARVIS implementation roadmap

**Working cadence:** target at least one focused hour per day. Each session should leave one verified increment, a learning note, and an updated task status. Do not turn the one-hour target into pressure to make unsafe or unreviewed changes.

## 1. Priority order

The project is built in dependency order:

1. Make the existing single-agent core observable and reliable.
2. Close high-priority security gaps before expanding its permissions.
3. Integrate the chosen model gateway and validate role-specific model/runtime compatibility.
4. Add the orchestration and reasoning runtimes.
5. Add isolated workers and independent QA.
6. Build the operations console over real telemetry.
7. Add carefully bounded swarm behavior only where needed.
8. Add optional voice, vision, MCP, and broader desktop integration after the core is dependable.

Do not start with a large frontend, a large SIEM stack, or several autonomous coding agents.

## 2. Milestones

### M0 — Architecture and repository baseline
**Status:** documentation prepared on docs/jarvis-architecture-blueprint; review pending.

Deliverables:
- Target architecture, operating model, security model, telemetry schema, and roadmap.
- Explicit distinction between implemented code and planned components.
- Branch and integration rules.

Exit criteria:
- Design documents are reviewed.
- The current code branch and diverged voice branch are understood.
- No feature is described as implemented unless it exists and is tested.

### M1 — Baseline reliability and telemetry spine
**Priority:** first implementation milestone.

Deliverables:
- A central event interface and versioned event schema.
- Run IDs and task IDs for the current CLI session.
- Events for run start/end, selected provider, fallback, model request outcome, tool request, authorization decision, tool start/end, exception, and final result.
- Redaction before events are persisted.
- Local SQLite run/event store or an equivalent minimal append-oriented store.
- CLI viewer that can show one run's ordered events.

Exit criteria:
- A simple real run can be reconstructed after process restart.
- Tool requested, tool authorized, and tool executed are distinct records.
- Provider fallback is visible and attributed to the actual provider/model.
- Tests prove secrets are redacted and failed actions are not logged as success.

### M2 — Security baseline and tool hardening
**Priority:** before enabling more automation.

Deliverables:
- Documented permission matrix and per-tool allowlists.
- Argument- and path-level validation.
- Workspace boundary checks.
- Approval records with scope and outcome.
- Run, tool, timeout, output, and retry limits.
- Terminal execution remains disabled until its design is hardened; replace free-form shell execution and substring blocklists with a restricted execution interface.
- Browser/network controls reviewed and adversarially tested.
- Security tests for prompt injection, path traversal, untrusted tool output, and secrets in logs.

Exit criteria:
- Unknown tools and scopes are denied by default.
- Approval occurs before execution and is tied to the exact action.
- Terminal stays off until its separate release gate passes.
- Audit evidence records blocked actions and stop reasons.

### M3 — FreeLLMAPI gateway adapter and model registry
Deliverables:
- A dedicated provider adapter for the local FreeLLMAPI endpoint.
- No provider secret stored in source code, logs, or agent prompt.
- Model registry with exact model ID, role suitability, provider, tool-call/JSON behavior, context observed, latency, rate limits, and smoke-test date.
- One reliable model route first, then additional candidates only after evaluation.
- Local Ollama fallback with resource-aware selection.

Exit criteria:
- A model request can be routed through FreeLLMAPI and correlated in the event store.
- Gateway outage, provider outage, model error, rate limit, and local fallback are distinct outcomes.
- Exact per-runtime protocol compatibility is tested; do not assume every agent runtime accepts the same endpoint.
- The project does not claim a free endpoint has unlimited tokens.

### M4 — Hermes and OpenClaw integration
Deliverables:
- Hermes configured as the primary reasoning/planning runtime.
- OpenClaw integrated as the task/control orchestrator.
- An adapter boundary between JARVIS policy/state and these runtimes.
- A single bounded workflow: intake, plan, assign one read-only worker, collect evidence, verify, report.
- Durable run/task state and pause/resume.
- Hard caps on turns, handoffs, wall-clock time, concurrency, and token/cost budget.

Exit criteria:
- One request has a run ID, plan summary, task record, owner, status, and final evidence.
- Handoffs are explicit and appear in the event timeline.
- Policy cannot be overridden by agent instructions.
- Stop/cancel and limit behavior are tested.

### M5 — Worker adapters and isolated workspaces
Deliverables:
- One coding worker adapter first, with Claude Code when its provider/protocol path is available.
- OpenCode as an alternative runtime.
- DeepSeek Harness as an experimental worker after compatibility and safety review.
- Git branch/worktree manager.
- Task contracts with file scope, owner, acceptance criteria, and required evidence.
- One write owner per worktree/task.

Exit criteria:
- A worker changes only its assigned workspace.
- Changed files, branch, base commit, and diff are recorded.
- No two workers can write to the same workspace concurrently.
- Worker errors/timeouts preserve artifacts and do not produce false success.

### M6 — QA Sentinel and verification pipeline
Deliverables:
- Deterministic test/lint/type/static checks.
- A separate reviewer role where useful.
- Structured QA reports with exact command, exit code, findings, and artifact links.
- Bounded repair/retest cycles.
- Human approval before integration/merge.

Exit criteria:
- The implementer cannot approve its own task.
- Required tests must pass or the run reports a failure/exception.
- Skipped checks are clearly shown.
- The final report links to evidence and unresolved issues.

### M7 — SOC-inspired Agent Operations Console
Deliverables:
- Run overview and live/refreshable status.
- Agent activity feed.
- Trace/task timeline.
- Tool and command audit.
- Approval queue.
- Model/provider health and token/latency view where data is available.
- Security event view.
- Filters by run, task, agent, event type, provider, status, and time.

Exit criteria:
- The dashboard reads real persisted events.
- A complete run can be reconstructed without relying on the model's narrative.
- It differentiates observed facts, derived warnings, and unverified claims.
- The UI does not emit or display fake activity.

### M8 — Bounded hybrid multi-agent and swarm capability
Deliverables:
- Sequential workflow for dependent work.
- Parallel fan-out for independent read-only tasks.
- Optional swarm/handoff pattern for dynamic specialist routing.
- All agent roles, handoff targets, and termination rules are allowlisted.
- Budgets and stop conditions enforced centrally.

Exit criteria:
- A swarm cannot continue indefinitely.
- Max agent count, turns, handoffs, retries, time, and token/cost limits are enforced.
- File ownership prevents concurrent conflicting edits.
- Human approval remains outside the agents' control.

### M9 — Optional capabilities
Potential future work:
- MCP tool ecosystem.
- Stronger browser automation with an isolated browser profile.
- Voice input/output.
- Vision and controlled computer interaction.
- Additional local models and specialist model endpoints.
- More advanced security analysis of JARVIS's own audit stream.

These are optional. They should not displace reliability, policy, audit, and verification work.

## 3. First vertical slice

The first end-to-end demonstration should be read-only and small:

1. User asks JARVIS to inspect a bounded repository.
2. Hermes produces a short plan and acceptance criteria.
3. OpenClaw assigns one research/inspection worker.
4. The worker returns evidence with file references.
5. QA Sentinel checks the report against the source.
6. The event store records each step.
7. The operations console reconstructs the run.
8. JARVIS reports facts, uncertainty, and evidence.

Only after this works should the first isolated coding task be added.

## 4. Daily one-hour session structure

Use a consistent 60-minute block:

- **5 minutes — select one task:** read the issue, expected outcome, and risk.
- **10 minutes — understand first:** inspect the relevant code/docs and write down the current behavior.
- **30 minutes — implement one bounded change:** avoid unrelated refactors.
- **10 minutes — verify:** run focused tests, inspect diffs, and check the event/audit output.
- **5 minutes — record learning:** update the session note, issue status, and next action.

For an exam-heavy or low-energy day, spend the hour on reading, testing, documenting, or reviewing a small change rather than starting a large implementation. Consistency matters more than maximizing lines of code.

## 5. Session completion checklist

- [ ] One clearly scoped task selected.
- [ ] Current behavior understood before editing.
- [ ] Changes kept on the correct branch/worktree.
- [ ] Tests or a documented manual verification run.
- [ ] Diff reviewed; no unrelated files changed.
- [ ] No credentials, private data, or generated secrets committed.
- [ ] Relevant roadmap/audit/session notes updated.
- [ ] Remaining risks and next task recorded.

## 6. How progress will be measured

Track working capabilities, not the number of agents or lines of code:
- Can a run be reconstructed from persisted events?
- Can a tool be denied before execution?
- Can an agent be stopped at a hard budget?
- Can one coding worker be isolated from the rest of the machine and other workers?
- Can QA catch a deliberately introduced defect?
- Can the dashboard distinguish a model claim from verified evidence?
- Can a provider/runtime be replaced without rewriting the rest of JARVIS?

A milestone is complete only when its exit criteria are demonstrated and the repository reflects the actual implementation.
