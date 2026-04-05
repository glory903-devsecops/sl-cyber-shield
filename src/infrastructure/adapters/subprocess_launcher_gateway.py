import os
import subprocess
import sys
from pathlib import Path

from src.ports.launcher_gateway import LauncherGateway


class SubprocessLauncherGateway(LauncherGateway):
    """OS and subprocess-backed implementation of launcher operations."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def is_docker_running(self) -> bool:
        try:
            subprocess.check_output(["docker", "info"], stderr=subprocess.STDOUT)
            return True
        except Exception:
            return False

    def boot_infrastructure(self) -> None:
        self._run_docker_compose_command(["up", "-d"])

    def teardown_infrastructure(self) -> None:
        self._run_docker_compose_command(["down"])

    def run_python_script(self, script_name: str) -> None:
        subprocess.call([sys.executable, script_name], cwd=self.project_root)

    def open_report_portal(self) -> bool:
        return self._open_path(self.project_root / "03.FinalReport" / "index.html")

    def open_readme(self) -> bool:
        return self._open_path(self.project_root / "README.md")

    def _run_docker_compose_command(self, command: list[str]) -> None:
        compose_cwd = self.project_root / "01.TestServer"
        try:
            subprocess.check_call(["docker", "compose", *command], cwd=compose_cwd)
        except Exception:
            subprocess.call(["docker-compose", *command], cwd=compose_cwd)

    def _open_path(self, path: Path) -> bool:
        if not path.exists():
            return False

        try:
            if sys.platform == "darwin":
                return subprocess.call(["open", str(path)]) == 0
            if sys.platform == "win32":
                os.startfile(str(path))
                return True
            return subprocess.call(["xdg-open", str(path)]) == 0
        except Exception:
            return False
