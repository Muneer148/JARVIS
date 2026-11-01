# JARVIS agent operating model

**Default pattern: Hermes plans, Paperclip coordinates the workforce, and JARVIS enforces security. Swarm handoffs are optional and bounded—not the default architecture.**

JARVIS is the product and primary user interface. The user normally speaks/types only to JARVIS. Hermes decomposes goals and replans; Paperclip manages worker-agent lifecycle and task coordination. JARVIS—not Paperclip—owns threat assessment, security policy, authorization, privacy, approvals, and containment.

## 1. Why multiple agents?

Multiple agents are useful when tasks genuinely need different capabilities, independent review, or separable work. Merely launching more model calls does not make a system better. It can increase token usage, latency, coordination cost, conflicting edits, and error propagation.

The project should first make one agent and one deterministic tool reliable, then add one bounded worker, then introduce multi-agent handoffs only where measured value exists.

## 2. Role definitions

| Role | Input | Output | Write access |
|---|---|---|---|
| Paperclip workforce control plane | Hermes task graph, JARVIS-approved constraints | Agent lifecycle, task assignment/status, scheduling, workspace/lock management, workflow history | Paperclip coordination state only; no security-policy authority |
| Hermes planner/reasoner | User request, relevant context, policy limits | Concise plan, acceptance criteria, task briefs, risk notes | No unrestricted project writes |
| Research worker | Read-only task brief and approved sources | Findings with source/evidence references | Read-only by default |
| Coding worker | One owned task, assigned worktree, allowed tools | Diff, implementation notes, test evidence | Only its assigned worktree |
| QA Sentinel | Acceptance criteria, diff, test access, evidence | Pass/fail findings, defects, test results | Read-only; may create reports, not silently rewrite worker code |
| Human operator | Approval request, evidence, risk, scope | Approve, deny, or request changes | Final authority for sensitive actions |

Claude Code, OpenCode, and DeepSeek Harness are candidate worker runtimes, not assumed-installed dependencies. Each needs an adapter, protocol test, permission profile, and kill/timeout behavior before it is used.

## 3. Workflow patterns

### A. Sequential workflow — default for dependent work

Example:

1. Hermes defines the problem and acceptance criteria.
2. Research worker gathers facts or inspects the repository.
3. Hermes turns findings into one implementation brief; Paperclip records and coordinates the assigned work.
4. One coding worker owns and changes the files.
5. QA Sentinel runs tests and reviews the diff.
6. Human approves integration or any consequential action.
7. JARVIS reports evidence and unresolved risks.

This pattern is predictable, easy to audit, and appropriate for most coding and troubleshooting tasks.

### B. Parallel fan-out — only for independent read tasks

Paperclip may schedule independent read-only subtasks to multiple workers, for example:
- Worker A inspects the API layer.
- Worker B inspects the permission model.
- Worker C checks the test suite.

A synthesis step compares results and resolves contradictions. Parallel workers do not write to the same files. Parallel execution must be bounded by worker count, time, and token budget.

### C. Swarm handoff — optional specialist-to-specialist delegation

A swarm is not simply several agents running simultaneously. In a swarm pattern, an agent can hand control to another agent based on a capability decision; the receiving agent continues the task and may hand it onward.

Use this only when dynamic specialist handoffs are more valuable than a predetermined task graph. Example: a researcher hands a finding to a security analyst, who hands a validated change request to a coder, who returns to QA. The handoff target, allowed roles, shared context, and termination criteria must be explicit.

A swarm can become difficult to predict if the agents keep handing off. Enforce:
- a maximum number of handoffs/turns;
- a maximum number of agents per run;
- a token or monetary budget;
- a wall-clock deadline;
- an allowlist of handoff targets;
- a retry limit and failure state;
- explicit completion and stop conditions;
- approval gates for privileged actions.

AutoGen's documentation describes Swarm handoffs and the need for termination conditions; its termination guide includes turn, token, and timeout limits. This project will evaluate patterns and libraries before selecting one; it will not adopt a framework solely because it has a swarm feature. References: [AutoGen Swarm](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html), [AutoGen termination](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html), and [LangGraph supervisor/swarm packages](https://reference.langchain.com/python/langgraph/overview).

## 4. Task contract

Every delegated task must be represented by a structured contract containing:

- run ID, task ID, parent task ID, and correlation/trace IDs;
- owner agent and role;
- goal and concise context;
- allowed tools and permission scope;
- workspace ID and permitted file scope;
- dependencies and handoff targets;
- acceptance criteria and required evidence;
- maximum turns, retries, time, and token/cost budget;
- status: queued, running, waiting_approval, blocked, failed, completed, or cancelled.

A worker must return a structured result:
- outcome and status;
- files/artifacts produced;
- commands/tools used;
- tests run and exact results;
- assumptions and evidence;
- risks and unresolved questions;
- recommended next handoff, if any.

A natural-language statement such as “done” is not a completion signal. Paperclip checks task/workflow state and required evidence references; JARVIS independently enforces security policy, and QA Sentinel verifies deliverables.

## 5. Ownership and write-conflict rules

1. One task has one write owner.
2. Each coding worker gets its own Git worktree or equivalent isolated workspace.
3. Two workers must not modify the same working tree concurrently.
4. Parallel read-only analysis is allowed when access is scoped.
5. QA and reviewers do not silently change the implementation they are reviewing.
6. If two tasks need the same file, Paperclip serializes the writes or creates a merge/integration task.
7. Only the integration step can propose merging a task branch, and the human retains final approval.

## 6. JARVIS security and human approval boundaries

Paperclip may represent workflow review states and surface approval requests, but it is not the security assessor or policy authority. JARVIS evaluates the requested action, enforces authorization at execution time, applies privacy/network/workspace rules, and decides whether human approval is required. Paperclip cannot approve an action on JARVIS's behalf.



The JARVIS-owned default policy is human approval before:
- deleting, overwriting, or moving user data outside a narrowly defined reversible workflow;
- installing software, packages, extensions, or system services;
- executing commands with broad system impact;
- accessing or using credentials, cookies, private keys, or sensitive accounts;
- sending messages, uploading files, purchasing, publishing, or triggering external side effects;
- accessing network destinations outside the task allowlist;
- changing firewall, OS, account, security, or persistence settings;
- merging to protected branches or deploying.

Read-only analysis within an assigned repository may run automatically when the policy allows it. Approvals must be logged with exact scope, decision, approver, and time. Approval is bound to that action; it is not a blanket grant for later actions.

## 7. Failure and recovery

- Model/provider failure: record the failed provider and fallback route; never silently change models without an event.
- Worker timeout: stop the task, preserve partial artifacts, and mark the run state.
- Invalid tool arguments: reject before execution and return a structured error.
- Approval denied: do not execute; record the denial and explain the blocked action.
- QA failure: return a bounded defect report to the assigned owner; do not allow endless self-repair loops.
- Conflicting changes: stop integration, compare diffs, and resolve through an explicit owner.
- Budget or handoff limit reached: stop safely and return partial evidence, not a fabricated success.

## 8. First multi-agent vertical slice

The first useful demonstration should be deliberately small:

1. User asks JARVIS to inspect a small repository and identify one bounded improvement.
2. Hermes writes a concise plan and acceptance criteria.
3. Paperclip assigns one read-only research/inspection worker.
4. The worker returns findings with file and line references.
5. Paperclip assigns one coding worker to one isolated worktree for a small change.
6. QA Sentinel runs the relevant tests and inspects the diff.
7. The dashboard displays the real task handoffs, model calls, tool events, test outcome, and approval state.
8. The user decides whether to integrate the change.

Do not start with five coding agents, recursive spawning, autonomous deployment, or multiple runtimes editing the same project.
