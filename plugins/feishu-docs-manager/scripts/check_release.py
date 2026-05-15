#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ".codex-plugin/plugin.json",
    "skills/feishu-docs-manager/SKILL.md",
    "skills/feishu-docs-manager/scripts/export_folder.py",
    "skills/feishu-docs-manager/references/scopes.md",
    "skills/feishu-docs-manager/agents/openai.yaml",
]
SECRET_PATTERNS = [
    re.compile(r"(app[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*['\"][^'\"]+['\"]", re.I),
    re.compile(r"\b[A-Za-z0-9_-]{32,}\b"),
]


def main():
    errors = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing {rel}")

    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid plugin.json: {exc}")
        manifest = {}

    if manifest.get("name") != "feishu-docs-manager":
        errors.append("plugin.json name must be feishu-docs-manager")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin.json skills must point to ./skills/")

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                if path.relative_to(ROOT).as_posix() == "scripts/check_release.py":
                    continue
                errors.append(f"possible secret pattern in {path.relative_to(ROOT)}: {pattern.pattern}")

    if errors:
        print("Release check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
