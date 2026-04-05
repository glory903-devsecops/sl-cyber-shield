import unittest

from src.application.shield_launcher import ShieldLauncherUseCase
from src.ports.launcher_gateway import LauncherGateway


class FakeLauncherGateway(LauncherGateway):
    def __init__(self, docker_running: bool = True):
        self.docker_running = docker_running
        self.booted = False
        self.torn_down = False
        self.ran_scripts: list[str] = []
        self.report_portal_opened = False
        self.readme_opened = False
        self.report_portal_result = True
        self.readme_result = True

    def is_docker_running(self) -> bool:
        return self.docker_running

    def boot_infrastructure(self) -> None:
        self.booted = True

    def teardown_infrastructure(self) -> None:
        self.torn_down = True

    def run_python_script(self, script_name: str) -> None:
        self.ran_scripts.append(script_name)

    def open_report_portal(self) -> bool:
        self.report_portal_opened = True
        return self.report_portal_result

    def open_readme(self) -> bool:
        self.readme_opened = True
        return self.readme_result


class TestShieldLauncherUseCase(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeLauncherGateway(docker_running=True)
        self.use_case = ShieldLauncherUseCase(self.gateway)

    def test_build_menu_reflects_docker_status(self):
        menu = self.use_case.build_menu()
        self.assertTrue(menu.status.docker_active)
        self.assertEqual(menu.options[0].key, "1")
        self.assertEqual(menu.options[-1].key, "q")

    def test_setup_choice_boots_infrastructure(self):
        outcome = self.use_case.handle_choice("1")
        self.assertTrue(self.gateway.booted)
        self.assertIn("Infrastructure booted", outcome.message)
        self.assertEqual(outcome.delay_seconds, 3)

    def test_main_choice_runs_main_script_and_pauses(self):
        outcome = self.use_case.handle_choice("2")
        self.assertEqual(self.gateway.ran_scripts, ["run.py"])
        self.assertTrue(outcome.pause_after)

    def test_inside_choice_runs_sub_script_and_pauses(self):
        outcome = self.use_case.handle_choice("3")
        self.assertEqual(self.gateway.ran_scripts, ["sub_run.py"])
        self.assertTrue(outcome.pause_after)

    def test_advanced_choice_runs_scenario3_script_and_pauses(self):
        outcome = self.use_case.handle_choice("4")
        self.assertEqual(self.gateway.ran_scripts, ["scenario3_run.py"])
        self.assertTrue(outcome.pause_after)

    def test_report_choice_opens_portal(self):
        outcome = self.use_case.handle_choice("5")
        self.assertTrue(self.gateway.report_portal_opened)
        self.assertEqual(outcome.delay_seconds, 1)
        self.assertEqual(outcome.message, "")

    def test_report_choice_returns_fallback_message_when_open_fails(self):
        self.gateway.report_portal_result = False
        outcome = self.use_case.handle_choice("5")
        self.assertIn("03.FinalReport/index.html", outcome.message)

    def test_cleanup_choice_tears_down_infrastructure(self):
        outcome = self.use_case.handle_choice("6")
        self.assertTrue(self.gateway.torn_down)
        self.assertIn("Infrastructure cleared", outcome.message)
        self.assertEqual(outcome.delay_seconds, 2)

    def test_readme_choice_opens_dashboard(self):
        outcome = self.use_case.handle_choice("7")
        self.assertTrue(self.gateway.readme_opened)
        self.assertEqual(outcome.message, "")

    def test_quit_choice_returns_exit_outcome(self):
        outcome = self.use_case.handle_choice("q")
        self.assertTrue(outcome.should_exit)
        self.assertIn("Exiting", outcome.message)

    def test_invalid_choice_is_ignored_without_side_effects(self):
        outcome = self.use_case.handle_choice("invalid")
        self.assertFalse(self.gateway.booted)
        self.assertFalse(self.gateway.torn_down)
        self.assertEqual(self.gateway.ran_scripts, [])
        self.assertEqual(outcome.delay_seconds, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
