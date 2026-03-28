import os
import sys
import time
import subprocess
import glob

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
    ascii_art = f"""
    {Colors.OKCYAN}{Colors.BOLD}
     ██████╗██╗   ██╗██████╗ ███████╗██████╗ 
    ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗
    ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝
    ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗
    ╚██████╗   ██║   ██████╔╝███████╗██║  ██║
     ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝
    
     ███████╗██╗  ██╗██╗███████╗██╗     ██████╗ 
     ██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗
     ███████╗███████║██║█████╗  ██║     ██║  ██║
     ╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║
     ███████║██║  ██║██║███████╗███████╗██████╔╝
     ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝
    {Colors.ENDC}"""
    print(ascii_art)
    print(f"      {Colors.OKBLUE}SL Factory Innovation | Cyber Security Attack-Range{Colors.ENDC}")
    print(f"      {Colors.HEADER}{'=' * 55}{Colors.ENDC}")

def check_docker():
    try:
        subprocess.check_output(["docker", "info"], stderr=subprocess.STDOUT)
        return True
    except:
        return False

def open_latest_report():
    report_dir = "03.FinalReport"
    reports = glob.glob(os.path.join(report_dir, "*.html"))
    if not reports:
        print(f"\n{Colors.WARNING}[!] 생성된 보고서가 없습니다.{Colors.ENDC}")
        return
    
    latest = max(reports, key=os.path.getctime)
    print(f"\n{Colors.OKGREEN}[*] 최신 보고서를 엽니다: {os.path.basename(latest)}{Colors.ENDC}")
    
    if sys.platform == "darwin":
        subprocess.call(["open", latest])
    elif sys.platform == "win32":
        os.startfile(latest)
    else:
        subprocess.call(["xdg-open", latest])

def run_script(script_name):
    print(f"\n{Colors.OKBLUE}[*] Starting {script_name}...{Colors.ENDC}")
    try:
        subprocess.call([sys.executable, script_name])
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[!] Simulation interrupted by user.{Colors.ENDC}")

def main():
    while True:
        clear_screen()
        print_header()
        
        docker_active = check_docker()
        status_text = f"{Colors.OKGREEN}[RUNNING]{Colors.ENDC}" if docker_active else f"{Colors.FAIL}[NOT FOUND]{Colors.ENDC}"
        print(f"  {Colors.BOLD}Infrastructure Status:{Colors.ENDC} {status_text}")
        
        print(f"\n  {Colors.BOLD}Select Simulation Option:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}1.{Colors.ENDC} [Main] 외부 해커 침투 (Spring4Shell Chain)")
        print(f"  {Colors.OKCYAN}2.{Colors.ENDC} [Sub] 내부자 위협 & 공급망 공격 (Insider Threat)")
        print(f"  {Colors.OKCYAN}3.{Colors.ENDC} 인프라 구축 (Docker Up)")
        print(f"  {Colors.OKCYAN}4.{Colors.ENDC} 인프라 종료 (Docker Down)")
        print(f"  {Colors.OKBLUE}5.{Colors.ENDC} {Colors.BOLD}결과 보고서 브라우징 (Browse Reports){Colors.ENDC}")
        print(f"  {Colors.OKBLUE}6.{Colors.ENDC} 프로젝트 대시보드 (README View)")
        print(f"  {Colors.WARNING}q.{Colors.ENDC} 종료 (Quit)")

        choice = input(f"\n  {Colors.BOLD}Choice > {Colors.ENDC}").lower()

        if choice == '1':
            run_script("run.py")
            input(f"\n{Colors.OKBLUE}Press Enter to continue...{Colors.ENDC}")
        elif choice == '2':
            run_script("sub_run.py")
            input(f"\n{Colors.OKBLUE}Press Enter to continue...{Colors.ENDC}")
        elif choice == '3':
            os.chdir("01.TestServer")
            try:
                # Try Docker Compose V2 first
                subprocess.check_call(["docker", "compose", "up", "-d"])
            except:
                # Fallback to Docker Compose V1
                subprocess.call(["docker-compose", "up", "-d"])
            os.chdir("..")
            print(f"{Colors.OKGREEN}[OK] Booting complete.{Colors.ENDC}")
            time.sleep(2)
        elif choice == '4':
            os.chdir("01.TestServer")
            try:
                subprocess.check_call(["docker", "compose", "down"])
            except:
                subprocess.call(["docker-compose", "down"])
            os.chdir("..")
            print(f"{Colors.OKGREEN}[OK] Infrastructure cleared.{Colors.ENDC}")
            time.sleep(2)
        elif choice == '5':
            open_latest_report()
            time.sleep(1)
        elif choice == '6':
            if sys.platform == "darwin":
                subprocess.call(["open", "README.md"])
            else:
                print(f"{Colors.OKBLUE}[*] README.md 파일을 텍스트 에디터로 확인하세요.{Colors.ENDC}")
                time.sleep(2)
        elif choice == 'q':
            print(f"\n{Colors.OKCYAN}SL Cyber-Shield를 종료합니다.{Colors.ENDC}")
            break
        else:
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
