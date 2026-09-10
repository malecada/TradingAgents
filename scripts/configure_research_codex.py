"""Render project-scoped Codex defaults; never edits personal config or plugin caches.

Run again after plugin updates or on another computer to resolve skill paths.
Existing unmanaged project configurations are preserved and require a manual merge.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


HEADER = "# Managed by scripts/configure_research_codex.py; regenerate after plugin updates."
SCOPED_OUT = (
    ("claude-plugins-official/superpowers", "using-superpowers"),
    ("claude-plugins-official/superpowers", "brainstorming"),
    ("caveman/caveman", "caveman"),
    ("claude-mem-local/claude-mem", "learn-codebase"),
)


def render(codex_dir: Path) -> tuple[str, list[str]]:
    lines = [HEADER, '# Project defaults; an existing task can retain its client/runtime overrides.',
             'model = "gpt-6-astra"', 'model_reasoning_effort = "high"', '',
             '[agents]', 'enabled = true', 'max_concurrent_threads_per_session = 3',
             'default_subagent_model = "gpt-6-astra"',
             'default_subagent_reasoning_effort = "medium"']
    paths = []
    for plugin, skill in SCOPED_OUT:
        for skill_file in sorted((codex_dir / "plugins/cache" / plugin).glob(f"*/skills/{skill}/SKILL.md")):
            # Explicit SKILL.md selectors were verified by Codex 0.153.4
            # prompt rendering; inventory metadata alone does not prove filtering.
            paths.append(str(skill_file.resolve()))
    for path in paths:
        lines.extend(['', '[[skills.config]]', 'path = ' + json.dumps(path), 'enabled = false'])
    return "\n".join(lines) + "\n", paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write managed project config; default only reports")
    parser.add_argument("--workspace-root", action="store_true", help="Also configure this checkout's parent workspace")
    parser.add_argument("--profile", action="store_true", help="Also write the selectable crypto-research user profile")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    codex_dir = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    content, paths = render(codex_dir)
    roots = [root, root.parent] if args.workspace_root else [root]
    targets = [base / ".codex/config.toml" for base in roots]
    if args.profile:
        targets.append(codex_dir / "crypto-research.config.toml")
    # Preflight every destination before any write.
    for target in targets:
        if target.exists() and not target.read_text().startswith(HEADER):
            raise SystemExit(f"Existing unmanaged configuration preserved: {target}. Merge the generated settings explicitly.")
    if args.apply:
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".toml.tmp")
            temporary.write_text(content)
            temporary.replace(target)
    print(json.dumps({"applied": args.apply, "targets": [str(t) for t in targets],
                      "model": "gpt-6-astra", "coordinator_effort": "high", "worker_effort": "medium",
                      "disabled_skill_paths": paths, "personal_config_changed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
