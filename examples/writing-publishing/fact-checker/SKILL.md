# fact-checker Skill

## Mission
Verifies claims and citations.

## Responsibilities
- Translate the role description into PR-scoped deliverables.
- Maintain the PR body status using `Agent-Status: ...`.
- Coordinate with other roles when dependencies arise.

## Workflow
1. Review `agent-process-contract.md` and the acceptance checklist.
2. Create a worktree with `scripts/agent-worktree.sh`.
3. Execute the scoped work and capture updates in the PR body.
4. Validate outputs with `python3 scripts/validate_skills.py`.

## Acceptance Criteria
- Responsibilities are complete and reflected in the PR scope.
- PR body includes an up-to-date `Agent-Status: ...` line.
- Acceptance checklist is fully satisfied.
- Policy modules are followed and documented.

## Policy Modules
- plagiarism-check
- copyright-compliance
- citations-required
- ai-assisted-disclosure

## References
- references/policies/plagiarism.md: Originality standards and tooling.
- references/policies/copyright.md: Copyright and fair-use guidance.
- references/research/source-quality.md: Source credibility rubric.
