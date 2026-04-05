from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MenuOption:
    """CLI launcher menu option."""

    key: str
    label: str
    pause_after: bool = False


@dataclass(frozen=True)
class LauncherStatus:
    """System state rendered in the launcher UI."""

    docker_active: bool


@dataclass(frozen=True)
class LauncherMenu:
    """View model for the launcher menu."""

    status: LauncherStatus
    options: Tuple[MenuOption, ...]


DEFAULT_MENU_OPTIONS: Tuple[MenuOption, ...] = (
    MenuOption("1", "[Phase: Setup] 인프라 구축 (Docker Up)"),
    MenuOption("2", "[Phase: Main] 외부 해커 침투 (Spring4Shell)", pause_after=True),
    MenuOption("3", "[Phase: Inside] 내부자 위협 데이터 유출 (Insider Threat)", pause_after=True),
    MenuOption("4", "[Phase: Advanced] 패치 우회 및 워터홀 공격 (Advanced Bypass)", pause_after=True),
    MenuOption("5", "[Phase: Analyze] 결과 보고서 확인 (Reports)"),
    MenuOption("6", "[Phase: Cleanup] 인프라 종료 (Docker Down)"),
    MenuOption("7", "[System] 프로젝트 대시보드 (README)"),
    MenuOption("q", "종료 (Quit)"),
)
