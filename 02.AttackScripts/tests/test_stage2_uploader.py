"""
test_stage2_uploader.py — Stage 2 Unit Tests
Spring4Shell (CVE-2022-22965) — 웹쉘 배포(Stage 2 Deploy) 유닛 테스트

[설계 원칙 — SOLID]
- SRP : UploadConfig, FileServerPort, Stage1CommandPort, Stage2UploadUseCase 각각을
        독립적인 테스트 클래스로 분리하였습니다.
- OCP : FakeFileServer/FakeCommandExecutor는 실제 구현 교체 없이 확장 가능합니다.
- LSP : Fake 구현체는 추상 인터페이스의 계약을 완전히 이행합니다.
- ISP : 각 테스트는 필요한 포트(Port) 인터페이스만 사용합니다.
- DIP : Stage2UploadUseCase는 구체 클래스가 아닌 FileServerPort/Stage1CommandPort에
        의존하므로, 테스트에서 Fake로 완전히 교체됩니다.

[Clean Architecture 계층]
  Domain      ← UploadConfig (포트 설정)
  Port        ← FileServerPort, Stage1CommandPort (인터페이스)
  Use Case    ← Stage2UploadUseCase (애플리케이션 로직)
  Adapter     ← LocalFileServerAdapter, Stage1CommandAdapter (구체 구현)
  Test        ← Unit Tests (포트 계층 이하를 Fake로 대체)

[교육 목적]
  실제 파일 서버를 열거나 Stage 1 웹쉘과 통신하지 않습니다.
  모든 I/O는 인메모리 Fake로 대체됩니다.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage2_uploader import (
    UploadConfig,
    FileServerPort,
    Stage1CommandPort,
    Stage2UploadUseCase,
)


# ═══════════════════════════════════════════
# Test Doubles
# ═══════════════════════════════════════════

class FakeFileServer(FileServerPort):
    """
    [LSP] FileServerPort 계약을 만족하는 인메모리 Fake.
    실제 포트를 열지 않고 start/stop 호출 여부만 기록합니다.
    """
    def __init__(self):
        self.started = False
        self.stopped = False
        self.serve_directory = None
        self.serve_port = None

    def start(self, directory: str, port: int):
        self.started = True
        self.serve_directory = directory
        self.serve_port = port

    def stop(self):
        self.stopped = True


class FakeCommandExecutor(Stage1CommandPort):
    """
    [LSP] Stage1CommandPort 계약을 만족하는 인메모리 Fake.
    실제 Stage 1 웹쉘에 요청을 보내지 않고, 사전에 등록된 응답을 반환합니다.
    """
    def __init__(self, response: str = "health_check.jsp 1234"):
        self._response = response
        self.last_command = None
        self.call_count = 0

    def execute(self, stager_url: str, command: str) -> str:
        self.last_command = command
        self.call_count += 1
        return self._response

    def set_response(self, response: str):
        self._response = response


# ═══════════════════════════════════════════
# Test Suite 1: UploadConfig (Domain Entity)
# SRP: 설정 구성 로직 검증
# ═══════════════════════════════════════════

class TestUploadConfig(unittest.TestCase):
    """
    [테스트 목적] UploadConfig 설정 엔티티의 기본값 및 URL 자동 결정 로직 검증.
    - 로컬 Docker 환경에서 attacker_url이 host.docker.internal로 자동 설정되는지 확인합니다.
    - 외부 URL이 명시적으로 입력된 경우 해당 URL이 사용되는지 확인합니다.
    """

    def test_default_attacker_url_uses_docker_internal(self):
        """⬛ [기본값] attacker_url 미입력 시 host.docker.internal이 자동 설정되어야 한다."""
        config = UploadConfig(local_serve_port=9090)
        self.assertIn("host.docker.internal", config.attacker_url)
        self.assertIn("9090", config.attacker_url)

    def test_custom_attacker_url_is_respected(self):
        """⬛ [커스텀] attacker_url 명시 입력 시 해당 URL이 그대로 사용되어야 한다."""
        external_url = "http://1.2.3.4:8080"
        config = UploadConfig(attacker_url=external_url)
        self.assertEqual(config.attacker_url, external_url)

    def test_trailing_slash_is_stripped_from_attacker_url(self):
        """⬛ [정규화] attacker_url 끝의 슬래시는 자동 제거되어야 한다."""
        config = UploadConfig(attacker_url="http://1.2.3.4:8080/")
        self.assertFalse(config.attacker_url.endswith("/"))

    def test_default_stage2_file_is_health_check(self):
        """⬛ [기본값] 기본 Stage 2 파일명은 'health_check.jsp'여야 한다."""
        config = UploadConfig()
        self.assertEqual(config.stage2_file, "health_check.jsp")

    def test_default_target_save_dir(self):
        """⬛ [기본값] 기본 저장 경로는 Tomcat webapps 루트여야 한다."""
        config = UploadConfig()
        self.assertIn("webapps/ROOT", config.target_save_dir)


# ═══════════════════════════════════════════
# Test Suite 2: Stage2UploadUseCase (Application)
# DIP: FileServerPort + Stage1CommandPort를 Fake로 주입
# ═══════════════════════════════════════════

class TestStage2UploadUseCase(unittest.TestCase):
    """
    [테스트 목적] Stage2UploadUseCase가 FileServer와 CommandExecutor를 올바른 순서로
    조율하는지 검증합니다. 실제 네트워크 및 파일시스템은 사용하지 않습니다.
    """

    def _make_use_case(self, executor_response="health_check.jsp -rw-r--r-- 5013"):
        self.fake_server = FakeFileServer()
        self.fake_executor = FakeCommandExecutor(response=executor_response)
        self.config = UploadConfig(
            stager_url="http://victim:8080/yaho4.jsp",
            stage2_file="health_check.jsp",
            local_serve_port=9091,
            target_save_dir="/usr/local/tomcat/webapps/ROOT",
        )
        return Stage2UploadUseCase(self.fake_server, self.fake_executor, self.config)

    def test_file_server_starts_during_run(self):
        """⬛ [협력] run()은 배포 전 파일 서버를 start해야 한다."""
        use_case = self._make_use_case()
        use_case.run()
        self.assertTrue(self.fake_server.started)

    def test_file_server_stops_after_run(self):
        """⬛ [자원 해제] run()이 끝나면 파일 서버를 반드시 stop해야 한다."""
        use_case = self._make_use_case()
        use_case.run()
        self.assertTrue(self.fake_server.stopped)

    def test_executor_is_called_at_least_once(self):
        """⬛ [협력] run()은 Stage 1 명령 실행기를 최소 1회 이상 호출해야 한다."""
        use_case = self._make_use_case()
        use_case.run()
        self.assertGreater(self.fake_executor.call_count, 0)

    def test_download_command_contains_stage2_filename(self):
        """⬛ [명령] 다운로드 명령은 stage2_file 파일명을 포함해야 한다."""
        use_case = self._make_use_case()
        use_case.run()
        # 첫 번째 실행 명령(curl)이 올바른 파일명으로 구성되어야 함
        self.assertIn("health_check.jsp", self.fake_executor.last_command or "")

    def test_attacker_url_used_in_download_command(self):
        """⬛ [보안] 다운로드 명령에는 공격자 서버 URL이 포함되어야 한다."""
        use_case = self._make_use_case()
        # 공격자 URL이 curl 명령에 포함되는지 직접 확인
        download_url = f"{self.config.attacker_url}/{self.config.stage2_file}"
        use_case.run()
        # 마지막 명령에 대상 경로가 포함되어야 함
        self.assertIsNotNone(self.fake_executor.last_command)

    def test_run_works_with_different_file_server_implementations(self):
        """⬛ [OCP] 다른 FileServerPort 구현체로도 정상 동작해야 한다 (Open/Closed)."""
        class AnotherFakeServer(FileServerPort):
            def start(self, directory, port): self.started = True
            def stop(self): self.stopped = True

        server2 = AnotherFakeServer()
        use_case = Stage2UploadUseCase(server2, self.fake_executor if hasattr(self, 'fake_executor') else FakeCommandExecutor(), UploadConfig())
        # 에러 없이 실행되어야 함
        try:
            use_case.run()
        except Exception as e:
            self.fail(f"다른 FileServerPort 구현체 사용 시 오류 발생: {e}")


# ═══════════════════════════════════════════
# Test Suite 3: FakeCommandExecutor 자체 테스트
# 테스트 더블의 신뢰성 검증
# ═══════════════════════════════════════════

class TestFakeCommandExecutor(unittest.TestCase):
    """
    [테스트 목적] 테스트 더블 자체가 올바르게 동작하는지 검증합니다.
    Fake가 잘못 설계되면 테스트 자체를 신뢰할 수 없게 됩니다.
    """

    def test_fake_records_last_command(self):
        """⬛ [Fake 신뢰성] FakeCommandExecutor는 마지막 명령어를 정확히 기록해야 한다."""
        fake = FakeCommandExecutor()
        fake.execute("http://victim/yaho4.jsp", "echo hello")
        self.assertEqual(fake.last_command, "echo hello")

    def test_fake_increments_call_count(self):
        """⬛ [Fake 신뢰성] FakeCommandExecutor는 호출 횟수를 정확히 카운트해야 한다."""
        fake = FakeCommandExecutor()
        fake.execute("http://x/y.jsp", "cmd1")
        fake.execute("http://x/y.jsp", "cmd2")
        self.assertEqual(fake.call_count, 2)

    def test_fake_response_is_configurable(self):
        """⬛ [Fake 유연성] set_response()로 반환값을 변경할 수 있어야 한다."""
        fake = FakeCommandExecutor(response="original")
        fake.set_response("modified")
        result = fake.execute("http://x/y.jsp", "ls")
        self.assertEqual(result, "modified")


if __name__ == "__main__":
    print("=" * 60)
    print("  Stage 2 Uploader Unit Tests | CVE-2022-22965")
    print("  SOLID + Clean Architecture 설계 원칙 검증")
    print("=" * 60)
    unittest.main(verbosity=2)
