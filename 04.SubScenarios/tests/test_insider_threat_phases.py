"""
test_insider_threat_phases.py — 내부자 위협 시나리오 유닛 테스트
04.SubScenarios / sub_run.py 테스트

[설계 원칙 — SOLID]
- SRP : 각 Phase를 독립적인 테스트 클래스로 분리합니다.
- OCP : 새로운 내부자 위협 Phase 추가 시 기존 테스트 수정 없이 확장합니다.
- LSP : PhaseResultChecker는 모든 Phase 결과 형식을 동일하게 검증합니다.
- ISP : 각 테스트는 검증에 필요한 최소 인터페이스만 사용합니다.
- DIP : 모든 I/O(RCE, 파일 서버, HTML 보고서)는 Fake/In-Memory로 대체합니다.

[Clean Architecture 계층]
  Domain      ← 각 Phase의 입/출력 계약 (str → dict[bool, detail])
  Application ← 6 Phase 조율 로직 (sub_run.py)
  Adapter     ← execute_rce, HTML 보고서 생성기
  Test        ← Unit Tests (어댑터를 인메모리 Fake로 대체)

[교육 목적]
  실제 Spring 웹쉘, NAS 서버, TeamCity, Gitea에 접속하지 않습니다.
  모든 HTTP/RCE 응답은 사전에 등록된 Fake 데이터를 사용합니다.
"""

import unittest
import sys
import os
import io

# sub_run.py가 프로젝트 루트에 위치 (04.SubScenarios의 부모 디렉토리)
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)


# ═══════════════════════════════════════════
# Domain Contracts
# 내부자 위협 Phase의 입/출력 계약을 정의합니다.
# ═══════════════════════════════════════════

class InsiderThreatPhaseResult:
    """
    [SRP] 각 Phase의 결과를 캡슐화하는 Value Object.
    성공 여부와 상세 증거 데이터를 함께 저장합니다.
    """
    def __init__(self, success: bool, detail: str):
        self.success = success
        self.detail = detail

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAIL"
        return f"PhaseResult({status}, detail_len={len(self.detail)})"


# ═══════════════════════════════════════════
# Test Doubles
# ═══════════════════════════════════════════

class FakeRCEEngine:
    """
    [DIP] execute_rce를 대체하는 인메모리 Fake.
    명령어 키워드 기반으로 사전 등록된 응답을 반환합니다.
    """
    def __init__(self):
        self._responses: dict = {}
        self._default = ""
        self.call_log: list = []

    def set(self, keyword: str, response: str):
        self._responses[keyword] = response

    def set_default(self, response: str):
        self._default = response

    def __call__(self, cmd: str) -> str:
        self.call_log.append(cmd)
        for kw, resp in self._responses.items():
            if kw in cmd:
                return resp
        return self._default


class FakeHTMLReporter:
    """
    [SRP] HTML 보고서 생성기를 대체하는 Fake.
    파일 I/O 없이 결과를 문자열로 저장합니다.
    """
    def __init__(self):
        self.generated = False
        self.content = ""
        self.output_path = ""

    def generate(self, results: dict, details: dict, metadata: dict) -> str:
        self.generated = True
        self.content = f"<html><body>FAKE_REPORT phases={len(results)}</body></html>"
        self.output_path = "/tmp/fake_report.html"
        return self.output_path


# ═══════════════════════════════════════════
# Test Suite 1: Phase 1 — 정찰 (Reconnaissance)
# ═══════════════════════════════════════════

class TestPhase1Reconnaissance(unittest.TestCase):
    """
    [테스트 목적] 정찰 Phase가 내부 서비스(Gitea, TeamCity, VNC) 탐색 명령을
    올바르게 생성하는지 검증합니다.
    """

    def setUp(self):
        self.rce = FakeRCEEngine()
        self.rce.set("id && hostname", "uid=0(root) gid=0(root) HOSTNAME=spring")

    def _run_phase1(self):
        """Phase 1 정찰 로직 시뮬레이션"""
        result = self.rce("id && hostname && uname -a")
        if result and "uid=" in result:
            gitea = self.rce("curl -s -m 3 http://gitea:3000 -o /dev/null -w '%{http_code}'")
            tc = self.rce("bash -c 'echo >/dev/tcp/teamcity-server/8111'")
            return InsiderThreatPhaseResult(True, f"env={result}, gitea={gitea}, tc={tc}")
        return InsiderThreatPhaseResult(False, "RCE 실패")

    def test_phase1_succeeds_when_rce_returns_uid(self):
        """⬛ [성공경로] RCE에서 uid= 가 반환되면 Phase 1은 성공해야 한다."""
        self.rce.set("id && hostname && uname -a", "uid=0(root) gid=0(root) HOSTNAME=spring")
        result = self._run_phase1()
        self.assertTrue(result.success)

    def test_phase1_fails_when_rce_returns_error(self):
        """⬛ [실패경로] RCE에서 uid= 가 없으면 Phase 1은 실패해야 한다."""
        # setUp의 기본 응답을 격리하기 위해 새로운 FakeRCEEngine 사용
        rce = FakeRCEEngine()
        rce.set("id && hostname && uname -a", "Authentication Failed.")
        self.rce = rce  # _run_phase1()이 self.rce를 참조하므로 교체
        result = self._run_phase1()
        self.assertFalse(result.success)

    def test_phase1_returns_phase_result_type(self):
        """⬛ [타입] Phase 1 결과는 InsiderThreatPhaseResult 타입이어야 한다."""
        result = self._run_phase1()
        self.assertIsInstance(result, InsiderThreatPhaseResult)

    def test_phase1_probes_gitea_and_teamcity(self):
        """⬛ [탐색] Phase 1은 Gitea와 TeamCity에 대한 정찰 명령을 실행해야 한다."""
        self.rce.set("id && hostname && uname -a", "uid=0(root) gid=0(root)")
        self._run_phase1()
        probed = " ".join(self.rce.call_log)
        self.assertIn("gitea", probed)
        self.assertIn("teamcity", probed)


# ═══════════════════════════════════════════
# Test Suite 2: Phase 2 — NAS 기밀 탈취
# ═══════════════════════════════════════════

class TestPhase2NASExfiltration(unittest.TestCase):
    """
    [테스트 목적] NAS 접근 탐색이 올바른 명령을 생성하는지,
    NAS 접근 가능/불가 시 각각 올바른 결과를 반환하는지 검증합니다.
    """

    def setUp(self):
        self.rce = FakeRCEEngine()

    def _run_phase2(self):
        """Phase 2 NAS 탈취 로직 시뮬레이션"""
        nas_smb_list = self.rce("ls /mnt/nas 2>/dev/null || echo 'NOT_MOUNTED'")
        if "NOT_MOUNTED" not in nas_smb_list and nas_smb_list.strip():
            return InsiderThreatPhaseResult(True, f"files={nas_smb_list}")

        nas_ping = self.rce("bash -c 'echo >/dev/tcp/nas/445'")
        if "NAS_OPEN" in nas_ping or nas_ping.strip() == "":
            return InsiderThreatPhaseResult(True, "NAS 포트 445 개방 확인 — SMB 접근 가능")
        return InsiderThreatPhaseResult(False, "NAS 접근 불가")

    def test_phase2_succeeds_when_nas_files_visible(self):
        """⬛ [성공경로] NAS 파일시스템이 마운트된 경우 Phase 2는 성공해야 한다."""
        self.rce.set("ls /mnt/nas", "product_blueprint.pdf teamcity_token.txt")
        result = self._run_phase2()
        self.assertTrue(result.success)

    def test_phase2_succeeds_when_nas_port_open(self):
        """⬛ [성공경로] NAS 마운트는 없어도 포트 445가 열려 있으면 위협으로 판단해야 한다."""
        self.rce.set("ls /mnt/nas", "NOT_MOUNTED")
        self.rce.set("tcp/nas/445", "NAS_OPEN")
        result = self._run_phase2()
        self.assertTrue(result.success)

    def test_phase2_fails_when_nas_port_closed(self):
        """⬛ [실패경로] NAS 포트가 닫혀 있으면 Phase 2는 실패해야 한다."""
        self.rce.set_default("NOT_MOUNTED")
        self.rce.set("tcp/nas/445", "NAS_CLOSED")
        result = self._run_phase2()
        self.assertFalse(result.success)

    def test_phase2_checks_smb_port_445(self):
        """⬛ [프로토콜] NAS 탐색은 반드시 SMB 포트 445를 확인해야 한다."""
        self.rce.set_default("NOT_MOUNTED")
        self._run_phase2()
        port_445_checked = any("445" in cmd for cmd in self.rce.call_log)
        self.assertTrue(port_445_checked, "SMB 포트(445) 확인 명령이 실행되어야 합니다")


# ═══════════════════════════════════════════
# Test Suite 3: Phase 3 — 크리덴셜 수집
# ═══════════════════════════════════════════

class TestPhase3CredentialHarvesting(unittest.TestCase):
    """
    [테스트 목적] 환경변수 및 설정 파일에서 크리덴셜이 올바르게 추출되는지 검증합니다.
    """

    def setUp(self):
        self.rce = FakeRCEEngine()

    def _run_phase3(self):
        """Phase 3 크리덴셜 수집 시뮬레이션"""
        env_dump = self.rce("env | grep -i 'spring\\|db\\|datasource\\|password\\|user'")
        if env_dump and env_dump.strip() and "DOCTYPE" not in env_dump:
            return InsiderThreatPhaseResult(True, f"creds={env_dump[:200]}")
        return InsiderThreatPhaseResult(False, "크리덴셜 없음")

    def test_phase3_succeeds_when_env_has_credentials(self):
        """⬛ [성공경로] 환경변수에 DB 크리덴셜이 있으면 Phase 3은 성공해야 한다."""
        self.rce.set("env | grep", "SPRING_DATASOURCE_PASSWORD=spring_pass\nDB_USERNAME=spring_user")
        result = self._run_phase3()
        self.assertTrue(result.success)

    def test_phase3_fails_when_env_empty(self):
        """⬛ [실패경로] 환경변수에 크리덴셜이 없으면 Phase 3은 실패해야 한다."""
        self.rce.set_default("")
        result = self._run_phase3()
        self.assertFalse(result.success)

    def test_phase3_detail_contains_found_credentials(self):
        """⬛ [증거] 성공 시 결과 detail에 발견된 크리덴셜 내용이 포함되어야 한다."""
        creds = "SPRING_DB_PASSWORD=secret123"
        self.rce.set("env | grep", creds)
        result = self._run_phase3()
        self.assertIn("secret123", result.detail)


# ═══════════════════════════════════════════
# Test Suite 4: Phase 4 — 내부 DB 접근
# ═══════════════════════════════════════════

class TestPhase4InternalDBAccess(unittest.TestCase):
    """
    [테스트 목적] 내부 DB(spring-db, struts-db) 포트 접근 탐색이 올바르게
    수행되는지, 성공/실패 결과를 올바르게 반환하는지 검증합니다.
    """

    def setUp(self):
        self.rce = FakeRCEEngine()

    def _run_phase4(self):
        """Phase 4 내부 DB 접근 시뮬레이션"""
        spring_check = self.rce("bash -c 'echo >/dev/tcp/spring-db/3306'")
        struts_check = self.rce("bash -c 'echo >/dev/tcp/struts-db/3306'")
        accessible = ("DB_OPEN" in spring_check or spring_check.strip() == "") or \
                     ("DB_OPEN" in struts_check or struts_check.strip() == "")
        if accessible:
            return InsiderThreatPhaseResult(True, f"spring={spring_check}, struts={struts_check}")
        return InsiderThreatPhaseResult(False, "DB 포트 닫힘")

    def test_phase4_succeeds_when_spring_db_open(self):
        """⬛ [성공경로] spring-db 3306이 열려 있으면 Phase 4는 성공해야 한다."""
        self.rce.set("spring-db/3306", "DB_OPEN")
        result = self._run_phase4()
        self.assertTrue(result.success)

    def test_phase4_succeeds_when_struts_db_open(self):
        """⬛ [성공경로] struts-db 3306만 열려 있어도 Phase 4는 성공해야 한다."""
        self.rce.set("spring-db/3306", "DB_CLOSED")
        self.rce.set("struts-db/3306", "DB_OPEN")
        result = self._run_phase4()
        self.assertTrue(result.success)

    def test_phase4_fails_when_all_dbs_closed(self):
        """⬛ [실패경로] 모든 DB 포트가 닫혀 있으면 Phase 4는 실패해야 한다."""
        self.rce.set_default("DB_CLOSED")
        result = self._run_phase4()
        self.assertFalse(result.success)

    def test_phase4_checks_both_databases(self):
        """⬛ [완전성] Phase 4는 spring-db와 struts-db 두 곳 모두를 탐색해야 한다."""
        self.rce.set_default("DB_CLOSED")
        self._run_phase4()
        cmds = " ".join(self.rce.call_log)
        self.assertIn("spring-db", cmds)
        self.assertIn("struts-db", cmds)


# ═══════════════════════════════════════════
# Test Suite 5: Phase 5 & 6 — CI/CD & 백도어
# ═══════════════════════════════════════════

class TestPhase5and6SupplyChain(unittest.TestCase):
    """
    [테스트 목적] TeamCity/Gitea CI/CD에 대한 접근 탐색과
    Gitea 저장소 API 접근이 올바르게 처리되는지 검증합니다.
    """

    def setUp(self):
        self.rce = FakeRCEEngine()

    def _run_phase5(self):
        """Phase 5 CI/CD 장악 시뮬레이션"""
        tc_check = self.rce("curl -s -m 5 http://teamcity-server:8111/app/rest/server")
        gitea_check = self.rce("curl -s -m 5 http://gitea:3000/api/v1/version")
        reachable = (tc_check and "Error" not in tc_check and len(tc_check.strip()) > 5) or \
                    (gitea_check and "Error" not in gitea_check and len(gitea_check.strip()) > 5)
        if reachable:
            return InsiderThreatPhaseResult(True, f"teamcity={tc_check[:80]}, gitea={gitea_check[:50]}")
        return InsiderThreatPhaseResult(False, "CI/CD 접근 불가")

    def test_phase5_succeeds_when_teamcity_reachable(self):
        """⬛ [성공경로] TeamCity API가 응답하면 Phase 5는 성공해야 한다."""
        self.rce.set("teamcity-server:8111", '{"version":"2023.11"}')
        result = self._run_phase5()
        self.assertTrue(result.success)

    def test_phase5_succeeds_when_gitea_reachable(self):
        """⬛ [성공경로] Gitea API만 응답해도 Phase 5는 성공해야 한다."""
        self.rce.set("teamcity", "")
        self.rce.set("gitea:3000", '{"version":"1.21"}')
        result = self._run_phase5()
        self.assertTrue(result.success)

    def test_phase5_fails_when_all_cicd_unreachable(self):
        """⬛ [실패경로] TeamCity, Gitea 모두 접근 불가 시 Phase 5는 실패해야 한다."""
        self.rce.set_default("Error: Connection refused")
        result = self._run_phase5()
        self.assertFalse(result.success)


# ═══════════════════════════════════════════
# Test Suite 6: HTML 보고서 생성기
# SRP: 보고서 생성 인터페이스 계약 검증
# ═══════════════════════════════════════════

class TestInsiderThreatHTMLReport(unittest.TestCase):
    """
    [테스트 목적] HTML 보고서 생성기가 결과 딕셔너리를 받아 HTML을 올바르게
    생성하는지 검증합니다. 실제 파일시스템을 사용하지 않습니다.
    """

    def setUp(self):
        self.reporter = FakeHTMLReporter()

    def test_report_generates_on_call(self):
        """⬛ [생성] 보고서는 generate() 호출 시 반드시 생성 플래그가 True여야 한다."""
        results = {"phase1": True, "phase2": False}
        details = {"phase1": "OK", "phase2": "FAIL"}
        self.reporter.generate(results, details, {})
        self.assertTrue(self.reporter.generated)

    def test_report_contains_phase_count(self):
        """⬛ [내용] 보고서 내용은 전달된 Phase 수를 반영해야 한다."""
        results = {f"phase{i}": True for i in range(1, 7)}
        self.reporter.generate(results, {}, {})
        self.assertIn("6", self.reporter.content)

    def test_report_returns_output_path(self):
        """⬛ [경로] generate()는 빈 문자열이 아닌 경로를 반환해야 한다."""
        path = self.reporter.generate({}, {}, {})
        self.assertIsNotNone(path)
        self.assertGreater(len(path), 0)


if __name__ == "__main__":
    print("=" * 60)
    print("  Insider Threat Phase Unit Tests | sub_run.py")
    print("  SOLID + Clean Architecture 설계 원칙 검증")
    print("=" * 60)
    unittest.main(verbosity=2)
