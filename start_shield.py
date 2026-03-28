import os
import sys
import time
import subprocess
import platform

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}   SL Cyber-Shield: Industrial Security Attack-Range Simulator{Colors.ENDC}")
    print(f"{Colors.OKCYAN}   Unified Control Center for SDF-IP Verification{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.ENDC}")

def check_docker():
    try:
        subprocess.check_output(["docker", "info"], stderr=subprocess.STDOUT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_script(script_name):
    print(f"\n{Colors.OKBLUE}[*] Starting {script_name}...{Colors.ENDC}")
    try:
        # Run with the same python interpreter
        subprocess.call([sys.executable, script_name])
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[!] Simulation interrupted by user.{Colors.ENDC}")

def main():
    while True:
        clear_screen()
        print_header()
        
        print(f"\n  {Colors.BOLD}시스템 상태 확인:{Colors.ENDC}")
        docker_active = check_docker()
        if docker_active:
            print(f"  - Docker Desktop: {Colors.OKGREEN}[RUNNING]{Colors.ENDC}")
        else:
            print(f"  - Docker Desktop: {Colors.FAIL}[NOT FOUND]{Colors.ENDC}")
            print(f"    {Colors.WARNING}주의: 시뮬레이션 서버(01.TestServer)가 작동하지 않을 수 있습니다.{Colors.ENDC}")

        print(f"\n  {Colors.BOLD}실행 옵션을 선택하세요:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}1.{Colors.ENDC} [Main] 외부 해커 취약점 체이닝 (run.py)")
        print(f"  {Colors.OKCYAN}2.{Colors.ENDC} [Sub] 내부자 위협 & 공급망 공격 (sub_run.py)")
        print(f"  {Colors.OKCYAN}3.{Colors.ENDC} 테스트 서버 환경 구축 (Docker Compose Up)")
        print(f"  {Colors.OKCYAN}4.{Colors.ENDC} 테스트 서버 환경 종료 (Docker Compose Down)")
        print(f"  {Colors.WARNING}q.{Colors.ENDC} 종료 (Quit)")

        choice = input(f"\n  {Colors.BOLD}Choice > {Colors.ENDC}").lower()

        if choice == '1':
            run_script("run.py")
            input(f"\n{Colors.OKBLUE}계속하려면 Enter를 누르세요...{Colors.ENDC}")
        elif choice == '2':
            run_script("sub_run.py")
            input(f"\n{Colors.OKBLUE}계속하려면 Enter를 누르세요...{Colors.ENDC}")
        elif choice == '3':
            print(f"\n{Colors.OKBLUE}[*] 인프라를 구축 중입니다 (01.TestServer)...{Colors.ENDC}")
            os.chdir("01.TestServer")
            subprocess.call(["docker-compose", "up", "-d"])
            os.chdir("..")
            print(f"{Colors.OKGREEN}[OK] 인프라 부팅 완료. 잠시 대기 후 시뮬레이션을 시작하세요.{Colors.ENDC}")
            time.sleep(3)
        elif choice == '4':
            print(f"\n{Colors.WARNING}[*] 인프라를 제거 중입니다...{Colors.ENDC}")
            os.chdir("01.TestServer")
            subprocess.call(["docker-compose", "down"])
            os.chdir("..")
            print(f"{Colors.OKGREEN}[OK] 인프라 정리 완료.{Colors.ENDC}")
            time.sleep(2)
        elif choice == 'q':
            print(f"\n{Colors.OKCYAN}SL Cyber-Shield를 종료합니다. 안녕히 가십시오.{Colors.ENDC}")
            break
        else:
            print(f"\n{Colors.FAIL}[ERROR] 잘못된 선택입니다.{Colors.ENDC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.OKCYAN}SL Cyber-Shield를 강제 종료합니다.{Colors.ENDC}")
        sys.exit(0)
