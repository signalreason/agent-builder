# System Builder Spec: PR-Driven Multi-Agent Workflow Generator

- Title
  - System Builder: Generate PR-Driven Agent Systems

- Summary
  - Build a CLI-driven system that takes a structured domain brief and generates a ready-to-use repo with agent roles, skills, PR contract, templates, and helper scripts. The output should be consistent, reproducible, and safe by default, so teams can spin up new domain systems (e.g., writing/publishing) without re-inventing the workflow.

- Goals
  - Generate a complete, PR-driven agent system from a domain brief.
  - Enforce the `agent-process-contract.md` workflow in every generated system.
  - Provide role-specific skills, templates, and safety policies.
  - Make outputs deterministic and easy to audit.

- Non-goals
  - Execute or manage ongoing domain work automatically.
  - Replace human approvals or legal review.
  - Generate CI/CD beyond basic validation hooks.

- Users and stakeholders
  - Maintainers who need new agent systems.
  - Agent operators (PM/Tech Lead/Developer/Reviewer equivalents).
  - Domain owners (e.g., editorial lead).

- Scope
  - In-scope
    - Parse a structured system brief (YAML).
    - Generate repo skeleton + role skills + templates.
    - Generate validation and helper scripts (worktrees, logging).
    - Optional GitHub PR scaffolding (draft PRs per split).
  - Out-of-scope
    - Running workflows or assigning agents automatically.
    - Publishing content or approving releases.

- Requirements
  - Functional
    - CLI entrypoint: `scripts/build_system.py <brief.yml> --out <path>`.
    - Read a YAML brief (schema below).
    - Produce required files:
      - `AGENTS.md`
      - `SKILLS.md`
      - `agent-process-contract.md`
      - `scripts/validate_skills.py`
      - `scripts/agent-worktree.sh`
      - `scripts/agent-chat.sh`
      - Role skill folders with `SKILL.md`
      - Optional `references/` and `assets/` content
    - Generate a PR template and a default status line in draft PR bodies.
    - Provide plug-in "policy modules" (e.g., plagiarism checks) chosen by brief.
  - Non-functional
    - Deterministic output for same inputs.
    - ASCII-first content.
    - Safe defaults: no destructive commands, worktree isolation required.
    - Minimal boilerplate with progressive disclosure (skills reference files).

- Data and integrations
  - GitHub CLI (`gh`) optional for draft PR scaffolding.
  - No network required by default.
  - Optional external policy tools (e.g., plagiarism checkers) must be explicitly enabled in brief.

- Constraints
  - Generated system must reference `agent-process-contract.md`.
  - PR body template must include `Agent-Status: ...`.
  - Roles must have acceptance criteria in their skills.

- Assumptions
  - Users can provide a system brief and adjust outputs after generation.
  - Teams use GitHub PRs and CLI-based workflows.

- Risks and mitigations
  - Incomplete briefs -> include validation + open questions section in output.
  - Role confusion -> enforce explicit responsibilities per role skill.
  - Security leakage -> default to ignoring sensitive keys, include warnings.

- Milestones and deliverables
  - M1: CLI + YAML schema + output tree creation.
  - M2: Role skills + PR templates + validation script.
  - M3: Policy modules + optional PR scaffolding.
  - M4: Example brief and example generated system.

- Acceptance criteria
  - Running `scripts/build_system.py` with a valid brief creates a repo that passes `scripts/validate_skills.py`.
  - Generated roles include workflows and acceptance criteria.
  - Generated PR template follows `agent-process-contract.md`.
  - Policy modules are included and referenced when selected in the brief.
  - Output tree matches the defined structure.

- Open questions
  - Do we need JSON as an alternate brief format?
  - Should draft PR creation be on by default?

---

## YAML Brief Schema (Concrete)

```yaml
system:
  name: writing-system
  description: PR-driven workflow for article publishing.
  version: 1

workflow:
  pr_process_contract: agent-process-contract.md
  use_worktrees: true
  create_draft_prs: false

roles:
  - name: project-manager
    description: Capture requirements and acceptance criteria.
  - name: tech-lead
    description: Split work into PRs and define scope.
  - name: developer
    description: Execute assigned PRs and tests.
  - name: reviewer
    description: Review PRs against acceptance criteria.

policies:
  - plagiarism-check
  - copyright-compliance
  - citations-required

templates:
  pr_body: templates/pr-body.md
  acceptance_checklist: templates/acceptance-checklist.md

references:
  - path: references/policies/plagiarism.md
    purpose: Rules for attribution and originality.
  - path: references/policies/copyright.md
    purpose: Usage rules for external content.
```

## Output Tree (Concrete)

```
<output>/
  AGENTS.md
  SKILLS.md
  agent-process-contract.md
  scripts/
    build_system.py
    validate_skills.py
    agent-worktree.sh
    agent-chat.sh
  templates/
    pr-body.md
    acceptance-checklist.md
  project-manager/
    SKILL.md
  tech-lead/
    SKILL.md
  developer/
    SKILL.md
  reviewer/
    SKILL.md
  references/
    policies/
      plagiarism.md
      copyright.md
```

## Example Generated System: Writing/Publishing

### Example Brief (Writing System)
```yaml
system:
  name: writing-publishing
  description: Multi-agent workflow for article publishing and research.
  version: 1

workflow:
  pr_process_contract: agent-process-contract.md
  use_worktrees: true
  create_draft_prs: true

roles:
  - name: editor-in-chief
    description: Defines editorial priorities and approves final pieces.
  - name: researcher
    description: Collects sources and verifies claims.
  - name: writer
    description: Drafts articles and integrates sources.
  - name: fact-checker
    description: Verifies claims and citations.
  - name: legal-reviewer
    description: Checks copyright and usage risks.
  - name: publisher
    description: Prepares final formatting and publishes.

policies:
  - plagiarism-check
  - copyright-compliance
  - citations-required
  - ai-assisted-disclosure

templates:
  pr_body: templates/pr-body.md
  acceptance_checklist: templates/acceptance-checklist.md

references:
  - path: references/policies/plagiarism.md
    purpose: Originality standards and tooling.
  - path: references/policies/copyright.md
    purpose: Copyright and fair-use guidance.
  - path: references/research/source-quality.md
    purpose: Source credibility rubric.
```

### Writing System Role Expectations (Generated Skill Bodies)
- Editor-in-chief: prioritizes topics, final approval, sets quality bar.
- Researcher: source gathering, citation coverage, claim verification.
- Writer: drafts, integrates citations, respects policies.
- Fact-checker: verifies all claims, challenges unsourced assertions.
- Legal-reviewer: clears copyright and licensing issues.
- Publisher: formatting, distribution, final QA checklist.

### Writing System Acceptance Criteria (Generated)
- All factual claims have citations from approved sources.
- Plagiarism check passes with documented tooling output.
- Copyright-sensitive content is cleared or removed.
- Draft has editor approval and reviewer sign-off.
- PR uses `Agent-Status` and follows the process contract.
