# Agent Builder

Generate a PR-driven multi-agent workflow repo from a YAML brief. The builder
produces a consistent set of role skills, templates, policies, and helper
scripts so teams can spin up new systems without re-inventing the workflow.

## Purpose
- Turn a YAML brief into a complete, PR-driven multi-agent workflow repo.

## Goals
- Produce deterministic, ASCII-first scaffolding with consistent skills and templates.
- Embed the PR process contract and optional draft PR scaffolding when enabled.
- Provide validation and helper scripts so teams can iterate quickly.

## Quickstart

1. Author a brief YAML (see `examples/briefs/writing-publishing.yml`).
2. Generate a system:

```sh
python3 scripts/build_system.py examples/briefs/writing-publishing.yml --out ./out/writing-publishing
```

3. Validate the generated repo:

```sh
python3 ./out/writing-publishing/scripts/validate_skills.py
```

Notes:
- The output directory must be empty.
- PyYAML is optional; a minimal YAML parser is used if it is unavailable.

## Brief Schema (Top-Level)

```yaml
system:
  name: writing-publishing
  description: Multi-agent workflow for article publishing and research.
  version: 1

workflow:
  pr_process_contract: agent-process-contract.md
  use_worktrees: true
  create_draft_prs: false

roles:
  - name: editor-in-chief
    description: Defines editorial priorities and approves final pieces.

policies:
  - plagiarism-check

templates:
  pr_body: templates/pr-body.md
  acceptance_checklist: templates/acceptance-checklist.md

references:
  - path: references/policies/plagiarism.md
    purpose: Originality standards and tooling.
```

## Generated Output

- `AGENTS.md` and `SKILLS.md` overview the system and role skills
- `agent-process-contract.md` defines the PR workflow rules
- `scripts/` includes `build_system.py`, `validate_skills.py`,
  `agent-worktree.sh`, and `agent-chat.sh`
- `templates/` includes `pr-body.md` and `acceptance-checklist.md`
- One directory per role with a `SKILL.md`
- `references/` contains policy modules and optional extra references
- Optional `scripts/scaffold_prs.sh` is emitted when `create_draft_prs` is true

## Helper Scripts

- `scripts/agent-worktree.sh <branch-name> <worktree-path>` creates a worktree
- `scripts/agent-chat.sh <role> <message>` appends to `logs/agent-chat.log`
- `scripts/scaffold_prs.sh <branch-name> <title>` creates a draft PR (requires `gh`)

## Examples

- `examples/briefs/writing-publishing.yml` is a sample brief
- `examples/writing-publishing/` shows a generated system from that brief

## Decision Log

- `logs/decisions.log` captures implementation decisions and defaults
