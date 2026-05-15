# Feishu/Lark Drive Scopes

Use minimal scopes and add only what the current task needs. Admin approval may be required; after approval, rerun `lark-cli auth login --scope "<scope>"` so the token receives the new scope.

## Common Tasks

List Drive folder contents:

```text
space:document:retrieve
drive:drive.metadata:readonly
```

Download ordinary Drive files:

```text
drive:file:download
```

Export online docs:

```text
docs:document:export
docs:document.content:read
docx:document:readonly
```

Export sheets:

```text
sheets:spreadsheet:read
docs:document:export
docs:document.content:read
```

Recommended minimal scope bundle for mixed folders:

```text
space:document:retrieve drive:drive.metadata:readonly drive:file:download docs:document:export docs:document.content:read docx:document:readonly sheets:spreadsheet:read
```

## Known lark-cli Behaviors

- `drive +pull` mirrors ordinary files only; it skips online docs/sheets/bitables/slides.
- `drive +export` can export `doc/docx/sheet/bitable`.
- `drive +export` requires relative output paths inside the current directory.
- Missing-scope errors usually include the exact scope to request. Prefer that exact scope over broad `--recommend`.
