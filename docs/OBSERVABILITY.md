# JARVIS Agent Operations Console and telemetry

**Product definition:** a JARVIS-owned Agent Operations Console with SOC-inspired investigation UX for JARVIS, Hermes, Paperclip, worker agents, runtimes, models, tools, and security controls. It is not a full SOC or SIEM in the first release. Security assessment and enforcement remain in JARVIS; Paperclip is only one telemetry/workflow source.

## 1. Purpose

The console should let the user answer, after or during any run:

- What did I ask JARVIS to do?
- Which plan was created, and which agent owns each task?
- Which agents, model providers, and models were used?
- What tools and commands were requested and actually executed?
- Which files changed, in which workspace, and on which branch?
- Which actions were blocked or required human approval?
- Which tests and security checks ran, and what was their result?
- Where did the run fail, retry, fall back to another model, or stop?
- What evidence supports the final answer?

The console also serves as a learning surface for log analysis, event correlation, timeline reconstruction, and investigation of unusual agent behavior.

A dashboard is not a security control by itself. It becomes useful only when real components emit reliable, structured events and the underlying policy actually blocks unsafe actions.

## 2. Initial dashboard layout

### A. Run overview
- Active, queued, paused-for-approval, completed, failed, and cancelled runs.
- Run duration and task count.
- Token/cost totals only when returned by the provider and correctly attributed.
- Budget usage and stop reason.

### B. Agent activity stream
A chronological stream of actual events, for example:
- Hermes created a plan.
- Paperclip assigned task T-014 to the researcher.
- Research worker fetched an approved source.
- Paperclip handed task T-014 to a coding worker.
- The coder changed three files in worktree W-03.
- QA Sentinel reported one failing test.
- The task owner submitted a fix.
- QA passed; run is waiting for integration approval.

Every event must link to its run and task. Agent names must identify the component that emitted the event, not just the model's self-description.

### C. Trace timeline
Expand one run into a causal timeline:
- user request and policy decision;
- plan and task creation;
- agent start/finish and handoffs;
- model request/response metadata;
- tool invocation and result;
- approval pause and decision;
- tests, review, artifacts, and final state.

### D. Tool and command audit
Show tool name, redacted arguments, permission scope, requesting agent/task, workspace, start/end time, status, result summary, and evidence link. Never show raw secrets or full environment variables.

### E. Approval queue
Show pending actions with requester, exact target, permission requested, risk, reason, expected side effects, evidence, and explicit approve/deny/cancel actions. A queued approval is not a completed action.

### F. Model/provider health
Show selected provider/model, adapter/runtime, latency, timeout/error, fallback, token usage when available, and rate-limit/cooldown state. Distinguish gateway failure from model output failure.

### G. JARVIS security events

Security findings, policy decisions, and containment actions are produced and owned by JARVIS. Paperclip can contribute task/agent lifecycle events, but it must not perform or approve security assessments.


Examples include policy denial, attempted out-of-workspace access, forbidden network target, secret-redaction event, repeated failed tool calls, retry-loop threshold, unexpected worker spawn, and suspicious command request.

Label each record as:
- **Observed:** directly recorded by a tool, runtime, test, or policy decision.
- **Derived:** computed from multiple observed events or thresholds.
- **Unverified:** a model claim not yet supported by tool or test evidence.

Do not manufacture alerts or activity to make the interface look busy.

## 3. Logs, metrics, and traces

These are related but different telemetry signals.

| Signal | What it answers | Example |
|---|---|---|
| Log/event | What happened at a particular time? | Tool call denied by policy |
| Metric | How often or how much? | 12 failed tool calls today; median model latency |
| Trace | How did one request move through the system? | User → JARVIS → Hermes → Paperclip → worker → model → tool → QA |

A trace is composed of spans. A span represents an operation with a start/end time, attributes, and parent context. Logs should carry the trace and span IDs when possible so that events from separate processes can be correlated.

Use a shared run ID, trace ID, task ID, agent ID, and span/parent-span IDs across the system. See [OpenTelemetry logs](https://opentelemetry.io/docs/concepts/signals/logs/), [OpenTelemetry log correlation](https://opentelemetry.io/docs/specs/otel/logs/), and [OpenTelemetry traces](https://opentelemetry.io/docs/specs/otel/overview/).

## 4. Event contract

Use versioned, structured events. The initial event contract should contain:

| Field | Purpose |
|---|---|
| schema_version | Allows the event format to evolve |
| event_id | Unique event identifier |
| timestamp | UTC event time in RFC 3339 format |
| event_name | Stable event type, such as tool.execution.completed |
| severity | DEBUG, INFO, WARN, or ERROR |
| source_component | Component that emitted the event |
| run_id | End-to-end JARVIS request |
| trace_id / span_id / parent_span_id | Correlates operations across runtimes |
| task_id / parent_task_id | Identifies delegated work |
| agent_id / agent_role | Runtime instance and its role |
| provider / model / adapter | Actual model route used, when applicable |
| tool_name | Tool that was requested or executed |
| permission_scope | Permissions and path/network scope |
| approval_id / approval_state | Approval linkage where relevant |
| workspace_id / branch | Coding workspace identity |
| status | queued, started, success, blocked, failed, cancelled, etc. |
| duration_ms | Measured execution duration |
| usage | Provider-reported input/output tokens or cost, if supplied |
| artifact_refs | Links to diff, report, test output, or evidence |
| summary | Short redacted human-readable statement |
| error_code | Stable machine-readable failure classification |

Example event:

```json
{
  "schema_version": "1.0",
  "event_id": "evt-example",
  "timestamp": "2026-10-31T12:00:00Z",
  "event_name": "tool.execution.completed",
  "severity": "INFO",
  "source_component": "worker-runtime",
  "run_id": "run-example",
  "trace_id": "trace-example",
  "span_id": "span-tool",
  "parent_span_id": "span-worker",
  "task_id": "task-example",
  "agent_id": "agent-coder-01",
  "agent_role": "coder",
  "provider": "configured-gateway",
  "model": "configured-model-id",
  "tool_name": "filesystem.write",
  "permission_scope": ["write:assigned-worktree"],
  "approval_id": null,
  "workspace_id": "worktree-example",
  "branch": "task/example",
  "status": "success",
  "duration_ms": 420,
  "usage": {"input_tokens": null, "output_tokens": null, "cost": null},
  "artifact_refs": ["artifacts/diff.patch"],
  "summary": "Wrote one file inside the assigned worktree.",
  "error_code": null
}
```

The example is illustrative. Do not write guessed token or cost values; use null when a provider does not expose them.

## 5. Event taxonomy

Use stable event names grouped by lifecycle:

- Run: run.created, run.started, run.paused, run.completed, run.failed, run.cancelled.
- Plan: plan.created, plan.revised, plan.approved.
- Task: task.created, task.assigned, task.started, task.handoff, task.blocked, task.completed, task.failed.
- Agent: agent.started, agent.stopped, agent.spawned, agent.limit_reached.
- Model: model.requested, model.completed, model.failed, model.fallback, model.rate_limited.
- Tool: tool.requested, tool.authorized, tool.denied, tool.started, tool.completed, tool.failed.
- Approval: approval.requested, approval.granted, approval.denied, approval.expired, approval.cancelled.
- Workspace: workspace.created, workspace.changed, workspace.diff_collected, workspace.cleaned.
- QA: test.started, test.passed, test.failed, review.completed, scan.finding.
- Security: security.policy_denied, security.scope_violation, security.secret_redacted, security.network_blocked, security.loop_threshold.
- Artifact: artifact.created, artifact.verified, artifact.rejected.

An event should be emitted by the component that can actually observe the action. Do not infer that a command executed just because an LLM requested it.

## 6. Storage and pipeline rollout

Start small and local:
1. Define an event schema and one central event-writing interface.
2. Instrument the current single-agent CLI: run start/end, provider selection/fallback, tool requested/authorized/denied/executed, and exceptions.
3. Persist run/task state and events locally with SQLite. Treat the event table as append-only at the application/API level; the dashboard uses read-only access.
4. Store bulky test outputs, diffs, and reports as run artifacts; link to them from events.
5. Add filters and a simple CLI event viewer before building the graphical dashboard.
6. Add run/trace/span propagation when Hermes, Paperclip, and worker runtimes are connected.
7. Evaluate OpenTelemetry instrumentation/export only when it makes cross-process correlation easier. Do not start by deploying a large SIEM/logging stack.

## 7. Metrics worth collecting

- Run success/failure/cancellation rate.
- Mean and percentile run/task duration.
- Model request latency, error rate, fallback rate, and rate-limit events.
- Tokens and costs where provider-reported values are available.
- Tool invocation count and error/denial rate.
- Approval wait time and approval/denial totals.
- Test pass/fail rate and retry count.
- Agent handoffs per run and loop/limit events.
- Workspace cleanup and rollback outcome.

Metrics must have clear definitions. For example, do not call an API response successful if the requested task later failed verification.

## 8. Security and privacy rules for telemetry

Never record:
- API keys, passwords, access tokens, cookies, private keys, or credential values;
- complete process environments;
- hidden chain-of-thought or private internal model reasoning;
- unnecessary raw user documents, private messages, or full prompt transcripts;
- unredacted tool arguments that may contain secrets.

Record concise plan summaries, action justifications, tool metadata, safe argument summaries, outcomes, and evidence references. Redact before persistence, not merely at display time. Restrict access to run data, define a retention policy, and protect the event store from casual modification.

## 9. First dashboard acceptance criteria

The first usable console is complete when a single real run can be opened and reconstructed with:
- run summary and final status;
- ordered event stream with source component and timestamps;
- task ownership and handoff path;
- provider/model and fallback information;
- tool invocation, permission decision, and result;
- approval state;
- test output and artifact references;
- failures and stop reasons.

No multi-agent UI should be built with fake events. First instrument one real request end-to-end, then add the graphical view.
