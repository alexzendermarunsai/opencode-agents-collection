import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "agents_sync.py"


class AgentsSyncTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None, input_text=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd or str(REPO_ROOT),
            text=True,
            input=input_text,
            capture_output=True,
            check=False,
        )

    def test_sync_safe_rewrites_permissions_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            frontend = (target / "frontend-developer.md").read_text(encoding="utf-8")
            self.assertIn("name: Frontend Developer", frontend)
            self.assertIn("  edit: allow\n", frontend)
            self.assertIn("  bash: deny\n", frontend)
            self.assertIn("  webfetch: deny\n", frontend)
            self.assertNotIn("  bash: ask\n", frontend)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn('    "Senior Developer": allow\n', orchestrator)
            self.assertIn('    "Technical Writer": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team")
            self.assertEqual(manifest["mode"], "safe")
            self.assertIn("frontend-developer.md", manifest["files"])

    def test_sync_creates_missing_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing" / "agents"

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(target.is_dir())
            self.assertTrue((target / ".opencode-agents-state.json").exists())

    def test_sync_trusted_preserves_authored_permission_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-plus", "--target", str(target), "--mode", "trusted")
            self.assertEqual(result.returncode, 0, result.stderr)

            content = (target / "devops-automator.md").read_text(encoding="utf-8")
            self.assertIn("  edit: allow\n", content)
            self.assertIn("  bash: ask\n", content)
            self.assertIn("  webfetch: deny\n", content)

    def test_sync_safe_supports_a_team_plus_gpt_5_4_with_plus_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-plus-gpt-5.4", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn('    "AI Engineer": allow\n', orchestrator)
            self.assertIn('    "Rapid Prototyper": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)

            devops = (target / "devops-automator.md").read_text(encoding="utf-8")
            self.assertIn("  edit: deny\n", devops)
            self.assertIn("  bash: deny\n", devops)
            self.assertIn("  webfetch: deny\n", devops)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-plus-gpt-5.4")
            self.assertEqual(manifest["mode"], "safe")

    def test_sync_safe_supports_a_team_plus_gpt_5_5_with_plus_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-plus-gpt-5.5", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn('    "AI Engineer": allow\n', orchestrator)
            self.assertIn('    "Rapid Prototyper": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)

            devops = (target / "devops-automator.md").read_text(encoding="utf-8")
            self.assertIn("  edit: deny\n", devops)
            self.assertIn("  bash: deny\n", devops)
            self.assertIn("  webfetch: deny\n", devops)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-plus-gpt-5.5")
            self.assertEqual(manifest["mode"], "safe")

    def test_sync_safe_supports_a_team_gpt_5_4_with_a_team_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-gpt-5.4", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn('    "Senior Project Manager": allow\n', orchestrator)
            self.assertIn('    "Technical Writer": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)
            self.assertNotIn('    "AI Engineer": allow\n', orchestrator)
            self.assertNotIn('    "DevOps Automator": allow\n', orchestrator)

            frontend = (target / "frontend-developer.md").read_text(encoding="utf-8")
            self.assertIn("  edit: allow\n", frontend)
            self.assertIn("  bash: deny\n", frontend)
            self.assertIn("  webfetch: deny\n", frontend)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-gpt-5.4")
            self.assertEqual(manifest["mode"], "safe")
            self.assertEqual(manifest["files"]["agents-orchestrator.md"]["source"], "a-team-gpt-5.4/agents/agents-orchestrator.md")

    def test_sync_safe_supports_a_team_gpt_5_5_with_a_team_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-gpt-5.5", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn('    "Senior Project Manager": allow\n', orchestrator)
            self.assertIn('    "Technical Writer": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)
            self.assertNotIn('    "AI Engineer": allow\n', orchestrator)
            self.assertNotIn('    "DevOps Automator": allow\n', orchestrator)

            frontend = (target / "frontend-developer.md").read_text(encoding="utf-8")
            self.assertIn("  edit: allow\n", frontend)
            self.assertIn("  bash: deny\n", frontend)
            self.assertIn("  webfetch: deny\n", frontend)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-gpt-5.5")
            self.assertEqual(manifest["mode"], "safe")
            self.assertEqual(manifest["files"]["agents-orchestrator.md"]["source"], "a-team-gpt-5.5/agents/agents-orchestrator.md")

    def test_sync_yolo_rewrites_ask_to_allow_and_records_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli(
                "sync",
                "--pack",
                "a-team",
                "--target",
                str(target),
                "--mode",
                "yolo",
                input_text="YOLO\n",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARNING: YOLO mode removes approval gates for risky actions.", result.stdout)
            self.assertIn("Type YOLO to continue:", result.stdout)

            writer = (target / "technical-writer.md").read_text(encoding="utf-8")
            self.assertIn("  webfetch: allow\n", writer)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn("  bash: allow\n", orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "yolo")

    def test_sync_yolo_cancels_without_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli(
                "sync",
                "--pack",
                "a-team",
                "--target",
                str(target),
                "--mode",
                "yolo",
                input_text="\n",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Cancelled.", result.stdout)
            self.assertFalse((target / ".opencode-agents-state.json").exists())
            self.assertFalse((target / "frontend-developer.md").exists())

    def test_sync_yolo_dry_run_does_not_require_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli(
                "sync",
                "--pack",
                "a-team",
                "--target",
                str(target),
                "--mode",
                "yolo",
                "--dry-run",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("Type YOLO to continue:", result.stdout)
            self.assertFalse((target / ".opencode-agents-state.json").exists())

    def test_sync_detects_drift_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            first = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertEqual(first.returncode, 0, first.stderr)

            path = target / "technical-writer.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nmanual edit\n", encoding="utf-8")

            second = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("drift", second.stderr)

            forced = self.run_cli("sync", "--pack", "a-team", "--target", str(target), "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr)

    def test_sync_refuses_unmanaged_conflict_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / "frontend-developer.md").write_text("local file", encoding="utf-8")

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unmanaged conflicting file exists", result.stderr)

    def test_reset_removes_only_managed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            keep = target / "notes.md"
            keep.write_text("keep me", encoding="utf-8")

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)

            reset = self.run_cli("reset", "--target", str(target))
            self.assertEqual(reset.returncode, 0, reset.stderr)
            self.assertTrue(keep.exists())
            self.assertFalse((target / "frontend-developer.md").exists())
            self.assertFalse((target / ".opencode-agents-state.json").exists())

    def test_status_rejects_manifest_parent_traversal_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / ".opencode-agents-state.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pack": "a-team",
                        "mode": "safe",
                        "files": {
                            "../x": {
                                "name": "bad",
                                "source": "a-team/agents/frontend-developer.md",
                                "installed_sha256": "deadbeef",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_cli("status", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe managed filename", result.stderr)

    def test_reset_rejects_manifest_parent_traversal_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            outside = Path(tmp) / "outside.md"
            outside.write_text("keep", encoding="utf-8")
            (target / ".opencode-agents-state.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pack": "a-team",
                        "mode": "safe",
                        "files": {
                            "../outside.md": {
                                "name": "bad",
                                "source": "a-team/agents/frontend-developer.md",
                                "installed_sha256": "deadbeef",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_cli("reset", "--target", str(target), "--force")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe managed filename", result.stderr)
            self.assertTrue(outside.exists())

    def test_sync_stale_managed_file_removal_stays_within_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            outside = Path(tmp) / "outside.md"
            outside.write_text("keep", encoding="utf-8")
            (target / ".opencode-agents-state.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "pack": "a-team",
                        "mode": "safe",
                        "files": {
                            "../outside.md": {
                                "name": "bad",
                                "source": "a-team/agents/frontend-developer.md",
                                "installed_sha256": "deadbeef",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target), "--force")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe managed filename", result.stderr)
            self.assertTrue(outside.exists())

    def test_sync_rejects_symlink_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_target = Path(tmp) / "real-agents"
            real_target.mkdir()
            target = Path(tmp) / "agents-link"
            target.symlink_to(real_target, target_is_directory=True)

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not be a symlink", result.stderr)

    def test_sync_rejects_inside_repo_target(self):
        target = REPO_ROOT / "tests"

        result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside source repo", result.stderr)

    def test_sync_rejects_git_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".git" / "agents"
            target.parent.mkdir()

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".git path", result.stderr)

    def test_status_rejects_symlinked_managed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)

            managed = target / "frontend-developer.md"
            managed.unlink()
            managed.symlink_to(Path(tmp) / "elsewhere.md")

            status = self.run_cli("status", "--target", str(target))
            self.assertNotEqual(status.returncode, 0)
            self.assertIn("managed file is a symlink", status.stderr)

    def test_status_json_reports_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            result = self.run_cli("sync", "--pack", "a-team-plus", "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)

            path = target / "ai-engineer.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

            status = self.run_cli("status", "--target", str(target), "--json")
            self.assertEqual(status.returncode, 0, status.stderr)
            payload = json.loads(status.stdout)
            self.assertEqual(payload["pack"], "a-team-plus")
            self.assertIn("ai-engineer.md", payload["drifted_files"])

    def test_interactive_sync_uses_guided_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"

            result = self.run_cli(
                "interactive",
                input_text=f"{target}\nsync\na-team\n\ny\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Current state: target=missing, manifest=missing", result.stdout)
            self.assertIn(f"Preview: action=sync, target={target}, pack=a-team, mode=safe, force=no", result.stdout)
            self.assertTrue((target / ".opencode-agents-state.json").exists())

    def test_interactive_sync_prompts_before_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            initial = self.run_cli("sync", "--pack", "a-team", "--target", str(target))
            self.assertEqual(initial.returncode, 0, initial.stderr)

            path = target / "technical-writer.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nmanual edit\n", encoding="utf-8")

            cancelled = self.run_cli(
                "interactive",
                input_text=f"{target}\nsync\na-team\n\nn\n",
            )
            self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
            self.assertIn("Needs force:", cancelled.stdout)
            self.assertIn("Cancelled.", cancelled.stdout)
            self.assertIn("manual edit", path.read_text(encoding="utf-8"))

            forced = self.run_cli(
                "interactive",
                input_text=f"{target}\nsync\na-team\n\ny\ny\n",
            )
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertIn("force=yes", forced.stdout)
            self.assertNotIn("manual edit", path.read_text(encoding="utf-8"))

    def test_interactive_sync_yolo_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"

            result = self.run_cli(
                "interactive",
                input_text=f"{target}\nsync\na-team\nyolo\ny\nYOLO\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Preview: action=sync, target={target}, pack=a-team, mode=yolo, force=no", result.stdout)
            self.assertIn("WARNING: YOLO mode removes approval gates for risky actions.", result.stdout)
            self.assertIn("Type YOLO to continue:", result.stdout)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["mode"], "yolo")


if __name__ == "__main__":
    unittest.main()
