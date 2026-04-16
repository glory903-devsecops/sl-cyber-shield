import sys
import time
from pathlib import Path

from src.application.shield_launcher import ShieldLauncherUseCase
from src.infrastructure.adapters.subprocess_launcher_gateway import SubprocessLauncherGateway
from src.infrastructure.presenters.console_launcher_presenter import ConsoleLauncherPresenter


def main() -> None:
    project_root = Path(__file__).resolve().parent
    gateway = SubprocessLauncherGateway(project_root)
    presenter = ConsoleLauncherPresenter()
    use_case = ShieldLauncherUseCase(gateway)

    while True:
        presenter.render_menu(use_case.build_menu())
        outcome = use_case.handle_choice(presenter.read_choice())
        presenter.show_message(outcome.message)

        if outcome.pause_after:
            presenter.pause()
        if outcome.delay_seconds:
            time.sleep(outcome.delay_seconds)
        if outcome.should_exit:
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
