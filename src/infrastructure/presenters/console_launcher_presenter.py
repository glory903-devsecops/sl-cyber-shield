import os

from src.domain.launcher import LauncherMenu
from src.ports.launcher_presenter import LauncherPresenter


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class ConsoleLauncherPresenter(LauncherPresenter):
    """Console-bound presenter for the launcher menu."""

    def render_menu(self, menu: LauncherMenu) -> None:
        self._clear_screen()
        self._print_header()
        status_text = (
            f"{Colors.OKGREEN}[RUNNING]{Colors.ENDC}"
            if menu.status.docker_active
            else f"{Colors.FAIL}[NOT FOUND]{Colors.ENDC}"
        )
        print(f"  System Status: {status_text}")
        print("\n  Select Simulation Phase:")

        for option in menu.options:
            color = Colors.WARNING if option.key == "q" else Colors.OKCYAN
            print(f"  {color}{option.key}.{Colors.ENDC} {option.label}")

    def read_choice(self) -> str:
        return input("\n  Choice > ")

    def show_message(self, message: str) -> None:
        if message:
            print(message)

    def pause(self, prompt: str = "\nPress Enter to continue...") -> None:
        input(prompt)

    def _clear_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _print_header(self) -> None:
        ascii_art = f"""
    {Colors.OKCYAN}{Colors.BOLD}
     ██████  ██    ██ ██████  ███████ ██████      ███████ ██   ██ ██ ███████ ██      ██████
    ██       ██    ██ ██   ██ ██      ██   ██     ██      ██   ██ ██ ██      ██      ██   ██
    ██        ██  ██  ██████  █████   ██████      ███████ ███████ ██ █████   ██      ██   ██
    ██         ████   ██   ██ ██      ██   ██          ██ ██   ██ ██ ██      ██      ██   ██
     ██████     ██    ██████  ███████ ██   ██     ███████ ██   ██ ██ ███████ ███████ ██████
    {Colors.ENDC}"""
        print(ascii_art)
        print(f"      {Colors.BOLD}SL Factory Innovation | Cyber Security Attack-Range Simulator{Colors.ENDC}")
        print(f"      {'=' * 75}")
