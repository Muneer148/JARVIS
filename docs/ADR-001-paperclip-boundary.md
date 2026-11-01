# ADR-001: JARVIS, Hermes, and Paperclip ownership boundary

- **Status:** Accepted target architecture
- **Date:** 1 November 2026
- **Scope:** Architecture and responsibility boundaries; no runtime integration is implied.

## Decision

JARVIS is the product, primary user interface, personal assistant, and system-level security authority. Paperclip is an internal JARVIS subsystem for managing the agent workforce. JARVIS is never registered as an agent managed by Paperclip.

The normal request path is:

`User → JARVIS → Hermes → Paperclip → worker agents → Paperclip → Hermes → JARVIS → User`

Voice and text are two interfaces into the same JARVIS request/session layer. They do not create separate agents or bypass policy.

## Responsibilities

### JARVIS owns
- User interaction, conversation/session state, and final response synthesis.
- Voice input/output interface and its privacy controls.
- Security policy, threat assessment, permission checks, and authorization at execution boundaries.
- Data sensitivity classification and external-provider privacy gates.
- Human approval policy and action-bound approval enforcement.
- Audit/detection, security-event interpretation, isolation requirements, and containment.
- Independent coordination of QA Sentinel and verification requirements.

### Hermes owns
- Understanding the request and planning/replanning.
- Decomposing goals into tasks and dependencies.
- Defining task briefs, owners/roles, acceptance criteria, budgets, and evidence requirements.
- Reviewing worker results and deciding whether the plan needs revision.

Hermes plans; it does not grant itself permissions or bypass JARVIS policy.

### Paperclip owns
- Internal agent organisation and worker lifecycle.
- Task assignment/status, scheduling/heartbeats, task dependencies and workflow coordination.
- Workspaces, Git worktrees/task locks, budgets, reviews, and work history.
- Reporting execution/workflow events to JARVIS.

Paperclip is not the security assessor, policy engine, approval authority, or primary user interface. A Paperclip review state is not proof that an action is safe or authorized.

### Worker agents own
- Only their assigned, bounded task and workspace.
- Returning outputs, artifacts, tool records, test evidence, and unresolved risks.
- They cannot expand their own permissions, task scope, network access, or budget.

### QA Sentinel owns
- Independent verification against acceptance criteria.
- Reporting test results, defects, and evidence.
- It does not silently approve its own implementation or override JARVIS policy.

## Security enforcement rule

All consequential tool/runtime actions must pass through JARVIS-owned authorization at the actual execution boundary, regardless of whether the request originated from Hermes, Paperclip, or a worker. Paperclip may coordinate and report; it cannot authorize. Do not rely on post-hoc logs, dashboard warnings, or workflow approvals as a substitute for pre-execution enforcement.

## Voice interface decision

JARVIS may have a spoken interface. The initial pipeline is push-to-talk microphone capture → speech-to-text → ordinary JARVIS request/session path → ordinary policy/planning/execution flow → text-to-speech → playback. Voice must not bypass approval or permission checks. Wake-word activation is deferred until recording indicators, privacy controls, and local processing boundaries are designed.

The existing `feature/voice-assistant` branch is an incomplete draft/interface foundation. It must be inspected and selectively ported to the current development line; do not merge it wholesale or describe it as a working voice feature.

## Consequences

- Hermes and Paperclip do not compete: Hermes plans/replans; Paperclip coordinates the workforce.
- The Agent Operations Console correlates JARVIS security telemetry with Paperclip workflow events.
- Paperclip can be replaced without changing JARVIS's security authority or user interface.
- This ADR defines the target architecture; it does not claim these integrations are implemented.
