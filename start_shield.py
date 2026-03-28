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
     CCCCCC  YY  YY  BBBBB   EEEEE  RRRRR   
    CC       YY  YY  BB  BB  EE     RR  RR  
    CC        YYYY   BBBBB   EEEEE  RRRRR   
    CC         YY    BB  BB  EE     RR  RR  
     CCCCCC    YY    BBBBB   EEEEE  RR  RR  
    
     SSSSSS  HH  HH  IIIII  EEEEE  L      DDDD  
    SS       HH  HH   III   EE     L      D   D 
     SSSSSS  HHHHHH   III   EEEEE  L      D   D 
          SS HH  HH   III   EE     L      D   D 
     SSSSSS  HH  HH  IIIII  EEEEE  LLLLL  DDDD  
    {Colors.ENDC}"""
    print(ascii_art)
    print(f"      SL Factory Innovation | Cyber Security Attack-Range Simulator")
    print(f"      {'=' * 65}")

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
        print(f"  {Colors.OKCYAN}2.{Colors.ENDC} [Phase: Execute] 외부 해커 침투 (Main Scenario)")
        print(f"  {Colors.OKCYAN}3.{Colors.ENDC} [Phase: Deep-Dive] 내부자 위협 분석 (Sub Scenario)")
        print(f"  {Colors.OKCYAN}4.{Colors.ENDC} [Phase: Analyze] 결과 보고서 확인 (Reports)")
        print(f"  {Colors.OKCYAN}5.{Colors.ENDC} [Phase: Cleanup] 인프라 종료 (Docker Down)")
        print(f"  {Colors.OKCYAN}6.{Colors.ENDC} [System] 프로젝트 대시보드 (README)")
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
            open_latest_report()
            time.sleep(1)
        elif choice == '5':
            os.chdir("01.TestServer")
            try:
                subprocess.check_call(["docker", "compose", "down"])
            except:
                subprocess.call(["docker-compose", "down"])
            os.chdir("..")
            print(f"\n[OK] Infrastructure cleared.")
            time.sleep(2)
        elif choice == '6':
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
