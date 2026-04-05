import unittest

from src.application.report_payloads import (
    build_advanced_report_payload,
    build_insider_report_payload,
    build_main_report_payload,
)


class TestBuildMainReportPayload(unittest.TestCase):
    def test_builds_step6_html_evidence_and_artifacts(self):
        payload = build_main_report_payload(
            report_filename="main_scenario_report_20260404_150000.html",
            current_time="2026-04-04 15:00:00",
            target_url="http://localhost:8011/spring-form/login",
            stage2_url="http://localhost:8011/health_check.jsp?pwd=glory&cmd=id",
            all_pass=False,
            labels={"step6": "STEP 6 | Info Leakage"},
            step_descriptions={"step6": "Extract DB credentials"},
            results={"step6": True},
            details={
                "step6": {
                    "clients": ["mysql"],
                    "config_file": "/tmp/application.properties",
                    "raw_props": "spring.datasource.password=secret",
                    "credentials": {
                        "url": "jdbc:mysql://spring-db:3306/sl_db",
                        "user": "sl_admin",
                        "pass": "secret",
                    },
                }
            },
            run_mode="",
            db_dump_result="",
            step8_result="",
            step9_result="",
        )

        self.assertEqual(payload["reportKind"], "main")
        self.assertEqual(payload["artifacts"][2]["value"], "03.FinalReport/main_scenario_report_20260404_150000.pdf")
        self.assertEqual(payload["sections"][0]["severity"], "critical")
        self.assertEqual(payload["sections"][0]["evidence"]["kind"], "html")
        self.assertIn("spring-db", payload["sections"][0]["evidence"]["content"])


class TestBuildInsiderReportPayload(unittest.TestCase):
    def test_builds_sections_from_phase_meta(self):
        payload = build_insider_report_payload(
            report_filename="sub_scenario_insider_threat_20260404_150500.html",
            current_time="2026-04-04 15:05:00",
            results={"phase1": True},
            details={"phase1": "<pre>evidence</pre>"},
            phase_meta=[
                (
                    "phase1",
                    "Phase 1",
                    "정찰",
                    "Low",
                    "desc",
                    "color",
                    "bg",
                    "border",
                )
            ],
        )

        self.assertEqual(payload["reportKind"], "insider")
        self.assertEqual(len(payload["sections"]), 1)
        self.assertEqual(payload["sections"][0]["severity"], "low")
        self.assertEqual(payload["sections"][0]["evidence"]["kind"], "html")


class TestBuildAdvancedReportPayload(unittest.TestCase):
    def test_builds_advanced_bundle_metadata(self):
        payload = build_advanced_report_payload(
            report_filename="Scenario3_AdvancedBypass_20260404_151000.html",
            current_time="2026-04-04 15:10:00",
        )

        self.assertEqual(payload["reportKind"], "advanced")
        self.assertEqual(payload["meta"]["generatedAt"], "2026-04-04 15:10:00")
        self.assertEqual(len(payload["sections"]), 4)
        self.assertEqual(payload["sections"][1]["title"], "Polymorphic Payload")


if __name__ == "__main__":
    unittest.main(verbosity=2)
