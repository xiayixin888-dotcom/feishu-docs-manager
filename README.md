# Feishu Docs Manager Codex Plugin

Codex plugin for downloading, exporting, listing, and troubleshooting Feishu/Lark Drive documents and folders with the official `lark-cli`.

## Contents

- `plugins/feishu-docs-manager/.codex-plugin/plugin.json` - plugin manifest
- `plugins/feishu-docs-manager/skills/feishu-docs-manager/` - bundled Codex skill
- `plugins/feishu-docs-manager/scripts/check_release.py` - pre-release safety check
- `.agents/plugins/marketplace.json` - local marketplace entry

## Install Locally

Copy or keep this repository as a Codex plugin source, then point Codex at the local marketplace:

```text
.agents/plugins/marketplace.json
```

The plugin currently contains one skill:

```text
feishu-docs-manager
```

## Before Publishing

Run:

```bash
python3 plugins/feishu-docs-manager/scripts/check_release.py
```

Do not commit Feishu/Lark credentials, OAuth tokens, downloaded documents, or exported files.
