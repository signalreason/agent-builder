# AGENTS

System: writing-publishing - Multi-agent workflow for article publishing and research. (v1)

Process Contract: agent-process-contract.md

Roles:
- editor-in-chief: Defines editorial priorities and approves final pieces. (editor-in-chief/SKILL.md)
- researcher: Collects sources and verifies claims. (researcher/SKILL.md)
- writer: Drafts articles and integrates sources. (writer/SKILL.md)
- fact-checker: Verifies claims and citations. (fact-checker/SKILL.md)
- legal-reviewer: Checks copyright and usage risks. (legal-reviewer/SKILL.md)
- publisher: Prepares final formatting and publishes. (publisher/SKILL.md)

Workflow:
- Worktrees required: yes
- Draft PRs: yes
- PR bodies must include 'Agent-Status: ...'

Templates:
- PR body: templates/pr-body.md
- Acceptance checklist: templates/acceptance-checklist.md

Policy Modules:
- plagiarism-check
- copyright-compliance
- citations-required
- ai-assisted-disclosure

Validation:
- Run `python3 scripts/validate_skills.py` from the repo root.
