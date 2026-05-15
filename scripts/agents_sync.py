#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = ".opencode-agents-state.json"
SUPPORTED_PACKS = (
    "a-team",
    "a-team-gpt-5.4",
    "a-team-gpt-5.5",
    "a-team-deepseekv4-pro",
    "chinese-team",
    "american-chinese-team",
    "a-team-plus",
    "a-team-plus-gpt-5.4",
    "a-team-plus-gpt-5.5",
    "a-team-plus-deepseekv4-pro",
)
SUPPORTED_MODES = ("safe", "trusted", "yolo")


class SyncError(Exception):
    pass


@dataclass(frozen=True)
class AgentSource:
    path: Path
    filename: str
    name: str
    authored_content: str


@dataclass(frozen=True)
class SyncPlan:
    target: Path
    rendered: dict[str, dict[str, str]]
    stale_files: list[str]
    planned_actions: list[str]


@dataclass(frozen=True)
class ResetPlan:
    target: Path
    manifest: dict[str, Any] | None
    planned_actions: list[str]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def format_os_error(exc: OSError) -> str:
    return exc.strerror or str(exc)


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError as exc:
        raise SyncError(f"unable to inspect path: {path}: {format_os_error(exc)}") from exc


def path_is_symlink(path: Path, label: str = "path") -> bool:
    try:
        return path.is_symlink()
    except OSError as exc:
        raise SyncError(f"unable to inspect {label}: {path}: {format_os_error(exc)}") from exc


def path_is_dir(path: Path, label: str = "path") -> bool:
    try:
        return path.is_dir()
    except OSError as exc:
        raise SyncError(f"unable to inspect {label}: {path}: {format_os_error(exc)}") from exc


def path_is_file(path: Path, label: str = "path") -> bool:
    try:
        return path.is_file()
    except OSError as exc:
        raise SyncError(f"unable to inspect {label}: {path}: {format_os_error(exc)}") from exc


def ensure_regular_file_if_exists(path: Path, label: str) -> None:
    if path_is_symlink(path, label):
        raise SyncError(f"{label} is a symlink: {path}")
    if not path_exists(path):
        return
    if not path_is_file(path, label):
        raise SyncError(f"{label} must be a regular file: {path}")


def ensure_regular_file_exists(path: Path, label: str) -> None:
    ensure_regular_file_if_exists(path, label)
    if not path_exists(path):
        raise SyncError(f"{label} does not exist: {path}")


def read_text(path: Path, label: str = "file") -> str:
    ensure_regular_file_exists(path, label)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SyncError(f"{label} is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise SyncError(f"unable to read {label}: {path}: {format_os_error(exc)}") from exc


def parse_frontmatter_sections(content: str) -> tuple[list[str], list[str], str]:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise SyncError("missing opening frontmatter marker")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise SyncError("missing closing frontmatter marker")

    return lines[: end_index + 1], lines[1:end_index], "".join(lines[end_index + 1 :])


def frontmatter_name(content: str) -> str:
    _, frontmatter_lines, _ = parse_frontmatter_sections(content)
    for line in frontmatter_lines:
        match = re.match(r"^name:\s*(.+?)\s*$", line.rstrip("\n"))
        if match:
            return match.group(1)
    raise SyncError("missing frontmatter name")


def build_permission_lines(permission: dict[str, Any]) -> list[str]:
    lines = ["permission:\n"]
    for key, value in permission.items():
        if isinstance(value, dict):
            lines.append(f"  {key}:\n")
            for nested_key, nested_value in value.items():
                lines.append(f'    "{nested_key}": {nested_value}\n')
        else:
            lines.append(f"  {key}: {value}\n")
    return lines


def rewrite_permission_block(content: str, permission: dict[str, Any]) -> str:
    opening_lines, frontmatter_lines, body = parse_frontmatter_sections(content)
    start = None
    end = None
    for index, line in enumerate(frontmatter_lines):
        if re.match(r"^permission:\s*$", line.rstrip("\n")):
            start = index
            end = index + 1
            while end < len(frontmatter_lines):
                candidate = frontmatter_lines[end]
                if candidate.strip() and not candidate.startswith((" ", "\t")):
                    break
                end += 1
            break
    if start is None or end is None:
        raise SyncError("missing permission block")

    new_frontmatter = frontmatter_lines[:start] + build_permission_lines(permission) + frontmatter_lines[end:]
    return "".join([opening_lines[0], *new_frontmatter, opening_lines[-1], body])


def rewrite_permission_ask_to_allow(content: str) -> str:
    opening_lines, frontmatter_lines, body = parse_frontmatter_sections(content)
    start = None
    end = None
    for index, line in enumerate(frontmatter_lines):
        if re.match(r"^permission:\s*$", line.rstrip("\n")):
            start = index
            end = index + 1
            while end < len(frontmatter_lines):
                candidate = frontmatter_lines[end]
                if candidate.strip() and not candidate.startswith((" ", "\t")):
                    break
                end += 1
            break
    if start is None or end is None:
        raise SyncError("missing permission block")

    rewritten_permission_lines = [frontmatter_lines[start]]
    for line in frontmatter_lines[start + 1 : end]:
        newline = "\n" if line.endswith("\n") else ""
        stripped = line[:-1] if newline else line
        rewritten = re.sub(
            r'^(\s*(?:"[^"]+"|[^:\n]+?)\s*:\s*)ask(\s*)$',
            r"\1allow\2",
            stripped,
        )
        rewritten_permission_lines.append(rewritten + newline)

    new_frontmatter = frontmatter_lines[:start] + rewritten_permission_lines + frontmatter_lines[end:]
    return "".join([opening_lines[0], *new_frontmatter, opening_lines[-1], body])


def safe_permission_matrix(pack: str, agent_names: list[str]) -> dict[str, dict[str, Any]]:
    orchestrator_tasks = {"*": "deny"}
    for name in agent_names:
        if name != "Agents Orchestrator":
            orchestrator_tasks[name] = "allow"

    common = {
        "Agents Orchestrator": {
            "edit": "deny",
            "bash": "deny",
            "webfetch": "deny",
            "task": orchestrator_tasks,
        },
        "Senior Project Manager": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
        "UX Architect": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
        "UI Designer": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
        "Reality Checker": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
        "UX Researcher": {"edit": "deny", "bash": "deny", "webfetch": "ask"},
        "API Tester": {"edit": "deny", "bash": "deny", "webfetch": "ask"},
        "Frontend Developer": {"edit": "allow", "bash": "deny", "webfetch": "deny"},
        "Backend Architect": {"edit": "allow", "bash": "deny", "webfetch": "deny"},
        "Senior Developer": {"edit": "allow", "bash": "deny", "webfetch": "deny"},
        "Technical Writer": {"edit": "allow", "bash": "deny", "webfetch": "ask"},
    }
    if pack in {
        "a-team",
        "a-team-gpt-5.4",
        "a-team-gpt-5.5",
        "a-team-deepseekv4-pro",
        "chinese-team",
        "american-chinese-team",
    }:
        return common
    if pack in {"a-team-plus", "a-team-plus-gpt-5.4", "a-team-plus-gpt-5.5", "a-team-plus-deepseekv4-pro"}:
        common.update(
            {
                "Performance Benchmarker": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
                "Security Engineer": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
                "Accessibility Auditor": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
                "DevOps Automator": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
                "AI Engineer": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
                "Rapid Prototyper": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
            }
        )
        return common
    raise SyncError(f"unsupported pack: {pack}")


def list_source_agents(pack: str) -> list[AgentSource]:
    if pack not in SUPPORTED_PACKS:
        raise SyncError(f"unsupported pack: {pack}")
    pack_dir = REPO_ROOT / pack / "agents"
    sources: list[AgentSource] = []
    for path in sorted(pack_dir.glob("*.md")):
        content = read_text(path, "source file")
        sources.append(
            AgentSource(
                path=path,
                filename=path.name,
                name=frontmatter_name(content),
                authored_content=content,
            )
        )
    if not sources:
        raise SyncError(f"no source agents found for pack: {pack}")
    return sources


def render_agent_content(pack: str, mode: str, source: AgentSource, all_names: list[str]) -> str:
    if mode == "trusted":
        return source.authored_content
    if mode == "yolo":
        return rewrite_permission_ask_to_allow(source.authored_content)
    if mode == "safe":
        matrix = safe_permission_matrix(pack, all_names)
        if source.name not in matrix:
            raise SyncError(f"safe mode has no permission mapping for: {source.name}")
        return rewrite_permission_block(source.authored_content, matrix[source.name])
    raise SyncError(f"unsupported mode: {mode}")


YOLO_WARNING_LINES = (
    "WARNING: YOLO mode removes approval gates for risky actions.",
    "Agents may run commands, edit files, or access the network without asking again.",
    "Mistakes or bad prompts can damage the workspace or expose data.",
    "Use YOLO mode only in an isolated, disposable, or well-backed-up target directory.",
)


def print_yolo_warning() -> None:
    for line in YOLO_WARNING_LINES:
        print(line)


def confirm_yolo() -> bool:
    print_yolo_warning()
    return input("Type YOLO to continue: ").strip() == "YOLO"


def atomic_write(path: Path, content: str, label: str = "target file") -> None:
    ensure_regular_file_if_exists(path, label)
    try:
        fd, temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    except OSError as exc:
        raise SyncError(f"unable to prepare write for {path}: {format_os_error(exc)}") from exc
    try:
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            ensure_regular_file_if_exists(path, label)
            os.replace(temp_path, path)
        except OSError as exc:
            raise SyncError(f"unable to write file: {path}: {format_os_error(exc)}") from exc
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def manifest_path(target: Path) -> Path:
    return target / MANIFEST_NAME


def validate_managed_filename(filename: str) -> str:
    if not isinstance(filename, str) or not filename:
        raise SyncError("manifest contains invalid managed filename")
    if Path(filename).is_absolute():
        raise SyncError(f"manifest contains unsafe managed filename: {filename}")
    if any(separator and separator in filename for separator in (os.sep, os.altsep, "/", "\\")):
        raise SyncError(f"manifest contains unsafe managed filename: {filename}")
    parts = Path(filename).parts
    if len(parts) != 1 or parts[0] in {".", ".."}:
        raise SyncError(f"manifest contains unsafe managed filename: {filename}")
    return filename


def managed_file_path(target: Path, filename: str) -> Path:
    safe_filename = validate_managed_filename(filename)
    path = target / safe_filename
    try:
        path.relative_to(target)
    except ValueError as exc:
        raise SyncError(f"manifest contains unsafe managed filename: {filename}") from exc
    return path


def manifest_files(manifest: dict[str, Any] | None, target: Path) -> dict[str, dict[str, Any]]:
    if not manifest:
        return {}
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        raise SyncError("manifest files entry must be an object")

    validated: dict[str, dict[str, Any]] = {}
    for filename, info in files.items():
        safe_filename = validate_managed_filename(filename)
        if not isinstance(info, dict):
            raise SyncError(f"manifest entry for {safe_filename} must be an object")
        managed_file_path(target, safe_filename)
        validated[safe_filename] = info
    return validated


def load_manifest(target: Path) -> dict[str, Any] | None:
    path = manifest_path(target)
    if path_is_symlink(path, "manifest path"):
        raise SyncError("manifest path is a symlink")
    if not path_exists(path):
        return None
    ensure_regular_file_if_exists(path, "manifest path")
    try:
        manifest = json.loads(read_text(path, "manifest path"))
    except json.JSONDecodeError as exc:
        raise SyncError(f"invalid manifest JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise SyncError("manifest root must be an object")
    return manifest


def ensure_safe_target(target_arg: str, *, allow_create: bool = False) -> Path:
    if not target_arg or not target_arg.strip():
        raise SyncError("target path must not be empty")

    target_input = Path(target_arg).expanduser()
    if path_is_symlink(target_input, "target directory"):
        raise SyncError("target directory must not be a symlink")
    target_input_exists = path_exists(target_input)
    if target_input_exists:
        if not path_is_dir(target_input, "target directory"):
            raise SyncError("target must be a directory")
        if path_is_symlink(target_input, "target directory"):
            raise SyncError("target directory must not be a symlink")
        unresolved_absolute = Path(os.path.abspath(target_input))
        target = target_input.resolve()
    else:
        if not allow_create:
            raise SyncError("target directory must already exist")

        existing_parent = target_input.parent
        missing_parts: list[str] = [target_input.name]
        while not path_exists(existing_parent):
            missing_parts.append(existing_parent.name)
            existing_parent = existing_parent.parent

        if not path_is_dir(existing_parent, "target parent"):
            raise SyncError("target parent must be a directory")
        if path_is_symlink(existing_parent, "target parent"):
            raise SyncError("target directory must not traverse symlinks")

        unresolved_parent = Path(os.path.abspath(existing_parent))
        resolved_parent = existing_parent.resolve()
        if unresolved_parent != resolved_parent:
            raise SyncError("target directory must not traverse symlinks")

        unresolved_absolute = Path(os.path.abspath(target_input))
        target = resolved_parent.joinpath(*reversed(missing_parts))

    home = Path.home().resolve()
    repo_root = REPO_ROOT.resolve()

    if target_input_exists and unresolved_absolute != target:
        raise SyncError("target directory must not traverse symlinks")

    if target == Path("/"):
        raise SyncError("refusing to operate on /")
    if target == home:
        raise SyncError("refusing to operate on home root")
    if any(part == ".git" for part in target.parts):
        raise SyncError("refusing to operate on .git path")
    if target == repo_root:
        raise SyncError("refusing to operate on source repo root")
    if repo_root in target.parents:
        raise SyncError("refusing to operate inside source repo")
    return target


def verify_no_symlink(path: Path, label: str) -> None:
    if path_is_symlink(path, label):
        raise SyncError(f"{label} is a symlink: {path}")


def file_hash_if_exists(path: Path, label: str = "file") -> str | None:
    ensure_regular_file_if_exists(path, label)
    if not path_exists(path):
        return None
    return sha256_text(read_text(path, label))


def managed_state(target: Path, manifest: dict[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    if not manifest:
        return [], [], []
    files = manifest_files(manifest, target)
    ok: list[str] = []
    drifted: list[str] = []
    missing: list[str] = []
    for rel_name, info in sorted(files.items()):
        path = managed_file_path(target, rel_name)
        ensure_regular_file_if_exists(path, "managed file")
        if not path_exists(path):
            missing.append(rel_name)
            continue
        current_hash = file_hash_if_exists(path, "managed file")
        if current_hash != info.get("installed_sha256"):
            drifted.append(rel_name)
        else:
            ok.append(rel_name)
    return ok, drifted, missing


def check_manifest_drift(target: Path, manifest: dict[str, Any] | None, force: bool) -> None:
    _, drifted, missing = managed_state(target, manifest)
    if (drifted or missing) and not force:
        problems = []
        if drifted:
            problems.append("drifted files: " + ", ".join(drifted))
        if missing:
            problems.append("missing files: " + ", ".join(missing))
        raise SyncError("managed target has drift; rerun with --force (" + "; ".join(problems) + ")")


def plan_sync(target: Path, pack: str, mode: str, force: bool) -> SyncPlan:
    sources = list_source_agents(pack)
    all_names = [source.name for source in sources]
    rendered: dict[str, dict[str, str]] = {}
    for source in sources:
        ensure_regular_file_if_exists(target / source.filename, "target file")
        rendered[source.filename] = {
            "name": source.name,
            "source": str(source.path.relative_to(REPO_ROOT)),
            "content": render_agent_content(pack, mode, source, all_names),
        }

    existing_manifest = load_manifest(target)
    check_manifest_drift(target, existing_manifest, force)

    planned_actions: list[str] = []
    existing_managed = set(manifest_files(existing_manifest, target).keys())
    desired_files = set(rendered.keys())
    stale_files = sorted(existing_managed - desired_files)
    for filename in stale_files:
        planned_actions.append(f"remove {managed_file_path(target, filename)}")

    for filename, info in sorted(rendered.items()):
        path = target / filename
        ensure_regular_file_if_exists(path, "target file")
        if path_exists(path) and (not existing_manifest or filename not in existing_managed) and not force:
            raise SyncError(f"unmanaged conflicting file exists: {path}; rerun with --force")
        current_hash = file_hash_if_exists(path, "target file")
        desired_hash = sha256_text(info["content"])
        if current_hash == desired_hash:
            planned_actions.append(f"keep {path}")
        elif path_exists(path):
            planned_actions.append(f"update {path}")
        else:
            planned_actions.append(f"write {path}")

    planned_actions.append(f"write {manifest_path(target)}")
    return SyncPlan(target=target, rendered=rendered, stale_files=stale_files, planned_actions=planned_actions)


def plan_reset(target: Path, force: bool) -> ResetPlan:
    manifest = load_manifest(target)
    if not manifest:
        return ResetPlan(target=target, manifest=None, planned_actions=[])

    check_manifest_drift(target, manifest, force)
    planned_actions = []
    for filename in sorted(manifest_files(manifest, target)):
        path = managed_file_path(target, filename)
        planned_actions.append(f"remove {path}")
    planned_actions.append(f"remove {manifest_path(target)}")
    return ResetPlan(target=target, manifest=manifest, planned_actions=planned_actions)


def print_actions(planned_actions: list[str]) -> None:
    for action in planned_actions:
        print(action)


def ensure_target_dir_for_mutation(target: Path) -> None:
    if path_exists(target):
        if path_is_symlink(target, "target directory"):
            raise SyncError("target directory must not be a symlink")
        if not path_is_dir(target, "target directory"):
            raise SyncError("target must be a directory")


def preflight_sync_mutation(plan: SyncPlan) -> None:
    ensure_target_dir_for_mutation(plan.target)
    ensure_regular_file_if_exists(manifest_path(plan.target), "manifest path")
    for filename in plan.stale_files:
        ensure_regular_file_if_exists(managed_file_path(plan.target, filename), "managed file")
    for filename in plan.rendered:
        ensure_regular_file_if_exists(plan.target / filename, "target file")


def preflight_reset_mutation(plan: ResetPlan) -> None:
    ensure_target_dir_for_mutation(plan.target)
    ensure_regular_file_if_exists(manifest_path(plan.target), "manifest path")
    if not plan.manifest:
        return
    for filename in manifest_files(plan.manifest, plan.target):
        ensure_regular_file_if_exists(managed_file_path(plan.target, filename), "managed file")


def print_dry_run(action: str, target: Path, planned_actions: list[str], *, pack: str | None = None, mode: str | None = None, force: bool = False) -> None:
    context = [f"action={action}", f"target={target}"]
    if pack is not None:
        context.append(f"pack={pack}")
    if mode is not None:
        context.append(f"mode={mode}")
    context.append(f"force={'yes' if force else 'no'}")

    print("DRY RUN: no files will be changed")
    print("Context: " + ", ".join(context))
    print(f"Planned changes: {summarize_actions(planned_actions)}")
    print("Detailed actions:")
    print_actions(planned_actions)


def summarize_status(payload: dict[str, Any]) -> str:
    target_state = "existing" if payload.get("target_exists") else "missing"
    summary = [
        f"target={target_state}",
        f"manifest={'present' if payload['manifest'] else 'missing'}",
        f"managed={payload['managed_files']}",
        f"drifted={len(payload['drifted_files'])}",
        f"missing={len(payload['missing_files'])}",
    ]
    if payload.get("pack"):
        summary.append(f"pack={payload['pack']}")
        summary.append(f"mode={payload['mode']}")
    return ", ".join(summary)


def render_status_human(payload: dict[str, Any]) -> str:
    target_state = "existing" if payload.get("target_exists") else "missing"
    lines = [
        f"target: {payload['target']}",
        f"target state: {target_state}",
        f"manifest: {'present' if payload['manifest'] else 'missing'}",
    ]
    if payload.get("pack"):
        lines.append(f"pack: {payload['pack']}")
        lines.append(f"mode: {payload['mode']}")
    lines.extend(
        [
            f"managed files: {payload['managed_files']}",
            f"ok files: {len(payload['ok_files'])}",
            f"drifted files: {len(payload['drifted_files'])}",
        ]
    )
    if payload["drifted_files"]:
        lines.append("  " + ", ".join(payload["drifted_files"]))
    lines.append(f"missing files: {len(payload['missing_files'])}")
    if payload["missing_files"]:
        lines.append("  " + ", ".join(payload["missing_files"]))
    return "\n".join(lines)


def summarize_actions(planned_actions: list[str]) -> str:
    counts = {"write": 0, "update": 0, "remove": 0, "keep": 0}
    for action in planned_actions:
        verb = action.split(" ", 1)[0]
        if verb in counts:
            counts[verb] += 1
    parts = [f"{verb}={count}" for verb, count in counts.items() if count]
    return ", ".join(parts) if parts else "no changes"


def prompt(message: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{message}{suffix}: ").strip()
    return value or (default or "")


def prompt_choice(message: str, choices: tuple[str, ...], default: str | None = None) -> str:
    default_index = choices.index(default) + 1 if default in choices else None
    while True:
        print(f"{message}:")
        for index, choice in enumerate(choices, start=1):
            print(f"  {index}) {choice}")
        suffix = f" [{default_index}]" if default_index is not None else ""
        value = input(f"Choose {message.lower()}{suffix}: ").strip()
        if not value and default_index is not None:
            return default
        if value.isdecimal():
            choice_index = int(value)
            if 1 <= choice_index <= len(choices):
                return choices[choice_index - 1]
        if value in choices:
            return value
        print(f"Please choose a number from 1-{len(choices)} or one of: {', '.join(choices)}")


def prompt_yes_no(message: str, default: bool = False) -> bool:
    label = "Y/n" if default else "y/N"
    while True:
        value = input(f"{message} [{label}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def interactive_command(args: argparse.Namespace) -> int:
    target_input = prompt("Target directory")
    target = ensure_safe_target(target_input, allow_create=True)

    payload = status_payload(target)
    print(f"Current state: {summarize_status(payload)}")

    action = prompt_choice("Action", ("sync", "status", "reset"))

    if action == "status":
        print(render_status_human(payload))
        return 0

    force = False
    if action == "sync":
        manifest_pack = payload.get("pack")
        manifest_mode = payload.get("mode")
        pack_default = manifest_pack if manifest_pack in SUPPORTED_PACKS else None
        mode_default = manifest_mode if manifest_mode in SUPPORTED_MODES else "safe"
        pack = prompt_choice("Pack", SUPPORTED_PACKS, default=pack_default)
        mode = prompt_choice("Mode", SUPPORTED_MODES, default=mode_default)
        try:
            plan = plan_sync(target, pack, mode, force=False)
        except SyncError as exc:
            message = str(exc)
            if "rerun with --force" not in message:
                raise
            print(f"Needs force: {message}")
            if not prompt_yes_no("Continue with force?", default=False):
                print("Cancelled.")
                return 0
            force = True
            plan = plan_sync(target, pack, mode, force=True)

        print(f"Preview: action=sync, target={target}, pack={pack}, mode={mode}, force={'yes' if force else 'no'}")
        print(f"Planned changes: {summarize_actions(plan.planned_actions)}")
        if not prompt_yes_no("Proceed?", default=False):
            print("Cancelled.")
            return 0
        if mode == "yolo" and not confirm_yolo():
            print("Cancelled.")
            return 0
        return sync_command(
            argparse.Namespace(
                target=str(target),
                pack=pack,
                mode=mode,
                dry_run=False,
                force=force,
                confirmed_yolo=mode == "yolo",
            )
        )

    try:
        plan = plan_reset(target, force=False)
    except SyncError as exc:
        message = str(exc)
        if "rerun with --force" not in message:
            raise
        print(f"Needs force: {message}")
        if not prompt_yes_no("Continue with force?", default=False):
            print("Cancelled.")
            return 0
        force = True
        plan = plan_reset(target, force=True)

    if not path_exists(target) or not plan.manifest:
        print("Preview: reset has nothing to remove")
    else:
        print(f"Preview: action=reset, target={target}, force={'yes' if force else 'no'}")
        print(f"Planned changes: {summarize_actions(plan.planned_actions)}")
    if not prompt_yes_no("Proceed?", default=False):
        print("Cancelled.")
        return 0
    if not path_exists(target):
        print("nothing to reset")
        return 0
    return reset_command(argparse.Namespace(target=str(target), dry_run=False, force=force))


def build_manifest(pack: str, mode: str, target: Path, rendered: dict[str, dict[str, str]]) -> dict[str, Any]:
    return {
        "version": 1,
        "pack": pack,
        "mode": mode,
        "repo_root": str(REPO_ROOT.resolve()),
        "target": str(target),
        "files": {
            filename: {
                "name": info["name"],
                "source": info["source"],
                "installed_sha256": sha256_text(info["content"]),
            }
            for filename, info in sorted(rendered.items())
        },
    }


def sync_command(args: argparse.Namespace) -> int:
    target = ensure_safe_target(args.target, allow_create=True)
    plan = plan_sync(target, args.pack, args.mode, args.force)

    if args.dry_run:
        print_dry_run("sync", target, plan.planned_actions, pack=args.pack, mode=args.mode, force=args.force)
        return 0

    if args.mode == "yolo" and not getattr(args, "confirmed_yolo", False):
        if not confirm_yolo():
            print("Cancelled.")
            return 0

    preflight_sync_mutation(plan)

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SyncError(f"unable to create target directory: {target}: {format_os_error(exc)}") from exc

    preflight_sync_mutation(plan)

    for filename in plan.stale_files:
        path = managed_file_path(target, filename)
        if path_exists(path):
            ensure_regular_file_if_exists(path, "managed file")
            try:
                path.unlink()
            except OSError as exc:
                raise SyncError(f"unable to remove managed file: {path}: {format_os_error(exc)}") from exc

    for filename, info in sorted(plan.rendered.items()):
        atomic_write(target / filename, info["content"], "target file")

    atomic_write(manifest_path(target), json.dumps(build_manifest(args.pack, args.mode, target, plan.rendered), indent=2) + "\n", "manifest path")
    print_actions(plan.planned_actions)
    return 0


def status_payload(target: Path) -> dict[str, Any]:
    manifest = load_manifest(target)
    ok, drifted, missing = managed_state(target, manifest)
    payload = {
        "target": str(target),
        "target_exists": path_exists(target),
        "manifest": manifest is not None,
        "managed_files": len(manifest_files(manifest, target)),
        "ok_files": ok,
        "drifted_files": drifted,
        "missing_files": missing,
    }
    if manifest:
        payload["pack"] = manifest.get("pack")
        payload["mode"] = manifest.get("mode")
    return payload


def status_command(args: argparse.Namespace) -> int:
    target = ensure_safe_target(args.target, allow_create=True)
    payload = status_payload(target)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_status_human(payload))
    return 0


def reset_command(args: argparse.Namespace) -> int:
    target = ensure_safe_target(args.target)
    plan = plan_reset(target, args.force)
    if args.dry_run:
        print_dry_run("reset", target, plan.planned_actions, force=args.force)
        return 0
    if not plan.manifest:
        print("nothing to reset")
        return 0

    preflight_reset_mutation(plan)

    for filename in sorted(manifest_files(plan.manifest, target)):
        path = managed_file_path(target, filename)
        if path_exists(path):
            ensure_regular_file_if_exists(path, "managed file")
            try:
                path.unlink()
            except OSError as exc:
                raise SyncError(f"unable to remove managed file: {path}: {format_os_error(exc)}") from exc
    try:
        manifest_path(target).unlink(missing_ok=True)
    except OSError as exc:
        raise SyncError(f"unable to remove manifest: {manifest_path(target)}: {format_os_error(exc)}") from exc
    print_actions(plan.planned_actions)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync curated OpenCode agent packs into a target directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync", help="sync a curated pack into a target directory")
    sync.add_argument("--pack", required=True, choices=SUPPORTED_PACKS)
    sync.add_argument("--target", required=True)
    sync.add_argument("--mode", default="safe", choices=SUPPORTED_MODES)
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument(
        "--force",
        action="store_true",
        help="overwrite unmanaged conflicts or managed drift; does not bypass safety checks",
    )
    sync.set_defaults(func=sync_command)

    status = subparsers.add_parser("status", help="show managed sync state for a target directory")
    status.add_argument("--target", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=status_command)

    reset = subparsers.add_parser("reset", help="remove only manifest-managed files from a target directory")
    reset.add_argument("--target", required=True)
    reset.add_argument("--dry-run", action="store_true")
    reset.add_argument(
        "--force",
        action="store_true",
        help="remove managed files even when drift/missing files are detected; does not bypass safety checks",
    )
    reset.set_defaults(func=reset_command)

    interactive = subparsers.add_parser("interactive", help="guided interactive wrapper around sync, status, and reset")
    interactive.set_defaults(func=interactive_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
