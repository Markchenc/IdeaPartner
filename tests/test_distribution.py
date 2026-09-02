from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_MANIFEST = REPOSITORY_ROOT / ".codex-plugin" / "plugin.json"
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "ideapartner"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from idea_review_runtime import __version__  # noqa: E402


class DistributionTests(unittest.TestCase):
    def test_plugin_manifest_points_to_the_versioned_skill(self) -> None:
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual("ideapartner", manifest["name"])
        self.assertEqual(__version__, manifest["version"])
        self.assertEqual("Apache-2.0", manifest["license"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertTrue((REPOSITORY_ROOT / manifest["skills"]).is_dir())
        self.assertEqual("ideapartner", SKILL_ROOT.name)
        self.assertTrue((SKILL_ROOT / "SKILL.md").is_file())
        self.assertTrue((SKILL_ROOT / "agents" / "openai.yaml").is_file())

        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        interface_text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("name: ideapartner", skill_text.split("---", 2)[1])
        self.assertIn('display_name: "IdeaPartner"', interface_text)
        self.assertIn("$ideapartner", interface_text)

    def test_packaged_copy_runs_from_a_unicode_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            plugin_root = temporary_root / "已安装插件" / "ideapartner"
            shutil.copytree(REPOSITORY_ROOT / ".codex-plugin", plugin_root / ".codex-plugin")
            shutil.copytree(REPOSITORY_ROOT / "skills", plugin_root / "skills")

            work_dir = temporary_root / "研究案例"
            work_dir.mkdir()
            idea_path = work_dir / "idea.md"
            idea_path.write_text("# Idea\n\nEvaluate an early research idea.\n", encoding="utf-8")
            runs_dir = work_dir / "审查运行"
            runtime = plugin_root / "skills" / "ideapartner" / "scripts" / "idea_review.py"
            environment = os.environ.copy()
            environment["PYTHONUTF8"] = "1"

            version = self._run(runtime, "--version", cwd=work_dir, env=environment)
            self.assertEqual(f"IdeaPartner runtime {__version__}", version.stdout.strip())

            initialized = self._run(
                runtime,
                "init",
                idea_path,
                "--runs-dir",
                runs_dir,
                "--run-id",
                "distribution-smoke",
                cwd=work_dir,
                env=environment,
            )
            init_result = json.loads(initialized.stdout)
            self.assertEqual("POSITIONING", init_result["state"])
            self.assertEqual(["m1-positioning"], init_result["ready_tasks"])
            run_manifest = json.loads(
                (runs_dir / "distribution-smoke" / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(__version__, run_manifest["runtime_version"])

            status = self._run(
                runtime,
                "status",
                runs_dir / "distribution-smoke",
                cwd=work_dir,
                env=environment,
            )
            status_result = json.loads(status.stdout)
            self.assertEqual("distribution-smoke", status_result["run_id"])
            self.assertEqual("POSITIONING", status_result["state"])

    def _run(
        self,
        runtime: Path,
        *arguments: object,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(runtime), *(str(argument) for argument in arguments)]
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result
