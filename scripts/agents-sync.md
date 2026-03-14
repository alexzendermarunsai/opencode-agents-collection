# Portable Agent Sync

Use `scripts/agents_sync.py` to install a curated pack into a live OpenCode agents directory outside this repository.

## When To Use It

- you want a portable live agents directory such as `~/.config/opencode/agents/`
- you want the source repo to stay read-only during normal use
- you want managed updates, drift checks, and a clean reset path

The script only installs from curated pack directories. It never installs from `reference-agents/`.

## Commands

Sync a pack into a target directory:

```bash
python3 scripts/agents_sync.py sync --pack a-team --target ~/.config/opencode/agents
```

If the target directory does not exist yet, `sync` creates it after applying the same safety checks.

Use `safe` mode explicitly:

```bash
python3 scripts/agents_sync.py sync --pack a-team-plus --target ~/.config/opencode/agents --mode safe
```

Preview changes first:

```bash
python3 scripts/agents_sync.py sync --pack a-team --target ~/.config/opencode/agents --dry-run
```

Check managed state:

```bash
python3 scripts/agents_sync.py status --target ~/.config/opencode/agents
python3 scripts/agents_sync.py status --target ~/.config/opencode/agents --json
```

Remove only manifest-managed files:

```bash
python3 scripts/agents_sync.py reset --target ~/.config/opencode/agents
python3 scripts/agents_sync.py reset --target ~/.config/opencode/agents --dry-run
```

## Modes

- `safe` installs the curated pack with a stricter portable permission profile; it rewrites each agent's `permission` block in the target directory
- `trusted` installs the curated pack exactly as authored in this repo, including the pack's current `permission` blocks

Use `safe` when the target directory is a general-purpose live setup and you want a conservative default. Use `trusted` when you want the pack behavior in the target to match the curated source files exactly.

## Manifest And Drift

Each managed target directory gets a state file named `.opencode-agents-state.json`.

- it records the installed pack, mode, source file paths, and installed content hashes
- `status` reads it to report managed, drifted, and missing files
- `reset` removes only files tracked in that state file

Manifest-managed filenames are restricted to plain filenames in the target root. The script rejects manifest entries that try to use absolute paths, parent traversal, or nested paths.

`sync` and `reset` stop if the managed target has drift unless you pass `--force`.

That includes cases like:

- a managed file was edited in the target directory
- a managed file was deleted from the target directory
- a same-named unmanaged file already exists where the script needs to install a file

Use `--dry-run` to inspect planned writes, updates, removals, and keeps before making changes. Use `--force` only when you intentionally want to overwrite or clean up target-directory conflicts.
