"""
test_stage3_lateral_movement.py — Stage 3 Unit Tests
Spring4Shell (CVE-2022-22965) — 횡적 이동(Lateral Movement) 유닛 테스트

[설계 원칙 — SOLID]
- SRP : LateralMovementCoordinator의 각 메서드를 독립적인 테스트 클래스로 분리합니다.
- OCP : FakeNetworkAdapter로 새로운 시나리오 추가 시 기존 코드 수정 없이 테스트 확장 가능합니다.
- LSP : FakeRCEExecutor는 실 execute_rce()와 동일한 시그니처를 유지합니다.
- ISP : 각 테스트는 최소한의 인터페이스만 활용합니다.
- DIP : 테스트는 LateralMovementCoordinator의 execute_rce() 메서드를 Monkeypatch하여
        실제 네트워크에 의존하지 않습니다.

[Clean Architecture 계층]
  Application ← LateralMovementCoordinator (Use Case 조율자)
  Adapter     ← execute_rce (웹쉘 통신 어댑터)
  Test        ← Unit Tests (어댑터를 Mock으로 교체)

[교육 목적]
  실제 Spring, TeamCity, Struts, NAS 서버가 없어도 동작합니다.
  Monkeypatch로 execute_rce를 가로채 사전 정의된 응답을 반환합니다.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage3_lateral_movement import LateralMovementCoordinator


# ═══════════════════════════════════════════
# Test Doubles & Helpers
# ═══════════════════════════════════════════

class RCEScriptLog:
    """
    [DIP] execute_rce 호출 기록 저장소.
    테스트에서 어떤 명령이 실행되었는지 추적합니다.
    """
    def __init__(self):
        self.commands = []
        self.responses = {}
        self.default_response = ""

    def set_response(self, keyword: str, response: str):
        """특정 키워드가 포함된 명령에 대해 응답을 사전 등록합니다."""
        self.responses[keyword] = response

    def execute(self, cmd: str) -> str:
        self.commands.append(cmd)
        for keyword, response in self.responses.items():
            if keyword in cmd:
                return response
        return self.default_response


def make_coordinator_with_fake_rce(script_log: RCEScriptLog) -> LateralMovementCoordinator:
    """
    [Factory] LateralMovementCoordinator를 생성하고 execute_rce를 Fake로 교체합니다.
    """
    coordinator = LateralMovementCoordinator(
        stage2_url="http://localhost:8011/health_check.jsp",
        pwd="glory"
    )
    # [Monkeypatch] 실제 HTTP 요청을 Fake로 교체 — DIP 구현
    coordinator.execute_rce = script_log.execute
    return coordinator


# ═══════════════════════════════════════════
# Test Suite 1: LateralMovementCoordinator 초기화
# SRP: 객체 생성 로직만 검증
# ═══════════════════════════════════════════

class TestLateralMovementCoordinatorInit(unittest.TestCase):
    """
    [테스트 목적] 생성자가 URL 파싱 및 내부 속성을 올바르게 초기화하는지 검증.
    """

    def setUp(self):
        self.stage2_url = "http://localhost:8011/health_check.jsp"
        self.coordinator = LateralMovementCoordinator(self.stage2_url, pwd="glory")

    def test_shell_url_is_set_from_stage2_url(self):
        """⬛ [초기화] shell_url은 stage2_url에서 경로까지 올바르게 파싱되어야 한다."""
        self.assertIn("localhost:8011", self.coordinator.shell_url)
        self.assertIn("health_check.jsp", self.coordinator.shell_url)

    def test_proxy_shell_url_uses_same_host(self):
        """⬛ [초기화] proxy_shell_url은 stage2_url과 동일한 호스트를 사용해야 한다."""
        self.assertIn("localhost:8011", self.coordinator.proxy_shell_url)
        self.assertIn("proxy.jsp", self.coordinator.proxy_shell_url)

    def test_nas_shell_url_uses_same_host(self):
        """⬛ [초기화] nas_shell_url은 stage2_url과 동일한 호스트를 사용해야 한다."""
        self.assertIn("localhost:8011", self.coordinator.nas_shell_url)
        self.assertIn("nasshell.jsp", self.coordinator.nas_shell_url)

    def test_default_password_is_glory(self):
        """⬛ [인증] 기본 비밀번호는 'glory'여야 한다."""
        self.assertEqual(self.coordinator.pwd, "glory")

    def test_custom_password_is_respected(self):
        """⬛ [인증] 커스텀 비밀번호가 올바르게 설정되어야 한다."""
        coordinator = LateralMovementCoordinator(self.stage2_url, pwd="custom_pass")
        self.assertEqual(coordinator.pwd, "custom_pass")


# ═══════════════════════════════════════════
# Test Suite 2: Base64 JSP 업로드 메서드
# SRP: _upload_jsp_via_echo 로직 검증
# ═══════════════════════════════════════════

class TestUploadJspViaEcho(unittest.TestCase):
    """
    [테스트 목적] _upload_jsp_via_echo가 올바른 Base64 인코딩 명령을 생성하는지 검증.
    실제 파일은 생성하지 않습니다.
    """

    def setUp(self):
        self.log = RCEScriptLog()
        self.coordinator = make_coordinator_with_fake_rce(self.log)

    def test_upload_sends_base64_encoded_command(self):
        """⬛ [인코딩] 업로드 명령은 Base64 인코딩 방식을 사용해야 한다."""
        self.coordinator._upload_jsp_via_echo("<% JSP_CONTENT %>", "/tmp/test.jsp")
        self.assertTrue(len(self.log.commands) > 0)
        # Base64 명령 형태 확인
        cmd = self.log.commands[0]
        self.assertIn("base64", cmd.lower())

    def test_upload_command_contains_target_path(self):
        """⬛ [경로] 업로드 명령은 목표 경로를 포함해야 한다."""
        target_path = "/usr/local/tomcat/webapps/ROOT/proxy.jsp"
        self.coordinator._upload_jsp_via_echo("<% TEST %>", target_path)
        cmd = self.log.commands[0]
        self.assertIn(target_path, cmd)

    def test_empty_jsp_content_still_executes(self):
        """⬛ [엣지케이스] 빈 JSP 콘텐츠도 명령을 실행해야 한다 (예외 없음)."""
        try:
            self.coordinator._upload_jsp_via_echo("", "/tmp/empty.jsp")
        except Exception as e:
            self.fail(f"빈 콘텐츠로 업로드 시 예외 발생: {e}")


# ═══════════════════════════════════════════
# Test Suite 3: TeamCity & Struts (Scenario 2)
# SRP: run_scenario2 흐름 검증
# ═══════════════════════════════════════════

class TestScenario2TeamcityStruts(unittest.TestCase):
    """
    [테스트 목적] Scenario 2 (TeamCity → Struts2 DB) 흐름에서
    - TeamCity 발견 시 올바른 URL이 설정되는지 검증합니다.
    - TeamCity를 찾지 못했을 때 조기 종료되는지 검증합니다.
    """

    def setUp(self):
        self.log = RCEScriptLog()
        self.coordinator = make_coordinator_with_fake_rce(self.log)

    def test_scenario2_finds_teamcity_when_port_open(self):
        """⬛ [성공경로] TeamCity 포트가 열려 있으면 teamcity_url이 설정되어야 한다."""
        # bash TCP 포트 체크가 OPEN 문자열 또는 빈 문자열(성공) 반환 시뮬레이션
        self.log.set_response("tcp/teamcity-server/8111", "OPEN")
        self.log.set_response("teamcity-server", "OPEN")
        self.coordinator.run_scenario2_teamcity_struts()
        # TeamCity URL이 설정되었는지 확인
        self.assertIsNotNone(self.coordinator.teamcity_url)

    def test_scenario2_early_exits_when_teamcity_not_found(self):
        """⬛ [실패경로] TeamCity가 없으면 나머지 단계를 실행하지 않아야 한다."""
        self.log.set_response("tcp/teamcity-server", "CLOSED")
        self.log.default_response = "CLOSED"
        result = self.coordinator.run_scenario2_teamcity_struts()
        # FAIL 메시지가 결과에 포함되어야 함
        self.assertIn("FAIL", result)

    def test_scenario2_executes_rce_at_least_once(self):
        """⬛ [협력] Scenario 2는 서버 탐색을 위해 최소 1회 RCE를 시도해야 한다."""
        self.log.default_response = "CLOSED"
        self.coordinator.run_scenario2_teamcity_struts()
        self.assertGreater(len(self.log.commands), 0)


# ═══════════════════════════════════════════
# Test Suite 4: NAS SMB (Scenario 3)
# SRP: run_scenario3 흐름 검증
# ═══════════════════════════════════════════

class TestScenario3NasSMB(unittest.TestCase):
    """
    [테스트 목적] Scenario 3 (NAS SMB 공격) 흐름에서
    - NAS 컨테이너 포트 탐색 명령이 실행되는지 검증합니다.
    - NAS를 찾지 못했을 때 올바르게 처리되는지 검증합니다.
    """

    def setUp(self):
        self.log = RCEScriptLog()
        self.coordinator = make_coordinator_with_fake_rce(self.log)

    def test_scenario3_checks_nas_reachability(self):
        """⬛ [탐색] Scenario 3는 NAS SMB 공격을 위해 RCE 명령을 최소 1회 실행해야 한다."""
        self.log.default_response = "CLOSED"
        result = self.coordinator.run_scenario3_nas_smb()
        # NAS 공격 시나리오는 JCIFS JAR 다운로드 후 RCE를 통해 파일 존재 확인
        # execute_rce가 최소 1회 호출되어야 함 (ls -la /tmp/*.jar)
        self.assertGreater(len(self.log.commands), 0, "Scenario 3는 최소 1회 RCE를 실행해야 합니다")

    def test_scenario3_returns_string_result(self):
        """⬛ [인터페이스] run_scenario3는 항상 문자열 결과를 반환해야 한다."""
        self.log.default_response = "CLOSED"
        result = self.coordinator.run_scenario3_nas_smb()
        self.assertIsInstance(result, str)

    def test_scenario3_fails_gracefully_when_nas_unavailable(self):
        """⬛ [견고성] NAS 접근 실패 시 예외가 아닌 실패 메시지를 반환해야 한다."""
        self.log.default_response = "CLOSED"
        try:
            result = self.coordinator.run_scenario3_nas_smb()
            self.assertIsInstance(result, str)
        except Exception as e:
            self.fail(f"NAS 미접근 시 예외 발생 (견고성 부족): {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Stage 3 Lateral Movement Unit Tests | CVE-2022-22965")
    print("  SOLID + Clean Architecture 설계 원칙 검증")
    print("=" * 60)
    unittest.main(verbosity=2)
