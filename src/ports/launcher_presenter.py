from abc import ABC, abstractmethod

from src.domain.launcher import LauncherMenu


class LauncherPresenter(ABC):
    """Presentation boundary for the launcher UI."""

    @abstractmethod
    def render_menu(self, menu: LauncherMenu) -> None:
        """Render the launcher menu."""

    @abstractmethod
    def read_choice(self) -> str:
        """Read the user's next choice."""

    @abstractmethod
    def show_message(self, message: str) -> None:
        """Display a follow-up message after an action."""

    @abstractmethod
    def pause(self, prompt: str = "\nPress Enter to continue...") -> None:
        """Wait for user acknowledgement."""
