from abc import ABC, abstractmethod


class LauncherGateway(ABC):
    """Infrastructure boundary used by the launcher use case."""

    @abstractmethod
    def is_docker_running(self) -> bool:
        """Return whether Docker is active and reachable."""

    @abstractmethod
    def boot_infrastructure(self) -> None:
        """Start the local Docker-based demo environment."""

    @abstractmethod
    def teardown_infrastructure(self) -> None:
        """Stop the local Docker-based demo environment."""

    @abstractmethod
    def run_python_script(self, script_name: str) -> None:
        """Run one of the interactive scenario scripts."""

    @abstractmethod
    def open_report_portal(self) -> bool:
        """Open the curated report portal or return False if unsupported."""

    @abstractmethod
    def open_readme(self) -> bool:
        """Open the project dashboard or return False if unsupported."""
