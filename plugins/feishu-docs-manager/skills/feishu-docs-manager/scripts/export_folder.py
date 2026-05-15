#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


FOLDER_RE = re.compile(r"/drive/folder/([^/?#]+)")
PROXY_RE = re.compile(r"^export\s+([A-Za-z_]*proxy|[A-Z_]*PROXY)=(.+)$")


def safe_name(value):
    return re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", value).strip(" .") or "untitled"


def load_proxy_env():
    env = os.environ.copy()
    zshrc = Path.home() / ".zshrc"
    if not zshrc.exists():
        return env

    try:
        lines = zshrc.read_text(encoding="utf-8").splitlines()
    except OSError:
        return env

    for line in lines:
        match = PROXY_RE.match(line.strip())
        if not match:
            continue
        key, value = match.groups()
        if key in env:
            continue
        env[key] = value.strip().strip("\"'")
    return env


def find_cli(cwd, requested=None):
    candidates = []
    if requested:
        candidates.append(Path(requested).expanduser())

    env_cli = os.environ.get("LARK_CLI")
    if env_cli:
        candidates.append(Path(env_cli).expanduser())

    which_cli = shutil.which("lark-cli")
    if which_cli:
        candidates.append(Path(which_cli))

    candidates.extend(
        [
            cwd / "lark-cli-bin" / "lark-cli",
            cwd / "lark-cli",
            Path.home() / ".local" / "bin" / "lark-cli",
            Path("/opt/homebrew/bin/lark-cli"),
            Path("/usr/local/bin/lark-cli"),
        ]
    )

    codex_root = Path.home() / "Documents" / "Codex"
    if codex_root.exists():
        candidates.extend(codex_root.glob("*/*/lark-cli-bin/lark-cli"))

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve() if candidate.exists() else candidate
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)

    raise FileNotFoundError(
        "lark-cli not found. Pass --cli, set LARK_CLI, add lark-cli to PATH, "
        "or place it at ./lark-cli-bin/lark-cli."
    )


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, env=load_proxy_env())


def explain_cli_error(text):
    if "keychain Get failed" in text or "keychain not initialized" in text:
        return (
            text
            + "\n\nDetected macOS Keychain access failure. In Codex, rerun the same "
            "lark-cli command with sandbox escalation/outside the sandbox so the CLI "
            "can read its saved OAuth token."
        )
    return text


def parse_folder_token(value):
    match = FOLDER_RE.search(value)
    if match:
        return match.group(1)
    return value.strip()


def extract_files(stdout):
    text = stdout.strip()
    if not text:
        return []
    start = text.find("{")
    if start > 0:
        text = text[start:]
    payload = json.loads(text)
    return payload.get("data", {}).get("files", [])


def list_folder(cli, folder_token, cwd):
    result = run(
        [
            cli,
            "drive",
            "files",
            "list",
            "--params",
            json.dumps({"folder_token": folder_token, "page_size": 50}),
            "--page-all",
            "--format",
            "json",
        ],
        cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(explain_cli_error(result.stderr or result.stdout))
    return extract_files(result.stdout)


def export_item(cli, item, out_dir, cwd):
    item_type = item["type"]
    token = item["token"]
    name = safe_name(item.get("name") or token)

    if item_type in ("doc", "docx"):
        ext = "pdf"
        target_dir = out_dir / "docx"
        cmd = [
            cli,
            "drive",
            "+export",
            "--token",
            token,
            "--doc-type",
            item_type,
            "--file-extension",
            ext,
            "--file-name",
            name,
            "--output-dir",
            str(target_dir),
            "--overwrite",
        ]
    elif item_type in ("sheet", "bitable"):
        ext = "xlsx"
        target_dir = out_dir / item_type
        cmd = [
            cli,
            "drive",
            "+export",
            "--token",
            token,
            "--doc-type",
            item_type,
            "--file-extension",
            ext,
            "--file-name",
            name,
            "--output-dir",
            str(target_dir),
            "--overwrite",
        ]
    elif item_type == "file":
        target_dir = out_dir / "file"
        target_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            cli,
            "drive",
            "+download",
            "--file-token",
            token,
            "--output",
            str(target_dir / name),
            "--overwrite",
        ]
    else:
        return {
            "name": item.get("name"),
            "token": token,
            "type": item_type,
            "returncode": 0,
            "skipped": True,
            "stdout": "",
            "stderr": f"unsupported type: {item_type}",
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    result = run(cmd, cwd)
    return {
        "name": item.get("name"),
        "token": token,
        "type": item_type,
        "returncode": result.returncode,
        "skipped": False,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main():
    parser = argparse.ArgumentParser(description="Export a Feishu/Lark Drive folder with lark-cli.")
    parser.add_argument("--folder-url", required=True, help="Folder URL or folder token.")
    parser.add_argument("--out", default="exports/feishu_folder", help="Relative output directory.")
    parser.add_argument("--cli", help="Path to lark-cli. Auto-detected when omitted.")
    args = parser.parse_args()

    cwd = Path.cwd()
    cli = find_cli(cwd, args.cli)
    out_dir = Path(args.out)
    if out_dir.is_absolute():
        print("--out must be a relative path inside the current directory.", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    folder_token = parse_folder_token(args.folder_url)
    files = list_folder(cli, folder_token, cwd)

    report = []
    for item in files:
        if item.get("type") == "folder":
            report.append(
                {
                    "name": item.get("name"),
                    "token": item.get("token"),
                    "type": "folder",
                    "returncode": 0,
                    "skipped": True,
                    "stdout": "",
                    "stderr": "nested folder skipped by this script",
                }
            )
            continue
        print(f"exporting {item.get('type')} {item.get('name')}")
        row = export_item(cli, item, out_dir, cwd)
        report.append(row)
        if row["returncode"] != 0:
            print(row["stderr"] or row["stdout"], file=sys.stderr)

    report_path = out_dir / "export_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    failures = [row for row in report if row["returncode"] != 0]
    skipped = [row for row in report if row.get("skipped")]
    print(f"done: {len(report) - len(failures) - len(skipped)} ok, {len(failures)} failed, {len(skipped)} skipped")
    print(f"report: {report_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
