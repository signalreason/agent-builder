#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "SKILLS.md",
    "agent-process-contract.md",
    "scripts/build_system.py",
    "scripts/validate_skills.py",
    "scripts/agent-worktree.sh",
    "scripts/agent-chat.sh",
    "templates/pr-body.md",
    "templates/acceptance-checklist.md",
]

SKIP_DIRS = {"scripts", "templates", "references", "assets", "logs"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = []

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"Missing required file: {rel}")

    pr_body = root / "templates/pr-body.md"
    if pr_body.exists():
        text = pr_body.read_text(encoding="utf-8")
        if "Agent-Status:" not in text:
            errors.append("PR body template missing 'Agent-Status:' line.")

    agents = root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        if "agent-process-contract.md" not in text:
            errors.append("AGENTS.md must reference agent-process-contract.md.")

    roles = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in SKIP_DIRS:
            continue
        skill_path = entry / "SKILL.md"
        if skill_path.exists():
            roles.append(entry)
            text = skill_path.read_text(encoding="utf-8")
            if "Acceptance Criteria" not in text:
                errors.append(
                    f"{entry.name}/SKILL.md missing Acceptance Criteria section."
                )
            if "Workflow" not in text:
                errors.append(
                    f"{entry.name}/SKILL.md missing Workflow section."
                )

    if not roles:
        errors.append("No role SKILL.md files found.")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
