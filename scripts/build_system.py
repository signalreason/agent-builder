#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import textwrap


POLICY_MODULES = {
    "plagiarism-check": textwrap.dedent(
        """\
        # Plagiarism Check Policy

        - Use approved tooling to scan drafts for originality.
        - Record tool name, version, and summary results in the PR body.
        - Resolve or cite any flagged passages before requesting review.
        """
    ),
    "copyright-compliance": textwrap.dedent(
        """\
        # Copyright Compliance Policy

        - Only use content that is authored in-house or licensed for use.
        - Document licenses and attributions in the PR body.
        - Remove or replace content that cannot be cleared.
        """
    ),
    "citations-required": textwrap.dedent(
        """\
        # Citations Required Policy

        - Every factual claim must have a citation.
        - List sources in the acceptance checklist or PR body.
        - Prefer primary sources when available.
        """
    ),
    "ai-assisted-disclosure": textwrap.dedent(
        """\
        # AI-Assisted Disclosure Policy

        - Disclose AI assistance in the PR body.
        - Document the prompts and tools used.
        - Human reviewers must verify all outputs.
        """
    ),
}

REQUIRED_FILES = [
    "AGENTS.md",
    "SKILLS.md",
    "agent-process-contract.md",
    "scripts/build_system.py",
    "scripts/validate_skills.py",
    "scripts/agent-worktree.sh",
    "scripts/agent-chat.sh",
]

DEFAULTS = {
    "system": {
        "name": "unnamed-system",
        "description": "No description provided.",
        "version": 1,
    },
    "workflow": {
        "pr_process_contract": "agent-process-contract.md",
        "use_worktrees": True,
        "create_draft_prs": False,
    },
    "templates": {
        "pr_body": "templates/pr-body.md",
        "acceptance_checklist": "templates/acceptance-checklist.md",
    },
}


class BriefError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a PR-driven agent system from a YAML brief."
    )
    parser.add_argument("brief", help="Path to system brief YAML")
    parser.add_argument("--out", required=True, help="Output directory")
    return parser.parse_args()


def load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None

    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise BriefError("Brief YAML must be a mapping at the top level.")
        return data

    return parse_yaml_minimal(text)


def parse_yaml_minimal(text: str) -> dict:
    tokens = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        stripped = raw.lstrip(" ")
        if stripped.startswith("#"):
            continue
        if "\t" in raw:
            raise BriefError(f"Tabs are not supported in YAML (line {line_no}).")
        indent = len(raw) - len(stripped)
        tokens.append((indent, stripped.rstrip(), line_no))

    if not tokens:
        return {}

    def parse_block(idx: int, indent: int):
        if idx >= len(tokens):
            return None, idx
        if tokens[idx][0] != indent:
            raise BriefError(
                f"Unexpected indentation at line {tokens[idx][2]}."
            )
        if tokens[idx][1].startswith("- "):
            return parse_list(idx, indent)
        return parse_map(idx, indent)

    def parse_map(idx: int, indent: int):
        mapping: dict = {}
        while idx < len(tokens) and tokens[idx][0] == indent:
            content, line_no = tokens[idx][1], tokens[idx][2]
            if content.startswith("- "):
                raise BriefError(f"Unexpected list item at line {line_no}.")
            key, sep, value = content.partition(":")
            if not sep:
                raise BriefError(f"Missing ':' in mapping at line {line_no}.")
            key = key.strip()
            value = value.lstrip(" ")
            idx += 1
            if value:
                mapping[key] = parse_scalar(value)
                continue
            if idx >= len(tokens) or tokens[idx][0] <= indent:
                mapping[key] = None
                continue
            child, idx = parse_block(idx, tokens[idx][0])
            mapping[key] = child
        return mapping, idx

    def parse_list(idx: int, indent: int):
        items = []
        while idx < len(tokens) and tokens[idx][0] == indent:
            content, line_no = tokens[idx][1], tokens[idx][2]
            if not content.startswith("- "):
                break
            item_content = content[2:]
            idx += 1
            if not item_content:
                if idx >= len(tokens) or tokens[idx][0] <= indent:
                    items.append(None)
                    continue
                child, idx = parse_block(idx, tokens[idx][0])
                items.append(child)
                continue
            if ":" in item_content:
                key, sep, value = item_content.partition(":")
                item = {}
                if value.strip():
                    item[key.strip()] = parse_scalar(value.strip())
                else:
                    if idx < len(tokens) and tokens[idx][0] > indent:
                        child, idx = parse_block(idx, tokens[idx][0])
                        item[key.strip()] = child
                    else:
                        item[key.strip()] = None
                if idx < len(tokens) and tokens[idx][0] > indent:
                    child, idx = parse_map(idx, tokens[idx][0])
                    if not isinstance(child, dict):
                        raise BriefError(
                            f"Expected mapping for list item at line {line_no}."
                        )
                    item.update(child)
                items.append(item)
                continue
            items.append(parse_scalar(item_content.strip()))
        return items, idx

    data, next_idx = parse_block(0, tokens[0][0])
    if next_idx != len(tokens):
        line_no = tokens[next_idx][2]
        raise BriefError(f"Unexpected content at line {line_no}.")
    if not isinstance(data, dict):
        raise BriefError("Brief YAML must be a mapping at the top level.")
    return data


def parse_scalar(value: str):
    value = strip_comment(value)
    if not value:
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    if (
        (value.startswith("\"") and value.endswith("\""))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    return value


def strip_comment(value: str) -> str:
    in_single = False
    in_double = False
    for idx, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return value[:idx].rstrip()
    return value.strip()


def normalize_brief(data: dict):
    open_questions = []

    system_raw = data.get("system") or {}
    workflow_raw = data.get("workflow") or {}
    templates_raw = data.get("templates") or {}

    system = {
        "name": system_raw.get("name") or DEFAULTS["system"]["name"],
        "description": system_raw.get("description")
        or DEFAULTS["system"]["description"],
        "version": system_raw.get("version")
        if system_raw.get("version") is not None
        else DEFAULTS["system"]["version"],
    }
    if "name" not in system_raw:
        open_questions.append("System name missing; used 'unnamed-system'.")
    if "description" not in system_raw:
        open_questions.append("System description missing; used a placeholder.")
    if "version" not in system_raw:
        open_questions.append("System version missing; defaulted to 1.")

    pr_contract = workflow_raw.get("pr_process_contract") or DEFAULTS["workflow"][
        "pr_process_contract"
    ]
    if pr_contract != "agent-process-contract.md":
        open_questions.append(
            "Brief requested a non-standard process contract; generated"
            " 'agent-process-contract.md' per spec."
        )
        pr_contract = "agent-process-contract.md"

    workflow = {
        "pr_process_contract": pr_contract,
        "use_worktrees": bool(
            workflow_raw.get("use_worktrees", DEFAULTS["workflow"]["use_worktrees"])
        ),
        "create_draft_prs": bool(
            workflow_raw.get(
                "create_draft_prs", DEFAULTS["workflow"]["create_draft_prs"]
            )
        ),
    }
    if "use_worktrees" not in workflow_raw:
        open_questions.append("Workflow use_worktrees missing; defaulted to true.")
    if "create_draft_prs" not in workflow_raw:
        open_questions.append(
            "Workflow create_draft_prs missing; defaulted to false."
        )

    roles_raw = data.get("roles")
    roles = []
    if not roles_raw:
        open_questions.append(
            "No roles provided; generated placeholder role 'owner'."
        )
        roles_raw = [
            {
                "name": "owner",
                "description": "Owns overall system delivery and coordination.",
            }
        ]

    for role in roles_raw:
        if not isinstance(role, dict):
            raise BriefError("Roles entries must be mappings.")
        name = role.get("name")
        description = role.get("description") or "No description provided."
        if not name:
            raise BriefError("Each role must include a name.")
        slug = slugify(name)
        if slug != name:
            open_questions.append(
                f"Role '{name}' normalized to directory '{slug}'."
            )
        roles.append(
            {
                "name": name,
                "description": description,
                "slug": slug,
            }
        )

    templates = {
        "pr_body": templates_raw.get("pr_body")
        or DEFAULTS["templates"]["pr_body"],
        "acceptance_checklist": templates_raw.get("acceptance_checklist")
        or DEFAULTS["templates"]["acceptance_checklist"],
    }
    if "pr_body" not in templates_raw:
        open_questions.append("Templates pr_body missing; used default path.")
    if "acceptance_checklist" not in templates_raw:
        open_questions.append(
            "Templates acceptance_checklist missing; used default path."
        )

    policies_raw = data.get("policies") or []
    if not isinstance(policies_raw, list):
        raise BriefError("Policies must be a list.")
    policies = [str(policy) for policy in policies_raw]

    references_raw = data.get("references") or []
    if not isinstance(references_raw, list):
        raise BriefError("References must be a list.")
    references = []
    for ref in references_raw:
        if not isinstance(ref, dict):
            raise BriefError("References entries must be mappings.")
        path = ref.get("path")
        purpose = ref.get("purpose") or "No purpose provided."
        if not path:
            raise BriefError("Reference entries must include a path.")
        references.append({"path": path, "purpose": purpose})

    return (
        {
            "system": system,
            "workflow": workflow,
            "roles": roles,
            "policies": policies,
            "templates": templates,
            "references": references,
        },
        open_questions,
    )


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower().strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "role"


def ensure_empty_dir(path: Path):
    if path.exists() and any(path.iterdir()):
        raise BriefError(f"Output path '{path}' is not empty.")
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def set_executable(path: Path):
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def render_agents(brief: dict, open_questions: list[str]) -> str:
    system = brief["system"]
    workflow = brief["workflow"]
    roles = brief["roles"]
    policies = brief["policies"]
    templates = brief["templates"]

    lines = [
        "# AGENTS",
        "",
        f"System: {system['name']} - {system['description']} (v{system['version']})",
        "",
        "Process Contract: agent-process-contract.md",
        "",
        "Roles:",
    ]
    for role in roles:
        lines.append(
            f"- {role['name']}: {role['description']} ({role['slug']}/SKILL.md)"
        )

    lines.extend(
        [
            "",
            "Workflow:",
            f"- Worktrees required: {'yes' if workflow['use_worktrees'] else 'no'}",
            f"- Draft PRs: {'yes' if workflow['create_draft_prs'] else 'no'}",
            "- PR bodies must include 'Agent-Status: ...'",
            "",
            "Templates:",
            f"- PR body: {templates['pr_body']}",
            f"- Acceptance checklist: {templates['acceptance_checklist']}",
        ]
    )

    if policies:
        lines.append("")
        lines.append("Policy Modules:")
        for policy in policies:
            lines.append(f"- {policy}")

    lines.extend(
        [
            "",
            "Validation:",
            "- Run `python3 scripts/validate_skills.py` from the repo root.",
        ]
    )

    if open_questions:
        lines.append("")
        lines.append("Open Questions:")
        for question in open_questions:
            lines.append(f"- {question}")

    return "\n".join(lines)


def render_skills(brief: dict) -> str:
    roles = brief["roles"]
    policies = brief["policies"]
    references = brief["references"]

    lines = [
        "# SKILLS",
        "",
        "Each role has a dedicated SKILL.md describing responsibilities, workflow,",
        "and acceptance criteria.",
        "",
        "Roles:",
    ]
    for role in roles:
        lines.append(f"- {role['name']}: {role['slug']}/SKILL.md")

    if policies:
        lines.append("")
        lines.append("Policy Modules:")
        for policy in policies:
            lines.append(f"- {policy}")

    if references:
        lines.append("")
        lines.append("References:")
        for ref in references:
            lines.append(f"- {ref['path']}: {ref['purpose']}")

    lines.extend(
        [
            "",
            "Validation:",
            "- Run `python3 scripts/validate_skills.py` before opening a PR.",
        ]
    )

    return "\n".join(lines)


def render_process_contract() -> str:
    return textwrap.dedent(
        """\
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
        """
    )


def render_pr_body_template() -> str:
    return textwrap.dedent(
        """\
        # Summary

        Agent-Status: Draft

        ## Scope
        -

        ## Acceptance Checklist
        - [ ] See templates/acceptance-checklist.md

        ## Risks / Notes
        -
        """
    )


def render_acceptance_checklist() -> str:
    return textwrap.dedent(
        """\
        # Acceptance Checklist

        - [ ] Acceptance criteria from the assigned role skill are satisfied.
        - [ ] Required policy modules are followed and documented.
        - [ ] PR body includes `Agent-Status: ...` and scope notes.
        - [ ] Validation script passes (`python3 scripts/validate_skills.py`).
        """
    )


def render_role_skill(role: dict, policies: list[str], references: list[dict]) -> str:
    lines = [
        f"# {role['name']} Skill",
        "",
        "## Mission",
        role["description"],
        "",
        "## Responsibilities",
        "- Translate the role description into PR-scoped deliverables.",
        "- Maintain the PR body status using `Agent-Status: ...`.",
        "- Coordinate with other roles when dependencies arise.",
        "",
        "## Workflow",
        "1. Review `agent-process-contract.md` and the acceptance checklist.",
        "2. Create a worktree with `scripts/agent-worktree.sh`.",
        "3. Execute the scoped work and capture updates in the PR body.",
        "4. Validate outputs with `python3 scripts/validate_skills.py`.",
        "",
        "## Acceptance Criteria",
        "- Responsibilities are complete and reflected in the PR scope.",
        "- PR body includes an up-to-date `Agent-Status: ...` line.",
        "- Acceptance checklist is fully satisfied.",
    ]

    if policies:
        lines.append("- Policy modules are followed and documented.")

    if policies:
        lines.extend(["", "## Policy Modules"])
        for policy in policies:
            lines.append(f"- {policy}")

    if references:
        lines.extend(["", "## References"])
        for ref in references:
            lines.append(f"- {ref['path']}: {ref['purpose']}")

    return "\n".join(lines)


def render_reference_stub(path: str, purpose: str) -> str:
    title = Path(path).stem.replace("-", " ").title()
    return textwrap.dedent(
        f"""\
        # {title}

        Purpose: {purpose}

        - Add detailed guidance here.
        """
    )


def render_worktree_script() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        if [ "$#" -lt 2 ]; then
          echo "Usage: $0 <branch-name> <worktree-path>"
          exit 1
        fi

        branch="$1"
        worktree_path="$2"

        if ! git rev-parse --git-dir >/dev/null 2>&1; then
          echo "Error: run from inside a git repository."
          exit 1
        fi

        if git show-ref --verify --quiet "refs/heads/$branch"; then
          git worktree add "$worktree_path" "$branch"
        else
          git worktree add -b "$branch" "$worktree_path"
        fi
        """
    )


def render_chat_script() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        if [ "$#" -lt 2 ]; then
          echo "Usage: $0 <role> <message>"
          exit 1
        fi

        role="$1"
        message="$2"
        log_dir="${LOG_DIR:-logs}"
        mkdir -p "$log_dir"
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        printf "[%s] [%s] %s\n" "$timestamp" "$role" "$message" >> "$log_dir/agent-chat.log"
        """
    )


def render_scaffold_script() -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        if ! command -v gh >/dev/null 2>&1; then
          echo "GitHub CLI (gh) is required to scaffold draft PRs."
          exit 1
        fi

        if [ "$#" -lt 2 ]; then
          echo "Usage: $0 <branch-name> <title>"
          exit 1
        fi

        branch="$1"
        title="$2"

        gh pr create --draft --title "$title" --body-file templates/pr-body.md --head "$branch"
        """
    )


def generate(output: Path, brief: dict, open_questions: list[str]):
    roles = brief["roles"]
    policies = brief["policies"]
    references = brief["references"]
    templates = brief["templates"]
    workflow = brief["workflow"]

    write_file(output / "AGENTS.md", render_agents(brief, open_questions))
    write_file(output / "SKILLS.md", render_skills(brief))
    write_file(output / "agent-process-contract.md", render_process_contract())

    scripts_dir = output / "scripts"
    write_file(scripts_dir / "validate_skills.py", render_validation_script())
    write_file(scripts_dir / "agent-worktree.sh", render_worktree_script())
    write_file(scripts_dir / "agent-chat.sh", render_chat_script())

    build_system_path = Path(__file__).resolve()
    write_file(scripts_dir / "build_system.py", build_system_path.read_text(encoding="utf-8"))

    write_file(output / templates["pr_body"], render_pr_body_template())
    write_file(output / templates["acceptance_checklist"], render_acceptance_checklist())

    for role in roles:
        role_dir = output / role["slug"]
        write_file(
            role_dir / "SKILL.md",
            render_role_skill(role, policies, references),
        )

    reference_paths = set()
    for ref in references:
        reference_paths.add(ref["path"])
        write_file(output / ref["path"], render_reference_stub(ref["path"], ref["purpose"]))

    for policy in policies:
        policy_path = f"references/policies/{policy}.md"
        if policy_path in reference_paths:
            continue
        policy_text = POLICY_MODULES.get(policy)
        if policy_text is None:
            policy_text = render_reference_stub(policy_path, "Policy module guidance.")
        write_file(output / policy_path, policy_text)

    if workflow["create_draft_prs"]:
        write_file(output / "scripts/scaffold_prs.sh", render_scaffold_script())

    for rel_path in REQUIRED_FILES:
        if not (output / rel_path).exists():
            raise BriefError(f"Missing required file: {rel_path}")

    for script in [
        output / "scripts/agent-worktree.sh",
        output / "scripts/agent-chat.sh",
        output / "scripts/build_system.py",
        output / "scripts/validate_skills.py",
        output / "scripts/scaffold_prs.sh",
    ]:
        if script.exists():
            set_executable(script)


def render_validation_script() -> str:
    return textwrap.dedent(
        """\
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
        """
    )


def main() -> int:
    args = parse_args()
    brief_path = Path(args.brief)
    output_path = Path(args.out)

    if not brief_path.exists():
        raise BriefError(f"Brief file not found: {brief_path}")

    data = load_yaml(brief_path)
    brief, open_questions = normalize_brief(data)

    ensure_empty_dir(output_path)
    generate(output_path, brief, open_questions)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BriefError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
