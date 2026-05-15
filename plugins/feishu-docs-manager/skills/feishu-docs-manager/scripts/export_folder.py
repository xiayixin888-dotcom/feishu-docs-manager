#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


FOLDER_RE = re.compile(r"/drive/folder/([^/?#]+)")


def safe_name(value):
    return re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", value).strip(" .") or "untitled"


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


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
        raise RuntimeError(result.stderr or result.stdout)
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
    parser.add_argument("--cli", default="lark-cli", help="Path to lark-cli.")
    args = parser.parse_args()

    cwd = Path.cwd()
    out_dir = Path(args.out)
    if out_dir.is_absolute():
        print("--out must be a relative path inside the current directory.", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    folder_token = parse_folder_token(args.folder_url)
    files = list_folder(args.cli, folder_token, cwd)

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
        row = export_item(args.cli, item, out_dir, cwd)
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
