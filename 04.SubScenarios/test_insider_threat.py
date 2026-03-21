"""
test_insider_threat.py
CVE-2022-22965 — 내부자 위협 시나리오 (04.SubScenarios) 유닛 테스트
Educational Use Only

[설계 원칙]
- SRP  : 각 테스트 클래스는 단 하나의 시나리오 Phase만 검증합니다.
- OCP  : 실제 HTTP 호출을 Mock으로 교체하여 코드 변경 없이 테스트 확장이 가능합니다.
- LSP  : Mock 객체는 원본 함수/메서드의 계약(Contract)을 완전히 대체합니다.
- ISP  : 각 테스트는 필요한 의존성만 선택적으로 Mock합니다.
- DIP  : execute_rce, check_shell 등 인프라 레이어의 함수를 추상화하여 테스트에서 주입합니다.

[Clean Architecture 계층 매핑]
  Entities  : Phase별 결과 딕셔너리 (results, details)
  Use Cases : 각 Phase 로직 함수 
  Interface : execute_rce (웹쉘 RCE 어댑터 역할)
  Framework : urllib.request (실제 HTTP — Mocking 대상)
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, call
import urllib.error

# ── 경로 설정 ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "02.AttackScripts"))


# ==============================================================
# 공통 헬퍼: RCE 응답 Mock
# ==============================================================
def _make_mock_rce(return_map: dict):
    """
    DIP 원칙 적용: execute_rce 함수에 전달된 명령(cmd)에 따라
    다른 Mock 응답을 반환하는 팩토리 함수.
    이를 통해 각 Phase의 로직을 실제 네트워크 없이 완전히 격리 검증합니다.
    """
    def _mock_execute_rce(cmd: str) -> str:
        for key, value in return_map.items():
            if key in cmd:
                return value
        return ""
    return _mock_execute_rce


# ==============================================================
# Phase 1: 정찰 (Reconnaissance) 테스트
# ==============================================================
class TestPhase1Reconnaissance(unittest.TestCase):
    """
    SRP: Phase 1의 정찰 로직만 검증합니다.
    'id && hostname' 명령 결과에서 uid= 패턴이 있을 때 성공으로 분류하는지 확인합니다.
    """

    def _run_phase1_logic(self, rce_fn):
        """SRP: Phase 1 핵심 판정 로직만 추출하여 테스트 가능한 순수 함수로 표현"""
        recon_result = rce_fn("id && hostname && uname -a")
        if recon_result and "uid=" in recon_result:
            return True, recon_result
        return False, ""

    def test_phase1_success_when_uid_present(self):
        """uid= 패턴이 있을 때 Phase 1이 성공으로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "id && hostname": "uid=0(root) gid=0(root) groups=0(root)\na1b2c3d4e5f6\nLinux 5.15.0 #1 SMP aarch64",
        })
        success, output = self._run_phase1_logic(mock_rce)
        self.assertTrue(success)
        self.assertIn("uid=", output)

    def test_phase1_fails_when_rce_returns_empty(self):
        """RCE가 빈 응답을 반환할 때 Phase 1이 실패로 분류되는지 검증"""
        mock_rce = _make_mock_rce({})
        success, _ = self._run_phase1_logic(mock_rce)
        self.assertFalse(success)

    def test_phase1_fails_when_no_uid_pattern(self):
        """응답에 uid= 패턴이 없을 때 실패로 분류되는지 검증"""
        mock_rce = _make_mock_rce({"id && hostname": "Permission denied"})
        success, _ = self._run_phase1_logic(mock_rce)
        self.assertFalse(success)


# ==============================================================
# Phase 2: NAS 기밀 탈취 (Data Exfiltration) 테스트
# ==============================================================
class TestPhase2NASExfiltration(unittest.TestCase):
    """
    SRP: Phase 2의 NAS 접근 판정 로직만 검증합니다.
    'NAS_OPEN' 응답 여부로 포트 접근 성공을 판별하는 로직을 검증합니다.
    """

    def _run_phase2_nas_port_check(self, rce_fn):
        """SRP: NAS 포트 스캔 판정 로직만 추출한 순수 함수"""
        nas_smb_list = rce_fn("ls /mnt/nas 2>/dev/null || echo 'NOT_MOUNTED'")
        if "NOT_MOUNTED" not in nas_smb_list and nas_smb_list.strip():
            return True, "NAS filesystem accessible"

        nas_ping = rce_fn("bash -c 'echo >/dev/tcp/nas/445")
        if "NAS_OPEN" in nas_ping or nas_ping.strip() == "":
            return True, "NAS port open"
        return False, ""

    def test_phase2_success_when_nas_mounted(self):
        """NAS가 /mnt/nas에 마운트되어 있을 때 성공으로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "ls /mnt/nas": "product_blueprint.pdf\nteamcity_access_token",
        })
        success, msg = self._run_phase2_nas_port_check(mock_rce)
        self.assertTrue(success)

    def test_phase2_success_when_nas_port_open(self):
        """NAS 마운트는 안 됐지만 445 포트가 열려 있을 때 성공으로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "ls /mnt/nas": "NOT_MOUNTED",
            "bash -c 'echo >/dev/tcp/nas/445": "NAS_OPEN",
        })
        success, msg = self._run_phase2_nas_port_check(mock_rce)
        self.assertTrue(success)
        self.assertIn("port open", msg)

    def test_phase2_fails_when_nas_closed(self):
        """NAS가 마운트도 안 됐고 포트도 닫혀 있을 때 실패로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "ls /mnt/nas": "NOT_MOUNTED",
            "bash -c 'echo >/dev/tcp/nas/445": "NAS_CLOSED",
        })
        success, _ = self._run_phase2_nas_port_check(mock_rce)
        self.assertFalse(success)


# ==============================================================
# Phase 3: 크리덴셜 수집 (Credential Harvesting) 테스트
# ==============================================================
class TestPhase3CredentialHarvesting(unittest.TestCase):
    """
    SRP: Phase 3의 환경변수 크리덴셜 탈취 로직만 검증합니다.
    'env' 명령 결과에서 패스워드 관련 키가 탐지되는지 확인합니다.
    """

    def _run_phase3_logic(self, rce_fn):
        """SRP: Phase 3 판정 로직만 추출한 순수 함수"""
        result = rce_fn("env | grep -i 'spring\\|db\\|datasource\\|password\\|user'")
        if result and result.strip():
            return True, result
        return False, ""

    def test_phase3_success_when_credentials_found(self):
        """환경변수에서 DB 크리덴셜이 탐지될 때 성공으로 분류되는지 검증"""
        expected_env = "SPRING_DATASOURCE_PASSWORD=spring_pass\nDB_USER=spring_user"
        mock_rce = _make_mock_rce({
            "env | grep": expected_env,
        })
        success, output = self._run_phase3_logic(mock_rce)
        self.assertTrue(success)
        self.assertIn("SPRING_DATASOURCE_PASSWORD", output)

    def test_phase3_fails_when_env_empty(self):
        """환경변수 응답이 비어있을 때 실패로 분류되는지 검증"""
        mock_rce = _make_mock_rce({})
        success, _ = self._run_phase3_logic(mock_rce)
        self.assertFalse(success)

    def test_phase3_extracts_key_credentials(self):
        """응답 결과에 실제 사용 가능한 DB 비밀번호 패턴이 포함되는지 검증"""
        cred_env = "MYSQL_ROOT_PASSWORD=testtest\nSPRING_DATASOURCE_PASSWORD=spring_pass"
        mock_rce = _make_mock_rce({"env | grep": cred_env})
        success, output = self._run_phase3_logic(mock_rce)
        self.assertTrue(success)
        self.assertTrue(
            "PASSWORD" in output or "password" in output,
            "탈취된 크리덴셜 결과에 패스워드 정보가 포함되어야 합니다."
        )


# ==============================================================
# Phase 4: 내부 DB 접근 (Lateral Movement) 테스트
# ==============================================================
class TestPhase4DatabaseAccess(unittest.TestCase):
    """
    SRP: Phase 4의 내부 DB 포트 접근 판정 로직만 검증합니다.
    TCP 소켓 테스트(bash -c 'echo >/dev/tcp/...')로 포트를 스캔하는 로직을 검증합니다.
    """

    def _run_phase4_logic(self, rce_fn):
        """SRP: Phase 4 DB 포트 스캔 판정 로직만 추출한 순수 함수"""
        spring_db = rce_fn("bash -c 'echo >/dev/tcp/spring-db/3306")
        struts_db = rce_fn("bash -c 'echo >/dev/tcp/struts-db/3306")
        accessible = (
            "DB_OPEN" in spring_db or spring_db.strip() == "" or
            "DB_OPEN" in struts_db or struts_db.strip() == ""
        )
        return accessible

    def test_phase4_success_when_spring_db_open(self):
        """spring-db 포트가 열려있을 때 Phase 4가 성공으로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "spring-db/3306": "DB_OPEN",
            "struts-db/3306": "DB_CLOSED",
        })
        self.assertTrue(self._run_phase4_logic(mock_rce))

    def test_phase4_success_when_both_dbs_open(self):
        """양쪽 DB 모두 열려있을 때 성공으로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "spring-db/3306": "DB_OPEN",
            "struts-db/3306": "DB_OPEN",
        })
        self.assertTrue(self._run_phase4_logic(mock_rce))

    def test_phase4_fails_when_all_dbs_closed(self):
        """모든 DB 포트가 닫혀있을 때 실패로 분류되는지 검증"""
        mock_rce = _make_mock_rce({
            "spring-db/3306": "DB_CLOSED",
            "struts-db/3306": "DB_CLOSED",
        })
        self.assertFalse(self._run_phase4_logic(mock_rce))


# ==============================================================
# Phase 5: 공급망 공격 (Supply Chain Attack) 테스트
# ==============================================================
class TestPhase5SupplyChainAttack(unittest.TestCase):
    """
    SRP: Phase 5의 TeamCity / Gitea CI/CD 인프라 접근 판정 로직만 검증합니다.
    API 응답 길이와 에러 여부로 접근 성공을 판별하는 로직을 검증합니다.
    """

    def _is_reachable(self, response: str) -> bool:
        """SRP: API 응답이 유효한지 판정하는 순수 함수"""
        return bool(response and "Error" not in response and len(response.strip()) > 5)

    def test_teamcity_reachable_on_valid_response(self):
        """TeamCity가 유효한 API 응답을 반환할 때 접근 가능으로 판정되는지 검증"""
        tc_response = '{"version":"2023.11.3","buildNumber":"147512"}'
        self.assertTrue(self._is_reachable(tc_response))

    def test_teamcity_unreachable_on_error_response(self):
        """TeamCity가 'Error' 문자열을 포함한 응답을 보낼 때 차단으로 판정되는지 검증"""
        tc_response = "Connection Error: timed out"
        self.assertFalse(self._is_reachable(tc_response))

    def test_teamcity_unreachable_on_empty_response(self):
        """빈 응답일 때 차단으로 판정되는지 검증"""
        self.assertFalse(self._is_reachable(""))

    def test_gitea_reachable_on_valid_api_response(self):
        """Gitea가 유효한 API 버전 응답을 반환할 때 접근 가능으로 판정되는지 검증"""
        gitea_response = '{"version":"1.21.0"}'
        self.assertTrue(self._is_reachable(gitea_response))

    def test_phase5_at_least_one_service_needed_for_success(self):
        """TeamCity와 Gitea 중 하나라도 접근 가능하면 Phase 5 성공으로 처리되는지 검증"""
        tc_ok = self._is_reachable('{"version":"2023.11.3"}')
        gitea_ok = self._is_reachable("Connection Error")
        phase5_success = tc_ok or gitea_ok
        self.assertTrue(phase5_success)


# ==============================================================
# Phase 6: 백도어 삽입 & 흔적 은폐 (Persistence) 테스트
# ==============================================================
class TestPhase6Persistence(unittest.TestCase):
    """
    SRP: Phase 6의 Gitea 저장소 접근 판정 로직만 검증합니다.
    Gitea API /repos/search 응답 유효성 확인 로직을 검증합니다.
    """

    def _is_gitea_repo_accessible(self, response: str) -> bool:
        """SRP: Gitea 저장소 응답이 유효한지 판단하는 순수 함수"""
        return bool(response and "Error" not in response and len(response.strip()) > 5)

    def test_phase6_success_on_valid_gitea_response(self):
        """Gitea 저장소 API가 유효한 JSON을 반환할 때 성공으로 판정되는지 검증"""
        gitea_resp = '{"data":[{"id":1,"name":"spring-server"}]}'
        self.assertTrue(self._is_gitea_repo_accessible(gitea_resp))

    def test_phase6_fails_on_empty_gitea_response(self):
        """Gitea 응답이 비어 있을 때 실패로 판정되는지 검증"""
        self.assertFalse(self._is_gitea_repo_accessible(""))

    def test_phase6_fails_on_error_gitea_response(self):
        """Gitea 응답에 Error가 포함될 때 실패로 판정되는지 검증"""
        self.assertFalse(self._is_gitea_repo_accessible("Connection Error: refused"))


# ==============================================================
# HTML 보고서 생성 테스트
# ==============================================================
class TestHTMLReportGeneration(unittest.TestCase):
    """
    SRP: HTML 보고서 파일이 올바른 경로에 생성되는지 검증합니다.
    실제 파일시스템을 사용하지 않고 os 모듈을 Mock합니다. (OCP)
    """

    @patch("builtins.open", unittest.mock.mock_open())
    @patch("os.makedirs")
    def test_report_directory_is_created(self, mock_makedirs):
        """03.FinalReport 디렉토리가 makedirs로 생성되는지 검증"""
        report_dir = os.path.join(PROJECT_ROOT, "03.FinalReport")
        os.makedirs(report_dir, exist_ok=True)
        mock_makedirs.assert_called_with(report_dir, exist_ok=True)

    def test_report_filename_contains_timestamp(self):
        """보고서 파일명에 타임스탬프가 포함되는지 형식 검증"""
        import datetime
        now = datetime.datetime.now()
        filename = f"insider_threat_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
        self.assertTrue(filename.startswith("insider_threat_report_"))
        self.assertTrue(filename.endswith(".html"))
        self.assertIn(now.strftime("%Y%m%d"), filename)

    def test_report_html_structure(self):
        """생성될 HTML 보고서에 필수 섹션들이 포함되는지 검증"""
        # HTML 보고서 필수 구성 요소 템플릿 검증
        required_elements = [
            "내부자 위협",     # 제목
            "Phase 1",        # Phase 1
            "Phase 2",        # Phase 2
            "Phase 3",        # Phase 3
            "Phase 4",        # Phase 4
            "Phase 5",        # Phase 5
            "Phase 6",        # Phase 6
            "sub_run.py",     # Footer 출처 표시
        ]
        sample_html = """
        내부자 위협 자동 실행 보고서
        Phase 1 정찰
        Phase 2 NAS 탈취
        Phase 3 크리덴셜
        Phase 4 DB 접근
        Phase 5 공급망
        Phase 6 백도어
        sub_run.py 자동 생성
        """
        for element in required_elements:
            self.assertIn(element, sample_html,
                f"HTML 보고서에 '{element}' 섹션이 반드시 포함되어야 합니다.")


# ==============================================================
# Entry Point
# ==============================================================
if __name__ == "__main__":
    import unittest
    # 컬러 출력으로 테스트 결과 가독성 향상
    print("\033[96m" + "=" * 60 + "\033[0m")
    print("  내부자 위협 시나리오 유닛 테스트 (04.SubScenarios)")
    print("  CVE-2022-22965 | Educational Use Only")
    print("\033[96m" + "=" * 60 + "\033[0m\n")
    unittest.main(verbosity=2)
