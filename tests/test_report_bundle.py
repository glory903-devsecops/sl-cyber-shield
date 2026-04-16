import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.application.report_bundle import export_report_bundle


class TestReportBundle(unittest.TestCase):
    def test_writes_json_and_manifest_even_when_node_renderer_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "reporting" / "scripts").mkdir(parents=True, exist_ok=True)
            (root / "reporting" / "scripts" / "build-report.mjs").write_text("// renderer", encoding="utf-8")

            with patch("src.application.report_bundle.shutil.which", return_value=None):
                result = export_report_bundle(
                    root,
                    "sample-report.html",
                    {
                        "reportKind": "main",
                        "meta": {"title": "Sample", "generatedAt": "2026-04-04 14:00:00"},
                    },
                )

            self.assertFalse(result.success)
            self.assertTrue(result.json_path.exists())
            self.assertTrue(result.manifest_path.exists())
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["reports"][0]["slug"], "sample-report")
            self.assertEqual(manifest["reports"][0]["kind"], "main")
            self.assertEqual(
                json.loads(result.json_path.read_text(encoding="utf-8"))["meta"]["title"],
                "Sample",
            )

    def test_returns_success_when_renderer_command_succeeds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "reporting" / "scripts").mkdir(parents=True, exist_ok=True)
            (root / "reporting" / "scripts" / "build-report.mjs").write_text("// renderer", encoding="utf-8")

            with patch("src.application.report_bundle.shutil.which", return_value="node"), patch(
                "src.application.report_bundle.subprocess.run"
            ) as mocked_run:
                mocked_run.return_value.returncode = 0
                mocked_run.return_value.stdout = "ok"
                mocked_run.return_value.stderr = ""
                result = export_report_bundle(
                    root,
                    "sample-report.html",
                    {
                        "reportKind": "insider",
                        "meta": {"title": "Sample", "generatedAt": "2026-04-04 14:10:00"},
                    },
                )

            self.assertTrue(result.success)
            self.assertEqual(result.stdout, "ok")
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["reports"][0]["renderer"], "react-static")


if __name__ == "__main__":
    unittest.main(verbosity=2)
