import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "agents_sync.py"


def load_agents_sync_module():
    spec = importlib.util.spec_from_file_location("agents_sync_under_test", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load agents_sync.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


AGENTS_SYNC = load_agents_sync_module()


DEEPSEEK_PACKS = ("a-team-deepseekv4-pro", "a-team-plus-deepseekv4-pro")
GPT_5_5_PACKS = ("a-team-gpt-5.5", "a-team-plus-gpt-5.5")

CHINESE_TEAM_EXPECTED_MODELS = {
    "agents-orchestrator.md": "opencode-go/qwen3.6-plus",
    "senior-developer.md": "opencode-go/deepseek-v4-pro",
    "frontend-developer.md": "opencode-go/deepseek-v4-pro",
    "backend-architect.md": "opencode-go/deepseek-v4-pro",
    "senior-project-manager.md": "opencode-go/glm-5.1",
    "ux-researcher.md": "opencode-go/glm-5.1",
    "ux-architect.md": "opencode-go/glm-5.1",
    "ui-designer.md": "opencode-go/glm-5.1",
    "api-tester.md": "opencode-go/glm-5.1",
    "reality-checker.md": "opencode-go/glm-5.1",
    "technical-writer.md": "opencode-go/glm-5.1",
}

DEEPSEEK_EXPECTED_VARIANTS = {
    "accessibility-auditor.md": "high",
    "agents-orchestrator.md": "high",
    "ai-engineer.md": "high",
    "api-tester.md": "medium",
    "backend-architect.md": "medium",
    "devops-automator.md": "medium",
    "frontend-developer.md": "medium",
    "performance-benchmarker.md": "high",
    "rapid-prototyper.md": "low",
    "reality-checker.md": "high",
    "security-engineer.md": "high",
    "senior-developer.md": "high",
    "senior-project-manager.md": "medium",
    "technical-writer.md": "low",
    "ui-designer.md": "low",
    "ux-architect.md": "medium",
    "ux-researcher.md": "medium",
}

GPT_5_5_EXPECTED_REASONING_EFFORT = {
    "accessibility-auditor.md": "high",
    "agents-orchestrator.md": "high",
    "ai-engineer.md": "high",
    "api-tester.md": "medium",
    "backend-architect.md": "medium",
    "devops-automator.md": "medium",
    "frontend-developer.md": "medium",
    "performance-benchmarker.md": "high",
    "rapid-prototyper.md": "low",
    "reality-checker.md": "high",
    "security-engineer.md": "high",
    "senior-developer.md": "high",
    "senior-project-manager.md": "medium",
    "technical-writer.md": "low",
    "ui-designer.md": "low",
    "ux-architect.md": "medium",
    "ux-researcher.md": "medium",
}

GPT_5_5_EXPECTED_PERMISSIONS = {
    "accessibility-auditor.md": {"edit": "deny", "bash": "ask", "webfetch": "deny"},
    "agents-orchestrator.md": {"edit": "deny", "bash": "ask", "webfetch": "deny"},
    "ai-engineer.md": {"edit": "allow", "bash": "ask", "webfetch": "ask"},
    "api-tester.md": {"edit": "deny", "bash": "ask", "webfetch": "ask"},
    "backend-architect.md": {"edit": "allow", "bash": "ask", "webfetch": "deny"},
    "devops-automator.md": {"edit": "allow", "bash": "ask", "webfetch": "deny"},
    "frontend-developer.md": {"edit": "allow", "bash": "ask", "webfetch": "ask"},
    "performance-benchmarker.md": {"edit": "deny", "bash": "ask", "webfetch": "deny"},
    "rapid-prototyper.md": {"edit": "allow", "bash": "ask", "webfetch": "deny"},
    "reality-checker.md": {"edit": "deny", "bash": "ask", "webfetch": "deny"},
    "security-engineer.md": {"edit": "deny", "bash": "ask", "webfetch": "deny"},
    "senior-developer.md": {"edit": "allow", "bash": "ask", "webfetch": "deny"},
    "senior-project-manager.md": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
    "technical-writer.md": {"edit": "allow", "bash": "deny", "webfetch": "ask"},
    "ui-designer.md": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
    "ux-architect.md": {"edit": "deny", "bash": "deny", "webfetch": "deny"},
    "ux-researcher.md": {"edit": "deny", "bash": "deny", "webfetch": "ask"},
}

GPT_5_5_REQUIRED_PROMPT_SECTION_GROUPS = (
    ("Stop Rules",),
    ("Core Responsibilities", "Core Rules"),
    ("Operating Guidance", "Operating Rules", "Default Operating Posture"),
    ("Success Criteria", "Completion Check"),
)

PLUS_ONLY_SPECIALISTS = (
    "Rapid Prototyper",
    "AI Engineer",
    "Performance Benchmarker",
    "Security Engineer",
    "Accessibility Auditor",
    "DevOps Automator",
)

LEAN_DEEPSEEK_TRIGGER_TERMS = {
    "Senior Project Manager": ("scope", "sequencing", "dependencies", "acceptance criteria"),
    "UX Researcher": ("user evidence", "usability signals", "feedback interpretation", "evidence gaps"),
    "UX Architect": ("flows", "ia", "forms", "navigation", "layout structure", "accessibility foundations"),
    "UI Designer": ("visual hierarchy", "components", "typography", "color", "states", "polish"),
    "Frontend Developer": ("ui implementation", "responsive behavior", "browser/app-flow checks"),
    "Backend Architect": ("apis", "data models", "auth", "integrations", "service boundaries", "reliability"),
    "Senior Developer": ("complex cross-layer implementation", "refactors", "integration cleanup"),
    "API Tester": ("api contracts", "auth", "validation", "error behavior", "integration testing"),
    "Reality Checker": ("final skeptical validation", "evidence gaps", "ship/handoff readiness"),
    "Technical Writer": ("readme", "guides", "references", "onboarding", "release notes", "documentation"),
}

LEAN_MISSING_SPECIALIST_FALLBACK_PATTERN = r"missing[-\s]+specialist|no\s+suitable\s+registered\s+agent(?:\s+existed)?"


class AgentsSyncTests(unittest.TestCase):
    def deepseek_agent_paths(self):
        for pack in DEEPSEEK_PACKS:
            agent_paths = sorted((REPO_ROOT / pack / "agents").glob("*.md"))
            self.assertTrue(agent_paths, pack)
            for path in agent_paths:
                yield pack, path

    def gpt_5_5_agent_paths(self):
        for pack in GPT_5_5_PACKS:
            agent_paths = sorted((REPO_ROOT / pack / "agents").glob("*.md"))
            self.assertTrue(agent_paths, pack)
            for path in agent_paths:
                yield pack, path

    def chinese_team_agent_paths(self):
        agent_paths = sorted((REPO_ROOT / "chinese-team" / "agents").glob("*.md"))
        self.assertTrue(agent_paths, "chinese-team")
        for path in agent_paths:
            yield path

    def read_agent_parts(self, path):
        content = path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"), path.name)
        _, frontmatter, body = content.split("---\n", 2)
        fields = {}
        for line in frontmatter.splitlines():
            if ": " in line and not line.startswith(" "):
                key, value = line.split(": ", 1)
                fields[key] = value
        return content, fields, body

    def parse_task_allowlist(self, content):
        _, frontmatter, _ = content.split("---\n", 2)
        allowlist = []
        in_task_block = False
        for line in frontmatter.splitlines():
            if line == "  task:":
                in_task_block = True
                continue
            if not in_task_block:
                continue
            if not line.startswith("    "):
                break
            match = re.fullmatch(r'    "([^"]+)": allow', line)
            if match and match.group(1) != "*":
                allowlist.append(match.group(1))
        return allowlist

    def parse_permission_block(self, content):
        _, frontmatter, _ = content.split("---\n", 2)
        permissions = {}
        in_permission_block = False
        for line in frontmatter.splitlines():
            if line == "permission:":
                in_permission_block = True
                continue
            if not in_permission_block:
                continue
            if not line.startswith("  "):
                break
            match = re.fullmatch(r"  (edit|bash|webfetch): (allow|ask|deny)", line)
            if match:
                permissions[match.group(1)] = match.group(2)
        return permissions

    def markdown_headings(self, body):
        return set(re.findall(r"^## (.+)$", body, re.MULTILINE))

    def markdown_section(self, body, heading):
        match = re.search(rf"^## {re.escape(heading)}\n\n(?P<section>.*?)(?=\n## |\Z)", body, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, heading)
        return match.group("section")

    def backticked_bullets_in_section(self, body, heading):
        section = self.markdown_section(body, heading)
        return re.findall(r"^- `([^`]+)`(?::|$)", section, re.MULTILINE)

    def specialist_trigger_rows(self, section):
        rows = {}
        for line in section.splitlines():
            match = re.fullmatch(r"\| `([^`]+)` \| (.+) \|", line)
            if match:
                rows[match.group(1)] = match.group(2)
        return rows

    def run_cli(self, *args, cwd=None, input_text=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd or str(REPO_ROOT),
            text=True,
            input=input_text,
            capture_output=True,
            check=False,
        )

    def run_main(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = AGENTS_SYNC.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def assert_friendly_probe_error(self, stderr, expected):
        self.assertIn("error:", stderr)
        self.assertIn(expected, stderr)
        self.assertIn("Permission denied", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_gpt_5_5_source_agents_use_gpt_5_5_model_and_reasoning_effort(self):
        for pack, path in self.gpt_5_5_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                _, fields, _ = self.read_agent_parts(path)
                self.assertIn(path.name, GPT_5_5_EXPECTED_REASONING_EFFORT)
                self.assertEqual(fields.get("model"), "openai/gpt-5.5")
                self.assertEqual(fields.get("reasoningEffort"), GPT_5_5_EXPECTED_REASONING_EFFORT[path.name])

    def test_gpt_5_5_source_agents_include_expected_permissions(self):
        for pack, path in self.gpt_5_5_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                content, _, _ = self.read_agent_parts(path)
                self.assertIn(path.name, GPT_5_5_EXPECTED_PERMISSIONS)
                self.assertEqual(self.parse_permission_block(content), GPT_5_5_EXPECTED_PERMISSIONS[path.name])

    def test_gpt_5_5_source_agents_keep_required_prompt_sections(self):
        for pack, path in self.gpt_5_5_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                _, _, body = self.read_agent_parts(path)
                headings = self.markdown_headings(body)
                for alternatives in GPT_5_5_REQUIRED_PROMPT_SECTION_GROUPS:
                    self.assertTrue(
                        headings.intersection(alternatives),
                        f"{path.name} missing one of: {', '.join(alternatives)}",
                    )

    def test_gpt_5_5_source_agents_do_not_include_deepseek_model_remnants(self):
        forbidden_literals = ("opencode-go/deepseek-v4-pro", "deepseek-v4-pro")

        for pack, path in self.gpt_5_5_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                content, _, _ = self.read_agent_parts(path)
                for literal in forbidden_literals:
                    self.assertNotIn(literal, content, path.name)

    def test_chinese_team_source_agents_use_expected_models_without_extra_routing_metadata(self):
        a_team_files = sorted(path.name for path in (REPO_ROOT / "a-team" / "agents").glob("*.md"))
        chinese_team_files = sorted(path.name for path in (REPO_ROOT / "chinese-team" / "agents").glob("*.md"))

        self.assertEqual(chinese_team_files, a_team_files)
        self.assertEqual(set(chinese_team_files), set(CHINESE_TEAM_EXPECTED_MODELS))
        for path in self.chinese_team_agent_paths():
            with self.subTest(agent=path.name):
                _, fields, body = self.read_agent_parts(path)
                self.assertEqual(fields.get("model"), CHINESE_TEAM_EXPECTED_MODELS[path.name])
                self.assertNotIn("variant", fields)
                self.assertNotIn("reasoningEffort", fields)

                if path.name == "agents-orchestrator.md":
                    self.assertIn("## Orchestration Operating Guidance", body)
                    self.assertIn("workstream ledger", body)
                    self.assertIn("Route by specialist responsibility", body)
                    self.assertIn("Parallelize only when workstreams are genuinely independent", body)
                    self.assertIn("Make every specialist handoff explicit", body)
                    self.assertIn("Require evidence before advancing a workstream", body)
                    self.assertIn("Handle conflicts by naming the disagreement", body)
                    self.assertIn("Do not resolve conflicts by taking over specialist work yourself", body)
                    self.assertIn(
                        "Final synthesis must distinguish verified evidence, specialist claims that were not independently verified, unresolved risks, and recommended next checks",
                        body,
                    )
                    self.assertNotIn("## Chinese Model Operating Guidance", body)
                    for forbidden in ("Qwen", "DeepSeek", "GLM", "Chinese model", "model family"):
                        self.assertNotIn(forbidden, body)

    def test_deepseek_source_agents_use_deepseek_v4_pro_model_and_variant(self):
        for pack, path in self.deepseek_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                _, fields, _ = self.read_agent_parts(path)
                self.assertEqual(fields.get("model"), "opencode-go/deepseek-v4-pro")
                self.assertEqual(fields.get("variant"), DEEPSEEK_EXPECTED_VARIANTS[path.name])

    def test_deepseek_source_agents_include_native_structured_prompt_guidance(self):
        required_markers = (
            "## DeepSeek v4 Pro Operating Guidance",
            "[Context]",
            "[Task]",
            "[Format]",
        )
        required_wording = (
            r"\bevidence\b",
            r"\bvalidat(?:e|ed|ion)\b",
            r"\buncertain(?:ty)?\b",
        )

        for pack, path in self.deepseek_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                _, _, body = self.read_agent_parts(path)
                for marker in required_markers:
                    self.assertIn(marker, body, path.name)
                for pattern in required_wording:
                    self.assertRegex(body, pattern, path.name)

    def test_deepseek_source_agents_do_not_include_gpt_model_remnants(self):
        forbidden_literals = ("reasoningEffort:", "openai/")
        forbidden_gpt_model_id = re.compile(r"\bgpt-\d", re.IGNORECASE)

        for pack, path in self.deepseek_agent_paths():
            with self.subTest(pack=pack, agent=path.name):
                content, _, _ = self.read_agent_parts(path)
                for literal in forbidden_literals:
                    self.assertNotIn(literal, content, path.name)
                self.assertIsNone(forbidden_gpt_model_id.search(content), path.name)

    def test_deepseek_orchestrators_route_with_declared_task_names(self):
        for pack in DEEPSEEK_PACKS:
            with self.subTest(pack=pack):
                agents_dir = REPO_ROOT / pack / "agents"
                orchestrator_path = agents_dir / "agents-orchestrator.md"
                content, _, body = self.read_agent_parts(orchestrator_path)

                allowlist = self.parse_task_allowlist(content)
                declared_names = []
                filename_stems = set()
                for agent_path in sorted(agents_dir.glob("*.md")):
                    if agent_path.name == "agents-orchestrator.md":
                        continue
                    _, fields, _ = self.read_agent_parts(agent_path)
                    declared_names.append(fields["name"])
                    filename_stems.add(agent_path.stem)

                registered_targets = self.backticked_bullets_in_section(body, "Registered Delegation Targets")
                routing_targets = self.backticked_bullets_in_section(body, "Routing Guide")

                self.assertEqual(set(allowlist), set(declared_names))
                self.assertCountEqual(registered_targets, allowlist)
                self.assertCountEqual(routing_targets, allowlist)
                self.assertFalse(filename_stems.intersection(registered_targets + routing_targets))

    def test_deepseek_orchestrators_define_delegation_first_boundary(self):
        specialist_domains = (
            "specialist judgment",
            "meaningful execution effort",
            "implementation",
            "design",
            "research",
            "testing",
            "documentation",
            "deployment",
            "audits",
            "validation",
        )
        direct_allowances = (
            "clarification",
            "decomposition",
            "routing",
            "light inspection",
            "merging specialist outputs",
            "concise synthesis",
            "trivial direct answers",
        )

        for pack in DEEPSEEK_PACKS:
            with self.subTest(pack=pack):
                orchestrator_path = REPO_ROOT / pack / "agents" / "agents-orchestrator.md"
                _, _, body = self.read_agent_parts(orchestrator_path)

                boundary = self.markdown_section(body, "Delegation-First Boundary")
                boundary_lower = boundary.lower()

                for domain in specialist_domains:
                    self.assertIn(domain, boundary_lower)
                self.assertRegex(boundary_lower, r"default\s+to\s+delegation")
                self.assertRegex(boundary_lower, r"matching\s+registered\s+agent\s+exists")
                self.assertRegex(boundary_lower, r"fewest useful tool loops.*must not.*skip required delegation")

                for allowance in direct_allowances:
                    self.assertIn(allowance, boundary_lower)

    def test_deepseek_orchestrators_reject_self_execution_and_check_delegation(self):
        for pack in DEEPSEEK_PACKS:
            with self.subTest(pack=pack):
                orchestrator_path = REPO_ROOT / pack / "agents" / "agents-orchestrator.md"
                _, _, body = self.read_agent_parts(orchestrator_path)

                rules = self.markdown_section(body, "Orchestration Rules")
                contract = self.markdown_section(body, "Delegation Contract and Completion Check")

                self.assertRegex(
                    rules.lower(),
                    r"do not perform specialist work yourself when a matching specialist exists",
                )
                self.assertRegex(contract.lower(), r"verify specialist work was delegated rather than absorbed")
                self.assertRegex(contract.lower(), r"suitable registered agent existed")
                self.assertIn("declared display name", (rules + contract).lower())

    def test_deepseek_plus_orchestrator_names_plus_domains_for_delegation(self):
        orchestrator_path = REPO_ROOT / "a-team-plus-deepseekv4-pro" / "agents" / "agents-orchestrator.md"
        _, _, body = self.read_agent_parts(orchestrator_path)
        delegation_text = (
            self.markdown_section(body, "Delegation-First Boundary")
            + "\n"
            + self.markdown_section(body, "Orchestration Rules")
        )

        for domain in ("security", "accessibility", "performance", "AI", "deployment"):
            with self.subTest(domain=domain):
                self.assertRegex(delegation_text, re.compile(rf"\b{re.escape(domain)}\b", re.IGNORECASE))

    def test_deepseek_lean_orchestrator_has_specialist_routing_trigger_table(self):
        orchestrator_path = REPO_ROOT / "a-team-deepseekv4-pro" / "agents" / "agents-orchestrator.md"
        content, _, body = self.read_agent_parts(orchestrator_path)
        section = self.markdown_section(body, "Specialist Routing Triggers")
        rows = self.specialist_trigger_rows(section)
        section_lower = section.lower()
        content_lower = content.lower()

        self.assertRegex(section_lower, r"materially\s+involves")
        self.assertRegex(section_lower, r"delegate[\s\S]+matching\s+specialist")
        self.assertRegex(section_lower, r"before\s+substantive\s+analysis")
        self.assertRegex(section_lower, r"final\s+synthesis")
        self.assertRegex(section_lower, r"do not perform[\s\S]+substantive work yourself")
        self.assertRegex(section_lower, r"registered agent exists")
        self.assertRegex(section_lower, r"trivial\s+direct\s+answers[\s\S]+identify[\s\S]+owning\s+specialist\s+only")
        self.assertNotRegex(content_lower, LEAN_MISSING_SPECIALIST_FALLBACK_PATTERN)

        self.assertCountEqual(rows.keys(), self.parse_task_allowlist(content))
        for specialist in PLUS_ONLY_SPECIALISTS:
            self.assertNotIn(specialist, rows)
            self.assertNotIn(f"`{specialist}`".lower(), section_lower)
            self.assertNotIn(specialist.lower(), content_lower)

    def test_deepseek_lean_orchestrator_trigger_table_names_key_domains(self):
        orchestrator_path = REPO_ROOT / "a-team-deepseekv4-pro" / "agents" / "agents-orchestrator.md"
        _, _, body = self.read_agent_parts(orchestrator_path)
        section = self.markdown_section(body, "Specialist Routing Triggers")
        rows = self.specialist_trigger_rows(section)

        self.assertCountEqual(rows, LEAN_DEEPSEEK_TRIGGER_TERMS)
        for specialist, terms in LEAN_DEEPSEEK_TRIGGER_TERMS.items():
            with self.subTest(specialist=specialist):
                row = rows[specialist].lower()
                for term in terms:
                    self.assertIn(term, row)

    def test_deepseek_plus_orchestrator_has_specialist_routing_trigger_table(self):
        orchestrator_path = REPO_ROOT / "a-team-plus-deepseekv4-pro" / "agents" / "agents-orchestrator.md"
        content, _, body = self.read_agent_parts(orchestrator_path)
        section = self.markdown_section(body, "Specialist Routing Triggers")
        rows = self.specialist_trigger_rows(section)
        section_lower = section.lower()

        self.assertNotIn("DevOps Mandatory Routing Gate", body)
        self.assertRegex(section_lower, r"materially\s+involves")
        self.assertRegex(section_lower, r"delegate[\s\S]+matching\s+specialist")
        self.assertRegex(section_lower, r"before\s+substantive\s+analysis")
        self.assertRegex(section_lower, r"final\s+synthesis")
        self.assertRegex(section_lower, r"do not perform[\s\S]+substantive work yourself")
        self.assertRegex(section_lower, r"registered agent exists")
        self.assertRegex(section_lower, r"trivial\s+direct\s+answers[\s\S]+identify[\s\S]+owning\s+specialist\s+only")
        self.assertNotIn("`devops-automator`", section_lower)

        self.assertCountEqual(rows, self.parse_task_allowlist(content))

    def test_deepseek_plus_orchestrator_trigger_table_names_key_domains(self):
        orchestrator_path = REPO_ROOT / "a-team-plus-deepseekv4-pro" / "agents" / "agents-orchestrator.md"
        _, _, body = self.read_agent_parts(orchestrator_path)
        section = self.markdown_section(body, "Specialist Routing Triggers")
        rows = self.specialist_trigger_rows(section)

        expected_terms = {
            "DevOps Automator": (
                "ci/cd",
                "deployment",
                "deploy",
                "release",
                "infrastructure",
                "infra",
                "environments",
                "env vars",
                "runtime configuration",
                "containers",
                "docker",
                "github actions",
                "workflows",
                "rollback",
                "monitoring",
                "operational safety",
                "production",
                "runtime reliability",
            ),
            "Security Engineer": ("auth risk", "permissions", "secrets", "vulnerabilities", "exposure", "hardening"),
            "Accessibility Auditor": ("wcag", "keyboard flow", "semantics", "contrast", "screen-reader risk"),
            "Performance Benchmarker": ("latency", "throughput", "benchmarks", "bottlenecks", "load/scalability"),
            "AI Engineer": ("prompts", "model behavior", "evals", "retrieval/ranking/generation", "inference workflows"),
            "API Tester": ("api contracts", "auth", "validation", "error behavior", "integration testing"),
            "Frontend Developer": ("ui implementation", "responsive behavior", "browser/app-flow checks"),
            "Backend Architect": ("apis", "data models", "auth", "integrations", "service boundaries", "reliability"),
        }

        for specialist, terms in expected_terms.items():
            with self.subTest(specialist=specialist):
                row = rows[specialist].lower()
                for term in terms:
                    self.assertIn(term, row)

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

    def test_sync_safe_supports_a_team_deepseekv4_pro_with_a_team_permissions_and_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-deepseekv4-pro", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/deepseek-v4-pro\n", orchestrator)
            self.assertIn("variant: high\n", orchestrator)
            self.assertIn('    "Senior Project Manager": allow\n', orchestrator)
            self.assertIn('    "Technical Writer": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)
            self.assertNotIn('    "AI Engineer": allow\n', orchestrator)
            self.assertNotIn('    "DevOps Automator": allow\n', orchestrator)

            frontend = (target / "frontend-developer.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/deepseek-v4-pro\n", frontend)
            self.assertIn("variant: medium\n", frontend)
            self.assertIn("  edit: allow\n", frontend)
            self.assertIn("  bash: deny\n", frontend)
            self.assertIn("  webfetch: deny\n", frontend)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-deepseekv4-pro")
            self.assertEqual(manifest["mode"], "safe")
            self.assertEqual(manifest["files"]["agents-orchestrator.md"]["source"], "a-team-deepseekv4-pro/agents/agents-orchestrator.md")

    def test_sync_safe_supports_chinese_team_with_lean_permissions_and_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "chinese-team", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/qwen3.6-plus\n", orchestrator)
            self.assertIn('    "Senior Project Manager": allow\n', orchestrator)
            self.assertIn('    "Technical Writer": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)
            self.assertNotIn('    "AI Engineer": allow\n', orchestrator)
            self.assertNotIn('    "DevOps Automator": allow\n', orchestrator)

            frontend = (target / "frontend-developer.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/deepseek-v4-pro\n", frontend)
            self.assertIn("  edit: allow\n", frontend)
            self.assertIn("  bash: deny\n", frontend)
            self.assertIn("  webfetch: deny\n", frontend)

            api_tester = (target / "api-tester.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/glm-5.1\n", api_tester)
            self.assertIn("  edit: deny\n", api_tester)
            self.assertIn("  bash: deny\n", api_tester)
            self.assertIn("  webfetch: ask\n", api_tester)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "chinese-team")
            self.assertEqual(manifest["mode"], "safe")
            self.assertEqual(manifest["files"]["agents-orchestrator.md"]["source"], "chinese-team/agents/agents-orchestrator.md")

    def test_sync_safe_supports_a_team_plus_deepseekv4_pro_with_plus_permissions_and_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("sync", "--pack", "a-team-plus-deepseekv4-pro", "--target", str(target), "--mode", "safe")
            self.assertEqual(result.returncode, 0, result.stderr)

            orchestrator = (target / "agents-orchestrator.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/deepseek-v4-pro\n", orchestrator)
            self.assertIn("variant: high\n", orchestrator)
            self.assertIn('    "AI Engineer": allow\n', orchestrator)
            self.assertIn('    "Rapid Prototyper": allow\n', orchestrator)
            self.assertIn('    "*": deny\n', orchestrator)

            devops = (target / "devops-automator.md").read_text(encoding="utf-8")
            self.assertIn("model: opencode-go/deepseek-v4-pro\n", devops)
            self.assertIn("variant: medium\n", devops)
            self.assertIn("  edit: deny\n", devops)
            self.assertIn("  bash: deny\n", devops)
            self.assertIn("  webfetch: deny\n", devops)

            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-plus-deepseekv4-pro")
            self.assertEqual(manifest["mode"], "safe")
            self.assertEqual(manifest["files"]["agents-orchestrator.md"]["source"], "a-team-plus-deepseekv4-pro/agents/agents-orchestrator.md")

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
            self.assertIn("DRY RUN: no files will be changed", result.stdout)
            self.assertIn(f"Context: action=sync, target={target}, pack=a-team, mode=yolo, force=no", result.stdout)
            self.assertIn("Planned changes:", result.stdout)
            self.assertIn("Detailed actions:", result.stdout)
            self.assertNotIn("Type YOLO to continue:", result.stdout)
            self.assertFalse((target / ".opencode-agents-state.json").exists())

    def test_sync_rejects_target_file_directory_with_friendly_error_even_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / "frontend-developer.md").mkdir()

            result = self.run_cli("sync", "--pack", "a-team", "--target", str(target), "--force")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("target file must be a regular file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

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

    def test_reset_dry_run_without_manifest_prints_noop_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            result = self.run_cli("reset", "--target", str(target), "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("DRY RUN: no files will be changed", result.stdout)
            self.assertIn(f"Context: action=reset, target={target}, force=no", result.stdout)
            self.assertIn("Planned changes: no changes", result.stdout)
            self.assertIn("Detailed actions:", result.stdout)
            self.assertNotIn("nothing to reset", result.stdout)

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

    def test_status_missing_safe_target_reports_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing" / "agents"

            result = self.run_cli("status", "--target", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("target state: missing", result.stdout)
            self.assertIn("manifest: missing", result.stdout)
            self.assertIn("managed files: 0", result.stdout)
            self.assertFalse(target.exists())

    def test_status_json_missing_safe_target_reports_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing" / "agents"

            result = self.run_cli("status", "--target", str(target), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["target"], str(target))
            self.assertFalse(payload["target_exists"])
            self.assertFalse(payload["manifest"])
            self.assertEqual(payload["managed_files"], 0)
            self.assertEqual(payload["drifted_files"], [])
            self.assertEqual(payload["missing_files"], [])
            self.assertFalse(target.exists())

    def test_status_rejects_manifest_directory_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / ".opencode-agents-state.json").mkdir()

            result = self.run_cli("status", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("manifest path must be a regular file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_status_rejects_invalid_utf8_manifest_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / ".opencode-agents-state.json").write_bytes(b"\xff")

            result = self.run_cli("status", "--target", str(target))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("manifest path is not valid UTF-8", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_status_handles_is_symlink_probe_failure_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            with mock.patch.object(type(target), "is_symlink", side_effect=PermissionError(13, "Permission denied")):
                code, stdout, stderr = self.run_main("status", "--target", str(target))

            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assert_friendly_probe_error(stderr, "unable to inspect target directory")

    def test_status_handles_is_dir_probe_failure_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()

            with mock.patch.object(type(target), "is_dir", side_effect=PermissionError(13, "Permission denied")):
                code, stdout, stderr = self.run_main("status", "--target", str(target))

            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assert_friendly_probe_error(stderr, "unable to inspect target directory")

    def test_status_handles_is_file_probe_failure_with_friendly_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            (target / ".opencode-agents-state.json").write_text("{}", encoding="utf-8")

            with mock.patch.object(type(target), "is_file", side_effect=PermissionError(13, "Permission denied")):
                code, stdout, stderr = self.run_main("status", "--target", str(target))

            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assert_friendly_probe_error(stderr, "unable to inspect manifest path")

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

    def test_interactive_choices_accept_numeric_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"

            result = self.run_cli(
                "interactive",
                input_text=f"{target}\n1\n3\n2\ny\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Action:\n  1) sync\n  2) status\n  3) reset", result.stdout)
            self.assertIn("Pack:\n  1) a-team\n  2) a-team-gpt-5.4\n  3) a-team-gpt-5.5\n  4) a-team-deepseekv4-pro", result.stdout)
            self.assertIn("Mode:\n  1) safe\n  2) trusted\n  3) yolo", result.stdout)
            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-gpt-5.5")
            self.assertEqual(manifest["mode"], "trusted")

    def test_prompt_choice_accepts_exact_text_and_empty_default(self):
        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=["trusted"]), contextlib.redirect_stdout(stdout):
            self.assertEqual(
                AGENTS_SYNC.prompt_choice("Mode", AGENTS_SYNC.SUPPORTED_MODES, default="safe"),
                "trusted",
            )

        with mock.patch("builtins.input", side_effect=[""]), contextlib.redirect_stdout(stdout):
            self.assertEqual(
                AGENTS_SYNC.prompt_choice("Mode", AGENTS_SYNC.SUPPORTED_MODES, default="safe"),
                "safe",
            )

    def test_prompt_choice_reprompts_empty_without_default_and_invalid_input(self):
        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=["", "4", "2"]), contextlib.redirect_stdout(stdout):
            result = AGENTS_SYNC.prompt_choice("Action", ("sync", "status", "reset"))

        self.assertEqual(result, "status")
        self.assertIn("Please choose a number from 1-3 or one of: sync, status, reset", stdout.getvalue())

    def test_interactive_status_is_read_only_without_proceed_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"

            result = self.run_cli(
                "interactive",
                input_text=f"{target}\nstatus\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("target state: missing", result.stdout)
            self.assertIn("manifest: missing", result.stdout)
            self.assertNotIn("Proceed?", result.stdout)
            self.assertFalse(target.exists())

    def test_interactive_sync_defaults_to_manifest_pack_and_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agents"
            target.mkdir()
            initial = self.run_cli("sync", "--pack", "a-team-plus", "--target", str(target), "--mode", "trusted")
            self.assertEqual(initial.returncode, 0, initial.stderr)

            result = self.run_cli(
                "interactive",
                input_text=f"{target}\nsync\n\n\ny\n",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Preview: action=sync, target={target}, pack=a-team-plus, mode=trusted, force=no", result.stdout)
            manifest = json.loads((target / ".opencode-agents-state.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["pack"], "a-team-plus")
            self.assertEqual(manifest["mode"], "trusted")

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
