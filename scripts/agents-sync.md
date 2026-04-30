# Portable Agent Sync

Use `scripts/agents_sync.py` to install a curated pack into a live OpenCode agents directory outside this repository.

## When To Use It

- you want a portable live agents directory such as `~/.config/opencode/agents/`
- you want the source repo to stay read-only during normal use
- you want managed updates, drift checks, and a clean reset path

The script only installs from curated pack directories. It never installs from `reference-agents/`.

Supported packs: `a-team`, `a-team-gpt-5.4`, `a-team-gpt-5.5`, `a-team-plus`, `a-team-plus-gpt-5.4`, and `a-team-plus-gpt-5.5`.

As a quick rule: use `a-team` packs for the leaner workflow, `a-team-plus` packs for broader shipping coverage, and the `*-gpt-*` variants when a specific GPT generation is your primary model.

## Commands

Sync a pack into a target directory:

```bash
python3 scripts/agents_sync.py sync --pack a-team --target ~/.config/opencode/agents
```

If the target directory does not exist yet, `sync` creates it after applying the same safety checks.

Use `safe` mode explicitly:

```bash
python3 scripts/agents_sync.py sync --pack a-team-gpt-5.4 --target ~/.config/opencode/agents --mode safe
```

Use `yolo` mode only when you intentionally want to remove approval prompts for `ask` permissions in the installed target files:

```bash
python3 scripts/agents_sync.py sync --pack a-team --target ~/.config/opencode/agents --mode yolo
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

Run the guided interactive wrapper:

```bash
python3 scripts/agents_sync.py interactive
```

Example session:

```text
$ python3 scripts/agents_sync.py interactive
Target directory: ~/.config/opencode/agents
Current state: target=existing, manifest=present, managed=11, drifted=0, missing=0, pack=a-team-gpt-5.4, mode=safe
Action (sync/status/reset): sync
Pack (a-team/a-team-gpt-5.4/a-team-gpt-5.5/a-team-plus/a-team-plus-gpt-5.4/a-team-plus-gpt-5.5): a-team-gpt-5.4
Mode (safe/trusted/yolo) [safe]:
Preview: action=sync, target=/home/alice/.config/opencode/agents, pack=a-team-gpt-5.4, mode=safe, force=no
Planned changes: write=1, keep=11
Proceed? [y/N]: y
```

Remove only manifest-managed files:

```bash
python3 scripts/agents_sync.py reset --target ~/.config/opencode/agents
python3 scripts/agents_sync.py reset --target ~/.config/opencode/agents --dry-run
```

## Modes

- `safe` installs the curated pack with a stricter portable permission profile; it rewrites each agent's `permission` block in the target directory
- `trusted` installs the curated pack exactly as authored in this repo, including the pack's current `permission` blocks
- `yolo` installs the curated pack like `trusted`, then rewrites only literal `ask` values inside the frontmatter `permission` block to `allow`; it does not change `deny`, and it does not change anything outside that block

Interactive mode uses the current manifest's pack and mode as sync defaults when they are available, falls back to `safe` mode for new targets, asks before enabling `force` when drift or unmanaged conflicts require it, and requires the same typed `YOLO` confirmation before executing a `yolo` sync.

Use `safe` when the target directory is a general-purpose live setup and you want a conservative default. Use `trusted` when you want the pack behavior in the target to match the curated source files exactly. Use `yolo` only in an isolated, disposable, or well-backed-up target directory.

## YOLO Warning

Before any non-dry-run `yolo` sync writes files, the script prints a strong warning and requires you to type `YOLO` exactly.

- it removes approval gates for risky actions
- agents may run commands, edit files, or access the network without asking again
- mistakes or bad prompts can damage the workspace or expose data
- use it only in an isolated, disposable, or well-backed-up target directory

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

Dry-run output starts with `DRY RUN: no files will be changed`, prints the action context and planned summary, then lists each detailed action, including no-op reset previews with no manifest. A dry-run `yolo` sync does not require the typed `YOLO` confirmation because no files are changed.

`--force` can overwrite same-named unmanaged conflicts during `sync`, replace managed files that drifted from the manifest, or let `reset` clean up a managed target even when files have drifted or gone missing. It does not bypass safety checks: target directories still cannot be unsafe locations or symlinks, manifest-managed filenames must stay in the target root, manifest/managed/target files must be regular files, and symlinks are still rejected.

`status --target <path>` is read-only. If `<path>` is a safe but missing target directory, it exits successfully and reports the target as missing, the manifest as missing, and zero managed files; `--json` reports the same state with `target_exists: false`.

The interactive wrapper does not bypass those checks; it surfaces the same force-required conditions and asks for explicit confirmation before rerunning with `force`. Read-only interactive status prints immediately without a separate `Proceed?` prompt. Interactive sync defaults to the current manifest's pack and mode when they are available, with `safe` as the fallback mode.
