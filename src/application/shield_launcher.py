from dataclasses import dataclass

from src.domain.launcher import DEFAULT_MENU_OPTIONS, LauncherMenu, LauncherStatus
from src.ports.launcher_gateway import LauncherGateway


@dataclass(frozen=True)
class LauncherOutcome:
    """Result of handling a launcher menu choice."""

    message: str = ""
    delay_seconds: float = 0
    pause_after: bool = False
    should_exit: bool = False


class ShieldLauncherUseCase:
    """Application service coordinating the launcher menu."""

    def __init__(self, gateway: LauncherGateway):
        self.gateway = gateway

    def build_menu(self) -> LauncherMenu:
        return LauncherMenu(
            status=LauncherStatus(docker_active=self.gateway.is_docker_running()),
            options=DEFAULT_MENU_OPTIONS,
        )

    def handle_choice(self, raw_choice: str) -> LauncherOutcome:
        choice = (raw_choice or "").strip().lower()
        option_lookup = {option.key: option for option in DEFAULT_MENU_OPTIONS}

        if choice == "1":
            self.gateway.boot_infrastructure()
            return LauncherOutcome(
                message="\n[OK] Infrastructure booted. Waiting for nodes...",
                delay_seconds=3,
            )

        if choice in {"2", "3", "4"}:
            script_name = {
                "2": "run.py",
                "3": "sub_run.py",
                "4": "scenario3_run.py",
            }[choice]
            self.gateway.run_python_script(script_name)
            return LauncherOutcome(pause_after=option_lookup[choice].pause_after)

        if choice == "5":
            opened = self.gateway.open_report_portal()
            return LauncherOutcome(
                message="" if opened else "\n[*] Open 03.FinalReport/index.html in your browser.",
                delay_seconds=1,
            )

        if choice == "6":
            self.gateway.teardown_infrastructure()
            return LauncherOutcome(
                message="\n[OK] Infrastructure cleared.",
                delay_seconds=2,
            )

        if choice == "7":
            opened = self.gateway.open_readme()
            return LauncherOutcome(
                message="" if opened else "\n[*] Open README.md in your editor.",
                delay_seconds=2,
            )

        if choice == "q":
            return LauncherOutcome(
                message="\nExiting SL Cyber-Shield Simulator.",
                should_exit=True,
            )

        return LauncherOutcome(delay_seconds=1)
