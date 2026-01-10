# Agent Process Contract

This system uses a PR-driven workflow with explicit agent roles.

## Contract Rules
- All work happens in a dedicated worktree per PR.
- The PR body must include an `Agent-Status: ...` line.
- Each PR must reference the relevant role acceptance criteria.
- No destructive commands are permitted in scripts or workflows.
- Approvals are required for any external tooling not listed in policies.

## Suggested Workflow
1. Read the relevant role skill and the acceptance checklist.
2. Create a worktree using `scripts/agent-worktree.sh`.
3. Execute the scoped tasks and record updates in the PR body.
4. Run validation (`python3 scripts/validate_skills.py`).
5. Request review when acceptance criteria are met.
