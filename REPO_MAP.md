# Repo Map: agent-builder

## Purpose and scope
Generate a PR-driven multi-agent workflow repo from a YAML brief. This map documents the builder itself.

## Quickstart commands
- `python3 scripts/build_system.py examples/briefs/writing-publishing.yml --out ./out/writing-publishing`
- `python3 ./out/writing-publishing/scripts/validate_skills.py`

## Top-level map
- `examples/` - sample briefs and generated output snapshots.
  - `examples/briefs/` - YAML briefs.
  - `examples/writing-publishing/` - example generated system.
- `logs/` - decision log and defaults.
- `scripts/` - CLI entry point and helper scripts.
- `specs/` - builder specification and notes.
- `templates/` - template files emitted into generated repos.
- `README.md` - usage, schema, and helper script summary.

## Key entry points
- `scripts/build_system.py` - main generator CLI.
- `scripts/validate_skills.py` - validates generated skills.
- `examples/briefs/writing-publishing.yml` - canonical brief example.

## Core flows and data movement
- YAML brief -> generator -> scaffolding output on disk.
- Optional PR scaffolding scripts emitted when enabled in the brief.

## External integrations
- Optional GitHub CLI usage via generated scripts (draft PR scaffolding).

## Configuration and deployment
- The brief YAML configures roles, policies, templates, and PR options.
- No runtime services; output is static files and scripts.

## Common workflows (build/test/release)
- Generate: `python3 scripts/build_system.py <brief> --out <dir>`
- Validate output: `python3 <out>/scripts/validate_skills.py`

## Read-next list
- `README.md`
- `scripts/build_system.py`
- `scripts/validate_skills.py`
- `specs/system-builder-spec.md`
- `templates/`

## Unknowns and follow-ups
- No automated test suite referenced in this repo.
