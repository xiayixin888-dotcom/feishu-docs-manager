---
name: feishu-docs-manager
description: Download, export, mirror, and inspect Feishu/Lark Drive documents, folders, sheets, and files with the official lark-cli. Use when Codex needs to batch download a Feishu folder, export online docs to PDF/DOCX, export sheets to XLSX/CSV, list Drive folder contents, handle lark-cli OAuth/device-code authorization, request missing scopes, or troubleshoot Feishu/Lark Open Platform permission errors.
---

# Feishu Docs Manager

Use the official `lark-cli` first for Feishu/Lark Drive work. Prefer user OAuth/device-code authorization over asking the user to create a custom app manually. Treat app secrets and tokens as sensitive: do not echo them in final answers, command strings, reports, or generated docs.

## Workflow

1. Locate or install `lark-cli`.
   - Check `which lark-cli` and local project paths such as `lark-cli-bin/lark-cli`.
   - If npm/npx is unavailable, download the official GitHub Release binary into the workspace instead of requiring system installation.
   - Do not use third-party CLIs unless the user explicitly prefers them.
2. Configure and authorize.
   - Run `lark-cli config show` first.
   - If no app is configured, use `lark-cli config init --new` and send the exact verification URL to the user.
   - Use `lark-cli auth login --scope "<scopes>"` for minimal scopes. Send the exact device verification URL as plain text/code block.
   - After approval, run `lark-cli auth status` and verify the needed scopes are present.
3. Inspect the target.
   - Parse folder tokens from `/drive/folder/<token>`, doc tokens from `/docx/<token>` or `/docs/<token>`, sheets from `/sheets/<token>`, bitables from `/base/<token>`.
   - For a folder, list contents with:
     `lark-cli drive files list --params '{"folder_token":"TOKEN","page_size":50}' --page-all --format json`
   - `drive +pull` only downloads ordinary Drive files (`type=file`) and skips online docs, sheets, bitables, slides, and shortcuts.
4. Export online documents.
   - Use `lark-cli drive +export`.
   - Default choices: `docx/doc -> pdf`, `sheet -> xlsx`, `bitable -> xlsx`.
   - Use relative `--output-dir` paths within the current working directory. `lark-cli` rejects absolute output paths as unsafe.
5. Verify.
   - Count local files by extension.
   - Check the script report for nonzero return codes.
   - Tell the user the output directory, count by type, and failures.

## Reusable Script

Use `scripts/export_folder.py` for batch folder exports when the task is larger than a couple of files.

Example:

```bash
python3 /Users/xia/.codex/skills/feishu-docs-manager/scripts/export_folder.py \
  --folder-url "https://example.feishu.cn/drive/folder/FOLDER_TOKEN" \
  --out exports/feishu_folder \
  --cli ./lark-cli-bin/lark-cli
```

The script lists the folder, exports online docs/sheets/bitables, downloads ordinary files, and writes `export_report.json`.

## Permission Loop

When `lark-cli` reports missing scopes, do not keep retrying the failing operation. Request the specific scope named in the error, wait for the user/admin approval, then rerun authorization and retry.

Common scopes are in `references/scopes.md`. Read that file when a permission error appears or when planning a new Feishu/Lark Drive workflow.

## User Interaction Rules

- For device authorization, relay the exact URL returned by `lark-cli`; do not rewrite, encode, shorten, or markdown-link it.
- If the user provides app credentials, configure via `--app-secret-stdin` when possible.
- If a command needs network access, request escalation using a narrow prefix rule for that exact CLI operation.
- Never include the app secret or access tokens in final summaries.
