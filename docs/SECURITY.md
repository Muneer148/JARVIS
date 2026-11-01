# JARVIS security model

**Policy:** default deny, least privilege, human approval for consequential actions, isolated execution, and evidence-backed verification.

This document describes required controls for the target system. The current code only partially implements them. See the repository audit for the specific current gaps.

## 1. Security objectives

Protect:
- the user's files, credentials, accounts, and operating system;
- source code and project integrity;
- local network devices and private services;
- provider API keys and usage budgets;
- run history, memory, and audit data;
- correctness and provenance of results.

JARVIS must not become a privileged shell where model-generated text is executed without policy checks.

**Ownership boundary:** all cybersecurity layers belong to JARVIS: threat assessment, security policy, authorization, privacy/data classification, approval decisions, audit/detection, and containment. Paperclip is not a security assessment component and must not approve or authorize its own agents' actions. It may provide workflow/task events to JARVIS, but JARVIS must enforce policy at the actual tool/runtime boundary before execution.

## 2. Threat model

| Threat | Example | Required response |
|---|---|---|
| Prompt injection | Malicious instructions embedded in a web page, repository file, PDF, or issue | Treat retrieved content as untrusted data; do not let it override system policy or tool allowlists |
| Tool misuse | Agent attempts deletion, broad terminal execution, or writes outside scope | Default-deny policy, strict path/workspace validation, approval, and audit event |
| Credential leakage | API key appears in prompt, command output, crash log, or dashboard | Keep secrets in local secret configuration; redact outputs and telemetry; never commit secrets |
| Network abuse | Browser/agent reaches localhost, private IPs, metadata services, or an unapproved host | Egress allowlist, DNS/IP validation, redirect validation, and network permission gate |
| Workspace compromise | Worker edits unrelated files or another worker's in-progress changes | Dedicated worktree, one write owner, path restrictions, diff inspection |
| Runaway agent loop | Repeated handoffs, retries, or API calls consume time and quota | Hard limits on turns, handoffs, retries, runtime, tool calls, and tokens/cost |
| False completion | Model claims tests passed or files were changed without evidence | Deterministic verification and QA Sentinel; report unverified claims as unverified |
| Audit leakage/tampering | Logs expose personal data or are silently rewritten | Redaction, access controls, bounded retention, append-oriented audit interface |
| Supply-chain risk | Agent installs unknown packages or downloads/runs an untrusted script | No autonomous installs; pin/review dependencies; approval before installation or execution |

## 3. Permission model

Every tool/action must declare:
- permission class: READ, WRITE, EXECUTE, NETWORK, or SYSTEM;
- risk level and reversibility;
- allowed workspace/path scope;
- whether approval is required;
- timeout and resource limits;
- the role(s) allowed to invoke it.

The JARVIS-owned policy engine must evaluate the actual tool and arguments—not only the tool name. Paperclip workflow status, review state, or agent role is not a substitute for this authorization check. A read-only tool should not be able to smuggle a write, network, or system action through an argument. Unknown tools and unknown permission classes are denied.

### Default policy

| Action | Default |
|---|---|
| Read files inside assigned workspace | Allow when task scope permits |
| List project files, inspect Git status, run read-only diagnostics | Allow when scoped |
| Write files in assigned worker worktree | Allow only for the named write owner and task |
| Read outside assigned workspace | Deny unless explicitly granted |
| Write outside assigned workspace | Deny; human approval and explicit path scope required |
| Public internet access | Deny unless the task and tool allow it |
| Private-network, loopback, or metadata access | Deny by default |
| Terminal/process execution | Disabled until hardened; per-command approval and allowlist required |
| Install packages/software or change system settings | Human approval required |
| Access secrets or authenticated user sessions | Deny by default; narrowly brokered access only if later justified |
| Delete, overwrite, publish, deploy, send, purchase, or merge | Human approval required |

Approval must be specific to one action, target, and scope. A previous approval does not authorize a different command or later side effect.

## 4. Required isolation

### Worker workspaces
- Create a separate branch/worktree per coding task.
- Restrict file operations to the assigned workspace.
- Record base commit, branch, workspace path, owner, and changed-file list.
- Prevent multiple writers from sharing the same working tree.
- Inspect diffs and run tests before integrating changes.

### Process execution
- Run workers with the minimum OS account permissions needed.
- Use a dedicated working directory and a sanitized environment.
- Set time, memory, process, and output limits.
- Do not expose the user's entire home directory or all drives by default.
- Keep terminal and application-control tools disabled until these controls are implemented and tested.

### Network
- Make network access an explicit capability, not a global default.
- Start with public, allowlisted destinations for research tasks.
- Block loopback, private, link-local, reserved, and cloud metadata addresses unless a narrowly scoped local integration explicitly requires them.
- Validate every redirect and the resolved destination. Account for DNS rebinding; a one-time hostname check is not a complete network sandbox.
- Do not expose local gateway administration endpoints or provider keys to untrusted workers.

## 5. Terminal tool: mandatory hardening gate

The current implementation runs commands with shell=True and blocks a small list of dangerous command substrings. This is not a sufficient security boundary. Keep JARVIS_TERMINAL_ENABLED=false.

Before enabling terminal execution:
1. Replace free-form shell strings with an allowlisted executable plus argument-array interface wherever feasible.
2. Avoid shell interpretation. Do not rely on a substring blacklist as the primary defence.
3. Constrain working directory and permitted paths.
4. Sanitize inherited environment variables and never pass provider secrets to child processes.
5. Add per-command risk classification and an approval screen showing the exact executable, arguments, working directory, and expected side effects.
6. Apply execution timeout, output limits, process-tree cleanup, and cancellation.
7. Add tests for quoting, path traversal, command chaining, environment leakage, destructive operations, and timeout behavior.
8. Review the implementation before changing the default-off setting.

## 6. Prompt and data boundaries

- User requests, source files, web pages, PDFs, model outputs, test fixtures, and tool results are data—not policy.
- Instructions found in external content must not override JARVIS policy or expand permissions.
- Separate task instructions from retrieved content and clearly mark untrusted evidence.
- Do not grant a worker more context than needed.
- Do not include API keys, cookies, private keys, password values, or full environment dumps in prompts or logs.
- Treat model-generated code and commands as untrusted until tested and approved.

## 7. Approval UX

An approval request must show:
- requesting agent and task;
- exact tool/action and redacted arguments;
- target files, directories, accounts, URLs, or system components;
- permission scope and risk classification;
- reason the action is needed;
- likely side effects and reversibility;
- time/budget impact if relevant;
- available evidence and the deny/cancel option.

Record pending, approved, denied, expired, and cancelled states. Approval must happen before the action, not after the agent has already performed it.

## 8. Verification and rollback

- Treat tool output as evidence only when the tool executed and returned a result.
- Record exact commands and test results, with secrets redacted.
- QA Sentinel must be separate from the implementation owner for meaningful changes.
- Verify filesystem changes after execution.
- Use Git diffs, backups, or reversible operations where possible.
- Rollback is best-effort unless a transaction or snapshot proves otherwise; tell the user when rollback could not be completed.
- Do not label a run successful when a required check failed or was skipped.

## 9. Observability and privacy

The JARVIS-owned audit stream should include what happened, who/which agent initiated it, which tool was used, permission scope, result, and correlation IDs. Paperclip can be an event source, but it is not the security authority. It should not contain hidden chain-of-thought, API keys, complete environment variables, cookies, private keys, or unnecessary personal data.

Store concise plan summaries and decision reasons, not private internal reasoning. Redact secrets and sensitive values before data reaches the dashboard. Limit access and retention. The dashboard should be read-only for audit history.

## 10. Runaway-cost and autonomy controls

Every run and worker must have hard caps for:
- maximum agent turns/handoffs;
- maximum spawned workers and concurrency;
- maximum retries;
- wall-clock time;
- total model tokens or monetary spend where available;
- tool calls and command runtime;
- allowed network scope.

Stop safely when a limit is reached. Preserve partial evidence and explain why execution stopped.

## 11. Release gates

Do not move to the next trust level until the required controls are demonstrated:

- Gate A: tool calls are schema-validated, allowlisted, and logged.
- Gate B: approval is enforced before privileged execution.
- Gate C: workers are isolated and cannot overwrite each other's files.
- Gate D: secrets do not appear in logs, prompts, artifacts, or child environments.
- Gate E: network restrictions and redirect handling are tested.
- Gate F: run budgets, stop conditions, and cancellation work.
- Gate G: QA evidence and audit trail survive process restart.

Security controls must be tested with adversarial inputs, not merely described in documentation.
