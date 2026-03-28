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
    # Bold ASCII variant as requested by the user
    ascii_art = f"""
    {Colors.OKCYAN}{Colors.BOLD}
     ██████  ██    ██ ██████  ███████ ██████      ███████ ██   ██ ██ ███████ ██      ██████  
    ██       ██    ██ ██   ██ ██      ██   ██     ██      ██   ██ ██ ██      ██      ██   ██ 
    ██        ██  ██  ██████  █████   ██████      ███████ ███████ ██ █████   ██      ██   ██ 
    ██         ████   ██   ██ ██      ██   ██          ██ ██   ██ ██ ██      ██      ██   ██ 
     ██████     ██    ██████  ███████ ██   ██     ███████ ██   ██ ██ ███████ ███████ ██████  
    {Colors.ENDC}"""
    print(ascii_art)
    print(f"      {Colors.BOLD}SL Factory Innovation | Cyber Security Attack-Range Simulator{Colors.ENDC}")
    print(f"      {'=' * 75}")

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
        print(f"\n[!] 생성된 보고서가 없습니다.")
        return
    
    latest = max(reports, key=os.path.getctime)
    print(f"\n[*] 최신 보고서를 엽니다: {os.path.basename(latest)}")
    
    if sys.platform == "darwin":
        subprocess.call(["open", latest])
    elif sys.platform == "win32":
        os.startfile(latest)
    else:
        subprocess.call(["xdg-open", latest])

def run_script(script_name):
    print(f"\n[*] Starting {script_name}...")
    try:
        subprocess.call([sys.executable, script_name])
    except KeyboardInterrupt:
        print(f"\n[!] Simulation interrupted by user.")

def main():
    while True:
        clear_screen()
        print_header()
        
        docker_active = check_docker()
        status_text = f"{Colors.OKGREEN}[RUNNING]{Colors.ENDC}" if docker_active else f"{Colors.FAIL}[NOT FOUND]{Colors.ENDC}"
        print(f"  System Status: {status_text}")
        
        print(f"\n  Select Simulation Phase:")
        print(f"  {Colors.OKCYAN}1.{Colors.ENDC} [Phase: Setup] 인프라 구축 (Docker Up)")
        print(f"  {Colors.OKCYAN}2.{Colors.ENDC} [Phase: Main] 외부 해커 침투 (Spring4Shell)")
        print(f"  {Colors.OKCYAN}3.{Colors.ENDC} [Phase: Inside] 내부자 위협 데이터 유출 (Insider Threat)")
        print(f"  {Colors.OKCYAN}4.{Colors.ENDC} [Phase: Advanced] 패치 우회 및 워터홀 공격 (Advanced Bypass)")
        print(f"  {Colors.OKCYAN}5.{Colors.ENDC} [Phase: Analyze] 결과 보고서 확인 (Reports)")
        print(f"  {Colors.OKCYAN}6.{Colors.ENDC} [Phase: Cleanup] 인프라 종료 (Docker Down)")
        print(f"  {Colors.OKCYAN}7.{Colors.ENDC} [System] 프로젝트 대시보드 (README)")
        print(f"  {Colors.WARNING}q.{Colors.ENDC} 종료 (Quit)")

        choice = input(f"\n  Choice > ").lower()

        if choice == '1':
            os.chdir("01.TestServer")
            try:
                subprocess.check_call(["docker", "compose", "up", "-d"])
            except:
                subprocess.call(["docker-compose", "up", "-d"])
            os.chdir("..")
            print(f"\n[OK] Infrastructure booted. Waiting for nodes...")
            time.sleep(3)
        elif choice == '2':
            run_script("run.py")
            input(f"\nPress Enter to continue...")
        elif choice == '3':
            run_script("sub_run.py")
            input(f"\nPress Enter to continue...")
        elif choice == '4':
            # Implementing new scenario based on 서브시나리오2.md
            if os.path.exists("scenario3_run.py"):
                run_script("scenario3_run.py")
            else:
                print(f"\n[!] Scenario 3 script not found. Creating it...")
                time.sleep(1)
            input(f"\nPress Enter to continue...")
        elif choice == '5':
            open_latest_report()
            time.sleep(1)
        elif choice == '6':
            os.chdir("01.TestServer")
            try:
                subprocess.check_call(["docker", "compose", "down"])
            except:
                subprocess.call(["docker-compose", "down"])
            os.chdir("..")
            print(f"\n[OK] Infrastructure cleared.")
            time.sleep(2)
        elif choice == '7':
            if sys.platform == "darwin":
                subprocess.call(["open", "README.md"])
            else:
                print(f"[*] Open README.md in your editor.")
                time.sleep(2)
        elif choice == 'q':
            print(f"\nExiting SL Cyber-Shield Simulator.")
            break
        else:
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
