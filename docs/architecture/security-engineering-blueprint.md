# JARVIS Security Engineering Blueprint

**Status:** Proposed architecture and engineering requirements  
**Scope:** Security of the JARVIS platform and safe provision of cybersecurity assistance  
**Principle:** Security is a core property of the platform, not an optional agent or a collection of prompt instructions.

## 1. Executive position

Security controls are common in AI-agent projects, but the presence of approvals, guardrails, sandbox options or audit logs does not by itself establish cybersecurity-grade engineering.

JARVIS must be designed so that a manipulated, misconfigured or compromised agent cannot independently grant itself privileges, access arbitrary data, execute unrestricted commands, or bypass the authorization boundary.

The system should be treated as a security-sensitive application that happens to use AI—not as an AI application that receives security later.

This document is a proposed engineering baseline. It is not a certification, penetration-test report, or claim that the current implementation already satisfies every requirement.

## 2. Two distinct cybersecurity responsibilities

JARVIS should support two related but separately governed capabilities.

### A. Security of JARVIS — defensive platform engineering

JARVIS protects its own users, data, models, integrations and execution environment.

Responsibilities include:

- Protect agent identities, credentials and sessions.
- Enforce least-privilege access to tools and data.
- Detect suspicious or unexpected agent behaviour.
- Prevent prompt injection from becoming unauthorized tool execution.
- Protect memory from poisoning, unauthorized writes and cross-user leakage.
- Restrict network egress and access to local services.
- Audit dependencies, models, plugins and MCP servers.
- Record evidence for sensitive actions.
- Revoke access and contain a compromised component.
- Recover safely after failed or malicious operations.

### B. Cybersecurity assistance — operational capability

JARVIS can help an authorized operator perform legitimate security work.

Potential capabilities include:

- SOC alert triage and investigation.
- Log analysis and threat hunting.
- Vulnerability assessment.
- Secure code review and application security analysis.
- Network inventory and monitoring.
- Incident investigation and reporting.
- Threat intelligence research.
- Authorized penetration-testing support.
- Security documentation and remediation tracking.

These capabilities must operate under explicit scope, authorization, rate limits and evidence requirements. The cybersecurity agent must not be exempt from JARVIS's own policy engine.

## 3. Proposed architecture

The AI hierarchy is not the security boundary. All agent actions that affect resources must pass through an independent control plane.

```text
                    User / Trusted Interface
                              |
                              v
                     JARVIS Agent Hierarchy
             Executive -> Supervisors -> Specialists
                              |
                              v
                 Untrusted Action Proposal
                              |
                              v
                INDEPENDENT SECURITY CONTROL PLANE
       Identity | Policy | Authorization | Risk | Approval
                              |
                              v
                    Validated Tool Broker
                              |
                              v
                 Isolated Execution Environments
       Filesystem | Terminal | Browser | APIs | MCP | Labs
                              |
                              v
                Verification + Evidence Collection
                              |
                              v
                   Audit / Alert / Recovery
```

The model may propose an action. It must not be the authority that decides whether the action is permitted. Authorization must be enforced by deterministic trusted code outside the model's control.

## 4. Security control plane

The control plane should be a JARVIS-owned subsystem with a narrow, testable interface.

### 4.1 Agent identity

Every agent and service should have an explicit identity.

An identity record should include:

- Stable agent/service identifier.
- Agent type and owning supervisor.
- Allowed task categories.
- Granted capabilities and resource scopes.
- Credential references, never raw secrets in prompts.
- Expiration or revocation state.
- Audit identity for every action.

Do not treat an agent's name, role description or self-reported identity as authentication.

### 4.2 Authorization and least privilege

Use deny-by-default authorization.

Permissions should be scoped by:

- **Principal:** which agent or service is acting.
- **Action:** read, write, execute, delete, transmit, configure, etc.
- **Resource:** exact files, folders, hosts, services or records.
- **Context:** task, environment, user approval and risk level.
- **Time:** short-lived grants where practical.

An agent should receive only the permissions required for its current task. A permission granted to one specialist must not automatically flow to its supervisor, sibling agents or delegated subagents.

### 4.3 Policy enforcement

The policy engine must be independent of the LLM and must validate every tool call at execution time.

It should check:

1. Authenticated principal.
2. Requested action and target resource.
3. Explicit scope and current permission.
4. Input schema and argument constraints.
5. Risk classification.
6. Approval requirement and approval validity.
7. Environment restrictions and resource limits.
8. Whether the action is still valid at execution time.

A natural-language statement such as “the user approved this” is not approval evidence. Approval must be represented by a trusted, attributable authorization record tied to the exact action or bounded action plan.

### 4.4 Risk-based approval

Suggested initial policy:

| Risk class | Example | Default handling |
|---|---|---|
| R0 — Read-only, low impact | Read an explicitly permitted project file | Allow within scope; log |
| R1 — Reversible, bounded | Create a file in an approved workspace | Validate; log; optionally approve by policy |
| R2 — Sensitive or externally visible | Send data to an external service, install a dependency, modify shared configuration | Explicit user approval and constrained execution |
| R3 — Destructive or privileged | Delete data, change security settings, execute privileged commands, alter firewall rules | Strong explicit approval, narrow scope, preflight and recovery plan |
| R4 — Prohibited or unauthorized | Credential theft, unauthorized access, evasion, destructive actions outside authorized scope | Deny |

Risk levels are an initial policy proposal; the actual matrix must be refined and tested against real tools and threat models. Approval does not make an otherwise prohibited action permissible.

## 5. Execution isolation

An agent should not execute arbitrary code with the same privileges as the JARVIS host process.

Required design direction:

- Separate the agent runtime from the tool execution broker.
- Use dedicated workspaces with explicit mount permissions.
- Prefer disposable containers or VMs for untrusted code.
- Restrict CPU, memory, process count, runtime and disk usage.
- Apply network egress allowlists or deny network access by default.
- Do not mount host home directories, SSH folders, browser profiles or secret stores into untrusted sandboxes.
- Run processes as unprivileged users.
- Keep privileged operations behind narrow, audited helpers.
- Destroy or reset disposable environments after use.
- Verify outputs before copying artifacts into trusted locations.

gVisor is a candidate to study for stronger container workload isolation; it is not a substitute for correct configuration, host hardening or threat modelling.

## 6. Data and secrets protection

### 6.1 Data classification

Classify resources before granting access. A proposed initial set:

- Public.
- Internal project data.
- Personal/private data.
- Confidential credentials and secrets.
- Security-sensitive operational data.

Agents should receive only the minimum classification needed for their task.

### 6.2 Secret handling

- Store secrets in a dedicated OS-backed or encrypted secret store.
- Give tools short-lived credential references where feasible.
- Never place API keys, passwords, tokens, cookies or private keys in prompts, logs, source code or committed configuration.
- Redact secrets from traces and exception messages.
- Rotate and revoke credentials after suspected exposure.
- Keep provider credentials separate from agent memory.

### 6.3 Memory security

Persistent memory is a data store and must be secured like one.

- Attribute each memory to its source, time and writer.
- Distinguish user-confirmed facts from model-inferred facts.
- Preserve provenance and confidence.
- Restrict which agents may write or update memory.
- Require validation for sensitive or high-impact memory changes.
- Prevent untrusted web pages, files or tool output from silently becoming trusted user instructions.
- Support correction, deletion and retention policies.
- Prevent cross-user or cross-project memory leakage.

## 7. AI-specific threat model

JARVIS should explicitly test for:

| Threat | Example | Required control |
|---|---|---|
| Direct prompt injection | User-supplied instruction attempts to override policy | Policy outside model; instruction hierarchy; action validation |
| Indirect prompt injection | A web page, PDF, email or repository tells the agent to exfiltrate data | Treat retrieved content as untrusted data; isolate instructions from evidence |
| Tool misuse | Agent invokes a tool beyond the task's scope | Broker-side authorization on every call |
| Excessive agency | Agent chains many individually plausible actions into a harmful result | Task budgets, step limits, risk checks and approval |
| Memory poisoning | Malicious content is stored as a trusted preference or instruction | Provenance, trust labels, write permissions and review |
| Credential leakage | Secret appears in a prompt, trace, output or tool argument | Secret vault, redaction and scoped credentials |
| Cross-agent privilege escalation | Specialist asks another agent to perform a forbidden action | Independent identity and authorization for every principal |
| Supply-chain compromise | Malicious dependency, plugin, model or MCP server | Pinning, provenance, scanning, review and isolation |
| Data exfiltration | Agent sends local files to an external endpoint | Egress policy, data classification and approval |
| Unsafe code execution | Model-generated code runs on the host | Disposable sandbox, unprivileged execution and resource limits |

A guardrail model can provide an additional detection signal, but it must not be the only control preventing any of these attacks.

## 8. Audit, observability and incident response

For every consequential action, retain a structured record sufficient to reconstruct what happened:

- Timestamp and task identifier.
- Authenticated agent/service identity.
- User or supervisor initiating the task.
- Proposed action and validated arguments.
- Target resource and scope.
- Policy decision and reason.
- Approval identity and exact approved action, if applicable.
- Execution environment and tool version.
- Actual result and verification result.
- Rollback or recovery outcome.
- Relevant model/provider metadata, with secrets and sensitive content redacted.

Logs should be access-controlled and protected against unauthorized modification. Avoid storing more personal or confidential data than needed.

### Incident containment

JARVIS should be able to:

1. Stop a running task.
2. Revoke an agent's short-lived permissions.
3. Disable a tool, integration or MCP server.
4. Block suspicious network egress.
5. Quarantine an execution workspace.
6. Preserve relevant evidence.
7. Restore trusted files from verified backups or rollback data.
8. Require explicit operator review before resuming.

A model-generated statement that an incident has been contained is not evidence. The system must verify the actual state.

## 9. Security validation and testing

Security must be tested continuously, not inferred from architecture diagrams.

### 9.1 Required test families

- Unit tests for policy decisions and permission boundaries.
- Integration tests proving every tool call passes through the broker.
- Negative tests for denied actions.
- Prompt-injection tests using hostile web pages, PDFs, email and repository files.
- Cross-agent privilege escalation tests.
- Secret-leakage tests across prompts, logs, outputs and traces.
- Filesystem path traversal and symlink tests.
- Network egress and local-service access tests.
- Dependency and software supply-chain scanning.
- Sandbox escape and resource-exhaustion testing within a controlled lab.
- Recovery and rollback tests.
- Regression tests for every previously discovered security failure.

### 9.2 Evaluation tools to investigate

- [Promptfoo](https://github.com/promptfoo/promptfoo) for adversarial testing and regression evaluation.
- [Invariant](https://github.com/invariantlabs-ai/invariant) for agent/tool policy and security concepts.
- [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) for additional guardrail patterns.
- [gVisor](https://github.com/google/gvisor) for isolated execution research.

These are candidates for evaluation, not automatic approvals or replacements for JARVIS's own enforcement.

## 10. Security rules for the cybersecurity agent

The cybersecurity department must use the same control plane as every other department, with additional domain-specific scope controls.

- Require an explicit target and authorization basis for active testing.
- Maintain allowlisted target ranges and permitted test windows.
- Distinguish passive analysis from active scanning and exploitation.
- Rate-limit scans and enforce concurrency limits.
- Block activity outside the approved scope.
- Preserve command, target, timestamp and result evidence.
- Require stronger approval for intrusive, destructive or availability-impacting tests.
- Keep lab environments isolated from public and personal networks.
- Do not infer authorization merely because a target is reachable.

JARVIS should support defensive investigation and authorized testing while refusing unauthorized access, persistence, credential theft, evasion or destructive activity.

## 11. Engineering requirements and implementation sequence

### Phase 0 — Baseline and threat model
- Inventory all current tools, permissions, data paths and network connections.
- Identify trust boundaries and sensitive resources.
- Document threats, assumptions and accepted risks.
- Establish a security test harness.

### Phase 1 — Trusted tool broker
- Define agent identities and capability manifests.
- Route every tool invocation through one broker.
- Implement deny-by-default authorization.
- Validate schemas, paths, targets and resource limits.
- Add structured audit events.
- Prove through tests that agents cannot bypass the broker.

### Phase 2 — Approval and execution isolation
- Bind approvals to exact actions and scopes.
- Separate execution from the main agent process.
- Add disposable workspaces and unprivileged execution.
- Add network egress restrictions.
- Implement verified rollback and task cancellation.

### Phase 3 — Data, memory and supply chain
- Add secret-store integration and redaction.
- Add data classification and memory provenance.
- Pin and audit dependencies.
- Establish model, plugin and MCP server review procedures.

### Phase 4 — Detection, response and continuous assurance
- Add anomaly signals and security alerts.
- Add permission revocation and quarantine.
- Run adversarial and regression suites in CI.
- Conduct periodic manual security reviews and authorized penetration tests.

## 12. Non-negotiable security invariants

1. **Default deny:** no capability is granted implicitly.
2. **Least privilege:** permissions are narrow, attributable and revocable.
3. **No self-authorization:** an agent cannot approve its own action or elevate its privileges.
4. **Independent enforcement:** trusted code, not model text, makes authorization decisions.
5. **Zero implicit trust:** agents, files, web pages, tools, MCP servers and model outputs are not trusted merely because they are connected.
6. **Isolation:** untrusted code runs in constrained environments.
7. **Human authorization:** sensitive and irreversible actions require explicit approval.
8. **Verification:** execution claims are checked against actual results.
9. **Auditability:** consequential actions produce attributable evidence.
10. **Fail closed:** if policy, identity or verification is unavailable or ambiguous, the action stops.
11. **Recovery:** important mutations have a tested rollback or recovery plan.
12. **No security bypass for specialist agents:** cybersecurity agents and administrators are also subject to policy.

## 13. Standards and primary references

- [OWASP Top 10 for Agentic Applications](https://owasp.org/www-project-top-10-for-agentic-applications/)
- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST Secure Software Development Framework (SSDF)](https://csrc.nist.gov/Projects/ssdf)
- [MITRE ATLAS](https://atlas.mitre.org/)

## 14. Current implementation status

This document defines the target architecture and requirements. It does **not** claim that all controls are implemented in the current JARVIS codebase.

The existing project README describes a useful starting workflow for filesystem mutations:

```text
Analyze -> Plan -> Validate -> Human approval -> Execute -> Verify -> Roll back on failure
```

The next engineering task is to inspect the implementation and tests to establish which invariants are already enforced in trusted code, which are only model instructions, and which are not implemented yet. Record that gap analysis before claiming security readiness.

---

**Architecture decision:** JARVIS is to be engineered as a security-conscious, local-first AI platform with cybersecurity assistance as a governed capability. Security is cross-cutting infrastructure, not a standalone agent.
